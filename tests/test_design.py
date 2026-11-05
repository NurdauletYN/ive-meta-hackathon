"""Design engine and project management: palettes, kit lint, versions, code download."""

from __future__ import annotations

import io
import json
import threading
import zipfile
from http.server import ThreadingHTTPServer
from pathlib import Path

from harness.kitlint import kit_violations
from harness.palettes import (
    PALETTES,
    apply_palette,
    current_palette,
    get_palette,
    palette_from_instruction,
    palette_tokens,
    pick_palette,
)
from harness.projects import build_zip, get_project, list_projects, write_meta
from harness.ui import HarnessUI, make_handler
from preflight.checks import contrast_ratio

ROOT = Path(__file__).resolve().parents[1]


def test_every_palette_meets_wcag_aa() -> None:
    for palette in PALETTES:
        for pair in palette_tokens(palette)["contrast_pairs"]:
            assert contrast_ratio(pair["foreground"], pair["background"]) >= 4.5, (palette.id, pair["name"])


def test_palette_ids_and_primaries_are_unique() -> None:
    assert len({p.id for p in PALETTES}) == len(PALETTES)
    assert len({p.primary for p in PALETTES}) == len(PALETTES)


def test_pick_palette_matches_keywords_and_is_stable() -> None:
    assert pick_palette("sportswear shoe shop").id == "volt"
    assert pick_palette("budget and savings tracker").id == "emerald"
    assert pick_palette("neighborhood tool sharing").id == "sand"
    odd = "qwertyuiop"
    assert pick_palette(odd).id == pick_palette(odd).id


def test_palette_from_instruction() -> None:
    sand = get_palette("sand")
    midnight = get_palette("midnight")
    assert palette_from_instruction("make it dark", sand).id == "midnight"
    assert palette_from_instruction("make it dark", midnight) is None
    assert palette_from_instruction("try the rose palette", sand).id == "rose"
    assert palette_from_instruction("use a different color scheme", sand).id != "sand"
    assert palette_from_instruction("Switch to a light theme", midnight).dark is False
    assert palette_from_instruction("add a favorites tab", sand) is None
    assert palette_from_instruction("make the button black", sand) is None


def test_apply_palette_roundtrip(tmp_path: Path) -> None:
    (tmp_path / "lib" / "app").mkdir(parents=True)
    (tmp_path / "lib" / "app" / "design_tokens.json").write_text(
        json.dumps({"spacing": {"md": 16}}), encoding="utf-8"
    )
    apply_palette(tmp_path, get_palette("plum"))
    data = json.loads((tmp_path / "lib" / "app" / "design_tokens.json").read_text(encoding="utf-8"))
    assert data["colors"]["accent"] == get_palette("plum").accent
    assert data["spacing"] == {"md": 16}
    assert current_palette(tmp_path).id == "plum"


def test_kit_violations_flags_raw_material(tmp_path: Path) -> None:
    feature = tmp_path / "lib" / "app" / "features" / "x"
    feature.mkdir(parents=True)
    (feature / "a.dart").write_text(
        "Scaffold(body: ListTile(title: Text('x'), tileColor: Colors.red))\nRocketScaffold(body: KitPage(children: []))\n",
        encoding="utf-8",
    )
    found = " ".join(kit_violations(tmp_path))
    assert "Scaffold" in found and "ListTile" in found and "Colors" in found
    assert "a.dart:2" not in found
    (feature / "a.dart").write_text("RocketScaffold(body: KitPage(children: []))\n", encoding="utf-8")
    assert kit_violations(tmp_path) == []


def test_rewrite_raw_material_swaps_scaffold(tmp_path: Path) -> None:
    from harness.kitlint import rewrite_raw_material

    feature = tmp_path / "lib" / "app" / "features"
    feature.mkdir(parents=True)
    path = feature / "a.dart"
    path.write_text("Scaffold(appBar: AppBar(title: Text('x')), body: ListTile(title: Text('x')))\n", encoding="utf-8")
    assert rewrite_raw_material(tmp_path) == 1
    text = path.read_text(encoding="utf-8")
    assert "RocketScaffold(" in text
    assert "AppBar(" not in text
    assert "ListRow(" in text


def _fake_run(runs: Path, run_id: str) -> None:
    project = runs / run_id / "project"
    (project / "lib" / "app").mkdir(parents=True)
    (project / "pubspec.yaml").write_text("name: demo\n", encoding="utf-8")
    (project / "lib" / "main.dart").write_text("void main() {}\n", encoding="utf-8")
    (project / "build" / "web").mkdir(parents=True)
    (project / "build" / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
    (project / ".env").write_text("SECRET=1", encoding="utf-8")
    (project / "ios").mkdir()
    (project / "ios" / "GoogleService-Info.plist").write_text("secret", encoding="utf-8")
    (project / "skin.html").write_text("<html></html>", encoding="utf-8")
    (runs / run_id / "spec.json").write_text(json.dumps({"app_name": "Block Tools"}), encoding="utf-8")
    apply_palette(project, get_palette("sand"))


def test_versions_fork_from_chosen_run_and_zip_has_no_secrets(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    for run_id in ("h-1", "i-2", "i-3"):
        _fake_run(runs, run_id)
    write_meta(runs, "h-1", kind="build", instruction="tool sharing app", pilot="fake", ok=True)
    write_meta(runs, "i-2", kind="improve", instruction="add favorites", pilot="fake", ok=True, from_run="h-1")
    # restore v1 and branch from it: the new version still gets the next number
    meta = write_meta(runs, "i-3", kind="improve", instruction="make it dark", pilot="fake", ok=True, from_run="h-1")
    assert meta["project"] == "h-1" and meta["version"] == 3 and meta["parent"] == "h-1"

    projects = list_projects(runs)
    assert len(projects) == 1 and projects[0]["versions"] == 3 and projects[0]["latest_run"] == "i-3"
    assert projects[0]["title"] == "Block Tools"
    detail = get_project(runs, "h-1")
    assert [v["version"] for v in detail["versions"]] == [1, 2, 3]
    assert detail["versions"][0]["preview"] == "/runs/h-1/project/build/web/"

    name, data = build_zip(runs, "i-3")
    assert name == "block-tools-v3.zip"
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert "block-tools-v3/pubspec.yaml" in names
    assert "block-tools-v3/README.md" in names
    joined = " ".join(names)
    for banned in (".env", "GoogleService-Info", "build/web", "skin.html"):
        assert banned not in joined
    assert build_zip(runs, "missing") is None


def test_http_projects_and_download(tmp_path: Path) -> None:
    import httpx

    runs = tmp_path / "runs"
    _fake_run(runs, "h-9")
    write_meta(runs, "h-9", kind="build", instruction="tool app", pilot="fake", ok=True)
    app = HarnessUI(ROOT, runs=runs, usage_path=tmp_path / "usage.jsonl")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(app))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{httpd.server_address[1]}"
        listed = httpx.get(f"{base}/api/projects", timeout=5).json()
        assert listed[0]["id"] == "h-9"
        assert httpx.get(f"{base}/api/project/h-9", timeout=5).json()["versions"][0]["version"] == 1
        assert httpx.get(f"{base}/api/project/nope", timeout=5).status_code == 404
        zipped = httpx.get(f"{base}/api/download/h-9.zip", timeout=5)
        assert zipped.status_code == 200
        assert zipped.headers["content-type"] == "application/zip"
        assert "attachment" in zipped.headers["content-disposition"]
        assert httpx.get(f"{base}/api/download/..%2Fx.zip", timeout=5).status_code == 404
        page = httpx.get(f"{base}/", timeout=5).text
        for needle in ('id="side"', 'id="project-list"', 'id="new-project"', 'id="version-chips"', "Download code", 'id="suggest"'):
            assert needle in page
    finally:
        httpd.shutdown()


def test_ui_build_writes_meta_and_improve_links_versions(tmp_path: Path) -> None:
    import time

    app = HarnessUI(ROOT, runs=tmp_path / "runs", usage_path=tmp_path / "usage.jsonl")
    assert app.start("build", {"idea": "sport shoe shop", "pilot": "fake", "run_id": "b-1", "build_web": False})["ok"]
    deadline = time.time() + 60
    while app.jobs["b-1"]["status"] == "running" and time.time() < deadline:
        time.sleep(0.05)
    assert app.jobs["b-1"]["status"] == "done", app.jobs["b-1"]
    tokens = json.loads((tmp_path / "runs" / "b-1" / "project" / "lib" / "app" / "design_tokens.json").read_text())
    assert tokens["colors"]["primary"] == get_palette("volt").primary

    assert app.start(
        "improve",
        {"idea": "make it dark", "pilot": "fake", "run_id": "b-2", "from_run": "b-1", "build_web": False},
    )["ok"]
    while app.jobs["b-2"]["status"] == "running" and time.time() < deadline:
        time.sleep(0.05)
    projects = list_projects(tmp_path / "runs")
    assert len(projects) == 1 and projects[0]["versions"] == 2
