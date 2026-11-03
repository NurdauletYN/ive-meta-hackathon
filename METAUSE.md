# How this project uses Meta models (Pilot backends)

Product direction is **Rocket harness** (protected Flutter capsule + guard + preflight). **Pilot** models only emit file operations into `lib/app/`. Sketch / SAM input was removed after Day 1.

| Model ID | Endpoint | Used by | Purpose |
| --- | --- | --- | --- |
| `muse-spark-1.3` | `POST /v1/responses` | `meta_client.text`, `scripts/day1/01_file_ops.py` | Structured JSON for write/patch/delete file operations |
| `muse-image-1.0` | `POST /v1/images/generations` | `meta_client.images`, `scripts/day1/04_muse_image_icon.py` | App icon generation; local Lanczos resize to 1024×1024 |

Standard mode only (`muse-spark-1.3`, not `-contributor`). Auth: `META_API_KEY`, base URL `https://api.meta.ai/v1`.

SAM 3.1 was tried on Day 1 and removed from the codebase; see `docs/day1-findings.md`.
