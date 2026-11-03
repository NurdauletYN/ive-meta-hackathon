"""Day 1 (b): does Muse Spark accept a hand-drawn sketch as an image input, and does it read it?

For every sketch in scripts/day1/samples/ we send the PNG as an input_image and ask for the UI
elements as JSON. Two answers are reported per sketch:
  - accepted: the API returned a valid response for the image request (yes/no)
  - type_recall: share of expected element types (button, text field, image, card) that the
    model reported at least once, from manifest.json

Overall PASS = every sketch accepted AND type_recall >= 0.5 on each sketch.
"""

from __future__ import annotations

import json

from _common import RESULTS_DIR, SAMPLES_DIR, load_client, run_guarded, save_json, verdict
from meta_client import MetaError, MuseSpark, image_input_from_path

ELEMENT_TYPES = ["button", "text field", "image", "card", "other"]
ELEMENTS_SCHEMA = {
    "type": "object",
    "properties": {
        "elements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ELEMENT_TYPES},
                    "label": {"type": "string"},
                },
                "required": ["type", "label"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["elements"],
    "additionalProperties": False,
}
PROMPT = (
    "This is a photo of a hand-drawn UI wireframe. List every UI element you see. For each, give its type "
    "(one of: button, text field, image, card, other) and its visible label (empty string if none). "
    "Return only the JSON."
)


def main() -> int:
    client = load_client()
    muse = MuseSpark(client)
    manifest = json.loads((SAMPLES_DIR / "manifest.json").read_text(encoding="utf-8"))["sketches"]
    out_dir = RESULTS_DIR / "b_image_input"
    results: list[dict[str, object]] = []

    for name, meta in sorted(manifest.items()):
        expected = {t: n for t, n in meta["expected_counts"].items() if n > 0}
        image = image_input_from_path(SAMPLES_DIR / name)
        try:
            out = muse.generate_structured(PROMPT, images=[image], schema=ELEMENTS_SCHEMA, schema_name="UiElements")
            accepted = True
            found = {t: 0 for t in ELEMENT_TYPES}
            for element in out.data.get("elements", []):
                found[element["type"]] += 1
            hits = [t for t in expected if found.get(t, 0) >= 1]
            recall = len(hits) / len(expected) if expected else 1.0
            error = None
            raw_text = out.text
        except MetaError as exc:
            accepted, found, recall, error, raw_text = False, {}, 0.0, str(exc), ""
        results.append(
            {
                "sketch": name,
                "accepted": accepted,
                "type_recall": round(recall, 3),
                "expected": expected,
                "found": found,
                "error": error,
            }
        )
        save_json(out_dir / f"{name}.json", {**results[-1], "output_text": raw_text})
        print(f"{name}: accepted={'yes' if accepted else 'no'} type_recall={recall:.2f} "
              f"expected={expected} found={ {k: v for k, v in found.items() if v} }"
              + (f" error={error}" if error else ""))

    all_accepted = all(bool(r["accepted"]) for r in results)
    all_read = all(float(r["type_recall"]) >= 0.5 for r in results)  # type: ignore[arg-type]
    save_json(out_dir / "summary.json", {"results": results, "all_accepted": all_accepted, "all_read": all_read})
    print(f"image input accepted by API: {'yes' if all_accepted else 'no'}; model read sketches: "
          f"{'yes' if all_read else 'no'}")
    return verdict(
        "(b) image input",
        all_accepted and all_read,
        f"accepted={'yes' if all_accepted else 'no'}, read={'yes' if all_read else 'no'} across {len(results)} sketches",
    )


if __name__ == "__main__":
    run_guarded(main)
