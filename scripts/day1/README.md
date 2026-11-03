# Day 1 smoke tests

Four checks from the kickoff plan. Each prints one `PASS` or `FAIL` line and saves raw outputs
under `ivebench/results/day1/`.

| Script | Check | Calls | Pass rule |
| --- | --- | --- | --- |
| `01_file_ops.py` | (a) Muse Spark returns file-operations JSON for a tiny Flutter prompt, 10 runs | 10 × `muse-spark-1.3` (structured output) | ≥ 9/10 runs produce exactly the expected write/patch/delete ops |
| `02_image_input.py` | (b) Muse Spark accepts a sketch as an image and reads it | 3 × `muse-spark-1.3` with `input_image` | every sketch accepted, and ≥ half of expected element types reported |
| `03_sam_samples.py` | (c) SAM 3.1 returns masks for button / text field / image / card on every sketch | 12 × `sam-3.1` | every expected element type returns ≥ 1 mask; overlays saved |
| `04_muse_image_icon.py` | (d) Muse Image generates a 1024×1024 app icon | 1 × `muse-image-1.0` | decoded image is exactly 1024×1024 |

## Run

```bash
uv sync --all-extras                 # Python 3.11 venv from uv.lock
cp .env.example .env                 # then put your key in META_API_KEY
uv run python scripts/day1/make_samples.py   # only if samples/ is missing (deterministic)
uv run python scripts/day1/01_file_ops.py
uv run python scripts/day1/02_image_input.py
uv run python scripts/day1/03_sam_samples.py
uv run python scripts/day1/04_muse_image_icon.py
```

Exit codes: `0` pass, `1` fail, `2` setup problem (no key).

## Sketches are stand-ins

`samples/` holds three **synthetic** wireframes drawn by `make_samples.py` (fixed seed, byte-identical
on re-run). They are not photos of hand-drawn sketches. Before quoting any numbers, add real
hand-drawn photos (PNG, JPEG or WebP) to `samples/`, list each one with its expected element counts in
`samples/manifest.json`, and re-run. Scripts 02 and 03 read the sketches listed in the manifest.
