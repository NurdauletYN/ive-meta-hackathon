# Status — 2026-11-04 17:40 UTC+5

Deadline: Thu Nov 5, 07:00 UTC+5 (Wed Nov 4, 9:00 PM ET).

Track: Indie / Push the Frontier. Standalone repo: https://github.com/NurdauletYN/ive-meta-hackathon. **Not** the private Ive product.

`main` is `43e4ae8` (merge of PR #23). Tags through `v1.0-billing`. Later merges on `main` without a new tag: launcher icons (PR #22), product studio (PR #23).

## Phase

Product path is built: capsule → design → build → gate → storepack → ship CLI, plus a studio that reads as a brief + phone. Measurement for the thesis (harness vs no harness, cheap vs strong pilot) is **not** a published table yet. Committed `ivebench/results/results.md` is **0/0**.

## What is done (on `main`)

| Area | What landed | Tag / PR |
| --- | --- | --- |
| Capsule | Flutter template, protected `lib/core/`, editable `lib/app/` | PR #4 |
| Guard + gate | File-op guard; analyze, tests, optional web, 12 preflight checks | PRs #4, #12, #18 |
| Pilot | `complete_json`, Fake / Muse Spark / Muse Spark Open, `--max-usd`, `usage.jsonl` | PRs #2, #5, #6 |
| Design / build | 3 looks, spec, guarded file ops, ≤2 gate-driven repairs, harness / bare / `scaffold_only` | PRs #5, #12, #18 |
| Studio | Brief + phone, looks, build, compare, store-check sheet | PRs #7–#10, #17, #23 |
| Sweep / report | Infra vs quality, resume, dirty-tree refusal, counts-only `harness report` + `--html` | PRs #10, #13, #14 |
| Ship | `harness ship --target testflight` (fake-runner tests; **no live Apple call in this repo**) | `v0.4-ship` PR #15 |
| Docs / hygiene | VISION, README, METAUSE, VIDEO_SCRIPT placeholders, LICENSE draft, `prepublish_check.sh` | `v0.5-docs` PR #16 |
| Evidence | +4 preflight checks, sameness, `scaffold_only` | `v0.7-evidence` PR #18 |
| Firebase | Config-gated `FirebaseAuthService`; demo fallback; **unverified on a device** | `v0.8-firebase` PR #19 |
| Storepack | Listing + privacy template + Muse Image icon; Lanczos 1024/512 | `v0.9-storepack` PR #20 |
| Launcher icons | `flutter_launcher_icons` from `icon_1024.png` | PR #22 |
| RevenueCat | Config-gated billing; paywall offerings; **unverified until a sandbox purchase** | `v1.0-billing` PR #21 |

PRs **#1–#23** are merged with merge commits.

## Results from the log (committed `ivebench/results/usage.jsonl`)

This is **spend / usage**, not a quality eval. Generated table lives in `METAUSE.md` (`uv run harness usage-report`).

| Model | Stage | Calls | Tokens in | Cached | Tokens out | Cost USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| fake | design | 3 | 1282 | 192 | 3543 | 0.030000 |
| muse-image-1.0 | image.generate | 1 | 0 | 0 | 0 | 0.010000 |
| muse-image-1.0 | storepack_icon | 1 | 0 | 0 | 0 | 0.010000 |
| muse-spark-1.3 | design | 1 | 121 | 0 | 4365 | 0.018703 |
| muse-spark-1.3 | file_ops | 44 | 64482 | 2161 | 266082 | 1.209074 |
| muse-spark-1.3 | spec | 21 | 5961 | 0 | 56208 | 0.246335 |
| muse-spark-1.3 | storepack | 2 | 84 | 0 | 1486 | 0.006420 |
| muse-spark-1.3 | text.generate | 1 | 15 | 0 | 287 | 0.001239 |
| muse-spark-1.3 | text.structured | 13 | 5646 | 750 | 19109 | 0.087446 |
| sam-3.1 | sam.segment_image | 14 | 0 | 0 | 0 | 0.035000 |
| **total (committed)** | | **101** | **77591** | **3103** | **351080** | **1.654217** |

SAM 3.1 is Day 1 history; that path was removed.

Notable committed live smoke:

- Storepack (`run_id=storepack-smoke`): one failed schema call ($0), then listing **$0.006421** + Muse Image icon **$0.01**. Raw API icon was 1600×1600; local copies 1024 and 512.

Local uncommitted extra in `usage.jsonl` (two studio harness builds after the last commit): `harness-384so` **$0.025423**, `harness-39ksi` **$0.038263**. Working-tree total about **$1.718**. Not in `METAUSE.md` until those lines are committed.

## Official quality results

Committed `ivebench/results/results.md`: **passed 0/0**. No classified sweep JSON (`outcome` in pass / quality_fail / infra_fail) is in git.

## Unofficial local sweep (not a published result)

`ivebench/results/sweep/` is **untracked**. `summary.json` has 16 rows (8 ideas × harness/bare). It records `ok=true` on every **harness** arm and `ok=false` on every **bare** arm. Several bare arms ended in `MetaRetryExhaustedError` (timeout). Those rows have **no classified `outcome`**, so `harness report` ignores them. Timeouts are infrastructure, not quality. **Do not quote 8/8 vs 0/8 as a thesis result.**

To produce a real table (not run here):

```bash
uv run harness sweep --pilots muse,baseten --modes bare,scaffold_only,harness --max-usd 8 --max-usd-per-pilot 4 --build-web
uv run harness report
uv run harness report --html
```

## Unverified

- Live TestFlight upload (ship tests use a fake subprocess).
- Firebase adapter on a real project/device.
- RevenueCat adapter until a sandbox purchase on a device.
- Privacy markdown is a **template, not legal advice**.
- Preflight pass rates are **not** Apple rejection rates.
- Launcher icons / Muse Image as a store icon until uploaded in App Store Connect.

## Still not done (submit)

- Make the repo **public**.
- 3-minute video (`docs/VIDEO_SCRIPT.md` still has `{RESULT_*}` placeholders).
- Honest published sweep + `harness report` (infra vs quality).
- Claim Meta $150; rotate any key that was pasted in chat.
- License choice pending owner (draft MIT in `LICENSE`).
- Studio does not run storepack or ship (CLI only, so Apple keys never hit the browser).

## Human commands still waiting

```bash
uv run harness sweep --pilots muse,baseten --modes bare,scaffold_only,harness --max-usd 8 --max-usd-per-pilot 4 --build-web
uv run harness report
uv run harness report --html
uv run harness sameness 'runs/sweep-*' --append-results ivebench/results/results.md
uv run harness usage-report --write-metause
bash scripts/prepublish_check.sh
```
