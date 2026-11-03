"""Flutter web build with a public --base-href so previews load in an iframe."""

from __future__ import annotations

import subprocess
from pathlib import Path


def normalize_base_href(value: str) -> str:
    href = value.strip()
    if not href.startswith("/"):
        href = "/" + href
    if not href.endswith("/"):
        href += "/"
    return href


def flutter_web_build(project: Path, base_href: str | None = None) -> tuple[bool, str]:
    cmd = ["flutter", "build", "web", "--release"]
    if base_href:
        cmd.extend(["--base-href", normalize_base_href(base_href)])
    proc = subprocess.run(cmd, cwd=project, capture_output=True, text=True)
    out = ((proc.stdout or "") + (proc.stderr or ""))[-2000:]
    return proc.returncode == 0, out
