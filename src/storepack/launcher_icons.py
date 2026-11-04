"""Install a 1024×1024 PNG as iOS/Android/web launcher icons via flutter_launcher_icons."""

from __future__ import annotations

import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

IMAGE_PATH = "assets/icon/app_icon.png"
LAUNCHER_CMD = ["dart", "run", "flutter_launcher_icons"]

_CONFIG_BLOCK = """
flutter_launcher_icons:
  android: true
  ios: true
  image_path: assets/icon/app_icon.png
  remove_alpha_ios: true
  web:
    generate: true
    image_path: assets/icon/app_icon.png
"""

Runner = Callable[[list[str], Path], tuple[int, str, float]]


def _default_runner(cmd: list[str], cwd: Path) -> tuple[int, str, float]:
    started = time.perf_counter()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    out = ((proc.stdout or "") + (proc.stderr or ""))[-8000:]
    return proc.returncode, out, round((time.perf_counter() - started) * 1000, 1)


def _restore_swift_asset_symbol_extensions(pbxproj: Path) -> None:
    """flutter_launcher_icons 0.14.4 writes AppIcon into the wrong build setting. Put YES back."""
    if not pbxproj.is_file():
        return
    text = pbxproj.read_text(encoding="utf-8")
    fixed = text.replace(
        "ASSETCATALOG_COMPILER_GENERATE_SWIFT_ASSET_SYMBOL_EXTENSIONS = AppIcon;",
        "ASSETCATALOG_COMPILER_GENERATE_SWIFT_ASSET_SYMBOL_EXTENSIONS = YES;",
    )
    if fixed != text:
        pbxproj.write_text(fixed, encoding="utf-8")


def ensure_launcher_config(pubspec: Path) -> bool:
    """Append a flutter_launcher_icons block if the pubspec has none. Returns True if written."""
    text = pubspec.read_text(encoding="utf-8")
    if "flutter_launcher_icons:" in text:
        return False
    pubspec.write_text(text.rstrip() + "\n" + _CONFIG_BLOCK, encoding="utf-8")
    return True


def apply_launcher_icons(
    project: Path,
    icon_1024: Path,
    *,
    runner: Runner | None = None,
) -> dict[str, Any]:
    """Copy the 1024 PNG into the Flutter project and run flutter_launcher_icons.

    Skips (does not fail the zip) when there is no pubspec.yaml. A failing dart run
    is reported with ok=False. No live Apple/Meta calls.
    """
    if not icon_1024.is_file():
        return {"ok": False, "skipped": True, "reason": "icon_1024 missing"}
    pubspec = project / "pubspec.yaml"
    if not pubspec.is_file():
        return {"ok": False, "skipped": True, "reason": "no pubspec.yaml"}
    dest = project / IMAGE_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(icon_1024.read_bytes())
    ensure_launcher_config(pubspec)
    code, out, ms = (runner or _default_runner)(list(LAUNCHER_CMD), project)
    _restore_swift_asset_symbol_extensions(project / "ios" / "Runner.xcodeproj" / "project.pbxproj")
    return {
        "ok": code == 0,
        "skipped": False,
        "path": IMAGE_PATH,
        "duration_ms": ms,
        "command": " ".join(LAUNCHER_CMD),
        "output": (out or "")[-1500:],
    }
