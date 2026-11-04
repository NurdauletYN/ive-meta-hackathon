"""Offline storepack tests: FakePilot listing, mock icon, no live Meta/Apple calls."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image
from harness.cli import main
from harness.prompts import BARE_REQUIREMENTS, CAPSULE_PREFIX
from pilot.fake import FakePilot
from pilot.session import PilotSession
from storepack.pack import LISTING_SCHEMA, build_storepack, fake_listing, mock_icon_png
from storepack.scan import read_app_name, scan_app

ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / "flutter_template"


def _png_size(data: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(data)) as img:
        return img.size


def _session(pilot: FakePilot, tmp_path: Path) -> PilotSession:
    return PilotSession(pilot, run_id="storepack-test", usage_path=tmp_path / "usage.jsonl")


def _project(tmp_path: Path, *, camera: bool = False, dart: str | None = None) -> Path:
    proj = tmp_path / "app"
    (proj / "lib" / "app").mkdir(parents=True)
    (proj / "ios" / "Runner").mkdir(parents=True)
    (proj / "lib" / "app" / "strings.dart").write_text(
        "class AppStrings { static const appName = 'Harbor Notes'; }\n",
        encoding="utf-8",
    )
    body = dart or (
        "class AuthService { Future<void> signIn({required String email, required String password}) async {} }\n"
        "class BillingService { Future<void> restorePurchases() async {} }\n"
        "Future<void> deleteAccount() async {}\n"
    )
    (proj / "lib" / "main.dart").write_text(body, encoding="utf-8")
    plist = """<?xml version="1.0" encoding="UTF-8"?>
<plist><dict>
	<key>CFBundleDisplayName</key>
	<string>Harbor Notes</string>
"""
    if camera:
        plist += "\t<key>NSCameraUsageDescription</key>\n\t<string>Take photos of notes.</string>\n"
    plist += "</dict></plist>\n"
    (proj / "ios" / "Runner" / "Info.plist").write_text(plist, encoding="utf-8")
    return proj


def test_listing_schema_forbids_extra_properties() -> None:
    assert LISTING_SCHEMA["additionalProperties"] is False
    assert set(LISTING_SCHEMA["required"]) == {"name", "subtitle", "description", "keywords"}


def test_scan_capsule_has_auth_billing_no_camera() -> None:
    facts = scan_app(CAPSULE)
    assert facts["auth"] is True
    assert facts["billing"] is True
    assert facts["account_deletion"] is True
    assert facts["permissions"] == []
    assert read_app_name(CAPSULE) == "Rocket Capsule"


def test_scan_detects_camera_permission(tmp_path: Path) -> None:
    facts = scan_app(_project(tmp_path, camera=True))
    assert "camera" in facts["permissions"]


def test_scan_empty_lib_has_no_auth(tmp_path: Path) -> None:
    facts = scan_app(_project(tmp_path, dart="// empty shell\n"))
    assert facts["auth"] is False
    assert facts["billing"] is False
    assert facts["account_deletion"] is False


def test_fake_storepack_writes_zip_and_lanczos_sizes(tmp_path: Path) -> None:
    proj = _project(tmp_path, camera=True)
    fake = FakePilot()
    listing = {
        "name": "Harbor Notes",
        "subtitle": "Notes for a harbor.",
        "description": "Write notes. Template listing.",
        "keywords": "notes,harbor",
    }
    fake.enqueue("storepack", listing)
    out = tmp_path / "pack"
    result = build_storepack(
        proj,
        out,
        session=_session(fake, tmp_path),
        image_fn=lambda _p: mock_icon_png(),
        icon_mock=True,
    )
    assert result["ok"] is True
    assert result["privacy_label"] == "template, not legal advice"
    assert result["listing"] == listing
    assert result["icon"]["mock"] is True
    assert result["icon"]["1024"] == [1024, 1024]
    assert result["icon"]["512"] == [512, 512]
    assert _png_size((out / "icon_1024.png").read_bytes()) == (1024, 1024)
    assert _png_size((out / "icon_512.png").read_bytes()) == (512, 512)
    assert (out / "icon_raw.png").is_file()
    privacy = (out / "privacy.md").read_text(encoding="utf-8")
    assert "TEMPLATE, NOT LEGAL ADVICE" in privacy
    assert "template" in privacy.lower()
    assert "not legal advice" in privacy.lower()
    assert "account sign-in" in privacy
    assert "billing" in privacy
    assert "camera" in privacy
    zpath = Path(result["zip"])
    with zipfile.ZipFile(zpath) as zf:
        names = set(zf.namelist())
    assert names == {
        "listing.json",
        "privacy.md",
        "icon_raw.png",
        "icon_1024.png",
        "icon_512.png",
    }


def test_privacy_omits_undetected_features(tmp_path: Path) -> None:
    proj = _project(tmp_path, dart="// no interfaces\n")
    fake = FakePilot()
    fake.enqueue("storepack", fake_listing("Empty"))
    result = build_storepack(
        proj,
        tmp_path / "empty",
        session=_session(fake, tmp_path),
        image_fn=lambda _p: mock_icon_png(),
    )
    privacy = Path(result["zip"]).with_name("privacy.md").read_text(encoding="utf-8")
    assert "No auth interface" in privacy
    assert "No billing interface" in privacy
    assert "No camera" in privacy


def test_prompts_never_include_credentials(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "sk-live-storepack-secret-value"
    monkeypatch.setenv("META_API_KEY", secret)
    monkeypatch.setenv("ASC_KEY_ID", "SHIPKEYID99")
    monkeypatch.setenv("ASC_ISSUER_ID", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    monkeypatch.setenv("ASC_KEY_PATH", "/tmp/AuthKey_SHIPKEYID99.p8")
    fake = FakePilot()
    fake.enqueue("storepack", fake_listing("Harbor Notes"))
    proj = _project(tmp_path)
    build_storepack(
        proj,
        tmp_path / "cred",
        session=_session(fake, tmp_path),
        image_fn=lambda prompt: mock_icon_png() if "sk-live" not in prompt else b"",
        icon_mock=True,
    )
    blob = "\n".join(f"{tag}\n{system}\n{user}" for tag, system, user in fake.calls)
    assert secret not in blob
    assert "SHIPKEYID99" not in blob
    assert "AuthKey_" not in blob
    assert "META_API_KEY" not in blob
    src = (ROOT / "src" / "storepack" / "pack.py").read_text(encoding="utf-8")
    assert "os.environ" not in src
    assert "META_API_KEY" not in src
    assert "ASC_KEY" not in src
    joined = CAPSULE_PREFIX + BARE_REQUIREMENTS
    assert secret not in joined


def test_cli_fake_storepack(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("harness.cli.DEFAULT_USAGE_PATH", tmp_path / "usage.jsonl")
    proj = _project(tmp_path)
    out = tmp_path / "cli-out"
    with pytest.raises(SystemExit) as ei:
        main(["storepack", str(proj), "--pilot", "fake", "--out", str(out), "--max-usd", "1"])
    assert ei.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["icon"]["mock"] is True
    assert (out / "storepack.zip").is_file()
    assert payload["privacy_label"] == "template, not legal advice"
