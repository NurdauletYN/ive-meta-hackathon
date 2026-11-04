"""Offline aggregation of usage.jsonl."""

from __future__ import annotations

import json
from pathlib import Path

from harness.usage_report import aggregate, patch_metause, render_usage


def test_aggregate_by_model_and_stage(tmp_path: Path) -> None:
    path = tmp_path / "usage.jsonl"
    path.write_text(
        json.dumps(
            {
                "model": "muse-spark-1.3",
                "stage": "spec",
                "input_tokens": 10,
                "cached_tokens": 2,
                "output_tokens": 20,
                "est_cost_usd": 0.01,
            }
        )
        + "\n"
        + json.dumps(
            {
                "model": "muse-spark-1.3",
                "op": "spec",
                "input_tokens": 5,
                "cached_tokens": 0,
                "output_tokens": 7,
                "est_cost_usd": 0.02,
            }
        )
        + "\n"
        + json.dumps(
            {
                "model": "muse-image-1.0",
                "op": "image.generate",
                "input_tokens": None,
                "est_cost_usd": 0.01,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    text = path.read_text(encoding="utf-8")
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    agg = { (r["model"], r["stage"]): r for r in aggregate(rows) }
    spark = agg[("muse-spark-1.3", "spec")]
    assert spark["calls"] == 2
    assert spark["input_tokens"] == 15
    assert spark["cached_tokens"] == 2
    assert spark["output_tokens"] == 27
    assert abs(spark["est_cost_usd"] - 0.03) < 1e-9
    md = render_usage(rows)
    assert "muse-spark-1.3" in md
    assert "muse-image-1.0" in md
    assert "0.030000" in md or "0.03" in md
    assert "API_KEY" not in md


def test_empty_usage() -> None:
    md = render_usage([])
    assert "| — | — | 0 | 0 | 0 | 0 | 0 |" in md


def test_patch_metause_replaces_markers(tmp_path: Path) -> None:
    dest = tmp_path / "METAUSE.md"
    dest.write_text("intro\n<!-- usage-report:start -->\nold\n<!-- usage-report:end -->\nend\n", encoding="utf-8")
    patch_metause(dest, "### Usage\n\n| Model | Calls |\n")
    text = dest.read_text(encoding="utf-8")
    assert "old" not in text
    assert "### Usage" in text
    assert text.startswith("intro")
    assert text.strip().endswith("end")
