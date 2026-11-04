"""Redact App Store Connect identifiers and key paths from logs and reports."""

from __future__ import annotations

import re
from pathlib import Path

_PEM = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S)
_UUID = re.compile(
    r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\b"
)
_P8 = re.compile(r"(?:/|[A-Za-z]:\\)[^\s'\"]+AuthKey_[A-Za-z0-9]+\.p8")
_KEY_FILE = re.compile(r"[^\s'\"]+\.p8")


def redact(text: str, *, key_id: str = "", issuer_id: str = "", key_path: str = "", team_id: str = "") -> str:
    out = text or ""
    out = _PEM.sub("[REDACTED_PEM]", out)
    for value in (key_path, key_id, issuer_id, team_id):
        if value:
            out = out.replace(value, "[REDACTED]")
    out = _P8.sub("[REDACTED_P8]", out)
    out = _KEY_FILE.sub("[REDACTED_P8]", out)
    out = _UUID.sub("[REDACTED_UUID]", out)
    return out


def redact_path(path: Path | str) -> str:
    return redact(str(path), key_path=str(path))
