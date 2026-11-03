"""Day 1 (c): does SAM 3.1 return boxes and masks for "button", "text field", "image", "card"?

Runs every sketch in scripts/day1/samples/ against each concept (one request per concept, since
SAM takes one noun phrase per request). Saves the raw SAM text, a JSON summary, and an overlay PNG
per (sketch, concept).

PASS = every (sketch, concept) pair where the manifest expects at least one element returned at least
one object, with no API errors. Exact-count agreement is reported separately (it is not a PASS condition).
"""

from __future__ import annotations

import json

from _common import RESULTS_DIR, SAMPLES_DIR, load_client, run_guarded, save_json, verdict
from overlay import draw_overlay
from PIL import Image

from meta_client import MetaError, MetaSam, image_input_from_path

CONCEPTS = ["button", "text field", "image", "card"]


def _slug(text: str) -> str:
    return text.replace(" ", "-")


def main() -> int:
    client = load_client()
    sam = MetaSam(client)
    manifest = json.loads((SAMPLES_DIR / "manifest.json").read_text(encoding="utf-8"))["sketches"]
    out_dir = RESULTS_DIR / "c_sam"
    rows: list[dict[str, object]] = []

    for name, meta in sorted(manifest.items()):
        stem = name.removesuffix(".png")
        image = image_input_from_path(SAMPLES_DIR / name)
        base = Image.open(SAMPLES_DIR / name).convert("RGB")
        for concept in CONCEPTS:
            expected = int(meta["expected_counts"].get(concept, 0))
            key = f"{stem}__{_slug(concept)}"
            try:
                result = sam.segment_image(image, concept)
            except MetaError as exc:
                rows.append({"sketch": name, "concept": concept, "expected": expected, "found": None, "error": str(exc)})
                print(f"{name} / {concept}: ERROR {exc}")
                continue
            (out_dir / "raw").mkdir(parents=True, exist_ok=True)
            (out_dir / "raw" / f"{key}.txt").write_text(result.raw_text, encoding="utf-8")
            draw_overlay(base, result.objects, out_dir / "overlays" / f"{key}.png")
            row = {
                "sketch": name,
                "concept": concept,
                "expected": expected,
                "found": result.count,
                "boxes": [
                    {
                        "object_id": o.object_id,
                        "left": o.left,
                        "top": o.top,
                        "right": o.right,
                        "bottom": o.bottom,
                        "confidence": o.confidence,
                        "mask_px": [o.mask_width, o.mask_height],
                    }
                    for o in result.objects
                ],
                "diagnostics": list(result.diagnostics),
                "error": None,
            }
            rows.append(row)
            print(f"{name} / {concept}: expected={expected} found={result.count}")

    save_json(out_dir / "summary.json", rows)
    needed = [r for r in rows if int(r["expected"]) > 0]  # type: ignore[call-overlap]
    errors = [r for r in rows if r["error"]]
    hits = [r for r in needed if r["found"]]
    exact = [r for r in rows if r["found"] == r["expected"] and r["error"] is None]
    print(f"expected>0 pairs with >=1 object: {len(hits)}/{len(needed)}; "
          f"exact count agreement (all pairs): {len(exact)}/{len(rows)}; api errors: {len(errors)}")
    return verdict(
        "(c) SAM 3.1 on sketches",
        not errors and len(hits) == len(needed),
        f"{len(hits)}/{len(needed)} expected element types returned >=1 mask; {len(errors)} API errors",
    )


if __name__ == "__main__":
    run_guarded(main)
