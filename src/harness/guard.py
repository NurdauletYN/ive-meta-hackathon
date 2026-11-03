"""Validate pilot file operations against capsule protected paths and safety rules."""

from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

MAX_FILE_BYTES = 256_000


class FileOp(BaseModel):
    op: Literal["write", "patch", "delete"]
    path: str = Field(min_length=1)
    content: str | None = None
    find: str | None = None
    replace: str | None = None

    @model_validator(mode="after")
    def _shape(self) -> FileOp:
        parts = self.path.split("/")
        if self.path.startswith("/") or ".." in parts or "\\" in self.path:
            raise ValueError(f"path must be relative and stay inside the project: {self.path!r}")
        if self.op == "write":
            if self.content is None or self.find is not None or self.replace is not None:
                raise ValueError("write needs content and no find/replace")
        elif self.op == "patch":
            if self.find is None or self.replace is None or self.content is not None:
                raise ValueError("patch needs find and replace and no content")
        else:
            if self.content is not None or self.find is not None or self.replace is not None:
                raise ValueError("delete takes only a path")
        return self


@dataclass(frozen=True)
class GuardViolation:
    code: str
    message: str
    path: str | None = None


def load_manifest(project_dir: Path) -> dict[str, Any]:
    path = project_dir / "capsule.manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing capsule.manifest.json in {project_dir}")
    return json.loads(path.read_text(encoding="utf-8"))


def _is_protected(rel_path: str, patterns: list[str]) -> bool:
    normalized = rel_path.replace("\\", "/")
    for pattern in patterns:
        if fnmatch.fnmatch(normalized, pattern):
            return True
        if pattern.endswith("/**") and normalized.startswith(pattern[:-3]):
            return True
    return False


def validate_operations(project_dir: Path, operations: list[dict[str, Any]]) -> list[GuardViolation]:
    manifest = load_manifest(project_dir)
    protected = list(manifest.get("protected_paths") or [])
    violations: list[GuardViolation] = []

    for raw in operations:
        try:
            op = FileOp.model_validate(raw)
        except ValidationError as exc:
            violations.append(GuardViolation("invalid_op", str(exc.errors()[0]["msg"])))
            continue

        if _is_protected(op.path, protected):
            violations.append(
                GuardViolation("protected_path", f"cannot modify protected path {op.path!r}", op.path)
            )

        if op.op == "write" and op.content is not None:
            data = op.content.encode("utf-8")
            if b"\x00" in data:
                violations.append(GuardViolation("binary_content", "write content must not contain NUL bytes", op.path))
            if len(data) > MAX_FILE_BYTES:
                violations.append(
                    GuardViolation("oversize", f"write content exceeds {MAX_FILE_BYTES} bytes", op.path)
                )
    return violations
