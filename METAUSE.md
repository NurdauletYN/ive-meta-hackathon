# How this project uses Meta models

Product: **Rocket** harness (protected Flutter capsule + guard + preflight + Pilot). Pilots emit JSON (design directions, AppSpec, file operations) through `src/pilot`. Sketch / SAM input was removed after Day 1 (`docs/day1-findings.md`).

Standard mode only (`muse-spark-1.3`, not `-contributor`). Auth: `META_API_KEY`, base URL `https://api.meta.ai/v1`. No credentials are passed to a Pilot prompt.

| Model | Job in the pipeline |
| --- | --- |
| Muse Spark (`muse-spark-1.3`) | Primary Pilot: 3 design directions, AppSpec, AppCatalog JSON (products and copy that the harness turns into kit screens), guarded file ops in bare mode, repair, storepack listing copy |
| Muse Image (`muse-image-1.0`) | Store-pack app icon (`harness storepack`): keep raw bytes, Lanczos 1024×1024 and 512×512 locally. Day 1 smoke also logged as `image.generate`. |
| Muse Spark Open (`meta-models/muse-spark-open-1026`) | Optional Pilot (`pilots.yaml` `baseten` / studio option). Same JSON protocol. Used only if `OPENAI_COMPAT_BASE_URL` and `OPENAI_COMPAT_API_KEY` are set. Whether it was used is stated in the generated usage block below, from the log. |
| Muse Image (kit photos) | 24 product photos bundled with the kit (`scripts/gen_kit_photos.py`), also generated with `muse-image-1.0`. |

`MuseSparkPilot` concatenates `system` then `user` so the capsule API prefix stays a stable prompt-cache prefix. Each `complete_json` appends one line to `ivebench/results/usage.jsonl`. `--max-usd` aborts that run when the sum for `run_id` is exhausted.

## Muse Spark Open attribution

The studio footer shows "Built with Muse Spark Open" only for a build that actually ran on that Pilot; otherwise it names the model that did run (for example Muse Spark, `muse-spark-1.3`). This repository makes no claim of Muse Spark Open use beyond what the usage block below reports from `usage.jsonl`.

Refresh the table with `uv run harness usage-report --write-metause`.

<!-- usage-report:start -->
### Usage by model and stage

Generated from `ivebench/results/usage.jsonl` by `harness usage-report`. Counts only.

| Model | Stage | Calls | Tokens in | Cached | Tokens out | Cost USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| muse-image-1.0 | image.generate | 1 | 0 | 0 | 0 | 0.010000 |
| muse-image-1.0 | kit_photo | 26 | 0 | 0 | 0 | 0.260000 |
| muse-image-1.0 | storepack_icon | 1 | 0 | 0 | 0 | 0.010000 |
| muse-spark-1.3 | catalog | 3 | 4746 | 0 | 8219 | 0.040863 |
| muse-spark-1.3 | design | 1 | 121 | 0 | 4365 | 0.018703 |
| muse-spark-1.3 | file_ops | 66 | 126198 | 4075 | 393401 | 1.825219 |
| muse-spark-1.3 | spec | 36 | 17077 | 0 | 84744 | 0.381508 |
| muse-spark-1.3 | storepack | 2 | 84 | 0 | 1486 | 0.006420 |
| muse-spark-1.3 | text.generate | 1 | 15 | 0 | 287 | 0.001239 |
| muse-spark-1.3 | text.structured | 13 | 5646 | 750 | 19109 | 0.087446 |
| sam-3.1 | sam.segment_image | 14 | 0 | 0 | 0 | 0.035000 |
| **total** | | 164 | 153887 | 4825 | 511611 | 2.676398 |

Offline FakePilot rows (7) are excluded from this table.
SAM 3.1 rows are Day 1 history; that path was removed from the product.
This table is usage, not a quality eval. Infra timeouts still appear as calls with `ok: false`.
Muse Spark Open: **no live calls in this log** (not used for any number or build reported here).
<!-- usage-report:end -->
