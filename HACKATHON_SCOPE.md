# Hackathon scope

Every module in this repo: who wrote it, when, and where it came from.
Rule: nothing here is copied from private code. Anything reused from before the event goes in
`preexisting/` with a README stating its origin, and is listed below.

Author for all Day 1 work: NurdauletYN, with a Cursor coding agent. Dates are commit dates.

## Modules

| Path | Status | Written | Origin | Notes |
| --- | --- | --- | --- | --- |
| `src/meta_client/config.py` | done (Day 1) | 2026-10-30 | NEW | Env settings. Rejects `-contributor` model IDs and missing keys. |
| `src/meta_client/errors.py` | done (Day 1) | 2026-10-30 | NEW | Typed errors: config, 4xx (never retried), auth, retries exhausted, bad response. |
| `src/meta_client/usage.py` | done (Day 1) | 2026-10-30 | NEW | One JSONL line per call: tokens, latency, attempts, cost. |
| `src/meta_client/pricing.py` | done (Day 1) | 2026-10-30 | NEW | Standard-mode prices, source cited in the file. Unknown models return None. |
| `src/meta_client/client.py` | done (Day 1) | 2026-10-30 | NEW | httpx transport: auth, timeouts, retries with backoff and jitter, Retry-After. |
| `src/meta_client/media.py` | done (Day 1) | 2026-10-30 | NEW | Base64 data URLs for image inputs. |
| `src/meta_client/text.py` | done (Day 1) | 2026-10-30 | NEW | Muse Spark over Responses: text and schema-constrained JSON. |
| `src/meta_client/images.py` | done (Day 1) | 2026-10-30 | NEW | Muse Image over `/v1/images/generations`. |
| `src/meta_client/segmentation.py` | done (Day 1) | 2026-10-30 | NEW (uses third-party parser) | SAM 3.1 on images. Parsing and mask decoding by `meta-sam-parser`. |
| `tests/test_meta_client.py` | done (Day 1) | 2026-10-30 | NEW | 39 offline tests: failure paths, retries, parsing. No network, no key. |
| `scripts/day1/` | in progress | 2026-10-30 | NEW | Smoke tests a–d from the kickoff prompt. |
| `src/sketch2layout/` | not started | — | — | Day 2. Placeholder package only. |
| `src/codegen/` | not started | — | — | Day 2. Placeholder package only. |
| `src/compile_runner/` | not started | — | — | Day 3. Placeholder package only. |
| `src/storepack/` | not started | — | — | Day 3. Placeholder package only. |
| `ivebench/` | not started | — | — | Eval harness. |
| `demo/` | not started | — | — | FastAPI demo. |
| `flutter_template/` | not started | — | — | Blank Flutter project for the compile runner. |

## Third-party dependencies (pinned in `uv.lock`)

These are dependencies, not copied code. Licenses are as the projects publish them; only the
meta-sam-parser license was read from its PyPI page in this session. Re-check the rest before release.

| Package | Used for | License |
| --- | --- | --- |
| httpx | HTTP client | BSD-3-Clause |
| pydantic | Typed models | MIT |
| python-dotenv | Loads `.env` | BSD-3-Clause |
| pillow | Image decode and overlays | MIT-CMU (HPND) |
| meta-sam-parser | SAM 3 output grammar and mask decoding (official Meta package) | **SAM License** (not MIT). Redistribution must include the SAM License text. Takes priority in the LICENSE decision. |
| pytest, pre-commit (dev) | Tests, git hooks | MIT |
| gitleaks v8.30.1 (tool, not a dependency) | Secret scan in the pre-commit hook | MIT |

## Preexisting code

None. If that changes, the code goes in `preexisting/` with a README and gets a row here.
