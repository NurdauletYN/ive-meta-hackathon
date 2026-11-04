"""Local studio so a human can drive design / build / compare in a phone frame."""

from __future__ import annotations

import json
import re
import shutil
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Empty
from typing import Any
from urllib.parse import urlparse

from pilot.canned import canned_pilot
from pilot.config import load_pilot
from pilot.protocol import BudgetExceeded
from pilot.session import PilotSession
from pilot.usage_log import DEFAULT_USAGE_PATH

from .build import run_build, run_improve
from .design import pick_direction, run_design
from .events import EventHub, EventLog
from .gate import gate_json, run_gate
from .projects import build_zip, get_project, list_projects, write_meta

_RUN_ID = re.compile(r"^[a-zA-Z0-9._-]{1,64}$")
MAX_JOBS = 2


class HarnessUI:
    def __init__(self, root: Path, *, runs: Path | None = None, usage_path: Path | None = None) -> None:
        self.root = root
        self.demo = root / "demo"
        self.runs = runs or (root / "runs")
        self.usage_path = usage_path or (root / DEFAULT_USAGE_PATH)
        self._lock = threading.Lock()
        self.job: dict[str, Any] = {"status": "idle", "kind": None, "run_id": None, "error": None, "summary": None}
        self.jobs: dict[str, dict[str, Any]] = {}
        self.hub = EventHub()

    def _running(self) -> int:
        return sum(1 for job in self.jobs.values() if job.get("status") == "running")

    def _session(self, pilot_name: str, run_id: str, max_usd: float | None, events: EventLog) -> PilotSession:
        if pilot_name == "fake":
            return PilotSession(
                canned_pilot(), run_id=run_id, usage_path=self.usage_path, max_usd=max_usd, events=events
            )
        yaml_path = self.root / "pilots.yaml"
        return PilotSession(
            load_pilot(pilot_name, yaml_path),
            run_id=run_id,
            usage_path=self.usage_path,
            max_usd=max_usd,
            events=events,
        )

    def ideas(self) -> list[dict[str, Any]]:
        path = self.root / "ivebench" / "ideas.jsonl"
        rows = []
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(json.loads(line))
        return rows

    def list_runs(self) -> list[dict[str, Any]]:
        if not self.runs.is_dir():
            return []
        out = []
        for child in sorted(self.runs.iterdir()):
            if not child.is_dir():
                continue
            item: dict[str, Any] = {
                "id": child.name,
                "gallery": (child / "gallery.html").is_file(),
                "preview": (child / "project" / "build" / "web" / "index.html").is_file(),
            }
            result_path = child / "result.json"
            if result_path.is_file():
                try:
                    data = json.loads(result_path.read_text(encoding="utf-8"))
                    item["ok"] = data.get("ok")
                    item["mode"] = data.get("mode")
                    item["pilot"] = data.get("pilot")
                except json.JSONDecodeError:
                    item["ok"] = None
            dirs = child / "directions.json"
            if dirs.is_file():
                item["kind"] = "design"
                try:
                    item["directions"] = [
                        {"name": d.get("name"), "primary": (d.get("tokens") or {}).get("colors", {}).get("primary")}
                        for d in json.loads(dirs.read_text(encoding="utf-8")).get("directions") or []
                    ]
                except json.JSONDecodeError:
                    pass
            elif result_path.is_file():
                item["kind"] = "build"
            out.append(item)
        return out

    def pick(self, run_id: str, n: int) -> dict[str, Any]:
        if not _RUN_ID.match(run_id):
            return {"ok": False, "error": "bad run_id"}
        try:
            path = pick_direction(self.runs / run_id, n)
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
            return {"ok": False, "error": str(exc)}
        self.hub.publish({"type": "picked", "run_id": run_id, "n": n, "name": (data.get("direction") or {}).get("name")})
        return {"ok": True, "choice": data}

    def start(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if self._running() >= MAX_JOBS:
                return {"ok": False, "error": f"already running {self._running()} jobs (max {MAX_JOBS})"}
            run_id = str(payload.get("run_id") or "").strip() or kind
            if not _RUN_ID.match(run_id):
                return {"ok": False, "error": "run_id must be 1-64 letters, digits, dot, underscore, or dash"}
            job = {
                "status": "running",
                "kind": kind,
                "run_id": run_id,
                "error": None,
                "summary": None,
                "pilot": payload.get("pilot"),
            }
            self.jobs[run_id] = job
            self.job = job
        thread = threading.Thread(target=self._run, args=(kind, payload, run_id), daemon=True)
        thread.start()
        return {"ok": True, "status": "running", "run_id": run_id}

    def start_compare(self, payload: dict[str, Any]) -> dict[str, Any]:
        base = str(payload.get("run_id") or "compare").strip() or "compare"
        idea = str(payload.get("idea") or "").strip()
        if not idea:
            return {"ok": False, "error": "idea is required"}
        started = []
        for mode in ("harness", "bare"):
            child = dict(payload)
            child["mode"] = mode
            child["run_id"] = f"{base}-{mode}"
            result = self.start("build", child)
            if not result.get("ok"):
                return result
            started.append(result["run_id"])
        return {"ok": True, "status": "running", "run_ids": started, "kind": "compare"}

    def _run(self, kind: str, payload: dict[str, Any], run_id: str) -> None:
        error = None
        summary: dict[str, Any] | None = None
        run_dir = self.runs / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        events = EventLog(run_dir / "events.jsonl", listeners=[self.hub.publish])
        idea = str(payload.get("idea") or payload.get("instruction") or "").strip()
        pilot = str(payload.get("pilot") or "fake")
        from_run = str(payload.get("from_run") or "").strip()
        try:
            if kind != "gate" and not idea:
                raise ValueError("idea is required")
            max_usd = payload.get("max_usd")
            max_usd_f = float(max_usd) if max_usd not in (None, "") else None
            capsule = self.root / "flutter_template"
            choice_from = str(payload.get("choice_from") or "").strip()
            if choice_from and _RUN_ID.match(choice_from):
                src = self.runs / choice_from / "choice.json"
                if src.is_file():
                    shutil.copyfile(src, run_dir / "choice.json")
            if kind == "design":
                session = self._session(pilot, run_id, max_usd_f, events)
                build_web = bool(payload.get("build_web"))
                skip = (lambda _p: (True, "skipped")) if not build_web else None
                result = run_design(
                    idea,
                    session,
                    capsule=capsule,
                    out_dir=run_dir,
                    build_fn=skip,
                    public_prefix=f"/runs/{run_id}/",
                )
                summary = {
                    "ok": result.get("contrast_ok") and result.get("diversity_ok"),
                    "directions": [d["name"] for d in result["directions"]],
                    "previews": [
                        {
                            "index": i,
                            "name": d["name"],
                            "primary": d["tokens"]["colors"]["primary"],
                            "url": (
                                f"/runs/{run_id}/dir_{i}/build/web/"
                                if build_web
                                else f"/runs/{run_id}/dir_{i}/skin.html"
                            ),
                        }
                        for i, d in enumerate(result["directions"], start=1)
                    ],
                    "gallery": f"/runs/{run_id}/gallery.html",
                    "contrast_ok": result.get("contrast_ok"),
                    "diversity_ok": result.get("diversity_ok"),
                    "builds": result.get("builds"),
                }
            elif kind == "build":
                session = self._session(pilot, run_id, max_usd_f, events)
                mode = str(payload.get("mode") or "harness")
                build_web = bool(payload.get("build_web"))
                href = f"/runs/{run_id}/project/build/web/"
                result = run_build(
                    idea,
                    session,
                    mode=mode,
                    run_dir=run_dir,
                    capsule=capsule,
                    build_web=build_web,
                    web_base_href=href,
                )
                gate = result.get("gate") or {}
                summary = {
                    "ok": result.get("ok"),
                    "error": result.get("error"),
                    "mode": mode,
                    "repair_rounds": result.get("repair_rounds"),
                    "tokens": result.get("tokens"),
                    "preview": (
                        href
                        if build_web and result.get("ok")
                        else f"/runs/{run_id}/project/skin.html"
                    ),
                    "gate_steps": [
                        {"name": s.get("name"), "ok": s.get("ok")} for s in (gate.get("steps") or [])
                    ],
                    "preflight": [
                        {"id": p.get("check_id"), "status": str(p.get("status")), "message": p.get("message")}
                        for p in (gate.get("preflight") or [])
                    ],
                    "result": f"/runs/{run_id}/result.json",
                }
            elif kind == "improve":
                if not from_run or not _RUN_ID.match(from_run):
                    raise ValueError("from_run is required")
                source = self.runs / from_run / "project"
                if not source.is_dir():
                    raise ValueError("no app to improve yet — send an idea first")
                session = self._session(pilot, run_id, max_usd_f, events)
                mode = str(payload.get("mode") or "harness")
                build_web = bool(payload.get("build_web"))
                href = f"/runs/{run_id}/project/build/web/"
                result = run_improve(
                    idea,
                    session,
                    run_dir=run_dir,
                    source_project=source,
                    capsule=self.root / "flutter_template",
                    build_web=build_web,
                    web_base_href=href,
                    mode=mode,
                )
                gate = result.get("gate") or {}
                summary = {
                    "ok": result.get("ok"),
                    "error": result.get("error"),
                    "mode": mode,
                    "kind": "improve",
                    "from_run": from_run,
                    "repair_rounds": result.get("repair_rounds"),
                    "tokens": result.get("tokens"),
                    "preview": (
                        href
                        if build_web and result.get("ok")
                        else f"/runs/{run_id}/project/skin.html"
                    ),
                    "gate_steps": [
                        {"name": s.get("name"), "ok": s.get("ok")} for s in (gate.get("steps") or [])
                    ],
                    "preflight": [
                        {"id": p.get("check_id"), "status": str(p.get("status")), "message": p.get("message")}
                        for p in (gate.get("preflight") or [])
                    ],
                    "result": f"/runs/{run_id}/result.json",
                }
            elif kind == "gate":
                project = run_dir / "project"
                if not project.is_dir():
                    project = self.root / "flutter_template"
                report = run_gate(project, build_web=bool(payload.get("build_web")))
                summary = json.loads(gate_json(report))
            else:
                raise ValueError(f"unknown job {kind}")
        except BudgetExceeded as exc:
            error = str(exc)
            events.emit("done", run_id=run_id, ok=False, error=error)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            events.emit("done", run_id=run_id, ok=False, error=error)
        if kind in ("build", "improve") and not run_id.endswith(("-harness", "-bare")):
            try:
                meta = write_meta(
                    self.runs,
                    run_id,
                    kind=kind,
                    instruction=idea,
                    pilot=pilot,
                    ok=error is None and bool((summary or {}).get("ok")),
                    from_run=from_run if kind == "improve" and _RUN_ID.match(from_run) else None,
                    error=error or (summary or {}).get("error"),
                )
                self.hub.publish({"type": "project", "run_id": run_id, "project": meta["project"], "version": meta["version"]})
            except OSError:
                pass
        job = {
            "status": "error" if error else "done",
            "kind": kind,
            "run_id": run_id,
            "error": error,
            "summary": summary,
            "pilot": payload.get("pilot"),
        }
        with self._lock:
            self.jobs[run_id] = job
            self.job = job


def make_handler(app: HarnessUI):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            sys.stderr.write("ui: " + (fmt % args) + "\n")

        def _send(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, payload: object) -> None:
            raw = json.dumps(payload, indent=2, default=str).encode("utf-8")
            self._send(code, raw, "application/json; charset=utf-8")

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(data, dict):
                raise ValueError("JSON object required")
            return data

        def _sse(self) -> None:
            queue = app.hub.subscribe()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            try:
                while True:
                    try:
                        event = queue.get(timeout=15)
                        payload = json.dumps(event, default=str)
                        self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    except Empty:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                return
            finally:
                app.hub.unsubscribe(queue)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            if path == "/api/events":
                self._sse()
                return
            if path == "/api/job":
                with app._lock:
                    payload = dict(app.job)
                    payload["jobs"] = list(app.jobs.values())
                    self._json(200, payload)
                return
            if path == "/api/ideas":
                self._json(200, app.ideas())
                return
            if path == "/api/results":
                dest = app.root / "ivebench" / "results" / "results.md"
                if not dest.is_file():
                    self._json(404, {"ok": False, "error": "results.md not found"})
                    return
                self._send(200, dest.read_bytes(), "text/markdown; charset=utf-8")
                return
            if path == "/api/runs":
                self._json(200, app.list_runs())
                return
            if path == "/api/projects":
                self._json(200, list_projects(app.runs))
                return
            if path.startswith("/api/project/"):
                project_id = path[len("/api/project/") :]
                found = get_project(app.runs, project_id) if _RUN_ID.match(project_id) else None
                if found is None:
                    self._json(404, {"ok": False, "error": "project not found"})
                else:
                    self._json(200, found)
                return
            if path.startswith("/api/download/") and path.endswith(".zip"):
                run_id = path[len("/api/download/") : -len(".zip")]
                built = build_zip(app.runs, run_id) if _RUN_ID.match(run_id) else None
                if built is None:
                    self._json(404, {"ok": False, "error": "no project to download"})
                    return
                name, data = built
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Content-Disposition", f'attachment; filename="{name}"')
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
                return
            if path.startswith("/runs/"):
                rel = path[len("/runs/") :]
                target = _safe_under(app.runs, rel)
                if target is None:
                    self._json(404, {"error": "not found"})
                    return
                self._send(200, target.read_bytes(), _content_type(target))
                return
            rel = "index.html" if path in ("/", "/index.html") else path.lstrip("/")
            target = _safe_under(app.demo, rel)
            if target is None:
                self._json(404, {"error": "not found"})
                return
            self._send(200, target.read_bytes(), _content_type(target))

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            try:
                payload = self._read_json()
            except (ValueError, json.JSONDecodeError) as exc:
                self._json(400, {"ok": False, "error": str(exc)})
                return
            if path == "/api/design":
                self._json(200, app.start("design", payload))
                return
            if path == "/api/build":
                self._json(200, app.start("build", payload))
                return
            if path == "/api/improve":
                self._json(200, app.start("improve", payload))
                return
            if path == "/api/compare":
                self._json(200, app.start_compare(payload))
                return
            if path == "/api/pick":
                self._json(200, app.pick(str(payload.get("run_id") or ""), int(payload.get("n") or 0)))
                return
            if path == "/api/gate":
                self._json(200, app.start("gate", payload))
                return
            self._json(404, {"error": "not found"})

    return Handler


def _safe_under(base: Path, rel: str) -> Path | None:
    if not rel or ".." in Path(rel).parts:
        return None
    target = (base / rel).resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError:
        return None
    if target.is_dir():
        index = target / "index.html"
        return index if index.is_file() else None
    return target if target.is_file() else None


def _content_type(path: Path) -> str:
    return {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".zip": "application/zip",
        ".wasm": "application/wasm",
        ".ttf": "font/ttf",
        ".otf": "font/otf",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".map": "application/json",
    }.get(path.suffix, "application/octet-stream")


def serve_ui(root: Path, port: int = 8765) -> None:
    app = HarnessUI(root)
    handler = make_handler(app)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Rocket studio at http://127.0.0.1:{port}/  (127.0.0.1 only)", flush=True)
    httpd.serve_forever()
