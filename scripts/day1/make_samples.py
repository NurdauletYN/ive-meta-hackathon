"""Generate the synthetic hand-drawn-style UI sketches used by the Day 1 smoke tests.

These are STAND-INS. Replace them with photos of real hand-drawn sketches (same folder, same
manifest.json format) before quoting any numbers. The output is deterministic: a fixed seed
means re-running this script produces byte-identical PNGs.

Usage:  uv run python scripts/day1/make_samples.py
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SAMPLES_DIR = Path(__file__).resolve().parent / "samples"
SEED = 20261030
W, H = 900, 1200
INK = (34, 34, 34)
PAPER = (255, 255, 255)

# Expected element counts per sketch. Used as ground truth for the smoke tests.
EXPECTED: dict[str, dict[str, int]] = {
    "login": {"button": 1, "text field": 2, "image": 1, "card": 0},
    "products": {"button": 1, "text field": 0, "image": 2, "card": 2},
    "settings": {"button": 1, "text field": 2, "image": 0, "card": 1},
}


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def _wobbly_line(draw: ImageDraw.ImageDraw, a: tuple[float, float], b: tuple[float, float], rng: random.Random) -> None:
    length = math.dist(a, b)
    steps = max(6, int(length // 35))
    prev: tuple[float, float] | None = None
    for s in range(steps + 1):
        t = s / steps
        point = (
            a[0] + (b[0] - a[0]) * t + rng.uniform(-2.5, 2.5),
            a[1] + (b[1] - a[1]) * t + rng.uniform(-2.5, 2.5),
        )
        if prev is not None:
            draw.line([prev, point], fill=INK, width=rng.choice((3, 4, 5)))
        prev = point


def _box(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, rng: random.Random) -> None:
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    for a, b in zip(corners, corners[1:]):
        _wobbly_line(draw, a, b, rng)


def _image_placeholder(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, rng: random.Random) -> None:
    _box(draw, x0, y0, x1, y1, rng)
    _wobbly_line(draw, (x0, y0), (x1, y1), rng)
    _wobbly_line(draw, (x1, y0), (x0, y1), rng)


def _label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int = 30) -> None:
    draw.text(xy, text, fill=INK, font=_font(size))


def _login(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    _label(d, (120, 110), "Sign in", 56)
    _image_placeholder(d, 330, 220, 570, 400, rng)
    _box(d, 120, 470, 780, 560, rng)
    _label(d, (140, 495), "Email")
    _box(d, 120, 610, 780, 700, rng)
    _label(d, (140, 635), "Password")
    _box(d, 120, 780, 780, 880, rng)
    _label(d, (360, 812), "Log in", 40)
    return img


def _products(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    _label(d, (120, 90), "Shop", 56)
    _box(d, 80, 200, 820, 560, rng)
    _image_placeholder(d, 110, 230, 360, 530, rng)
    _label(d, (400, 300), "Shoe", 40)
    _label(d, (400, 400), "$40", 36)
    _box(d, 80, 600, 820, 960, rng)
    _image_placeholder(d, 110, 630, 360, 930, rng)
    _label(d, (400, 700), "Bag", 40)
    _label(d, (400, 800), "$55", 36)
    _box(d, 240, 1010, 660, 1110, rng)
    _label(d, (370, 1040), "Add", 40)
    return img


def _settings(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    _label(d, (120, 110), "Profile", 56)
    _box(d, 80, 220, 820, 1000, rng)
    _box(d, 120, 300, 780, 390, rng)
    _label(d, (140, 325), "Name")
    _box(d, 120, 430, 780, 640, rng)
    _label(d, (140, 455), "Bio")
    _box(d, 120, 1040, 780, 1130, rng)
    _label(d, (370, 1070), "Save", 40)
    return img


BUILDERS = {"login": _login, "products": _products, "settings": _settings}


def main() -> None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {"seed": SEED, "canvas": [W, H], "sketches": {}}
    for index, (name, build) in enumerate(BUILDERS.items()):
        rng = random.Random(SEED + index)  # one stream per sketch, so adding a sketch does not shift the others
        img = build(rng)
        path = SAMPLES_DIR / f"{name}.png"
        img.save(path, format="PNG", optimize=True)
        manifest["sketches"][f"{name}.png"] = {"expected_counts": EXPECTED[name]}  # type: ignore[index]
        print(f"wrote {path.relative_to(SAMPLES_DIR.parent.parent.parent)}")
    (SAMPLES_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
