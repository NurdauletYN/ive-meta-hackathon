"""Apply validated write/patch/delete ops inside a project directory."""

from __future__ import annotations

from pathlib import Path

from .guard import FileOp, GuardViolation


def apply_operations(project_dir: Path, operations: list[FileOp]) -> list[GuardViolation]:
    root = project_dir.resolve()
    errors: list[GuardViolation] = []
    for op in operations:
        target = (root / op.path).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            errors.append(GuardViolation("escape", f"resolved path left the project: {op.path}", op.path))
            continue
        if op.op == "write":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(op.content or "", encoding="utf-8")
        elif op.op == "patch":
            if not target.is_file():
                errors.append(GuardViolation("missing", f"patch target does not exist: {op.path}", op.path))
                continue
            text = target.read_text(encoding="utf-8")
            find = op.find or ""
            if find not in text:
                errors.append(GuardViolation("find_miss", f"find string not in {op.path}", op.path))
                continue
            target.write_text(text.replace(find, op.replace or "", 1), encoding="utf-8")
        else:
            if target.is_file():
                target.unlink()
    return errors
