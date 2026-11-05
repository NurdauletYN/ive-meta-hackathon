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

from pilot.protocol import BudgetExceeded
from pilot.schemas import APP_SPEC_SCHEMA, CATALOG_SCHEMA, FILE_OPS_SCHEMA, AppCatalog, AppSpec, schema_errors
from pilot.session import PilotSession

from .apply import apply_operations
from .copy_project import copy_tree
from .gate import GateReport, StepResult, run_gate
from .guard import FileOp, validate_operations
from preflight.types import CheckStatus

from .branding import apply_branding
from .prompts import BARE_REQUIREMENTS, CAPSULE_PREFIX
from .skin import write_skin_from_project
from .kitlint import kit_violations, rewrite_raw_material
from .kit_writer import write_app_catalog
from .palettes import apply_palette, current_palette, palette_from_instruction, pick_palette
from .tokens import apply_tokens
from pilot.schemas import Direction

HARNESS_ALLOWED = ["lib/app/features/**", "lib/app/strings.dart", "lib/app/strings"]
MAX_GUARD_ROUNDS = 2
MAX_GATE_REPAIRS = 2

GateFn = Callable[[Path], GateReport]
CreateFn = Callable[[Path], None]

_KIT_FONTS = """  fonts:
    - family: KitSans
      fonts:
        - asset: lib/core/kit/fonts/DMSans-Regular.ttf
        - asset: lib/core/kit/fonts/DMSans-SemiBold.ttf
          weight: 600
        - asset: lib/core/kit/fonts/DMSans-Bold.ttf
          weight: 700
"""


def _ensure_kit_pubspec(project: Path) -> None:
    pub = project / "pubspec.yaml"
    if not pub.is_file():
        return
    text = pub.read_text(encoding="utf-8")
    if "lib/core/kit/photos/" not in text:
        needle = "    - lib/app/design_tokens.json"
        if needle in text:
            text = text.replace(needle, needle + "\n    - lib/core/kit/photos/")
        elif "  assets:\n" in text:
            text = text.replace("  assets:\n", "  assets:\n    - lib/core/kit/photos/\n", 1)
    if "family: KitSans" not in text and "  uses-material-design: true" in text:
        text = text.replace("  uses-material-design: true", "  uses-material-design: true\n" + _KIT_FONTS.rstrip(), 1)
    pub.write_text(text, encoding="utf-8")



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
            "hero_hint": " ".join([spec.app_name, *[screen.id.replace("_", " ") for screen in spec.screens]]),
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
            for op in parsed:
                session.emit("file", op=op.op, path=op.path, preview=(op.content or "")[:500])
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
        for v in violations:
            session.emit("guard", code=v.code, path=v.path, message=v.message)
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


def _polish(
    session: PilotSession,
    system: str,
    user: str,
    project: Path,
    *,
    allowed_prefixes: list[str] | None,
) -> list[str]:
    """Deterministic chrome rewrite, then one model pass if screens still bypass the kit."""
    rewrite_raw_material(project)
    problems = kit_violations(project)
    if not problems:
        return []
    session.emit("stage", name="polish", status="start", issues=len(problems))
    try:
        request_and_apply_ops(
            session,
            system,
            user,
            project,
            allowed_prefixes=allowed_prefixes,
            extra_feedback=(
                "Design pass. These lines bypass the kit and look like stock Material:\n"
                + "\n".join(problems)
                + "\n\nRewrite only the affected files with kit widgets and theme colors. "
                "Keep behavior and the FeatureRoute class.\n\n"
                f"Current files:\n{_read_feature_files(project)}"
            ),
        )
    except BudgetExceeded:
        raise
    except Exception as exc:  # noqa: BLE001
        session.emit("stage", name="polish", status="skip", error=f"{type(exc).__name__}")
        return problems
    remaining = kit_violations(project)
    session.emit("stage", name="polish", status="ok", issues=len(remaining))
    return remaining


_KIT_PHOTO_KEYS = (
    "shoe, jacket, hoodie, shorts, cleat, coffee, tool, plant, bag, headphone, "
    "burger, salad, pastry, dumbbell, bike, book, camera, watch, sunglasses, "
    "skincare, candle, lamp, suitcase, guitar"
)


def _catalog_user(spec: AppSpec, idea: str, *, extra: str = "") -> str:
    base = (
        f"AppSpec:\n{spec.model_dump_json()}\n\nIdea: {idea}\n\n"
        "Return AppCatalog JSON only (no Dart, no file paths). "
        "8–12 products with unique id, title, subtitle, price (include $), category, badge, emoji. "
        f"photo must be one of: {_KIT_PHOTO_KEYS}. "
        "shop_hero_* and profile_* copy must match the app theme. "
        "browse_label and profile_label are short tab names; browse_icon and profile_icon are single emojis. "
        "detail_path is a route like /item."
    )
    return base if not extra else base + "\n\n" + extra


def _request_catalog(
    session: PilotSession,
    system: str,
    user: str,
    run_dir: Path,
) -> AppCatalog:
    catalog = _schema_loop(session, system, user, CATALOG_SCHEMA, "catalog", AppCatalog)
    (run_dir / "catalog.json").write_text(catalog.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return catalog


def _write_catalog_from_model(
    session: PilotSession,
    system: str,
    user: str,
    project: Path,
    run_dir: Path,
) -> AppCatalog:
    session.emit("stage", name="catalog", status="start")
    t0 = time.perf_counter()
    catalog = _request_catalog(session, system, user, run_dir)
    write_app_catalog(project, catalog)
    ms = round((time.perf_counter() - t0) * 1000, 1)
    session.emit("stage", name="catalog", status="ok", ms=ms, products=len(catalog.products))
    return catalog


def _read_feature_files(project: Path, limit: int = 12) -> str:
    features = project / "lib" / "app" / "features"
    root = features if features.is_dir() else project / "lib"
    if not root.is_dir():
        return ""
    chunks: list[str] = []
    for path in sorted(root.rglob("*.dart"))[:limit]:
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


def _apply_choice_tokens(run_dir: Path, project: Path) -> str | None:
    path = run_dir / "choice.json"
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    direction = Direction.model_validate(raw["direction"])
    apply_tokens(project, direction)
    return direction.name


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
    web_base_href: str | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    stages: dict[str, float] = {}
    run_dir.mkdir(parents=True, exist_ok=True)
    project = run_dir / "project"
    href = web_base_href or f"/runs/{run_dir.name}/project/build/web/"
    gate = gate_fn or (lambda p: run_gate(p, build_web=build_web, base_href=href))

    session.emit("stage", name="prepare", status="start", mode=mode)
    t0 = time.perf_counter()
    max_repairs = MAX_GATE_REPAIRS
    if mode in ("harness", "scaffold_only"):
        copy_tree(capsule, project)
        system = CAPSULE_PREFIX
        allowed = HARNESS_ALLOWED
        if mode == "scaffold_only":
            max_repairs = 0
    elif mode == "bare":
        creator = create_fn or (lambda dest: default_flutter_create(dest, capsule / "pubspec.yaml"))
        creator(project)
        system = BARE_REQUIREMENTS
        allowed = None
    else:
        raise ValueError("mode must be harness, scaffold_only, or bare")
    choice_name = _apply_choice_tokens(run_dir, project)
    if not choice_name and mode in ("harness", "scaffold_only"):
        palette = pick_palette(idea)
        apply_palette(project, palette)
        choice_name = palette.name
    if choice_name:
        session.emit("choice", name=choice_name)
    stages["prepare_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    session.emit("stage", name="prepare", status="ok", ms=stages["prepare_ms"])

    spec: AppSpec | None = None
    ops_log: dict[str, Any] = {}
    report: GateReport | None = None
    repair_rounds = 0
    error: str | None = None
    try:
        session.emit("stage", name="spec", status="start")
        t0 = time.perf_counter()
        spec = _schema_loop(
            session,
            system,
            (
                f"Write an AppSpec for this idea:\n{idea}\n\n"
                "Plan at least 3 screens: a main browse/list, a detail or create flow, "
                "and a profile/summary. One data model. Short copy."
            ),
            APP_SPEC_SCHEMA,
            "spec",
            AppSpec,
        )
        (run_dir / "spec.json").write_text(spec.model_dump_json(indent=2) + "\n", encoding="utf-8")
        apply_spec_assets(project, spec)
        apply_branding(project, spec)
        stages["spec_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        session.emit("stage", name="spec", status="ok", app_name=spec.app_name, ms=stages["spec_ms"])
        items = [screen.id.replace("_", " ") for screen in spec.screens] or [slide.title for slide in spec.onboarding]
        write_skin_from_project(
            project,
            title=mode,
            app_name=spec.app_name,
            idea=idea,
            items=items,
            cta=spec.paywall_cta or "Open",
        )
        skin_url = f"/runs/{run_dir.name}/project/skin.html"
        session.emit("preview", url=skin_url, mode=mode, kind="skin")

        catalog_user = _catalog_user(spec, idea)
        if mode in ("harness", "scaffold_only"):
            session.emit("stage", name="file_ops", status="start")
            t0 = time.perf_counter()
            _write_catalog_from_model(session, system, catalog_user, project, run_dir)
            stages["build_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            session.emit("stage", name="file_ops", status="ok", ms=stages["build_ms"], applied=4)
            ops_log = {"applied": 4, "catalog": True}
        else:
            build_user = (
                f"AppSpec:\n{spec.model_dump_json()}\n\n"
                "Implement the app with file operations under lib/. Terse Dart, no comments."
            )
            session.emit("stage", name="file_ops", status="start")
            t0 = time.perf_counter()
            ops_log = request_and_apply_ops(session, system, build_user, project, allowed_prefixes=allowed)
            stages["build_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            session.emit("stage", name="file_ops", status="ok", ms=stages["build_ms"], applied=ops_log.get("applied"))

        session.emit("stage", name="gate", status="start")
        t0 = time.perf_counter()
        report = gate(project)
        _emit_gate(session, report)
        while not report.ok and repair_rounds < max_repairs:
            repair_rounds += 1
            session.emit("repair", round=repair_rounds)
            fail_text = _failing_text(report)
            if mode in ("harness", "scaffold_only") and spec is not None:
                _write_catalog_from_model(
                    session,
                    system,
                    _catalog_user(
                        spec,
                        idea,
                        extra=f"Gate failed (round {repair_rounds}). Fix the catalog data:\n{fail_text}",
                    ),
                    project,
                    run_dir,
                )
            else:
                build_user = (
                    f"AppSpec:\n{spec.model_dump_json()}\n\n"
                    "Fix ONLY gate errors. Terse Dart under lib/."
                )
                files = _read_relevant_files(project)
                request_and_apply_ops(
                    session,
                    system,
                    build_user,
                    project,
                    allowed_prefixes=allowed,
                    extra_feedback=(
                        f"Gate failed (round {repair_rounds}). Fix ONLY these errors:\n{fail_text}\n\n"
                        f"Relevant files:\n{files}"
                    ),
                )
            report = gate(project)
            _emit_gate(session, report)
        stages["gate_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        session.emit("stage", name="gate", status="ok" if report.ok else "fail", ms=stages["gate_ms"])
        if build_web and report.ok:
            session.emit("preview", url=href, mode=mode, kind="web")
    except BudgetExceeded:
        raise
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        if report is None:
            report = GateReport(
                project_dir=str(project),
                ok=False,
                steps=[StepResult("exception", False, 0.0, error)],
                preflight=[],
            )

    token_totals = _token_totals(session.usage_path, session.run_id)
    result = {
        "pilot": session.pilot.name,
        "mode": mode,
        "idea": idea,
        "run_id": session.run_id,
        "ok": bool(report and report.ok),
        "error": error,
        "gate": _gate_summary(report) if report is not None else None,
        "repair_rounds": repair_rounds,
        "ops": ops_log,
        "tokens": token_totals,
        "wall_ms": round((time.perf_counter() - started) * 1000, 1),
        "stage_ms": stages,
        "project": str(project),
    }
    (run_dir / "result.json").write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    skin_url = f"/runs/{run_dir.name}/project/skin.html"
    preview = href if build_web and result["ok"] else (skin_url if (project / "skin.html").is_file() else None)
    session.emit(
        "done",
        ok=result["ok"],
        error=error,
        preview=preview,
        mode=mode,
    )
    return result


def run_improve(
    instruction: str,
    session: PilotSession,
    *,
    run_dir: Path,
    source_project: Path,
    capsule: Path | None = None,
    gate_fn: GateFn | None = None,
    build_web: bool = True,
    web_base_href: str | None = None,
    mode: str = "harness",
) -> dict[str, Any]:
    """Apply a follow-up instruction to an existing generated app. Does not copy a fresh capsule."""
    started = time.perf_counter()
    stages: dict[str, Any] = {}
    run_dir.mkdir(parents=True, exist_ok=True)
    project = run_dir / "project"
    href = web_base_href or f"/runs/{run_dir.name}/project/build/web/"
    gate = gate_fn or (lambda p: run_gate(p, build_web=build_web, base_href=href))
    allowed = HARNESS_ALLOWED if mode in ("harness", "scaffold_only") else None
    system = CAPSULE_PREFIX if mode != "bare" else BARE_REQUIREMENTS

    session.emit("stage", name="prepare", status="start", mode=mode)
    t0 = time.perf_counter()
    if not source_project.is_dir():
        raise FileNotFoundError(f"no app to improve at {source_project}")
    copy_tree(source_project, project)
    if capsule is not None:
        kit_src = capsule / "lib" / "core" / "kit"
        kit_dst = project / "lib" / "core" / "kit"
        if kit_src.is_dir():
            if kit_dst.exists():
                shutil.rmtree(kit_dst)
            shutil.copytree(kit_src, kit_dst)
        _ensure_kit_pubspec(project)
    new_palette = palette_from_instruction(instruction, current_palette(project)) if mode != "bare" else None
    if new_palette is not None:
        apply_palette(project, new_palette)
        session.emit("choice", name=new_palette.name)
    stages["prepare_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    session.emit("stage", name="prepare", status="ok", ms=stages["prepare_ms"])

    ops_log: dict[str, Any] = {}
    report: GateReport | None = None
    repair_rounds = 0
    error: str | None = None
    spec: AppSpec | None = None
    try:
        spec_path = source_project.parent / "spec.json"
        if spec_path.is_file():
            spec = AppSpec.model_validate_json(spec_path.read_text(encoding="utf-8"))
        session.emit("stage", name="file_ops", status="start")
        t0 = time.perf_counter()
        if mode in ("harness", "scaffold_only"):
            if spec is None:
                raise ValueError("missing spec.json on source run — build an app first")
            prev = source_project.parent / "catalog.json"
            extra = f"Apply this change only:\n{instruction}"
            if prev.is_file():
                extra += f"\n\nPrevious catalog JSON:\n{prev.read_text(encoding='utf-8')}"
            if new_palette is not None:
                extra += f"\n\nThe color palette was switched to {new_palette.name}; keep layout, adjust copy if needed."
            _write_catalog_from_model(
                session,
                system,
                _catalog_user(spec, instruction, extra=extra),
                project,
                run_dir,
            )
            stages["build_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            session.emit("stage", name="file_ops", status="ok", ms=stages["build_ms"], applied=4)
            ops_log = {"applied": 4, "catalog": True}
        else:
            current = _read_feature_files(project)
            improve_user = (
                f"The app already exists. Apply this change only:\n{instruction}\n\n"
                "Terse Dart under lib/. Writes use content; find and replace must be JSON null.\n\n"
                f"Current feature files:\n{current}"
            )
            ops_log = request_and_apply_ops(session, system, improve_user, project, allowed_prefixes=allowed)
            stages["build_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            session.emit("stage", name="file_ops", status="ok", ms=stages["build_ms"], applied=ops_log.get("applied"))

        session.emit("stage", name="gate", status="start")
        t0 = time.perf_counter()
        report = gate(project)
        _emit_gate(session, report)
        max_repairs = 0 if mode == "scaffold_only" else MAX_GATE_REPAIRS
        while not report.ok and repair_rounds < max_repairs:
            repair_rounds += 1
            session.emit("repair", round=repair_rounds)
            fail_text = _failing_text(report)
            if mode in ("harness", "scaffold_only") and spec is not None:
                _write_catalog_from_model(
                    session,
                    system,
                    _catalog_user(
                        spec,
                        instruction,
                        extra=f"Gate failed (round {repair_rounds}). Fix the catalog:\n{fail_text}",
                    ),
                    project,
                    run_dir,
                )
            else:
                files = _read_feature_files(project)
                improve_user = f"Fix gate errors for:\n{instruction}"
                request_and_apply_ops(
                    session,
                    system,
                    improve_user,
                    project,
                    allowed_prefixes=allowed,
                    extra_feedback=(
                        f"Gate failed (round {repair_rounds}). Fix ONLY these errors:\n{fail_text}\n\n"
                        f"Relevant files:\n{files}"
                    ),
                )
            report = gate(project)
            _emit_gate(session, report)
        stages["gate_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        session.emit("stage", name="gate", status="ok" if report.ok else "fail", ms=stages["gate_ms"])
        if build_web and report.ok:
            session.emit("preview", url=href, mode=mode, kind="web")
    except BudgetExceeded:
        raise
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        if report is None:
            report = GateReport(
                project_dir=str(project),
                ok=False,
                steps=[StepResult("exception", False, 0.0, error)],
                preflight=[],
            )

    token_totals = _token_totals(session.usage_path, session.run_id)
    result = {
        "pilot": session.pilot.name,
        "mode": mode,
        "idea": instruction,
        "run_id": session.run_id,
        "ok": bool(report and report.ok),
        "error": error,
        "gate": _gate_summary(report) if report is not None else None,
        "repair_rounds": repair_rounds,
        "ops": ops_log,
        "tokens": token_totals,
        "wall_ms": round((time.perf_counter() - started) * 1000, 1),
        "stage_ms": stages,
        "project": str(project),
        "kind": "improve",
    }
    (run_dir / "result.json").write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    skin_url = f"/runs/{run_dir.name}/project/skin.html"
    preview = href if build_web and result["ok"] else (skin_url if (project / "skin.html").is_file() else None)
    session.emit("done", ok=result["ok"], error=error, preview=preview, mode=mode)
    return result


def _emit_gate(session: PilotSession, report: GateReport) -> None:
    for step in report.steps:
        session.emit("gate_step", name=step.name, ok=step.ok, ms=step.duration_ms)
    for check in report.preflight:
        session.emit(
            "preflight",
            check_id=check.check_id,
            status=str(check.status),
            message=check.message,
            file=check.file,
        )
