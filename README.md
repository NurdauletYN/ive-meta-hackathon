# ive-meta-hackathon

**Rocket** = locked Flutter foundation (protected `lib/core/`), guards, and store preflight verifiers.  
**Pilot** = any model that proposes design directions and emits file operations into the editable `lib/app/` layer.

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
uv run harness ui --port 8765   # http://127.0.0.1:8765/  phone studio; fake first
```

Offline Pilot loop (no API key): `FakePilot` is canned JSON for tests.

```bash
uv run pytest tests/test_pilot.py
```

Design / build against a live Pilot (Muse Spark by default):

```bash
uv run harness design "Neighborhood tool library" --pilot muse --out runs/demo-design --max-usd 3
uv run harness design pick demo-design 1
uv run harness serve runs/demo-design
uv run harness build "Neighborhood tool library" --pilot muse --mode harness --run demo-h --max-usd 3
uv run harness build "Neighborhood tool library" --pilot muse --mode bare --run demo-b --max-usd 3
```

Optional Meta API smoke (needs `.env` from `.env.example`):

```bash
cp .env.example .env   # set META_API_KEY
uv run python scripts/day1/01_file_ops.py
uv run python scripts/day1/04_muse_image_icon.py
uv run harness build "Neighborhood tool library" --pilot muse --mode harness --run smoke-h --max-usd 3
```

`--max-usd` sums `ivebench/results/usage.jsonl` for the current `run_id` and exits 3 when the cap is crossed. OpenAI-compatible Pilots (Baseten Muse Spark Open, etc.) are listed in `pilots.yaml`; they refuse to call the network if `OPENAI_COMPAT_*` is unset.

## Layout

| Path | Role |
| --- | --- |
| `flutter_template/` | Capsule Flutter app (`capsule.manifest.json`, protected core, editable app) |
| `src/harness/` | Guard, gate, design gallery, spec/build/repair CLI |
| `src/pilot/` | `complete_json` protocol, Fake/Muse/OpenAI-compat, budget, usage log |
| `src/preflight/` | Deterministic store-readiness checks |
| `src/meta_client/` | Muse Spark + Muse Image adapters (Pilot backends) |
| `ivebench/ideas.jsonl` | Eight eval ideas |
| `docs/preflight.md` | What each check means (not legal advice) |
| `scripts/day1/` | Early API smoke tests (historical) |

## NEW vs PREEXISTING

| Item | Status |
| --- | --- |
| This repo and harness | **NEW** (hackathon) |
| Private Ive product code | **Not included** (adapter planned later) |
| Ideas reimplemented here | See `HACKATHON_SCOPE.md` § pre-existing concepts |

Demo GIF and eval table: not yet (full ivebench sweep not in this phase).
