"""Append one usage JSONL line per pilot call (run_id, pilot, stage)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .protocol import Usage

DEFAULT_USAGE_PATH = Path("ivebench/results/usage.jsonl")


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def append_usage(
    path: Path,
    *,
    run_id: str,
    pilot: str,
    stage: str,
    usage: Usage,
    model: str,
    ok: bool = True,
    error: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "ts": now_iso(),
        "run_id": run_id,
        "pilot": pilot,
        "stage": stage,
        "model": model,
        "ok": ok,
        "input_tokens": usage.input_tokens,
        "cached_tokens": usage.cached_tokens,
        "output_tokens": usage.output_tokens,
        "latency_ms": usage.latency_ms,
        "est_cost_usd": usage.est_cost_usd,
        "error": error,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def spent_for_run(path: Path, run_id: str) -> float:
    if not path.is_file():
        return 0.0
    total = 0.0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("run_id") != run_id:
            continue
        total += float(row.get("est_cost_usd") or 0.0)
    return total
