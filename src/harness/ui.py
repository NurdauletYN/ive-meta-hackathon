"""Local dashboard so a human can drive design / build / gate without the private Ive UI."""

from __future__ import annotations

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pilot.canned import canned_pilot
from pilot.config import load_pilot
from pilot.protocol import BudgetExceeded
from pilot.session import PilotSession
from pilot.usage_log import DEFAULT_USAGE_PATH

from .build import run_build
from .design import run_design
from .gate import gate_json, run_gate

_RUN_ID = re.compile(r"^[a-zA-Z0-9._-]{1,64}$")


class HarnessUI:
    def __init__(self, root: Path, *, runs: Path | None = None, usage_path: Path | None = None) -> None:
        self.root = root
        self.demo = root / "demo"
        self.runs = runs or (root / "runs")
        self.usage_path = usage_path or (root / DEFAULT_USAGE_PATH)
        self._lock = threading.Lock()
        self.job: dict[str, Any] = {"status": "idle", "kind": None, "run_id": None, "error": None, "summary": None}

    def _session(self, pilot_name: str, run_id: str, max_usd: float | None) -> PilotSession:
        usage = self.usage_path
        if pilot_name == "fake":
            return PilotSession(canned_pilot(), run_id=run_id, usage_path=usage, max_usd=max_usd)
        yaml_path = self.root / "pilots.yaml"
        return PilotSession(load_pilot(pilot_name, yaml_path), run_id=run_id, usage_path=usage, max_usd=max_usd)

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
            item: dict[str, Any] = {"id": child.name, "gallery": (child / "gallery.html").is_file()}
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
            elif result_path.is_file():
                item["kind"] = "build"
            out.append(item)
        return out

    def start(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if self.job.get("status") == "running":
                return {"ok": False, "error": "a job is already running"}
            run_id = str(payload.get("run_id") or "").strip() or kind
            if not _RUN_ID.match(run_id):
                return {"ok": False, "error": "run_id must be 1-64 letters, digits, dot, underscore, or dash"}
            self.job = {"status": "running", "kind": kind, "run_id": run_id, "error": None, "summary": None}
        thread = threading.Thread(target=self._run, args=(kind, payload, run_id), daemon=True)
        thread.start()
        return {"ok": True, "status": "running", "run_id": run_id}

    def _run(self, kind: str, payload: dict[str, Any], run_id: str) -> None:
        error = None
        summary: dict[str, Any] | None = None
        try:
            idea = str(payload.get("idea") or "").strip()
            if kind != "gate" and not idea:
                raise ValueError("idea is required")
            pilot = str(payload.get("pilot") or "fake")
            max_usd = payload.get("max_usd")
            max_usd_f = float(max_usd) if max_usd not in (None, "") else None
            capsule = self.root / "flutter_template"
            if kind == "design":
                session = self._session(pilot, run_id, max_usd_f)
                build_web = bool(payload.get("build_web"))
                skip = (lambda _p: (True, "skipped")) if not build_web else None
                result = run_design(
                    idea,
                    session,
                    capsule=capsule,
                    out_dir=self.runs / run_id,
                    build_fn=skip,
                )
                summary = {
                    "ok": result.get("contrast_ok") and result.get("diversity_ok"),
                    "directions": [d["name"] for d in result["directions"]],
                    "gallery": f"/runs/{run_id}/gallery.html",
                    "contrast_ok": result.get("contrast_ok"),
                    "diversity_ok": result.get("diversity_ok"),
                    "builds": result.get("builds"),
                }
            elif kind == "build":
                session = self._session(pilot, run_id, max_usd_f)
                mode = str(payload.get("mode") or "harness")
                result = run_build(
                    idea,
                    session,
                    mode=mode,
                    run_dir=self.runs / run_id,
                    capsule=capsule,
                    build_web=bool(payload.get("build_web")),
                )
                gate = result.get("gate") or {}
                summary = {
                    "ok": result.get("ok"),
                    "error": result.get("error"),
                    "repair_rounds": result.get("repair_rounds"),
                    "tokens": result.get("tokens"),
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
                project = self.runs / run_id / "project"
                if not project.is_dir():
                    project = self.root / "flutter_template"
                report = run_gate(project, build_web=bool(payload.get("build_web")))
                summary = json.loads(gate_json(report))
            else:
                raise ValueError(f"unknown job {kind}")
        except BudgetExceeded as exc:
            error = str(exc)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        with self._lock:
            self.job = {
                "status": "error" if error else "done",
                "kind": kind,
                "run_id": run_id,
                "error": error,
                "summary": summary,
            }


def make_handler(app: HarnessUI):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            sys_stderr_write = __import__("sys").stderr.write
            sys_stderr_write("ui: " + (fmt % args) + "\n")

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

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            if path == "/api/job":
                with app._lock:
                    self._json(200, app.job)
                return
            if path == "/api/ideas":
                self._json(200, app.ideas())
                return
            if path == "/api/runs":
                self._json(200, app.list_runs())
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
    return target if target.is_file() else None


def _content_type(path: Path) -> str:
    return {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
        ".png": "image/png",
    }.get(path.suffix, "application/octet-stream")


def serve_ui(root: Path, port: int = 8765) -> None:
    app = HarnessUI(root)
    handler = make_handler(app)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Rocket harness UI at http://127.0.0.1:{port}/  (127.0.0.1 only)")
    httpd.serve_forever()
