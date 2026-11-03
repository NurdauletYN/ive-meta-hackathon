"""Day 1 (d): can Muse Image generate a 1024x1024 app icon from a text prompt?

PASS = the API returns an image that decodes and is exactly 1024x1024 pixels.
The docs say `size` sets the aspect ratio, not exact pixels, so the decoded size is the check.
The icon is saved as-is either way, so a size miss is visible in the output rather than hidden.
"""

from __future__ import annotations

import json

from _common import RESULTS_DIR, load_client, run_guarded, save_json, verdict
from meta_client import MuseImage

PROMPT = (
    "App icon for a tool that turns hand-drawn sketches into mobile apps: a flat, rounded-square icon, "
    "a pencil line turning into a phone screen, bold shapes, deep blue and white, centered, no text."
)


def main() -> int:
    client = load_client()
    out_dir = RESULTS_DIR / "d_icon"
    images = MuseImage(client).generate(PROMPT, size="1024x1024", output_format="png", n=1)
    icon = images[0]
    out_dir.mkdir(parents=True, exist_ok=True)
    icon_path = out_dir / "icon_1024.png"
    icon_path.write_bytes(icon.data)

    record = client.usage.records[-1]
    save_json(
        out_dir / "response.json",
        {
            "prompt": PROMPT,
            "requested_size": "1024x1024",
            "decoded_size": [icon.width, icon.height],
            "output_format": icon.output_format,
            "bytes": len(icon.data),
            "image_file": icon_path.name,
            "usage": {
                "images": record.images,
                "est_cost_usd": record.est_cost_usd,
                "latency_ms": record.latency_ms,
                "attempts": record.attempts,
            },
        },
    )
    print(json.dumps({"decoded_size": [icon.width, icon.height], "bytes": len(icon.data)}))
    passed = (icon.width, icon.height) == (1024, 1024)
    return verdict(
        "(d) Muse Image 1024x1024 icon",
        passed,
        f"saved {icon_path.name}, decoded size {icon.width}x{icon.height}",
    )


if __name__ == "__main__":
    run_guarded(main)
