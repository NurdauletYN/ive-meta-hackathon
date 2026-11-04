"""Fake-subprocess tests for harness ship. No live Apple / Pilot calls."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from harness.cli import main
from harness.gate import GateReport
from harness.prompts import BARE_REQUIREMENTS, CAPSULE_PREFIX
from harness.redact import redact
from harness.ship import (
    REQUIRED_ENV,
    COUNTER_NAME,
    ShipError,
    apply_ios_identity,
    next_build_number,
    parse_altool_errors,
    run_ship,
)

ROOT = Path(__file__).resolve().parents[1]
KEY_ID = "SHIPKEYID01"
ISSUER = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
TEAM = "TEAMID0001"
BUNDLE = "com.example.shipapp"

PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDisplayName</key>
	<string>Rocket Capsule</string>
	<key>CFBundleName</key>
	<string>rocket_capsule</string>
	<key>CFBundleShortVersionString</key>
	<string>$(FLUTTER_BUILD_NAME)</string>
	<key>CFBundleVersion</key>
	<string>$(FLUTTER_BUILD_NUMBER)</string>
</dict>
</plist>
"""

PBX = """
PRODUCT_BUNDLE_IDENTIFIER = com.rocket.capsule.rocketCapsule;
PRODUCT_BUNDLE_IDENTIFIER = com.rocket.capsule.rocketCapsule.RunnerTests;
"""


def _ok_gate(project: Path) -> GateReport:
    return GateReport(project_dir=str(project), ok=True, steps=[], preflight=[])


def _bad_gate(project: Path) -> GateReport:
    return GateReport(project_dir=str(project), ok=False, steps=[], preflight=[])


def _project(tmp_path: Path) -> Path:
    proj = tmp_path / "app"
    (proj / "ios" / "Runner").mkdir(parents=True)
    (proj / "ios" / "Runner.xcodeproj").mkdir(parents=True)
    (proj / "lib" / "app").mkdir(parents=True)
    (proj / "ios" / "Runner" / "Info.plist").write_text(PLIST, encoding="utf-8")
    (proj / "ios" / "Runner.xcodeproj" / "project.pbxproj").write_text(PBX, encoding="utf-8")
    (proj / "pubspec.yaml").write_text("name: rocket_capsule\nversion: 1.0.0+1\n", encoding="utf-8")
    (proj / "lib" / "app" / "strings.dart").write_text(
        "class AppStrings { static const appName = 'Harbor Notes'; }\n",
        encoding="utf-8",
    )
    return proj


def _env(tmp_path: Path) -> dict[str, str]:
    p8 = tmp_path / "keys" / f"AuthKey_{KEY_ID}.p8"
    p8.parent.mkdir(parents=True, exist_ok=True)
    p8.write_text("not-a-real-key\n", encoding="utf-8")
    return {
        "ASC_KEY_ID": KEY_ID,
        "ASC_ISSUER_ID": ISSUER,
        "ASC_KEY_PATH": str(p8),
        "APPLE_TEAM_ID": TEAM,
        "BUNDLE_ID": BUNDLE,
    }


def _success_runner_for(env: dict[str, str]):
    def runner(cmd: list[str], cwd: Path) -> tuple[int, str, float]:
        leak = f"apiKey {env['ASC_KEY_ID']} issuer {env['ASC_ISSUER_ID']} file {env['ASC_KEY_PATH']} team {env['APPLE_TEAM_ID']}"
        if cmd and cmd[0] == "flutter":
            ipa_dir = cwd / "build" / "ios" / "ipa"
            ipa_dir.mkdir(parents=True, exist_ok=True)
            (ipa_dir / "App.ipa").write_bytes(b"ipa")
            return 0, "Built ipa " + leak, 12.0
        return 0, "No errors. " + leak, 8.0

    return runner


def _ship(tmp_path: Path, **kwargs):
    proj = kwargs.pop("project", None) or _project(tmp_path)
    env = kwargs.pop("env") if "env" in kwargs else _env(tmp_path)
    defaults = {
        "project_dir": proj,
        "env": env,
        "runner": _success_runner_for(env),
        "gate_fn": _ok_gate,
    }
    defaults.update(kwargs)
    return run_ship(**defaults)


def test_success_writes_redacted_report(tmp_path: Path) -> None:
    result = _ship(tmp_path)
    assert result["ok"] is True
    assert result["outcome"] == "uploaded"
    assert result["bundle_id"] == BUNDLE
    assert result["version"] == "1.0.0"
    assert result["build"] == 1
    assert result["ipa"].endswith("App.ipa")
    assert result["errors"] == []
    names = [s["name"] for s in result["steps"]]
    assert "gate" in names
    assert "flutter_build_ipa" in names
    assert "altool_upload" in names
    assert all("duration_ms" in s for s in result["steps"])
    blob = json.dumps(result)
    assert KEY_ID not in blob
    assert ISSUER not in blob
    assert TEAM not in blob
    assert ".p8" not in blob
    report = (tmp_path / "app" / "ship_report.json").read_text(encoding="utf-8")
    assert KEY_ID not in report
    assert ISSUER not in report
    plist = (tmp_path / "app" / "ios" / "Runner" / "Info.plist").read_text(encoding="utf-8")
    assert "Harbor Notes" in plist
    assert "ITSAppUsesNonExemptEncryption" in plist
    assert "<false/>" in plist
    assert "<string>1.0.0</string>" in plist
    assert "<string>1</string>" in plist
    pbx = (tmp_path / "app" / "ios" / "Runner.xcodeproj" / "project.pbxproj").read_text(encoding="utf-8")
    assert BUNDLE in pbx
    assert "com.rocket.capsule.rocketCapsule;" not in pbx
    export = (tmp_path / "app" / "ios" / "ExportOptions.plist").read_text(encoding="utf-8")
    assert "app-store-connect" in export


def test_flutter_build_failure(tmp_path: Path) -> None:
    def runner(cmd: list[str], cwd: Path) -> tuple[int, str, float]:
        return 1, "Error: Xcode build failed", 4.0

    result = _ship(tmp_path, runner=runner)
    assert result["ok"] is False
    assert result["outcome"] == "failed"
    assert result["ipa"] is None
    assert any("flutter build ipa failed" in e for e in result["errors"])


def test_upload_failure_parses_validation_error(tmp_path: Path) -> None:
    def runner(cmd: list[str], cwd: Path) -> tuple[int, str, float]:
        if cmd and cmd[0] == "flutter":
            ipa_dir = cwd / "build" / "ios" / "ipa"
            ipa_dir.mkdir(parents=True, exist_ok=True)
            (ipa_dir / "App.ipa").write_bytes(b"ipa")
            return 0, "ok", 1.0
        return 1, "ERROR ITMS-90161: Invalid Bundle. The bundle identifier cannot be changed.", 3.0

    result = _ship(tmp_path, runner=runner)
    assert result["ok"] is False
    joined = " ".join(result["errors"])
    assert "ITMS-90161" in joined
    assert "Invalid Bundle" in joined


def test_missing_credentials(tmp_path: Path) -> None:
    with pytest.raises(ShipError, match="missing credentials"):
        _ship(tmp_path, env={})


def test_missing_p8_file(tmp_path: Path) -> None:
    env = _env(tmp_path)
    env["ASC_KEY_PATH"] = str(tmp_path / "missing.p8")
    with pytest.raises(ShipError, match="does not exist"):
        _ship(tmp_path, env=env)


def test_dry_run_prints_commands_and_executes_nothing(tmp_path: Path) -> None:
    called: list[list[str]] = []

    def runner(cmd: list[str], cwd: Path) -> tuple[int, str, float]:
        called.append(cmd)
        raise AssertionError("dry-run must not execute")

    proj = _project(tmp_path)
    result = _ship(tmp_path, project=proj, runner=runner, dry_run=True)
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["outcome"] == "dry_run"
    assert called == []
    assert any("flutter build ipa" in c for c in result["commands"])
    assert any("altool" in c and "[REDACTED]" in c for c in result["commands"])
    assert not (proj / COUNTER_NAME).exists()
    assert not (proj / "ios" / "ExportOptions.plist").exists()
    assert not (proj / "ship_report.json").exists()
    dumped = json.dumps(result)
    assert KEY_ID not in dumped
    assert ISSUER not in dumped


def test_build_number_increments(tmp_path: Path) -> None:
    proj = _project(tmp_path)
    env = _env(tmp_path)
    first = _ship(tmp_path, project=proj, env=env)
    second = _ship(tmp_path, project=proj, env=env)
    assert first["build"] == 1
    assert second["build"] == 2
    assert (proj / COUNTER_NAME).read_text(encoding="utf-8").strip() == "2"


def test_gate_not_green_refuses(tmp_path: Path) -> None:
    with pytest.raises(ShipError, match="gate is not green"):
        _ship(tmp_path, gate_fn=_bad_gate)


def test_next_build_number_and_identity(tmp_path: Path) -> None:
    proj = _project(tmp_path)
    assert next_build_number(proj) == 1
    assert next_build_number(proj) == 2
    apply_ios_identity(proj, bundle_id=BUNDLE, display_name="Harbor Notes", version="1.2.3", build=9)
    plist = (proj / "ios" / "Runner" / "Info.plist").read_text(encoding="utf-8")
    assert "Harbor Notes" in plist
    assert "1.2.3" in plist
    assert "<string>9</string>" in plist


def test_parse_altool_errors() -> None:
    raw = "INFO ok\nERROR ITMS-9000: Invalid Provisioning Profile\n"
    found = parse_altool_errors(raw)
    assert any("ITMS-9000" in line for line in found)


def test_redact_key_id_issuer_and_paths() -> None:
    path = f"/var/secret/AuthKey_{KEY_ID}.p8"
    text = f"key={KEY_ID} issuer={ISSUER} team={TEAM} file={path}"
    out = redact(text, key_id=KEY_ID, issuer_id=ISSUER, key_path=path, team_id=TEAM)
    assert KEY_ID not in out
    assert ISSUER not in out
    assert TEAM not in out
    assert path not in out
    assert ".p8" not in out
    words = ["BEGIN", "PRIVATE", "KEY"]
    pem = "-----" + " ".join(words) + "-----\nabc\n-----END " + " ".join(words[1:]) + "-----"
    hidden = redact(pem)
    assert "[REDACTED_PEM]" in hidden
    assert "PRIVATE KEY" not in hidden


def test_ship_never_calls_pilot() -> None:
    import harness.ship as ship

    src = inspect.getsource(ship)
    assert "complete_json" not in src
    assert "PilotSession" not in src
    assert "from pilot" not in src
    assert "import pilot" not in src


def test_pilot_prompts_contain_no_credentials() -> None:
    from harness.design import DESIGN_SYSTEM

    blobs = [CAPSULE_PREFIX, BARE_REQUIREMENTS, DESIGN_SYSTEM]
    for path in (
        ROOT / "src" / "harness" / "prompts.py",
        ROOT / "src" / "harness" / "design.py",
        ROOT / "src" / "harness" / "build.py",
        ROOT / "src" / "pilot" / "canned.py",
    ):
        blobs.append(path.read_text(encoding="utf-8"))
    joined = "\n".join(blobs)
    for needle in REQUIRED_ENV:
        assert needle not in joined
    assert "AuthKey_" not in joined
    assert "PRIVATE KEY" not in joined


def test_cli_dry_run_and_missing_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    for name in REQUIRED_ENV:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(SystemExit) as ei:
        main(["ship", str(tmp_path), "--dry-run"])
    assert ei.value.code == 1
    err = capsys.readouterr().err
    assert "missing credentials" in err
    assert KEY_ID not in err

    env = _env(tmp_path)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(SystemExit) as ei:
        main(["ship", str(_project(tmp_path)), "--dry-run"])
    assert ei.value.code == 0
    out = capsys.readouterr().out
    assert "DRY-RUN" in out
    assert "flutter build ipa" in out
    assert KEY_ID not in out
    assert ISSUER not in out
