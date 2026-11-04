"""Detect what the generated app actually has, so copy is not invented."""

from __future__ import annotations

import re
from pathlib import Path

_APP_NAME_RE = re.compile(r"static const appName\s*=\s*'([^']*)'")

_PERMISSION_KEYS = (
    ("NSCameraUsageDescription", "camera"),
    ("NSPhotoLibraryUsageDescription", "photos"),
    ("NSMicrophoneUsageDescription", "microphone"),
    ("NSLocationWhenInUseUsageDescription", "location"),
    ("NSFaceIDUsageDescription", "face_id"),
)


def read_app_name(project: Path) -> str:
    path = project / "lib" / "app" / "strings.dart"
    if path.is_file():
        match = _APP_NAME_RE.search(path.read_text(encoding="utf-8", errors="replace"))
        if match:
            return match.group(1)
    return "App"


def scan_app(project: Path) -> dict[str, bool | list[str]]:
    texts: list[str] = []
    lib = project / "lib"
    if lib.is_dir():
        for dart in lib.rglob("*.dart"):
            texts.append(dart.read_text(encoding="utf-8", errors="replace"))
    blob = "\n".join(texts)
    plist = ""
    info = project / "ios" / "Runner" / "Info.plist"
    if info.is_file():
        plist = info.read_text(encoding="utf-8", errors="replace")
    permissions: list[str] = []
    for key, label in _PERMISSION_KEYS:
        if key in plist:
            permissions.append(label)
    if "permission_handler" in blob:
        permissions.append("runtime_permissions_plugin")
    return {
        "auth": "AuthService" in blob or "signIn(" in blob,
        "billing": "BillingService" in blob or "restorePurchases" in blob,
        "account_deletion": "deleteAccount" in blob,
        "permissions": permissions,
    }
