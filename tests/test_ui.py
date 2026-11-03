"""Local harness UI: canned FakePilot jobs and path safety."""

from __future__ import annotations

import json
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path

from harness.ui import HarnessUI, _safe_under, make_handler

ROOT = Path(__file__).resolve().parents[1]


def test_safe_under_blocks_escape(tmp_path: Path) -> None:
    (tmp_path / "ok.txt").write_text("x", encoding="utf-8")
    assert _safe_under(tmp_path, "ok.txt") is not None
    assert _safe_under(tmp_path, "../ok.txt") is None


def test_ui_design_job_with_fake(tmp_path: Path) -> None:
    app = HarnessUI(ROOT, runs=tmp_path / "runs", usage_path=tmp_path / "usage.jsonl")
    started = app.start(
        "design",
        {"idea": "tool library", "pilot": "fake", "run_id": "ui-d", "build_web": False},
    )
    assert started["ok"] is True
    deadline = time.time() + 30
    while app.job["status"] == "running" and time.time() < deadline:
        time.sleep(0.05)
    assert app.job["status"] == "done", app.job
    assert app.job["summary"]["directions"] == ["Harbor", "Ember", "Grove"]
    assert (tmp_path / "runs" / "ui-d" / "gallery.html").is_file()


def test_ui_http_design_and_reject_second_job(tmp_path: Path) -> None:
    app = HarnessUI(ROOT, runs=tmp_path / "runs", usage_path=tmp_path / "usage.jsonl")
    handler = make_handler(app)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        import httpx

        port = httpd.server_address[1]
        base = f"http://127.0.0.1:{port}"
        ideas = httpx.get(f"{base}/api/ideas", timeout=5).json()
        assert len(ideas) == 8
        page = httpx.get(f"{base}/", timeout=5)
        assert page.status_code == 200
        assert "Rocket harness" in page.text
        started = httpx.post(
            f"{base}/api/design",
            json={"idea": "swap books", "pilot": "fake", "run_id": "http-d", "build_web": False},
            timeout=5,
        ).json()
        assert started["ok"] is True
        busy = httpx.post(
            f"{base}/api/design",
            json={"idea": "other", "pilot": "fake", "run_id": "http-d2", "build_web": False},
            timeout=5,
        ).json()
        assert busy["ok"] is False
        deadline = time.time() + 30
        job = {}
        while time.time() < deadline:
            job = httpx.get(f"{base}/api/job", timeout=5).json()
            if job.get("status") != "running":
                break
            time.sleep(0.05)
        assert job.get("status") == "done", job
        gallery = httpx.get(f"{base}/runs/http-d/gallery.html", timeout=5)
        assert gallery.status_code == 200
        deny = httpx.get(f"{base}/runs/../.env", timeout=5)
        assert deny.status_code == 404
    finally:
        httpd.shutdown()
