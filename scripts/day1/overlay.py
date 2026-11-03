"""Draw SAM masks and boxes onto a sketch for visual checks.

SAM masks are box-local: each mask raster covers exactly its box, starting at (left, top).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from PIL import Image, ImageDraw

from meta_client import SamObject

PALETTE: tuple[tuple[int, int, int], ...] = (
    (235, 64, 52),
    (42, 128, 230),
    (52, 170, 84),
    (245, 156, 22),
    (150, 80, 220),
    (0, 170, 170),
)


def mask_to_image(obj: SamObject) -> Image.Image:
    """0/1 raster to an 'L' image (255 = inside the mask)."""
    if len(obj.mask) != obj.mask_width * obj.mask_height:
        raise ValueError(
            f"object {obj.object_id}: mask has {len(obj.mask)} pixels, expected "
            f"{obj.mask_width}x{obj.mask_height}"
        )
    return Image.frombytes("L", (obj.mask_width, obj.mask_height), bytes(255 if v else 0 for v in obj.mask))


def paint_mask(canvas: Image.Image, obj: SamObject, color: tuple[int, int, int], alpha: float = 0.45) -> None:
    """Blend `color` over the masked pixels of `canvas` (RGB), at the object's box position."""
    left, top = round(obj.left), round(obj.top)
    box = (left, top, left + obj.mask_width, top + obj.mask_height)
    region = canvas.crop(box)
    solid = Image.new("RGB", region.size, color)
    blended = Image.blend(region, solid, alpha)
    canvas.paste(Image.composite(blended, region, mask_to_image(obj)), box[:2])


def draw_overlay(base: Image.Image, objects: Sequence[SamObject], out_path: Path) -> None:
    canvas = base.convert("RGB")
    draw = ImageDraw.Draw(canvas)
    for index, obj in enumerate(objects):
        color = PALETTE[index % len(PALETTE)]
        paint_mask(canvas, obj, color)
        rect = [round(obj.left), round(obj.top), round(obj.right) - 1, round(obj.bottom) - 1]
        draw.rectangle(rect, outline=color, width=4)
        draw.text((rect[0] + 4, rect[1] + 4), obj.object_id, fill=color)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, format="PNG")
