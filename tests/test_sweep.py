"""ivebench sweep: FakePilot, infra retry, quality fail, resume, dirty tree."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from harness.gate import GateReport, StepResult
from harness.sweep import DirtyTreeError, load_ideas, run_id_for, run_sweep
from pilot.canned import APP_SPEC, BARE_OPS, TOOL_CATALOG
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


def _session_fn(fake: FakePilot, usage: Path):
    def make_session(run_id: str, _pilot: str, max_usd: float | None) -> PilotSession:
        return PilotSession(fake, run_id=run_id, usage_path=usage, max_usd=max_usd)

    return make_session


def test_load_ideas() -> None:
    ideas = load_ideas(ROOT / "ivebench" / "ideas.jsonl")
    assert len(ideas) == 8
    assert ideas[0]["id"] == "tool_library"


def test_sweep_one_idea_harness_and_bare(tmp_path: Path) -> None:
    usage = tmp_path / "usage.jsonl"
    fake = FakePilot(cost_per_call=0.01)
    fake.enqueue("spec", APP_SPEC, APP_SPEC)
    fake.enqueue("catalog", TOOL_CATALOG)
    fake.enqueue("file_ops", BARE_OPS)
    ideas = [{"id": "tool_library", "title": "Tools", "blurb": "borrow tools"}]
    summary = run_sweep(
        ideas=ideas,
        make_session=_session_fn(fake, usage),
        capsule=CAPSULE,
        out_dir=tmp_path / "out",
        runs=tmp_path / "runs",
        usage_path=usage,
        pilots=["fake"],
        max_usd=3,
        build_web=False,
        gate_fn=_pass_gate,
        create_fn=_bare_create,
        sha="deadbeef",
        log_path=tmp_path / "runs" / "sweep.log",
    )
    assert summary["n"] == 2
    assert summary["ok_harness"] == 1
    assert summary["ok_bare"] == 1
    rid = run_id_for("fake", "tool_library", "harness")
    payload = json.loads((tmp_path / "out" / f"{rid}.json").read_text(encoding="utf-8"))
    assert payload["git_sha"] == "deadbeef"
    assert payload["outcome"] == "pass"
    assert "stage_ms" in payload
    assert (tmp_path / "runs" / rid / "project" / "skin.html").is_file()
    assert (tmp_path / "runs" / "sweep.log").is_file()


def test_sweep_stops_on_budget(tmp_path: Path) -> None:
    usage = tmp_path / "usage.jsonl"
    fake = FakePilot(cost_per_call=0.02)
    summary = run_sweep(
        ideas=[{"id": "tool_library", "title": "Tools", "blurb": "borrow tools"}],
        make_session=_session_fn(fake, usage),
        capsule=CAPSULE,
        out_dir=tmp_path / "out",
        runs=tmp_path / "runs",
        usage_path=usage,
        pilots=["fake"],
        max_usd=0,
        build_web=False,
        gate_fn=_pass_gate,
        create_fn=_bare_create,
    )
    assert all(r.get("skipped") for r in summary["rows"])
    assert summary["ok_harness"] == 0


def test_timeout_classified_infra_and_retried(tmp_path: Path) -> None:
    usage = tmp_path / "usage.jsonl"
    fake = FakePilot()
    calls = {"n": 0}

    def execute(*_a, **_k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("timeout: The request timed out")
        return {
            "ok": True,
            "pilot": "fake",
            "repair_rounds": 0,
            "tokens": {"input": 1, "cached": 0, "output": 1, "est_cost_usd": 0.0},
            "wall_ms": 10,
            "stage_ms": {"spec_ms": 1},
        }

    summary = run_sweep(
        ideas=[{"id": "tool_library", "title": "Tools", "blurb": "x"}],
        make_session=_session_fn(fake, usage),
        capsule=CAPSULE,
        out_dir=tmp_path / "out",
        runs=tmp_path / "runs",
        usage_path=usage,
        pilots=["fake"],
        modes=("harness",),
        execute=execute,
        sha="abc",
    )
    assert calls["n"] == 2
    row = summary["rows"][0]
    assert row["outcome"] == "pass"
    assert row["retried"] is True


def test_quality_failure(tmp_path: Path) -> None:
    usage = tmp_path / "usage.jsonl"
    fake = FakePilot()

    def execute(*_a, **_k):
        return {
            "ok": False,
            "error": "preflight failed",
            "pilot": "fake",
            "repair_rounds": 2,
            "tokens": {"input": 1, "cached": 0, "output": 1, "est_cost_usd": 0.0},
            "wall_ms": 10,
            "stage_ms": {},
        }

    summary = run_sweep(
        ideas=[{"id": "tool_library", "title": "Tools", "blurb": "x"}],
        make_session=_session_fn(fake, usage),
        capsule=CAPSULE,
        out_dir=tmp_path / "out",
        runs=tmp_path / "runs",
        usage_path=usage,
        pilots=["fake"],
        modes=("harness",),
        execute=execute,
    )
    assert summary["rows"][0]["outcome"] == "quality_fail"
    assert summary["quality_fail"] == 1
    assert summary["infra"] == 0


def test_resume_skips_completed(tmp_path: Path) -> None:
    usage = tmp_path / "usage.jsonl"
    fake = FakePilot()
    out = tmp_path / "out"
    rid = run_id_for("fake", "tool_library", "harness")
    (out).mkdir()
    (out / f"{rid}.json").write_text(
        json.dumps({"outcome": "pass", "ok": True, "retried": False, "run_id": rid}) + "\n",
        encoding="utf-8",
    )
    called = {"n": 0}

    def execute(*_a, **_k):
        called["n"] += 1
        raise AssertionError("should not run")

    summary = run_sweep(
        ideas=[{"id": "tool_library", "title": "Tools", "blurb": "x"}],
        make_session=_session_fn(fake, usage),
        capsule=CAPSULE,
        out_dir=out,
        runs=tmp_path / "runs",
        usage_path=usage,
        pilots=["fake"],
        modes=("harness",),
        execute=execute,
    )
    assert called["n"] == 0
    assert summary["rows"][0].get("resumed") is True


def test_dirty_tree_refusal(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / "dirty.txt").write_text("nope\n", encoding="utf-8")
    usage = tmp_path / "usage.jsonl"
    fake = FakePilot()
    with pytest.raises(DirtyTreeError):
        run_sweep(
            ideas=[{"id": "tool_library", "title": "T", "blurb": "x"}],
            make_session=_session_fn(fake, usage),
            capsule=CAPSULE,
            out_dir=tmp_path / "out",
            runs=tmp_path / "runs",
            usage_path=usage,
            pilots=["fake"],
            modes=("harness",),
            git_repo=repo,
            require_clean_git=True,
            execute=lambda *_a, **_k: {"ok": True},
        )
