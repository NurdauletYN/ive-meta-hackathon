"""Generate the kit product photo pack with Muse Image.

Usage:
    uv run python scripts/gen_kit_photos.py --max-usd 0.40

Writes 720px JPEGs to flutter_template/lib/core/kit/photos/. Every call is logged to
ivebench/results/usage.jsonl. Needs the Meta key from env or Keychain (same as the pilot).
"""

from __future__ import annotations

import argparse
import io
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image  # noqa: E402

from meta_client import MetaClient, MuseImage, load_settings  # noqa: E402
from meta_client.pricing import image_cost_usd  # noqa: E402
from pilot.protocol import Usage  # noqa: E402
from pilot.usage_log import DEFAULT_USAGE_PATH, append_usage  # noqa: E402

OUT = ROOT / "flutter_template" / "lib" / "core" / "kit" / "photos"

STYLE = (
    "Premium e-commerce product photo of {thing}, single subject centered, soft studio light, "
    "gentle shadow, smooth {tone} gradient background, sharp focus, high-end catalog photography. "
    "No text, no logos, no watermark, no people."
)

PHOTOS: dict[str, tuple[str, str]] = {
    "shoe": ("a modern white and neon running sneaker", "light grey"),
    "jacket": ("a lightweight technical windbreaker jacket on a hanger", "warm sand"),
    "hoodie": ("a heavyweight charcoal hoodie, folded", "pale blue"),
    "shorts": ("performance athletic shorts, folded", "soft mint"),
    "cleat": ("a football boot with studs", "dusk blue"),
    "coffee": ("a ceramic cup of latte art coffee with beans nearby", "cream"),
    "tool": ("a steel claw hammer and wrench on a workbench", "slate"),
    "plant": ("a leafy potted houseplant in a terracotta pot", "soft sage"),
    "bag": ("a leather crossbody bag", "blush"),
    "headphone": ("over-ear wireless headphones", "deep violet"),
    "burger": ("a gourmet cheeseburger with fries", "warm orange"),
    "salad": ("a colorful fresh salad bowl", "light green"),
    "pastry": ("fresh croissants on a plate", "buttery yellow"),
    "dumbbell": ("a pair of hex dumbbells", "graphite"),
    "bike": ("a sleek city bicycle", "pale teal"),
    "book": ("a stack of three hardcover books", "dusty rose"),
    "camera": ("a vintage mirrorless camera", "cool grey"),
    "watch": ("a minimalist wristwatch", "midnight blue"),
    "sunglasses": ("stylish sunglasses", "peach"),
    "skincare": ("skincare serum bottles with a dropper", "soft pink"),
    "candle": ("a scented candle in a glass jar", "warm beige"),
    "lamp": ("a modern designer table lamp", "light stone"),
    "suitcase": ("a hard shell travel suitcase", "sky blue"),
    "guitar": ("an acoustic guitar", "amber"),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-usd", type=float, required=True)
    parser.add_argument("--only", nargs="*", help="regenerate only these names")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    names = [n for n in PHOTOS if not args.only or n in args.only]
    per_image = image_cost_usd("muse-image-1.0", 1)
    if per_image * len(names) > args.max_usd:
        print(f"{len(names)} images x ${per_image:.3f} exceeds --max-usd {args.max_usd}", file=sys.stderr)
        return 2

    lock = threading.Lock()
    spent = 0.0
    failures: list[str] = []

    def one(name: str) -> None:
        nonlocal spent
        thing, tone = PHOTOS[name]
        prompt = STYLE.format(thing=thing, tone=tone)
        settings = replace(load_settings(), usage_log=None)
        client = MetaClient(settings)
        try:
            images = MuseImage(client).generate(prompt, size="1024x1024", n=1)
        except Exception as exc:  # noqa: BLE001
            with lock:
                failures.append(f"{name}: {type(exc).__name__}: {exc}")
            return
        finally:
            client.close()
        last = client.usage.records[-1] if client.usage.records else None
        cost = last.est_cost_usd if last is not None else per_image
        with Image.open(io.BytesIO(images[0].data)) as img:
            img.convert("RGB").resize((720, 720), Image.Resampling.LANCZOS).save(
                OUT / f"{name}.jpg", format="JPEG", quality=84, optimize=True
            )
        with lock:
            spent += cost or 0.0
            append_usage(
                ROOT / DEFAULT_USAGE_PATH,
                run_id="kit-photos",
                pilot="muse-image",
                stage="kit_photo",
                usage=Usage(
                    input_tokens=0,
                    cached_tokens=0,
                    output_tokens=0,
                    latency_ms=last.latency_ms if last is not None else 0.0,
                    est_cost_usd=cost,
                ),
                model=last.model if last is not None else "muse-image-1.0",
            )
            print(f"ok {name} (${spent:.3f} total)", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(one, names))

    for line in failures:
        print("FAILED", line, file=sys.stderr)
    print(f"done: {len(names) - len(failures)}/{len(names)} images, ${spent:.3f}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
