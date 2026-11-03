# ive-meta-hackathon

**Rocket** = locked Flutter foundation (protected `lib/core/`), guards, and store preflight verifiers.  
**Pilot** = any model that emits file operations into the editable `lib/app/` layer.

Sketch / SAM input was dropped after Day 1 (see `docs/day1-findings.md`).

## Quick start (judges, under 5 minutes)

```bash
cd ive-meta-hackathon
uv sync --all-extras
export PATH="$HOME/.local/bin:$PATH"   # gitleaks for pre-commit
pre-commit install                     # optional secret scan on commit

cd flutter_template && flutter pub get && cd ..
uv run harness gate flutter_template --build-web
uv run pytest
```

Optional Meta API smoke (needs `.env` from `.env.example`):

```bash
cp .env.example .env   # set META_API_KEY
uv run python scripts/day1/01_file_ops.py
uv run python scripts/day1/04_muse_image_icon.py
```

## Layout

| Path | Role |
| --- | --- |
| `flutter_template/` | Capsule Flutter app (`capsule.manifest.json`, protected core, editable app) |
| `src/harness/` | File-op guard + `harness gate` CLI |
| `src/preflight/` | Deterministic store-readiness checks |
| `src/meta_client/` | Muse Spark + Muse Image adapters (Pilot backends) |
| `docs/preflight.md` | What each check means (not legal advice) |
| `scripts/day1/` | Early API smoke tests (historical) |

## NEW vs PREEXISTING

| Item | Status |
| --- | --- |
| This repo and harness | **NEW** (hackathon) |
| Private Ive product code | **Not included** (adapter planned later) |
| Ideas reimplemented here | See `HACKATHON_SCOPE.md` § pre-existing concepts |

Demo GIF and eval table: not yet (eval harness not built in this phase).
