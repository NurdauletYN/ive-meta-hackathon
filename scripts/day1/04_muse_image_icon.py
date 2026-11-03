"""Day 1 (d): Muse Image icon generation with local Lanczos resize to 1024×1024.

The API may return a different pixel size than requested; we keep the raw bytes and also write
``icon_1024.png`` via ``resize_lanczos_to_square``. PASS = the resized file is exactly 1024×1024.
"""

from __future__ import annotations

import json

from _common import RESULTS_DIR, load_client, run_guarded, save_json, verdict
from meta_client import MuseImage, resize_lanczos_to_square

PROMPT = (
    "App icon for a mobile app shipping tool: flat rounded-square icon, bold blue and white, "
    "simple rocket motif, centered, no text."
)


def main() -> int:
    client = load_client()
    out_dir = RESULTS_DIR / "d_icon"
    out_dir.mkdir(parents=True, exist_ok=True)
    icon = MuseImage(client).generate(PROMPT, size="1024x1024", output_format="png", n=1)[0]
    raw_path = out_dir / "icon_raw.png"
    raw_path.write_bytes(icon.data)
    resized_bytes, w, h = resize_lanczos_to_square(icon.data, 1024)
    resized_path = out_dir / "icon_1024.png"
    resized_path.write_bytes(resized_bytes)

    record = client.usage.records[-1]
    save_json(
        out_dir / "response.json",
        {
            "prompt": PROMPT,
            "requested_size": "1024x1024",
            "api_decoded_size": [icon.width, icon.height],
            "resized_size": [w, h],
            "raw_file": raw_path.name,
            "resized_file": resized_path.name,
            "usage": {
                "images": record.images,
                "est_cost_usd": record.est_cost_usd,
                "latency_ms": record.latency_ms,
            },
        },
    )
    print(json.dumps({"api_size": [icon.width, icon.height], "resized": [w, h]}))
    return verdict(
        "(d) Muse Image icon + local 1024 resize",
        (w, h) == (1024, 1024),
        f"raw {icon.width}x{icon.height} -> {w}x{h} saved as {resized_path.name}",
    )


if __name__ == "__main__":
    run_guarded(main)
