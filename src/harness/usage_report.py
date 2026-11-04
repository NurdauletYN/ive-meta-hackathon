"""Aggregate ivebench/results/usage.jsonl by model and stage. No keys."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

MARKER_START = "<!-- usage-report:start -->"
MARKER_END = "<!-- usage-report:end -->"


def load_usage(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            rows.append(data)
    return rows


def _num(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {"calls": 0, "input": 0, "cached": 0, "output": 0, "cost": 0.0}
    )
    for row in rows:
        model = str(row.get("model") or "unknown")
        stage = str(row.get("stage") or row.get("op") or "unknown")
        b = buckets[(model, stage)]
        b["calls"] += 1
        b["input"] += _num(row.get("input_tokens"))
        b["cached"] += _num(row.get("cached_tokens"))
        b["output"] += _num(row.get("output_tokens"))
        b["cost"] += _num(row.get("est_cost_usd"))
    out = [
        {
            "model": model,
            "stage": stage,
            "calls": int(vals["calls"]),
            "input_tokens": int(vals["input"]),
            "cached_tokens": int(vals["cached"]),
            "output_tokens": int(vals["output"]),
            "est_cost_usd": round(vals["cost"], 6),
        }
        for (model, stage), vals in sorted(buckets.items())
    ]
    return out


def render_usage(rows: list[dict[str, Any]]) -> str:
    agg = aggregate(rows)
    lines = [
        "### Usage by model and stage",
        "",
        "Generated from `ivebench/results/usage.jsonl` by `harness usage-report`. Counts only.",
        "",
        "| Model | Stage | Calls | Tokens in | Cached | Tokens out | Cost USD |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    if not agg:
        lines.append("| — | — | 0 | 0 | 0 | 0 | 0 |")
    else:
        for row in agg:
            lines.append(
                f"| {row['model']} | {row['stage']} | {row['calls']} | "
                f"{row['input_tokens']} | {row['cached_tokens']} | {row['output_tokens']} | "
                f"{row['est_cost_usd']:.6f} |"
            )
        total_calls = sum(r["calls"] for r in agg)
        total_in = sum(r["input_tokens"] for r in agg)
        total_cached = sum(r["cached_tokens"] for r in agg)
        total_out = sum(r["output_tokens"] for r in agg)
        total_cost = sum(r["est_cost_usd"] for r in agg)
        lines.append(
            f"| **total** | | {total_calls} | {total_in} | {total_cached} | {total_out} | {total_cost:.6f} |"
        )
    lines += [
        "",
        "SAM 3.1 rows are Day 1 history; that path was removed from the product.",
        "This table is usage, not a quality eval. Infra timeouts still appear as calls with `ok: false`.",
        "",
    ]
    return "\n".join(lines)


def patch_metause(metause: Path, table: str) -> Path:
    body = metause.read_text(encoding="utf-8") if metause.is_file() else ""
    block = f"{MARKER_START}\n{table.rstrip()}\n{MARKER_END}\n"
    if MARKER_START in body and MARKER_END in body:
        start = body.index(MARKER_START)
        end = body.index(MARKER_END) + len(MARKER_END)
        body = body[:start] + block.rstrip() + body[end:]
        if not body.endswith("\n"):
            body += "\n"
    else:
        body = (body.rstrip() + "\n\n" + block) if body.strip() else block
    metause.write_text(body, encoding="utf-8")
    return metause
