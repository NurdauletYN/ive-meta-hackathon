# Hackathon scope

Every module: who wrote it, when, and origin. No code copied from the private Ive repo.

Author: NurdauletYN + Cursor agent (commit dates below).

## Direction change (2026-11-03)

Sketch / image / SAM pipeline **dropped**. Focus: **model-agnostic Flutter app-shipping harness** (Rocket capsule, file-op guard, preflight, `harness gate`).

## Pilot layer (2026-11-03)

Any model can propose 3 design directions and build an app inside the capsule (or a blank Flutter project in `--mode bare`). File ops are guarded; gate failures get up to 2 repair rounds. Every `complete_json` call appends usage to `ivebench/results/usage.jsonl`.

Playwright screenshots were **skipped** (optional; install not pursued inside the 10-minute budget).

## Modules

| Path | Status | Written | Origin | Notes |
| --- | --- | --- | --- | --- |
| `src/meta_client/*` | done | 2026-10-30 | NEW | Muse Spark + Muse Image adapters, usage logging |
| `src/meta_client/images.py` resize helpers | done | 2026-11-03 | NEW | Lanczos 1024×1024 after Muse Image |
| `scripts/day1/01`, `04` | kept | 2026-10-30 | NEW | API smoke; sketch/SAM scripts removed |
| `src/harness/guard.py` | done | 2026-11-03 | NEW | Validates file ops vs `capsule.manifest.json` + build allowlist |
| `src/harness/gate.py`, `cli.py` | done | 2026-11-03 | NEW | `harness gate` / `design` / `build` / `serve` |
| `src/harness/design.py`, `build.py`, `apply.py` | done | 2026-11-03 | NEW | Directions + spec/file-ops/repair |
| `src/harness/prompts.py` | done | 2026-11-03 | NEW | Byte-stable `CAPSULE_PREFIX` (cache) + bare requirements |
| `src/pilot/*` | done | 2026-11-03 | NEW | Protocol, Fake/Muse/OpenAI-compat, budget, usage JSONL |
| `pilots.yaml` | done | 2026-11-03 | NEW | muse / fake / baseten (`meta-models/muse-spark-open-1026`) |
| `HACKATHON_RULES.md`, `PLAN.md` | done | 2026-11-03 | NEW | Organizer rules for models + remaining work |
| `src/preflight/*` | done | 2026-11-04 | NEW | Eight checks; `interactive_home` WARNs on a static generated screen |
| `src/harness/branding.py` | done | 2026-11-04 | NEW | Writes spec `app_name` into strings.dart, web title, manifest |
| `flutter_template/` | done | 2026-11-03 | NEW | Capsule: protected `lib/core/`, editable `lib/app/` |
| `flutter_template/lib/app/features/registry.dart` | done | 2026-11-03 | NEW | Pilot-editable extra routes; first entry is home. Core router change in `capsule.manifest.json` `core_changes` |
| `ivebench/ideas.jsonl` | done | 2026-11-03 | NEW | 8 app ideas (no medical / mental health / nutrition / sports / job screening / political) |
| `docs/preflight.md` | done | 2026-11-03 | NEW | Check descriptions; not legal advice |
| `tests/test_guard.py`, `test_preflight.py`, `test_pilot.py` | done | 2026-11-03 | NEW | Guard, preflight, FakePilot e2e (repair, guard, invalid JSON, budget) |
| `src/codegen/`, `compile_runner/` | not started | — | — | Placeholder READMEs only; repair loop lives in `src/harness/build.py` |
| `src/storepack/` | done | 2026-11-04 | NEW | Icon (raw + Lanczos 1024/512), listing JSON, privacy template zip; FakePilot tests + one live Muse Image smoke |
| `flutter_launcher_icons` | done | 2026-11-04 | NEW | Storepack copies `icon_1024.png` to `assets/icon/app_icon.png` and runs `dart run flutter_launcher_icons` |
| `docs/storepack.md` | done | 2026-11-04 | NEW | Commands; template-not-legal-advice; what is unverified |
| `demo/` + `src/harness/ui.py` | done | 2026-11-04 | NEW | Phone-first studio: ticker, details drawer, compare, design pick. Not the Ive product. |
| `src/harness/events.py` | done | 2026-11-03 | NEW | Run event jsonl + in-process hub (live SSE, no history replay) |
| `src/harness/web_build.py` | done | 2026-11-03 | NEW | `flutter build web --base-href` so iframe previews resolve |
| `src/harness/skin.py` | done | 2026-11-04 | NEW | Immediate HTML phone screen from tokens while Flutter builds |
| `src/harness/sweep.py` | done | 2026-11-04 | NEW | ideas × live pilots × harness/bare; infra vs quality; resume; dirty-tree refusal |
| `src/harness/classify.py` | done | 2026-11-04 | NEW | pass / quality_fail / infra_fail |
| `src/harness/report.py` | done | 2026-11-04 | NEW | `harness report` → counts-only results.md |
| `src/harness/ship.py`, `redact.py` | done | 2026-11-04 | NEW | `harness ship --target testflight`; fake-runner tests; no live Apple calls |
| `docs/ship.md` | done | 2026-11-04 | NEW | Manual ASC prerequisites; what is and is not automated |
| `docs/VISION.md` | done | 2026-11-04 | NEW | Product goal (Rocket = harness, model = pilot) |
| `src/harness/usage_report.py` | done | 2026-11-04 | NEW | `harness usage-report` from usage.jsonl |
| `docs/VIDEO_SCRIPT.md` | done | 2026-11-04 | NEW | 3-minute outline with `{RESULT_*}` placeholders |
| `LICENSE` | done | 2026-11-04 | NEW | Draft MIT; choice pending owner confirmation |
| `scripts/prepublish_check.sh` | done | 2026-11-04 | NEW | Gitleaks, secret filenames, tests, gate, clone, README links |
| `demo/` studio polish | done | 2026-11-04 | NEW | Evidence panel, Muse Spark default, compare-without-harness, 960px |
| `demo/` product UI | done | 2026-11-04 | NEW | Idea/phone split, store-check sheet, product copy. Not the Ive product. |
| `harness report --html` | done | 2026-11-04 | NEW | Static GitHub Pages page; no keys, no live calls |
| `src/preflight` +4 checks | done | 2026-11-04 | NEW | smoke_tests_pass, account_deletion_erases_data, home_not_webview, remote_code |
| `src/harness/sameness.py` | done | 2026-11-04 | NEW | Pairwise Jaccard 5-grams over lib/app; report only |
| `scaffold_only` mode | done | 2026-11-04 | NEW | Capsule + guard, one build call, zero repair rounds |
| `lib/core/auth/firebase_*` | done | 2026-11-04 | NEW | Config-gated FirebaseAuthService; fake gateway tests; no live calls |
| `lib/core/billing/revenuecat_*` | done | 2026-11-04 | NEW | Config-gated RevenueCatBillingService; fake gateway tests; paywall offerings; no live calls |
| `docs/revenuecat.md` | done | 2026-11-04 | NEW | Product setup in ASC + RevenueCat; unverified until a sandbox purchase |
| `lib/core/kit/` | done | 2026-11-04 | NEW | Token-driven widgets (RocketScaffold, ItemCard, …). Protected. |
| `docs/kit_api.md` | done | 2026-11-04 | NEW | Compact kit API; concatenated into CAPSULE_PREFIX |
| `kit_usage`, `not_text_only` | done | 2026-11-04 | NEW | Preflight WARN checks on generated screens |
| preview tour | done | 2026-11-04 | NEW | Hash routes + studio chips for locked flows; web preview starts at onboarding |
| studio guided flow | done | 2026-11-04 | NEW | Describe → look → build → check → ship; live SSE stepper; report empty state |
| studio chat | done | 2026-11-04 | NEW | Single text field; first send builds, later sends call `/api/improve` on the same app |
| studio grok UI | done | 2026-11-04 | NEW | Dark Grok-style chat: centered empty state, pill composer, send morph, motion. Phone stays. |
| live quality check | done | 2026-11-04 | NEW | 3 Muse Spark builds, $1.50 cap; see docs/quality_check.md |

**Removed after Day 1:** `src/sketch2layout/`, SAM adapter, `meta-sam-parser`, wireframe samples, SAM smoke script.

## Pre-existing concepts reimplemented during the event

These are **ideas** common in app-shipping tooling, reimplemented here from scratch for the hackathon (not copied from private Ive code):

| Concept | Where in this repo |
| --- | --- |
| Protected-file guard (pilot cannot edit core) | `src/harness/guard.py` + `capsule.manifest.json` |
| File operations format (write / patch / delete) | `src/harness/apply.py`, guard validator |
| Compile / repair loop | `src/harness/build.py` (gate-driven, max 2 rounds) |
| Design-direction gallery | `src/harness/design.py` + `harness serve` |

## Third-party dependencies (`uv.lock`)

| Package | Use |
| --- | --- |
| httpx, pydantic, python-dotenv, pillow | Meta adapters + resize |
| pytest, pre-commit (dev) | Tests, gitleaks hook |
| Flutter: go_router, flutter_markdown, firebase_core, firebase_auth, purchases_flutter, flutter_launcher_icons | Capsule template |

## Preexisting code

None in `preexisting/`. Day 1 SAM negative finding kept in `docs/day1-findings.md` only.
