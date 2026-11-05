"""Studio build identity so a stale `harness ui` process is obvious."""

from __future__ import annotations

import hashlib
from pathlib import Path

STUDIO_VERSION = "2026.11.05-catalog"

_TRACKED = (
    "src/harness/prompts.py",
    "src/harness/build.py",
    "src/harness/kit_writer.py",
    "src/harness/palettes.py",
    "src/pilot/schemas.py",
)


def studio_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for rel in _TRACKED:
        path = root / rel
        if path.is_file():
            digest.update(rel.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def studio_info(root: Path) -> dict[str, str | bool]:
    return {
        "version": STUDIO_VERSION,
        "fingerprint": studio_fingerprint(root),
        "catalog_writer": True,
    }
