# Day 1 smoke tests (historical)

Only **01_file_ops** and **04_muse_image_icon** remain. Sketch and SAM scripts were removed with the direction change.

```bash
uv run python scripts/day1/01_file_ops.py
uv run python scripts/day1/04_muse_image_icon.py   # saves icon_raw.png + icon_1024.png (Lanczos)
```

See `docs/day1-findings.md` for Oct 30 API results.
