# How this project uses Meta models

Every Meta call goes through `src/meta_client/`. Model IDs and request shapes come from the
Meta docs (https://dev.meta.ai/docs/quickstart, /docs/models, /docs/pricing-rate-limits) and
the official cookbook (https://github.com/meta-models/meta-model-cookbook). All calls use
**Standard mode** (no `-contributor` models).

| Model ID | Endpoint | Used by (module) | What it does here | Why it is needed |
| --- | --- | --- | --- | --- |
| `muse-spark-1.3` | `POST /v1/responses` | `meta_client.text` → codegen, sketch2layout (checks) | Text generation; JSON constrained by a schema (`text.format`) for file operations | Writes the Flutter file operations (write/patch/delete) as schema-valid JSON. Muse Spark is the Meta model we use for text generation with a JSON schema. |
| `muse-spark-1.3` (image input) | `POST /v1/responses` with `input_image` | `scripts/day1/02_image_input.py` | Reads a hand-drawn sketch | Tests whether a sketch can be sent directly as an image. If it can, Muse Spark can describe elements next to SAM's masks. |
| `sam-3.1` | `POST /v1/responses` with `input_image` | `meta_client.segmentation` → sketch2layout | Concept prompts ("button", "text field", "image", "card") return a box and mask per match | Gives pixel-accurate boxes and masks for UI elements. A text model can name elements but can't return reliable pixel geometry. Parsed with the official `meta-sam-parser`. |
| `muse-image-1.0` | `POST /v1/images/generations` | `meta_client.images` → storepack | 1024×1024 app icon from a text prompt | Store listing needs an icon. Image generation is the only Meta model that produces images here. |

## Facts we verified from the docs (2026-10-30)

- Auth: `Authorization: Bearer <key>`. The Meta docs name the variable `MODEL_API_KEY`; this repo reads `META_API_KEY`.
- Muse Spark structured output: `text.format` with `type: "json_schema"`, `name`, `schema`, `strict` (Responses API). Recursive schemas return 400.
- SAM 3.1 zero matches is a valid completed response with an empty output text. Concepts that are lists ("bus, bicycle") return zero matches, so we reject them before sending.
- SAM box coordinates on the wire are inclusive (`x2`, `y2`). The parser returns half-open `right` and `bottom`.
- SAM masks use base85 (not base64) with a `~` (lossless) or `!` (one_bit) marker. We decode with the official parser, not our own decoder.
- Muse Image `size` sets the aspect ratio only. The returned pixel size can differ, so we record the decoded size.
- Muse Image accepts only `image_generation` tools on the Responses API. Day 1 uses the images endpoint, which has no tools.
- Pricing (Standard): Muse Spark 1.3 $1.25 / $0.15 cached / $4.25 per 1M input / cached / output tokens. Muse Image $0.01 per image. SAM 3.1 $2.50 per 1,000 images.
- Retry guidance: 429 backoff with jitter, honour `Retry-After`. 503 is retryable on image calls. 500 is not retried.

## Not verified yet (will be stated in docs/day1-findings.md if still open)

- Whether `cached_tokens` is included in `input_tokens` (we assume yes, the OpenAI convention).
- Whether a SAM request with zero matches is billed.
- Whether the fixed-seed reproducibility the eval needs is available. No `seed` field is documented; the image docs say an unknown `seed` returns 400, so we do not send one.
