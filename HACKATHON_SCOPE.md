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
| `src/preflight/*` | done | 2026-11-03 | NEW | Seven deterministic checks + fixtures |
| `flutter_template/` | done | 2026-11-03 | NEW | Capsule: protected `lib/core/`, editable `lib/app/` |
| `flutter_template/lib/app/features/registry.dart` | done | 2026-11-03 | NEW | Pilot-editable extra routes; one-time human core router change in `capsule.manifest.json` `core_changes` |
| `ivebench/ideas.jsonl` | done | 2026-11-03 | NEW | 8 app ideas (no medical / mental health / nutrition / sports / job screening / political) |
| `docs/preflight.md` | done | 2026-11-03 | NEW | Check descriptions; not legal advice |
| `tests/test_guard.py`, `test_preflight.py`, `test_pilot.py` | done | 2026-11-03 | NEW | Guard, preflight, FakePilot e2e (repair, guard, invalid JSON, budget) |
| `src/codegen/`, `compile_runner/`, `storepack/` | not started | — | — | Placeholder READMEs only; repair loop lives in `src/harness/build.py` |
| `demo/` | not started | — | — | Placeholder README only |

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
| Flutter: go_router, flutter_markdown | Capsule template |

## Preexisting code

None in `preexisting/`. Day 1 SAM negative finding kept in `docs/day1-findings.md` only.
