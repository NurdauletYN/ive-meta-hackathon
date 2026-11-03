# How this project uses Meta models (Pilot backends)

Product direction is **Rocket harness** (protected Flutter capsule + guard + preflight + Pilot layer). **Pilot** models emit JSON (design directions, AppSpec, file operations) through `src/pilot`. Sketch / SAM input was removed after Day 1.

| Model ID | Endpoint | Used by | Purpose |
| --- | --- | --- | --- |
| `muse-spark-1.3` | `POST /v1/responses` | `meta_client.text`, `pilot.muse.MuseSparkPilot`, `scripts/day1/01_file_ops.py` | Structured JSON: design directions, AppSpec, write/patch/delete |
| `muse-image-1.0` | `POST /v1/images/generations` | `meta_client.images`, `scripts/day1/04_muse_image_icon.py` | App icon generation; local Lanczos resize to 1024×1024 |
| `meta-models/muse-spark-open-1026` | OpenAI-compatible `POST /chat/completions` | `pilot.openai_compat.OpenAICompatPilot` via `pilots.yaml` `baseten` | Same Pilot protocol; **no call** unless `OPENAI_COMPAT_BASE_URL` and `OPENAI_COMPAT_API_KEY` are set |

Standard mode only (`muse-spark-1.3`, not `-contributor`). Auth: `META_API_KEY`, base URL `https://api.meta.ai/v1`. Model IDs are not changed from Day 1.

`MuseSparkPilot` concatenates `system` then `user` so the capsule API prefix stays a stable prompt-cache prefix. Each `complete_json` appends one line to `ivebench/results/usage.jsonl` (`run_id`, pilot, stage, tokens, cached_tokens, est. cost). `--max-usd` aborts that run when the sum for `run_id` is exhausted.

SAM 3.1 was tried on Day 1 and removed from the codebase; see `docs/day1-findings.md`.
