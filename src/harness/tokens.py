"""Write a Direction's tokens into lib/app/design_tokens.json."""

from __future__ import annotations

import json
from pathlib import Path

from pilot.schemas import DesignTokens, Direction


def tokens_to_json(tokens: DesignTokens) -> dict:
    return {
        "colors": tokens.colors.model_dump(),
        "contrast_pairs": [p.model_dump() for p in tokens.contrast_pairs],
        "corner_radius": tokens.corner_radius,
        "typography": tokens.typography,
        "spacing": tokens.spacing.model_dump(),
        "radii": tokens.radii.model_dump(),
        "type_scale": tokens.type_scale.model_dump(),
    }


def apply_tokens(project_dir: Path, direction: Direction) -> Path:
    path = project_dir / "lib" / "app" / "design_tokens.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tokens_to_json(direction.tokens), indent=2) + "\n", encoding="utf-8")
    return path
