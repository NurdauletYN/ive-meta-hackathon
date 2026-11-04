"""Pairwise structural similarity of lib/app across generated apps. Report only."""

from __future__ import annotations

import re
from itertools import combinations
from pathlib import Path
from typing import Any

_STRING = re.compile(r"'''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\"|'[^'\\]*'|\"[^\"\\]*\"")
_NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")
_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _project_root(path: Path) -> Path | None:
    if (path / "lib" / "app").is_dir():
        return path
    nested = path / "project"
    if (nested / "lib" / "app").is_dir():
        return nested
    return None


def iter_projects(glob_pat: str, *, cwd: Path | None = None) -> list[Path]:
    base = cwd or Path(".")
    found: list[Path] = []
    for match in sorted(base.glob(glob_pat)):
        root = _project_root(match)
        if root is not None:
            found.append(root)
    return found


def app_tokens(project: Path) -> list[str]:
    app = project / "lib" / "app"
    if not app.is_dir():
        return []
    parts: list[str] = []
    for dart in sorted(app.rglob("*.dart")):
        text = dart.read_text(encoding="utf-8", errors="replace")
        text = _STRING.sub(" ", text)
        text = _NUMBER.sub(" ", text)
        parts.extend(_TOKEN.findall(text))
    return parts


def grams(tokens: list[str], n: int = 5) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def jaccard(a: set[Any], b: set[Any]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def pairwise(projects: list[Path]) -> list[dict[str, Any]]:
    labeled = [(p.name if p.name != "project" else p.parent.name, grams(app_tokens(p))) for p in projects]
    rows = []
    for (na, ga), (nb, gb) in combinations(labeled, 2):
        rows.append({"a": na, "b": nb, "jaccard": round(jaccard(ga, gb), 4), "grams_a": len(ga), "grams_b": len(gb)})
    return rows


def render_sameness(rows: list[dict[str, Any]]) -> str:
    lines = [
        "## Structural sameness (`lib/app/**`)",
        "",
        "Pairwise Jaccard over identifier 5-grams after stripping string and numeric literals. Report only; no pass/fail threshold.",
        "",
        "| App A | App B | Jaccard | 5-grams A | 5-grams B |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    if not rows:
        lines.append("| — | — | — | 0 | 0 |")
        lines.append("")
        lines.append("No project pairs under the given glob.")
    else:
        for row in rows:
            lines.append(
                f"| {row['a']} | {row['b']} | {row['jaccard']:.4f} | {row['grams_a']} | {row['grams_b']} |"
            )
    lines.append("")
    return "\n".join(lines)
