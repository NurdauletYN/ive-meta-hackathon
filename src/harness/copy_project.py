"""Copy the capsule (or a flutter create tree) without build caches."""

from __future__ import annotations

import shutil
from pathlib import Path

IGNORE = shutil.ignore_patterns(
    ".dart_tool",
    "build",
    ".git",
    "__pycache__",
    ".venv",
    "ios/Pods",
    "android/.gradle",
    ".idea",
    ".DS_Store",
)


def copy_tree(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=IGNORE)
    return dest
