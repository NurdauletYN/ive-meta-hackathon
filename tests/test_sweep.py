"""ivebench sweep: FakePilot, stubbed gate, budget skip."""

from __future__ import annotations

import json
from pathlib import Path

from harness.gate import GateReport, StepResult
from harness.sweep import load_ideas, run_sweep
from pilot.canned import APP_SPEC, BARE_OPS, FILE_OPS
from pilot.fake import FakePilot
from pilot.session import PilotSession

ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / "flutter_template"


def _pass_gate(project: Path) -> GateReport:
    return GateReport(str(project), True, [StepResult("preflight", True, 1.0)], [])


def _bare_create(dest: Path) -> None:
    dest.mkdir(parents=True)
    (dest / "lib").mkdir()
    (dest / "lib" / "main.dart").write_text("void main() {}\n", encoding="utf-8")
    (dest / "pubspec.yaml").write_text("name: bare_app\n", encoding="utf-8")
    (dest / "capsule.manifest.json").write_text(
        json.dumps({"protected_paths": ["pubspec.yaml"], "editable_paths": ["lib/**"]}),
        encoding="utf-8",
    )


def test_load_ideas() -> None:
    ideas = load_ideas(ROOT / "ivebench" / "ideas.jsonl")
    assert len(ideas) == 8
    assert ideas[0]["id"] == "tool_library"


def test_sweep_one_idea_harness_and_bare(tmp_path: Path) -> None:
    usage = tmp_path / "usage.jsonl"
    fake = FakePilot(cost_per_call=0.01)
    fake.enqueue("spec", APP_SPEC, APP_SPEC)
    fake.enqueue("file_ops", FILE_OPS, BARE_OPS)

    def make_session(run_id: str, max_usd: float | None) -> PilotSession:
        return PilotSession(fake, run_id=run_id, usage_path=usage, max_usd=max_usd)

    ideas = [{"id": "tool_library", "title": "Tools", "blurb": "borrow tools"}]
    summary = run_sweep(
        ideas=ideas,
        make_session=make_session,
        capsule=CAPSULE,
        out_dir=tmp_path / "out",
        runs=tmp_path / "runs",
        usage_path=usage,
        max_usd=3,
        build_web=False,
        gate_fn=_pass_gate,
        create_fn=_bare_create,
    )
    assert summary["n"] == 2
    assert summary["ok_harness"] == 1
    assert summary["ok_bare"] == 1
    assert (tmp_path / "out" / "summary.json").is_file()
    assert (tmp_path / "runs" / "sweep-tool_library-harness" / "project" / "skin.html").is_file()


def test_sweep_stops_on_budget(tmp_path: Path) -> None:
    usage = tmp_path / "usage.jsonl"
    fake = FakePilot(cost_per_call=0.02)

    def make_session(run_id: str, max_usd: float | None) -> PilotSession:
        return PilotSession(fake, run_id=run_id, usage_path=usage, max_usd=max_usd)

    summary = run_sweep(
        ideas=[{"id": "tool_library", "title": "Tools", "blurb": "borrow tools"}],
        make_session=make_session,
        capsule=CAPSULE,
        out_dir=tmp_path / "out",
        runs=tmp_path / "runs",
        usage_path=usage,
        max_usd=0,
        build_web=False,
        gate_fn=_pass_gate,
        create_fn=_bare_create,
    )
    assert all(r.get("skipped") for r in summary["rows"])
    assert summary["ok_harness"] == 0
    assert summary["ok_bare"] == 0
