"""Run analyze, optional web build, and preflight; emit one JSON report."""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from preflight import run_preflight
from preflight.types import CheckResult, CheckStatus


@dataclass
class StepResult:
    name: str
    ok: bool
    duration_ms: float
    detail: str | None = None


@dataclass
class GateReport:
    project_dir: str
    ok: bool
    steps: list[StepResult]
    preflight: list[CheckResult]


def _run(cmd: list[str], cwd: Path) -> tuple[int, str, float]:
    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    duration_ms = round((time.perf_counter() - started) * 1000, 1)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()[:4000], duration_ms


def run_gate(project_dir: Path, *, build_web: bool = False) -> GateReport:
    project = project_dir.resolve()
    steps: list[StepResult] = []

    code, out, ms = _run(["flutter", "analyze", "--no-fatal-infos"], project)
    steps.append(StepResult("flutter_analyze", code == 0, ms, out if code else None))

    if build_web:
        code, out, ms = _run(["flutter", "build", "web", "--release"], project)
        steps.append(StepResult("flutter_build_web", code == 0, ms, out if code else None))

    preflight = run_preflight(project)
    preflight_ok = all(r.status != CheckStatus.FAIL for r in preflight)
    steps.append(
        StepResult(
            "preflight",
            preflight_ok,
            0.0,
            None if preflight_ok else "one or more checks failed",
        )
    )

    ok = all(step.ok for step in steps)
    return GateReport(
        project_dir=str(project),
        ok=ok,
        steps=steps,
        preflight=preflight,
    )


def gate_json(report: GateReport) -> str:
    payload = {
        "project_dir": report.project_dir,
        "ok": report.ok,
        "steps": [asdict(s) for s in report.steps],
        "preflight": [asdict(r) for r in report.preflight],
    }
    return json.dumps(payload, indent=2, default=str)
