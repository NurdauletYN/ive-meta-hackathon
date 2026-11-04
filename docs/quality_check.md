# Quality check (live, capped) — 2026-11-04

Three Muse Spark (`muse-spark-1.3`) harness builds. Cap **$1.50 total**. Costs from `ivebench/results/usage.jsonl`.

Playwright is not installed here (`playwright` missing on PATH and in the venv). Phone screenshots were not captured.

`META_TIMEOUT_S=180` for these runs. Default client timeout stays 90s. The first coffee-shop file_ops call timed out at 90s; the build prompt was tightened (4 compact writes) and the retry passed.

This is **not** the 8-idea published sweep. Official `ivebench/results/results.md` remains 0/0.

| Idea | run_id | Gate | Repairs | Cost USD | Kit widget types | More than text lists |
| --- | --- | --- | ---: | ---: | ---: | --- |
| coffee shop app | q-coffee | infra timeout on file_ops (no gate) | 0 | 0.008322 | — | — |
| coffee shop app | q-coffee2 | **pass** | 0 | 0.073273 | 11 | yes |
| neighborhood tool library | q-tools | **pass** | 1 | 0.093322 | 12 | yes |
| language flashcards | q-cards | **pass** | 0 | 0.055018 | 10 | yes |

Quality-check spend **$0.229935**. Three of three completed builds passed analyze, tests, web, and preflight (including `kit_usage` and `not_text_only`).
