"""Local harness UI: canned FakePilot jobs and path safety."""

from __future__ import annotations

import shutil
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
    assert (tmp_path / "runs" / "ui-d" / "dir_2" / "skin.html").is_file()
    skin = (tmp_path / "runs" / "ui-d" / "dir_2" / "skin.html").read_text(encoding="utf-8")
    assert "#C62828" in skin
    assert "Ember" in skin


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
        assert "Rocket studio" in page.text
        assert 'id="ticker"' in page.text
        assert "<summary>" in page.text
        assert 'id="steps"' in page.text
        assert "draft" in page.text or "looks" in page.text
        assert "Offline demo (no API)" in page.text
        assert "Compare without harness" in page.text
        assert 'id="evidence"' in page.text
        assert 'value="muse" selected' in page.text
        assert "Muse Spark" in page.text
        started = httpx.post(
            f"{base}/api/design",
            json={"idea": "swap books", "pilot": "fake", "run_id": "http-d", "build_web": False},
            timeout=5,
        ).json()
        assert started["ok"] is True
        second = httpx.post(
            f"{base}/api/design",
            json={"idea": "other", "pilot": "fake", "run_id": "http-d2", "build_web": False},
            timeout=5,
        ).json()
        assert second["ok"] is True
        third = httpx.post(
            f"{base}/api/build",
            json={"idea": "third", "pilot": "fake", "run_id": "http-d3", "mode": "harness", "build_web": False},
            timeout=5,
        ).json()
        assert third["ok"] is False
        deadline = time.time() + 45
        job = {}
        while time.time() < deadline:
            job = httpx.get(f"{base}/api/job", timeout=5).json()
            running = [j for j in job.get("jobs") or [] if j.get("status") == "running"]
            if not running:
                break
            time.sleep(0.05)
        assert not [j for j in job.get("jobs") or [] if j.get("status") == "running"], job
        gallery = httpx.get(f"{base}/runs/http-d/gallery.html", timeout=5)
        assert gallery.status_code == 200
        skin = httpx.get(f"{base}/runs/http-d/dir_1/skin.html", timeout=5)
        assert skin.status_code == 200
        assert "Harbor" in skin.text
        deny = httpx.get(f"{base}/runs/../.env", timeout=5)
        assert deny.status_code == 404
        page = httpx.get(f"{base}/", timeout=5)
        assert "Rocket studio" in page.text or "Rocket harness" in page.text
    finally:
        httpd.shutdown()


def test_choice_json_is_applied_during_build(tmp_path: Path) -> None:
    from harness.build import run_build
    from harness.design import pick_direction, run_design
    from harness.gate import GateReport, StepResult
    from pilot.canned import canned_pilot
    from pilot.session import PilotSession

    usage = tmp_path / "usage.jsonl"
    session = PilotSession(canned_pilot(), run_id="ch", usage_path=usage)
    out = tmp_path / "design"
    run_design(
        "tools",
        session,
        capsule=ROOT / "flutter_template",
        out_dir=out,
        build_fn=lambda _p: (True, "skipped"),
    )
    pick_direction(out, 2)
    run_dir = tmp_path / "build"
    run_dir.mkdir()
    shutil.copyfile(out / "choice.json", run_dir / "choice.json")
    session2 = PilotSession(canned_pilot(), run_id="chb", usage_path=usage)

    def pass_gate(project):
        tokens = (project / "lib" / "app" / "design_tokens.json").read_text(encoding="utf-8")
        assert "#C62828" in tokens  # Ember
        return GateReport(str(project), True, [StepResult("preflight", True, 1.0)], [])

    result = run_build(
        "tools",
        session2,
        mode="harness",
        run_dir=run_dir,
        capsule=ROOT / "flutter_template",
        gate_fn=pass_gate,
        build_web=False,
    )
    assert result["ok"] is True


def test_event_log_writes_jsonl(tmp_path: Path) -> None:
    from harness.events import EventLog

    path = tmp_path / "events.jsonl"
    seen = []
    log = EventLog(path, listeners=[seen.append])
    log.emit("stage", run_id="r", name="spec", status="ok")
    assert seen[0]["type"] == "stage"
    line = path.read_text(encoding="utf-8").strip()
    assert "spec" in line


def test_compare_rejected_when_slots_full(tmp_path: Path) -> None:
    app = HarnessUI(ROOT, runs=tmp_path / "runs", usage_path=tmp_path / "usage.jsonl")
    with app._lock:
        app.jobs["hold-a"] = {"status": "running"}
        app.jobs["hold-b"] = {"status": "running"}
    started = app.start_compare({"idea": "tools", "pilot": "fake", "run_id": "cmp", "build_web": False})
    assert started["ok"] is False


def test_normalize_base_href() -> None:
    from harness.web_build import normalize_base_href

    assert normalize_base_href("runs/x/project/build/web") == "/runs/x/project/build/web/"
    assert normalize_base_href("/already/") == "/already/"


def test_skin_escapes_html(tmp_path: Path) -> None:
    from harness.skin import write_skin

    path = write_skin(
        tmp_path / "skin.html",
        title="<script>x</script>",
        app_name="Tools",
        idea="borrow & return",
        primary="#C62828",
        items=["Hammer"],
        cta="Open",
    )
    text = path.read_text(encoding="utf-8")
    assert "<script>x</script>" not in text
    assert "&lt;script&gt;x&lt;/script&gt;" in text
    assert "#C62828" in text
    assert "Hammer" in text


def test_event_hub_does_not_replay() -> None:
    from harness.events import EventHub

    hub = EventHub()
    hub.publish({"type": "old", "run_id": "past"})
    queue = hub.subscribe()
    assert queue.empty()
    hub.publish({"type": "live", "run_id": "now"})
    assert queue.get_nowait()["type"] == "live"
