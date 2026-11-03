"""Fair ivebench sweep: each idea × harness/bare, same Pilot, honest results JSON."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pilot.protocol import BudgetExceeded
from pilot.session import PilotSession
from pilot.usage_log import spent_for_run

from .build import CreateFn, GateFn, run_build

MakeSession = Callable[[str, float | None], PilotSession]


def load_ideas(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def run_sweep(
    *,
    ideas: list[dict[str, Any]],
    make_session: MakeSession,
    capsule: Path,
    out_dir: Path,
    runs: Path,
    usage_path: Path,
    modes: tuple[str, ...] = ("harness", "bare"),
    max_usd: float | None = None,
    build_web: bool = False,
    gate_fn: GateFn | None = None,
    create_fn: CreateFn | None = None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    run_ids: list[str] = []
    for idea in ideas:
        idea_id = str(idea["id"])
        blurb = str(idea.get("blurb") or idea.get("title") or idea_id)
        for mode in modes:
            run_id = f"sweep-{idea_id}-{mode}"
            spent = sum(spent_for_run(usage_path, rid) for rid in run_ids)
            remaining = None if max_usd is None else round(max_usd - spent, 6)
            if remaining is not None and remaining <= 0:
                rows.append(
                    {
                        "idea": idea_id,
                        "mode": mode,
                        "run_id": run_id,
                        "ok": False,
                        "error": "budget",
                        "skipped": True,
                    }
                )
                continue
            session = make_session(run_id, remaining)
            try:
                result = run_build(
                    blurb,
                    session,
                    mode=mode,
                    run_dir=runs / run_id,
                    capsule=capsule,
                    gate_fn=gate_fn,
                    create_fn=create_fn if mode == "bare" else None,
                    build_web=build_web,
                )
            except BudgetExceeded as exc:
                run_ids.append(run_id)
                rows.append(
                    {
                        "idea": idea_id,
                        "title": idea.get("title"),
                        "mode": mode,
                        "run_id": run_id,
                        "ok": False,
                        "error": str(exc),
                        "skipped": False,
                    }
                )
                continue
            run_ids.append(run_id)
            row = {
                "idea": idea_id,
                "title": idea.get("title"),
                "mode": mode,
                "run_id": run_id,
                "ok": result.get("ok"),
                "error": result.get("error"),
                "repair_rounds": result.get("repair_rounds"),
                "tokens": result.get("tokens"),
                "wall_ms": result.get("wall_ms"),
            }
            rows.append(row)
            (out_dir / f"{run_id}.json").write_text(
                json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8"
            )
    summary = {
        "n": len(rows),
        "ok_harness": sum(1 for r in rows if r.get("mode") == "harness" and r.get("ok")),
        "ok_bare": sum(1 for r in rows if r.get("mode") == "bare" and r.get("ok")),
        "spent_usd": sum(spent_for_run(usage_path, rid) for rid in run_ids),
        "rows": rows,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary
