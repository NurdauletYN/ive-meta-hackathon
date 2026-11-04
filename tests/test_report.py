"""Counts-only results.md from sweep JSON."""

from __future__ import annotations

import json
from pathlib import Path

from harness.report import render_results, write_results


def _row(**kwargs):
    base = {
        "run_id": "sweep-muse-tool_library-harness",
        "idea": "tool_library",
        "pilot": "muse",
        "mode": "harness",
        "outcome": "pass",
        "ok": True,
        "repair_rounds": 1,
        "tokens": {"est_cost_usd": 0.05, "input": 10, "cached": 0, "output": 10},
        "wall_ms": 80000,
        "error": None,
    }
    base.update(kwargs)
    return base


def test_report_splits_infra_and_quality(tmp_path: Path) -> None:
    rows = [
        _row(),
        _row(
            run_id="sweep-muse-tool_library-bare",
            mode="bare",
            outcome="infra_fail",
            ok=False,
            error="MetaRetryExhaustedError: timeout",
        ),
        _row(
            run_id="sweep-muse-book_swap-harness",
            idea="book_swap",
            outcome="quality_fail",
            ok=False,
            error="preflight failed",
            tokens={"est_cost_usd": 0.04},
        ),
    ]
    text = render_results(rows)
    assert "passed / completed" in text
    assert "1/2" in text  # muse harness: 1 pass / (1 pass + 1 quality)
    assert "infra_fail" in text
    assert "timeout" in text
    assert "not quality" in text
    assert "Limits" in text
    assert "in-memory mocks" in text
    assert "significance" not in text.lower()
    dest = write_results(tmp_path, tmp_path / "results.md")
    # empty dir → still writes
    assert dest.is_file()


def test_skips_rows_without_classified_outcome(tmp_path: Path) -> None:
    sweep = tmp_path / "sweep"
    sweep.mkdir()
    (sweep / "sweep-muse-old-harness.json").write_text(
        json.dumps({"pilot": "muse", "mode": "harness", "ok": True, "idea": "should-not-appear"}) + "\n",
        encoding="utf-8",
    )
    dest = tmp_path / "results.md"
    write_results(sweep, dest)
    text = dest.read_text(encoding="utf-8")
    assert "should-not-appear" not in text
    assert "0/0" in text


def test_write_results_from_files(tmp_path: Path) -> None:
    sweep = tmp_path / "sweep"
    sweep.mkdir()
    (sweep / "sweep-muse-tool_library-harness.json").write_text(
        json.dumps(_row()) + "\n", encoding="utf-8"
    )
    dest = tmp_path / "results.md"
    write_results(sweep, dest)
    text = dest.read_text(encoding="utf-8")
    assert "tool_library" in text
    assert "muse" in text
