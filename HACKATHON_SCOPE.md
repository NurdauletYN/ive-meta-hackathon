# Hackathon scope

Every module: who wrote it, when, and origin. No code copied from the private Ive repo.

Author: NurdauletYN + Cursor agent (commit dates below).

## Direction change (2026-11-03)

Sketch / image / SAM pipeline **dropped**. Focus: **model-agnostic Flutter app-shipping harness** (Rocket capsule, file-op guard, preflight, `harness gate`).

## Modules

| Path | Status | Written | Origin | Notes |
| --- | --- | --- | --- | --- |
| `src/meta_client/*` | done | 2026-10-30 | NEW | Muse Spark + Muse Image adapters, usage logging |
| `src/meta_client/images.py` resize helpers | done | 2026-11-03 | NEW | Lanczos 1024×1024 after Muse Image |
| `scripts/day1/01`, `04` | kept | 2026-10-30 | NEW | API smoke; sketch/SAM scripts removed |
| `src/harness/guard.py` | done | 2026-11-03 | NEW | Validates file ops vs `capsule.manifest.json` |
| `src/harness/gate.py`, `cli.py` | done | 2026-11-03 | NEW | `harness gate` JSON report |
| `src/preflight/*` | done | 2026-11-03 | NEW | Seven deterministic checks + fixtures |
| `flutter_template/` | done | 2026-11-03 | NEW | Capsule app: protected `lib/core/`, editable `lib/app/` |
| `docs/preflight.md` | done | 2026-11-03 | NEW | Check descriptions; not legal advice |
| `tests/test_guard.py`, `test_preflight.py` | done | 2026-11-03 | NEW | Guard + per-check fixtures |
| `src/codegen/`, `compile_runner/`, `storepack/` | not started | — | — | Placeholder READMEs only |
| `ivebench/`, `demo/` | not started | — | — | Placeholder READMEs only |

**Removed after Day 1:** `src/sketch2layout/`, SAM adapter, `meta-sam-parser`, wireframe samples, SAM smoke script.

## Pre-existing concepts reimplemented during the event

These are **ideas** common in app-shipping tooling, reimplemented here from scratch for the hackathon (not copied from private Ive code):

| Concept | Where in this repo |
| --- | --- |
| Protected-file guard (pilot cannot edit core) | `src/harness/guard.py` + `capsule.manifest.json` |
| File operations format (write / patch / delete) | `scripts/day1/file_ops.py`, guard validator |
| Compile / repair loop **idea** | Not implemented yet; `src/compile_runner/` placeholder only |

## Third-party dependencies (`uv.lock`)

| Package | Use |
| --- | --- |
| httpx, pydantic, python-dotenv, pillow | Meta adapters + resize |
| pytest, pre-commit (dev) | Tests, gitleaks hook |
| Flutter: go_router, flutter_markdown | Capsule template |

## Preexisting code

None in `preexisting/`. Day 1 SAM negative finding kept in `docs/day1-findings.md` only.
