"""Fair ivebench sweep: ideas × pilots × harness/bare, infra vs quality, resumable."""

from __future__ import annotations

import json
import subprocess
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from pilot.protocol import BudgetExceeded
from pilot.session import PilotSession
from pilot.usage_log import spent_for_run

from .build import CreateFn, GateFn, run_build
from .classify import INFRA, classify_result

MakeSession = Callable[[str, str, float | None], PilotSession]
ExecuteFn = Callable[..., dict[str, Any]]


class DirtyTreeError(RuntimeError):
    """Sweep refuses to start when git status is not empty."""


class RateLimiter:
    def __init__(self, min_interval_s: float = 0.5) -> None:
        self.min_interval_s = min_interval_s
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delay = self.min_interval_s - (now - self._last)
            if delay > 0:
                time.sleep(delay)
            self._last = time.monotonic()


def load_ideas(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def git_sha(repo: Path) -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        return "unknown"
    return proc.stdout.strip()


def git_dirty(repo: Path) -> str:
    proc = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True, check=False
    )
    return proc.stdout.strip()


def run_id_for(pilot: str, idea_id: str, mode: str) -> str:
    return f"sweep-{pilot}-{idea_id}-{mode}"


def _terminal(data: dict[str, Any]) -> bool:
    outcome = data.get("outcome")
    if outcome in {"pass", "quality_fail", "skipped"}:
        return True
    if outcome == INFRA and data.get("retried"):
        return True
    return False


def _append_log(path: Path | None, message: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) + " " + message + "\n")


def _call_with_timeout(fn: Callable[[], dict[str, Any]], timeout_s: float) -> dict[str, Any]:
    box: dict[str, Any] = {}

    def target() -> None:
        try:
            box["result"] = fn()
        except BaseException as exc:  # noqa: BLE001 — must surface timeout vs quality
            box["exc"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout_s)
    if thread.is_alive():
        raise TimeoutError(f"run exceeded {timeout_s}s")
    if "exc" in box:
        raise box["exc"]
    return box["result"]


def run_sweep(
    *,
    ideas: list[dict[str, Any]],
    make_session: MakeSession,
    capsule: Path,
    out_dir: Path,
    runs: Path,
    usage_path: Path,
    pilots: list[str] | None = None,
    modes: tuple[str, ...] = ("harness", "bare"),
    max_usd: float | None = None,
    max_usd_per_pilot: float | None = None,
    build_web: bool = False,
    gate_fn: GateFn | None = None,
    create_fn: CreateFn | None = None,
    execute: ExecuteFn | None = None,
    git_repo: Path | None = None,
    require_clean_git: bool = False,
    sha: str | None = None,
    call_timeout_s: float = 300.0,
    run_timeout_s: float = 900.0,
    log_path: Path | None = None,
    min_interval_s: float = 0.0,
) -> dict[str, Any]:
    _ = call_timeout_s  # applied by the Pilot/client the caller constructed
    if require_clean_git:
        repo = git_repo or Path.cwd()
        dirty = git_dirty(repo)
        if dirty:
            raise DirtyTreeError("sweep refuses to start on a dirty git tree:\n" + dirty)
    out_dir.mkdir(parents=True, exist_ok=True)
    runs.mkdir(parents=True, exist_ok=True)
    names = list(pilots or ["fake"])
    sha = sha or (git_sha(git_repo) if git_repo is not None else "unknown")
    execute = execute or run_build
    lock = threading.Lock()
    rows: list[dict[str, Any]] = []
    run_ids_by_pilot: dict[str, list[str]] = {name: [] for name in names}

    def spent_pilot(name: str) -> float:
        return sum(spent_for_run(usage_path, rid) for rid in run_ids_by_pilot[name])

    def spent_all() -> float:
        return sum(spent_pilot(name) for name in names)

    def one_pilot(pilot_name: str) -> list[dict[str, Any]]:
        limiter = RateLimiter(min_interval_s)
        local: list[dict[str, Any]] = []
        for idea in ideas:
            idea_id = str(idea["id"])
            blurb = str(idea.get("blurb") or idea.get("title") or idea_id)
            for mode in modes:
                rid = run_id_for(pilot_name, idea_id, mode)
                existing = out_dir / f"{rid}.json"
                if existing.is_file():
                    try:
                        prior = json.loads(existing.read_text(encoding="utf-8"))
                    except json.JSONDecodeError:
                        prior = {}
                    if _terminal(prior):
                        _append_log(log_path, f"skip {rid} already {prior.get('outcome')}")
                        local.append(
                            {
                                "idea": idea_id,
                                "mode": mode,
                                "pilot": pilot_name,
                                "run_id": rid,
                                "ok": prior.get("ok"),
                                "outcome": prior.get("outcome"),
                                "skipped": True,
                                "resumed": True,
                            }
                        )
                        continue
                with lock:
                    total = spent_all()
                    per = spent_pilot(pilot_name)
                remaining_total = None if max_usd is None else round(max_usd - total, 6)
                remaining_pilot = None if max_usd_per_pilot is None else round(max_usd_per_pilot - per, 6)
                remaining_bits = [v for v in (remaining_total, remaining_pilot) if v is not None]
                remaining = min(remaining_bits) if remaining_bits else None
                if remaining is not None and remaining <= 0:
                    row = {
                        "idea": idea_id,
                        "mode": mode,
                        "pilot": pilot_name,
                        "run_id": rid,
                        "ok": False,
                        "error": "budget",
                        "outcome": "skipped",
                        "skipped": True,
                    }
                    local.append(row)
                    _write_result(out_dir / f"{rid}.json", {**row, "git_sha": sha})
                    _append_log(log_path, f"budget skip {rid}")
                    continue
                retried = False
                outcome = INFRA
                result: dict[str, Any] | None = None
                error: str | None = None
                for attempt in (1, 2):
                    limiter.wait()
                    session = make_session(rid, pilot_name, remaining)
                    started = time.perf_counter()
                    try:

                        def _go() -> dict[str, Any]:
                            return execute(
                                blurb,
                                session,
                                mode=mode,
                                run_dir=runs / rid,
                                capsule=capsule,
                                gate_fn=gate_fn,
                                create_fn=create_fn if mode == "bare" else None,
                                build_web=build_web,
                            )

                        result = _call_with_timeout(_go, run_timeout_s)
                        wall_s = (time.perf_counter() - started)
                        error = result.get("error")
                        outcome = classify_result(
                            ok=bool(result.get("ok")),
                            error=error,
                            wall_s=wall_s,
                            run_timeout_s=run_timeout_s,
                        )
                    except BudgetExceeded as exc:
                        error = str(exc)
                        outcome = "skipped"
                        result = {"ok": False, "error": error, "repair_rounds": 0, "tokens": {}, "wall_ms": 0, "stage_ms": {}}
                    except Exception as exc:
                        error = f"{type(exc).__name__}: {exc}"
                        wall_s = time.perf_counter() - started
                        outcome = classify_result(
                            ok=False, error=error, exc=exc, wall_s=wall_s, run_timeout_s=run_timeout_s
                        )
                        result = {
                            "ok": False,
                            "error": error,
                            "repair_rounds": 0,
                            "tokens": {},
                            "wall_ms": round(wall_s * 1000, 1),
                            "stage_ms": {},
                        }
                    retried = attempt == 2
                    if outcome != INFRA or attempt == 2:
                        break
                    _append_log(log_path, f"infra retry {rid} after {error}")
                assert result is not None
                with lock:
                    run_ids_by_pilot[pilot_name].append(rid)
                payload = {
                    **result,
                    "pilot": result.get("pilot") or pilot_name,
                    "model": getattr(session.pilot, "model", pilot_name),
                    "mode": mode,
                    "idea": idea_id,
                    "title": idea.get("title"),
                    "run_id": rid,
                    "git_sha": sha,
                    "outcome": outcome,
                    "retried": retried,
                    "ok": bool(result.get("ok")) and outcome == "pass",
                }
                _write_result(out_dir / f"{rid}.json", payload)
                local.append(
                    {
                        "idea": idea_id,
                        "title": idea.get("title"),
                        "mode": mode,
                        "pilot": pilot_name,
                        "run_id": rid,
                        "ok": payload["ok"],
                        "outcome": outcome,
                        "error": payload.get("error"),
                        "repair_rounds": payload.get("repair_rounds"),
                        "tokens": payload.get("tokens"),
                        "wall_ms": payload.get("wall_ms"),
                        "retried": retried,
                        "skipped": False,
                    }
                )
                _append_log(log_path, f"{outcome} {rid} retried={retried}")
        return local

    if len(names) == 1:
        rows.extend(one_pilot(names[0]))
    else:
        with ThreadPoolExecutor(max_workers=len(names)) as pool:
            futs = {pool.submit(one_pilot, name): name for name in names}
            for fut in as_completed(futs):
                rows.extend(fut.result())

    summary = {
        "n": len(rows),
        "git_sha": sha,
        "pilots": names,
        "ok_harness": sum(1 for r in rows if r.get("mode") == "harness" and r.get("outcome") == "pass"),
        "ok_scaffold_only": sum(1 for r in rows if r.get("mode") == "scaffold_only" and r.get("outcome") == "pass"),
        "ok_bare": sum(1 for r in rows if r.get("mode") == "bare" and r.get("outcome") == "pass"),
        "infra": sum(1 for r in rows if r.get("outcome") == INFRA),
        "quality_fail": sum(1 for r in rows if r.get("outcome") == "quality_fail"),
        "spent_usd": spent_all(),
        "rows": rows,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    return summary


def _write_result(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
