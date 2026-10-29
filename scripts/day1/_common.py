"""Shared helpers for the Day 1 smoke tests.

Every smoke script prints one `PASS` or `FAIL` line, saves its raw outputs under
ivebench/results/day1/, and exits 0 on PASS, 1 on FAIL, 2 on setup problems (no key).
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from meta_client import MetaClient, MetaConfigError, MetaError, load_settings

DAY1_DIR = Path(__file__).resolve().parent
ROOT = DAY1_DIR.parents[1]
SAMPLES_DIR = DAY1_DIR / "samples"
RESULTS_DIR = ROOT / "ivebench" / "results" / "day1"


def load_client() -> MetaClient:
    try:
        settings = load_settings()
    except MetaConfigError as exc:
        print(f"SETUP FAIL: {exc}")
        sys.exit(2)
    return MetaClient(settings)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_guarded(main: Callable[[], int]) -> None:
    """Run a smoke test; turn any Meta error into a FAIL line instead of a traceback."""
    try:
        code = main()
    except MetaError as exc:
        print(f"FAIL: Meta API error: {exc}")
        code = 1
    sys.exit(code)


def verdict(name: str, passed: bool, detail: str) -> int:
    print(f"{'PASS' if passed else 'FAIL'} {name}: {detail}")
    return 0 if passed else 1
