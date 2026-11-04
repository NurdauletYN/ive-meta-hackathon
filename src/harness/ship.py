"""Upload a gated Flutter iOS build to App Store Connect. Credentials never go to a Pilot."""

from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .gate import GateReport, run_gate
from .redact import redact

REQUIRED_ENV = ("ASC_KEY_ID", "ASC_ISSUER_ID", "ASC_KEY_PATH", "APPLE_TEAM_ID", "BUNDLE_ID")
COUNTER_NAME = ".ship-build-number"
Runner = Callable[[list[str], Path], tuple[int, str, float]]


class ShipError(RuntimeError):
    """User-facing ship failure. Message is already redacted."""


def _default_runner(cmd: list[str], cwd: Path) -> tuple[int, str, float]:
    import subprocess

    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    out = ((proc.stdout or "") + (proc.stderr or ""))[-8000:]
    return proc.returncode, out, round((time.perf_counter() - started) * 1000, 1)


def _creds(env: Mapping[str, str]) -> dict[str, str]:
    missing = [name for name in REQUIRED_ENV if not (env.get(name) or "").strip()]
    if missing:
        raise ShipError("missing credentials: " + ", ".join(missing) + ". Set them in the environment, not in a prompt.")
    key_path = Path(env["ASC_KEY_PATH"].strip()).expanduser()
    if not key_path.is_file():
        raise ShipError("ASC_KEY_PATH does not exist (path redacted). Place the .p8 next to your local keychain copy.")
    return {name: env[name].strip() for name in REQUIRED_ENV}


def next_build_number(project: Path) -> int:
    path = project / COUNTER_NAME
    current = 0
    if path.is_file():
        try:
            current = int(path.read_text(encoding="utf-8").strip() or "0")
        except ValueError:
            current = 0
    nxt = current + 1
    path.write_text(str(nxt) + "\n", encoding="utf-8")
    return nxt


def _display_name(project: Path) -> str:
    strings = project / "lib" / "app" / "strings.dart"
    if strings.is_file():
        match = re.search(r"appName = '([^']+)'", strings.read_text(encoding="utf-8"))
        if match:
            return match.group(1)
    return "App"


def _set_plist_string(text: str, key: str, value: str) -> str:
    pattern = rf"(<key>{re.escape(key)}</key>\s*<string>)[^<]*(</string>)"
    if re.search(pattern, text):
        return re.sub(pattern, rf"\g<1>{value}\g<2>", text, count=1)
    return text.replace(
        "</dict>\n</plist>",
        f"\t<key>{key}</key>\n\t<string>{value}</string>\n</dict>\n</plist>",
        1,
    )


def _ensure_encryption_false(text: str) -> str:
    if "ITSAppUsesNonExemptEncryption" in text:
        return re.sub(
            r"(<key>ITSAppUsesNonExemptEncryption</key>\s*)<(true|false)/>",
            r"\1<false/>",
            text,
            count=1,
        )
    return text.replace(
        "</dict>\n</plist>",
        "\t<key>ITSAppUsesNonExemptEncryption</key>\n\t<false/>\n</dict>\n</plist>",
        1,
    )


def apply_ios_identity(project: Path, *, bundle_id: str, display_name: str, version: str, build: int) -> None:
    plist_path = project / "ios" / "Runner" / "Info.plist"
    if plist_path.is_file():
        text = plist_path.read_text(encoding="utf-8")
        text = _set_plist_string(text, "CFBundleDisplayName", display_name)
        text = _set_plist_string(text, "CFBundleName", display_name)
        text = _set_plist_string(text, "CFBundleShortVersionString", version)
        text = _set_plist_string(text, "CFBundleVersion", str(build))
        text = _ensure_encryption_false(text)
        plist_path.write_text(text, encoding="utf-8")
    pbx = project / "ios" / "Runner.xcodeproj" / "project.pbxproj"
    if pbx.is_file():
        body = pbx.read_text(encoding="utf-8")
        body = body.replace(
            "com.rocket.capsule.rocketCapsule.RunnerTests",
            f"{bundle_id}.RunnerTests",
        )
        body = body.replace("com.rocket.capsule.rocketCapsule", bundle_id)
        pbx.write_text(body, encoding="utf-8")
    pubspec = project / "pubspec.yaml"
    if pubspec.is_file():
        pub = pubspec.read_text(encoding="utf-8")
        pub = re.sub(r"^version:\s*.*$", f"version: {version}+{build}", pub, count=1, flags=re.M)
        pubspec.write_text(pub, encoding="utf-8")


def write_export_options(project: Path, team_id: str) -> Path:
    path = project / "ios" / "ExportOptions.plist"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
        "\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
        "<plist version=\"1.0\"><dict>\n"
        "\t<key>method</key><string>app-store-connect</string>\n"
        f"\t<key>teamID</key><string>{team_id}</string>\n"
        "\t<key>signingStyle</key><string>automatic</string>\n"
        "</dict></plist>\n",
        encoding="utf-8",
    )
    return path


def parse_altool_errors(output: str) -> list[str]:
    errors = []
    for line in output.splitlines():
        stripped = line.strip()
        if re.search(r"\b(ERROR|Error|failed|Invalid|validation)\b", stripped):
            errors.append(stripped[:300])
    return errors


def _find_ipa(project: Path) -> Path | None:
    ipa_dir = project / "build" / "ios" / "ipa"
    if not ipa_dir.is_dir():
        return None
    ipas = sorted(ipa_dir.glob("*.ipa"))
    return ipas[-1] if ipas else None


def run_ship(
    project_dir: Path,
    *,
    target: str = "testflight",
    dry_run: bool = False,
    env: Mapping[str, str] | None = None,
    runner: Runner | None = None,
    gate_fn: Callable[[Path], GateReport] | None = None,
    skip_gate: bool = False,
) -> dict[str, Any]:
    if target != "testflight":
        raise ShipError(f"unsupported target {target!r} (only testflight)")
    project = project_dir.resolve()
    environ = env or os.environ
    creds = _creds(environ)
    key_id, issuer, key_path, team_id, bundle_id = (
        creds["ASC_KEY_ID"],
        creds["ASC_ISSUER_ID"],
        creds["ASC_KEY_PATH"],
        creds["APPLE_TEAM_ID"],
        creds["BUNDLE_ID"],
    )
    display = _display_name(project)
    version = "1.0.0"
    pubspec = project / "pubspec.yaml"
    if pubspec.is_file():
        match = re.search(r"^version:\s*([0-9]+(?:\.[0-9]+)*)", pubspec.read_text(encoding="utf-8"), re.M)
        if match:
            version = match.group(1)
    export_path = project / "ios" / "ExportOptions.plist"
    commands = [
        f"flutter build ipa --release --export-options-plist={export_path}",
        "xcrun altool --upload-app --type ios -f <ipa> --apiKey [REDACTED] --apiIssuer [REDACTED]",
    ]
    planned = [
        "gate (must already be green)",
        "ios identity (bundle, display name, version, build)",
        "ITSAppUsesNonExemptEncryption=false",
        "ExportOptions.plist method=app-store-connect",
        *commands,
    ]
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "planned": planned,
            "commands": commands,
            "bundle_id": bundle_id,
            "display_name": display,
            "version": version,
            "target": target,
            "outcome": "dry_run",
        }

    steps: list[dict[str, Any]] = []
    if not skip_gate:
        started = time.perf_counter()
        report = (gate_fn or run_gate)(project)
        steps.append(
            {
                "name": "gate",
                "ok": report.ok,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            }
        )
        if not report.ok:
            raise ShipError("gate is not green; refuse to ship")

    build = next_build_number(project)
    apply_ios_identity(project, bundle_id=bundle_id, display_name=display, version=version, build=build)
    export = write_export_options(project, team_id)
    run = runner or _default_runner

    ipa_cmd = ["flutter", "build", "ipa", "--release", f"--export-options-plist={export}"]
    code, out, ms = run(ipa_cmd, project)
    out = redact(out, key_id=key_id, issuer_id=issuer, key_path=key_path, team_id=team_id)
    steps.append({"name": "flutter_build_ipa", "ok": code == 0, "duration_ms": ms, "detail": out[-500:]})
    if code != 0:
        payload = _report(
            project, steps, None, bundle_id, version, build, False,
            ["flutter build ipa failed"], key_id, issuer, key_path, team_id,
        )
        return payload

    ipa = _find_ipa(project)
    if ipa is None:
        return _report(
            project, steps, None, bundle_id, version, build, False,
            ["ipa not found under build/ios/ipa"], key_id, issuer, key_path, team_id,
        )

    upload = [
        "xcrun",
        "altool",
        "--upload-app",
        "--type",
        "ios",
        "-f",
        str(ipa),
        "--apiKey",
        key_id,
        "--apiIssuer",
        issuer,
    ]
    code, out, ms = run(upload, project)
    out = redact(out, key_id=key_id, issuer_id=issuer, key_path=key_path, team_id=team_id)
    parsed = parse_altool_errors(out)
    steps.append({"name": "altool_upload", "ok": code == 0, "duration_ms": ms, "detail": out[-500:]})
    ok = code == 0
    errors = [] if ok else (parsed or ["upload failed"])
    return _report(project, steps, ipa, bundle_id, version, build, ok, errors, key_id, issuer, key_path, team_id)


def _report(
    project: Path,
    steps: list[dict[str, Any]],
    ipa: Path | None,
    bundle_id: str,
    version: str,
    build: int,
    ok: bool,
    errors: list[str],
    key_id: str,
    issuer: str,
    key_path: str,
    team_id: str,
) -> dict[str, Any]:
    secrets = {"key_id": key_id, "issuer_id": issuer, "key_path": key_path, "team_id": team_id}
    payload = {
        "ok": ok,
        "dry_run": False,
        "outcome": "uploaded" if ok else "failed",
        "bundle_id": bundle_id,
        "version": version,
        "build": build,
        "ipa": str(ipa) if ipa else None,
        "steps": steps,
        "errors": [redact(e, **secrets) for e in errors],
        "project": str(project),
    }
    raw = json.dumps(payload, indent=2, default=str)
    raw = redact(raw, **secrets)
    payload = json.loads(raw)
    dest = project / "ship_report.json"
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
