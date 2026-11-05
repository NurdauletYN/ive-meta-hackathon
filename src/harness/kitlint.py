"""Find generated screens that bypass the kit (raw Material widgets, hardcoded colors).

Used for one polish pass before the gate, so apps look designed instead of stock Material.
"""

from __future__ import annotations

import re
from pathlib import Path

_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bListTile\s*\("), "ListTile: use ListSection + ListRow, or ItemCard"),
    (re.compile(r"\bCircleAvatar\s*\("), "CircleAvatar: use KitPhotoTile or an emoji in ListRow"),
    (re.compile(r"\bFilterChip\s*\("), "FilterChip: use ChipRow"),
    (re.compile(r"(?<![A-Za-z])Card\s*\("), "Card: use ItemCard, ProductCard, or ListSection"),
    (re.compile(r"(?<![A-Za-z])AppBar\s*\("), "AppBar: RocketScaffold(title:) already provides it"),
    (re.compile(r"(?<![A-Za-z])Scaffold\s*\("), "Scaffold: use RocketScaffold"),
    (re.compile(r"Image\.network"), "Image.network: use KitPhoto keys only"),
    (re.compile(r"\bColor\s*\(\s*0x"), "hardcoded Color(0x...): use Theme.of(context).colorScheme"),
    (re.compile(r"\bColors\.(?!transparent)\w+"), "Colors.*: use Theme.of(context).colorScheme"),
)


def rewrite_raw_material(project: Path) -> int:
    """Deterministic v0-style autofix: swap stock Material chrome for kit names. Never invent layout."""
    root = project / "lib" / "app" / "features"
    if not root.is_dir():
        return 0
    changed = 0
    for path in root.rglob("*.dart"):
        text = path.read_text(encoding="utf-8")
        new = re.sub(r"(?<![A-Za-z])Scaffold\s*\(", "RocketScaffold(", text)
        new = re.sub(r"appBar:\s*AppBar\((?:[^()]|\([^()]*\))*\)\s*,", "", new)
        new = re.sub(r"\bListTile\s*\(", "ListRow(", new)
        new = re.sub(r"\bFilterChip\s*\(", "InputChip(", new)
        new = new.replace("Navigator.push(", "context.go(")
        new = new.replace("MaterialPageRoute(", "(")
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def kit_violations(project: Path, *, limit: int = 8) -> list[str]:
    """`path:line message` for each raw-widget use under lib/app/features."""
    root = project / "lib" / "app" / "features"
    found: list[str] = []
    if not root.is_dir():
        return found
    for path in sorted(root.rglob("*.dart")):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(project).as_posix()
        for pattern, message in _RULES:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                found.append(f"{rel}:{line} {message}")
                if len(found) >= limit:
                    return found
    return found
