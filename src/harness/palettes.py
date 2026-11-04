"""Curated design palettes. A build without a chosen direction gets one of these, not a default blue.

Every palette meets WCAG AA (4.5:1) for its text pairs; tests assert it.
"""

from __future__ import annotations

import json
import re
import zlib
from dataclasses import dataclass
from pathlib import Path

from preflight.checks import contrast_ratio


@dataclass(frozen=True)
class Palette:
    id: str
    name: str
    primary: str
    on_primary: str
    surface: str
    on_surface: str
    accent: str
    surface_alt: str
    corner_radius: float = 16
    keywords: tuple[str, ...] = ()

    @property
    def dark(self) -> bool:
        return contrast_ratio(self.surface, "#FFFFFF") > contrast_ratio(self.surface, "#000000")


PALETTES: tuple[Palette, ...] = (
    Palette("volt", "Ink & Volt", "#C6FF3D", "#0B0B0F", "#0B0B0F", "#F5F5F7", "#FF5C39", "#17171E", 18,
            ("sport", "shoe", "sneaker", "fitness", "gym", "run", "wear", "cleat", "football", "soccer", "training")),
    Palette("midnight", "Midnight Violet", "#8B7BFF", "#0E0B24", "#0F1020", "#F2F3FA", "#38D6FF", "#1A1B30", 18,
            ("music", "game", "gaming", "night", "crypto", "stream", "podcast", "audio", "tech", "ai")),
    Palette("emerald", "Emerald Night", "#34D399", "#04201A", "#07130F", "#EAF7F1", "#FBBF24", "#10221B", 16,
            ("finance", "money", "budget", "invest", "wallet", "bank", "stock", "expense", "savings")),
    Palette("terracotta", "Terracotta", "#B4400E", "#FFFFFF", "#FBF5EE", "#2B1B12", "#F59E0B", "#F2E6D8", 20,
            ("food", "cafe", "coffee", "restaurant", "recipe", "bakery", "pizza", "burger", "kitchen", "menu", "meal")),
    Palette("forest", "Forest", "#166534", "#FFFFFF", "#F2F7F1", "#14231A", "#84CC16", "#E2EDE0", 18,
            ("plant", "garden", "eco", "green", "nature", "farm", "outdoor", "hike", "camp")),
    Palette("rose", "Rose Quartz", "#BE185D", "#FFFFFF", "#FFF6F8", "#2A1220", "#FB7185", "#FBE4EA", 22,
            ("beauty", "skin", "makeup", "salon", "wedding", "flower", "gift", "fashion", "boutique")),
    Palette("ocean", "Deep Ocean", "#0B5FFF", "#FFFFFF", "#F3F7FC", "#0E1B2E", "#00C2A8", "#E2EBF7", 16,
            ("water", "swim", "boat", "weather", "sea", "dive", "surf", "health", "clinic", "fitness tracker")),
    Palette("sky", "Sky Atlas", "#0369A1", "#FFFFFF", "#F1F8FF", "#0C2233", "#F97316", "#DDEBF7", 18,
            ("travel", "trip", "hotel", "flight", "city", "tour", "map", "booking", "vacation")),
    Palette("plum", "Plum Studio", "#6D28D9", "#FFFFFF", "#FAF7FF", "#1F1233", "#F472B6", "#EEE6FB", 20,
            ("book", "read", "art", "design", "creative", "photo", "journal", "write", "learn", "course", "school")),
    Palette("sand", "Sand & Charcoal", "#1F2937", "#FFFFFF", "#F8F5EF", "#1C1917", "#D97706", "#EDE7DB", 14,
            ("home", "tool", "furniture", "decor", "hardware", "repair", "market", "shop", "store", "interior")),
    Palette("mono", "Mono Poster", "#111111", "#FFFFFF", "#FFFFFF", "#111111", "#FF4D00", "#F1F1F1", 12,
            ("minimal", "watch", "camera", "studio", "portfolio", "magazine", "news", "notes", "todo", "task")),
)

_BY_ID = {p.id: p for p in PALETTES}


def get_palette(palette_id: str) -> Palette:
    return _BY_ID[palette_id]


def pick_palette(idea: str) -> Palette:
    """Keyword match first (most hits wins); otherwise a stable hash so a rerun looks the same."""
    text = idea.lower()
    words = set(re.findall(r"[a-z]+", text))
    best: Palette | None = None
    best_hits = 0
    for palette in PALETTES:
        hits = sum(1 for kw in palette.keywords if (kw in words or (" " in kw and kw in text)))
        if hits > best_hits:
            best, best_hits = palette, hits
    if best is not None:
        return best
    return PALETTES[zlib.crc32(text.encode("utf-8")) % len(PALETTES)]


_DARK_WORDS = re.compile(r"\b(dark|night)\b")
_LIGHT_WORDS = re.compile(r"\b(light|bright|white)\b")
_CHANGE_WORDS = re.compile(r"\b(colou?rs?|palette|theme|look|style|vibe|skin)\b")


def current_palette(project_dir: Path) -> Palette | None:
    path = project_dir / "lib" / "app" / "design_tokens.json"
    try:
        primary = str(json.loads(path.read_text(encoding="utf-8"))["colors"]["primary"]).upper()
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return None
    return next((p for p in PALETTES if p.primary.upper() == primary), None)


def palette_from_instruction(text: str, current: Palette | None) -> Palette | None:
    """A palette change asked for in plain words ("make it dark", "try rose"), else None."""
    lowered = text.lower()
    for palette in PALETTES:
        if re.search(rf"\b{re.escape(palette.id)}\b", lowered) or palette.name.lower() in lowered:
            return palette if current is None or palette.id != current.id else None
    if _DARK_WORDS.search(lowered) and (current is None or not current.dark):
        return next(p for p in PALETTES if p.id == "midnight")
    if _LIGHT_WORDS.search(lowered) and (current is None or current.dark) and (
        _CHANGE_WORDS.search(lowered) or "switch" in lowered or "make it" in lowered
    ):
        return next(p for p in PALETTES if p.id == "ocean")
    if _CHANGE_WORDS.search(lowered) and re.search(r"\b(different|another|new|change|switch|fresh|other)\b", lowered):
        ids = [p.id for p in PALETTES]
        index = ids.index(current.id) if current is not None else -1
        return PALETTES[(index + 1) % len(PALETTES)]
    return None


def palette_tokens(palette: Palette, base: dict | None = None) -> dict:
    """design_tokens.json content for a palette, keeping spacing/radii/type from `base`."""
    data = dict(base or {})
    data["colors"] = {
        "primary": palette.primary,
        "on_primary": palette.on_primary,
        "surface": palette.surface,
        "on_surface": palette.on_surface,
        "accent": palette.accent,
        "surface_alt": palette.surface_alt,
    }
    data["contrast_pairs"] = [
        {"name": "body_on_surface", "foreground": palette.on_surface, "background": palette.surface},
        {"name": "on_primary", "foreground": palette.on_primary, "background": palette.primary},
        {"name": "body_on_alt", "foreground": palette.on_surface, "background": palette.surface_alt},
    ]
    data["corner_radius"] = palette.corner_radius
    data.setdefault("typography", "default")
    return data


def apply_palette(project_dir: Path, palette: Palette) -> Path:
    path = project_dir / "lib" / "app" / "design_tokens.json"
    base = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(palette_tokens(palette, base), indent=2) + "\n", encoding="utf-8")
    return path
