"""App builder: spec -> guarded file ops -> gate-driven repair. harness or bare mode."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from pilot.schemas import APP_SPEC_SCHEMA, FILE_OPS_SCHEMA, AppSpec, schema_errors
from pilot.session import PilotSession

from .apply import apply_operations
from .copy_project import copy_tree
from .gate import GateReport, run_gate
from .guard import FileOp, validate_operations
from preflight.types import CheckStatus

from .prompts import BARE_REQUIREMENTS, CAPSULE_PREFIX

HARNESS_ALLOWED = ["lib/app/features/**", "lib/app/strings.dart", "lib/app/strings"]
MAX_GUARD_ROUNDS = 2
MAX_GATE_REPAIRS = 2

GateFn = Callable[[Path], GateReport]
CreateFn = Callable[[Path], None]


def _schema_loop(session: PilotSession, system: str, user: str, schema: dict, tag: str, model: type) -> Any:
    payload = session.complete_json(system, user, schema, tag)
    errors = schema_errors(payload, model)
    attempts = 0
    while errors and attempts < 2:
        attempts += 1
        payload = session.complete_json(
            system,
            "JSON failed validation:\n" + "\n".join(errors) + "\n\nOriginal request:\n" + user,
            schema,
            tag,
        )
        errors = schema_errors(payload, model)
    if errors:
        raise ValueError(f"{tag} JSON invalid after retries: " + "; ".join(errors))
    return model.model_validate(payload)


def apply_spec_assets(project: Path, spec: AppSpec) -> None:
    onboarding = {
        "slots": {
            "hero_title": spec.onboarding[0].title,
            "hero_body": spec.onboarding[0].body,
            "slide2_title": spec.onboarding[1].title,
            "slide2_body": spec.onboarding[1].body,
            "slide3_title": spec.onboarding[2].title,
            "slide3_body": spec.onboarding[2].body,
        }
    }
    dest = project / "assets" / "onboarding" / "onboarding.json"
    if dest.parent.is_dir() or dest.parent.parent.is_dir():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(onboarding, indent=2) + "\n", encoding="utf-8")


def _ops_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    ops = payload.get("operations")
    if not isinstance(ops, list):
        return []
    return ops


def request_and_apply_ops(
    session: PilotSession,
    system: str,
    user: str,
    project: Path,
    *,
    allowed_prefixes: list[str] | None,
    extra_feedback: str = "",
) -> dict[str, Any]:
    log: dict[str, Any] = {"guard_rounds": 0, "violations": [], "apply_errors": []}
    prompt = user if not extra_feedback else user + "\n\n" + extra_feedback
    payload = session.complete_json(system, prompt, FILE_OPS_SCHEMA, "file_ops")
    for round_i in range(MAX_GUARD_ROUNDS + 1):
        ops = _ops_from_payload(payload)
        violations = validate_operations(project, ops, allowed_prefixes=allowed_prefixes)
        if not violations:
            parsed = [FileOp.model_validate(raw) for raw in ops]
            apply_errors = apply_operations(project, parsed)
            log["apply_errors"] = [asdict(e) for e in apply_errors]
            if apply_errors and round_i < MAX_GUARD_ROUNDS:
                log["guard_rounds"] = round_i + 1
                payload = session.complete_json(
                    system,
                    prompt
                    + "\n\nApply errors:\n"
                    + "\n".join(e.message for e in apply_errors)
                    + "\nReturn corrected file operations only.",
                    FILE_OPS_SCHEMA,
                    "file_ops",
                )
                continue
            log["applied"] = len(parsed)
            return log
        log["violations"].extend(asdict(v) for v in violations)
        if round_i >= MAX_GUARD_ROUNDS:
            break
        log["guard_rounds"] = round_i + 1
        payload = session.complete_json(
            system,
            prompt
            + "\n\nGuard violations (do not repeat them):\n"
            + "\n".join(f"{v.code}: {v.message}" for v in violations)
            + "\nReturn corrected file operations only.",
            FILE_OPS_SCHEMA,
            "file_ops",
        )
    log["applied"] = 0
    return log


def _token_totals(usage_path: Path, run_id: str) -> dict[str, Any]:
    import json as _json

    from pilot.usage_log import spent_for_run

    inp = cached = out = 0
    if usage_path.is_file():
        for line in usage_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = _json.loads(line)
            if row.get("run_id") != run_id:
                continue
            inp += int(row.get("input_tokens") or 0)
            cached += int(row.get("cached_tokens") or 0)
            out += int(row.get("output_tokens") or 0)
    return {
        "input": inp,
        "cached": cached,
        "output": out,
        "est_cost_usd": spent_for_run(usage_path, run_id),
    }


def _gate_summary(report: GateReport) -> dict[str, Any]:
    return {
        "ok": report.ok,
        "steps": [asdict(s) for s in report.steps],
        "preflight": [asdict(r) for r in report.preflight],
    }


def _failing_text(report: GateReport) -> str:
    lines: list[str] = []
    for step in report.steps:
        if not step.ok:
            lines.append(f"{step.name}: {step.detail or 'failed'}")
    for check in report.preflight:
        if check.status == CheckStatus.FAIL:
            loc = f"{check.file}:{check.line}" if check.file else ""
            lines.append(f"preflight {check.check_id} {loc}: {check.message}")
    return "\n".join(lines) or "gate failed"


def _read_relevant_files(project: Path, limit: int = 8) -> str:
    chunks: list[str] = []
    lib = project / "lib"
    if not lib.is_dir():
        return ""
    for path in sorted(lib.rglob("*.dart"))[:limit]:
        chunks.append(f"--- {path.relative_to(project)} ---\n{path.read_text(encoding='utf-8')[:4000]}")
    return "\n\n".join(chunks)


def default_flutter_create(dest: Path, pubspec: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    subprocess.run(
        ["flutter", "create", str(dest), "--org", "com.rocket.bare", "--project-name", "bare_app", "--platforms=web"],
        check=True,
        capture_output=True,
        text=True,
    )
    shutil.copyfile(pubspec, dest / "pubspec.yaml")
    (dest / "capsule.manifest.json").write_text(
        json.dumps({"protected_paths": ["pubspec.yaml", "pubspec.lock"], "editable_paths": ["lib/**"]}),
        encoding="utf-8",
    )


def run_build(
    idea: str,
    session: PilotSession,
    *,
    mode: str,
    run_dir: Path,
    capsule: Path,
    gate_fn: GateFn | None = None,
    create_fn: CreateFn | None = None,
    build_web: bool = True,
) -> dict[str, Any]:
    started = time.perf_counter()
    stages: dict[str, float] = {}
    run_dir.mkdir(parents=True, exist_ok=True)
    project = run_dir / "project"
    gate = gate_fn or (lambda p: run_gate(p, build_web=build_web))

    t0 = time.perf_counter()
    if mode == "harness":
        copy_tree(capsule, project)
        system = CAPSULE_PREFIX
        allowed = HARNESS_ALLOWED
    elif mode == "bare":
        creator = create_fn or (lambda dest: default_flutter_create(dest, capsule / "pubspec.yaml"))
        creator(project)
        system = BARE_REQUIREMENTS
        allowed = None
    else:
        raise ValueError("mode must be harness or bare")
    stages["prepare_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    spec: AppSpec = _schema_loop(
        session,
        system,
        f"Write an AppSpec for this idea:\n{idea}",
        APP_SPEC_SCHEMA,
        "spec",
        AppSpec,
    )
    (run_dir / "spec.json").write_text(spec.model_dump_json(indent=2) + "\n", encoding="utf-8")
    apply_spec_assets(project, spec)
    stages["spec_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    build_user = (
        f"AppSpec:\n{spec.model_dump_json()}\n\nEmit file operations to implement the spec inside the project."
    )
    ops_log = request_and_apply_ops(session, system, build_user, project, allowed_prefixes=allowed)
    stages["build_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    t0 = time.perf_counter()
    report = gate(project)
    repair_rounds = 0
    while not report.ok and repair_rounds < MAX_GATE_REPAIRS:
        repair_rounds += 1
        fail_text = _failing_text(report)
        files = _read_relevant_files(project)
        request_and_apply_ops(
            session,
            system,
            build_user,
            project,
            allowed_prefixes=allowed,
            extra_feedback=f"Gate failed (round {repair_rounds}). Fix ONLY these errors:\n{fail_text}\n\nRelevant files:\n{files}",
        )
        report = gate(project)
    stages["gate_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    token_totals = _token_totals(session.usage_path, session.run_id)
    result = {
        "pilot": session.pilot.name,
        "mode": mode,
        "idea": idea,
        "run_id": session.run_id,
        "ok": report.ok,
        "gate": _gate_summary(report),
        "repair_rounds": repair_rounds,
        "ops": ops_log,
        "tokens": token_totals,
        "wall_ms": round((time.perf_counter() - started) * 1000, 1),
        "stage_ms": stages,
        "project": str(project),
    }
    (run_dir / "result.json").write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    return result
