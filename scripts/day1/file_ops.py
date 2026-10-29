"""File-operations plan: JSON schema sent to Muse Spark, plus a strict local validator.

Used by 01_file_ops.py. Codegen (Day 2) will reuse the same shape.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

# Sent as text.format (Responses API structured output). strict=True: every property is required,
# nullable fields use a union with null, and no extra keys are allowed.
FILE_OPS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "operations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "op": {"type": "string", "enum": ["write", "patch", "delete"]},
                    "path": {"type": "string"},
                    "content": {"type": ["string", "null"]},
                    "find": {"type": ["string", "null"]},
                    "replace": {"type": ["string", "null"]},
                },
                "required": ["op", "path", "content", "find", "replace"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["operations"],
    "additionalProperties": False,
}


class FileOp(BaseModel):
    op: Literal["write", "patch", "delete"]
    path: str = Field(min_length=1)
    content: str | None = None
    find: str | None = None
    replace: str | None = None

    @model_validator(mode="after")
    def _check(self) -> FileOp:
        parts = self.path.split("/")
        if self.path.startswith("/") or ".." in parts or "\\" in self.path:
            raise ValueError(f"path must be relative and stay inside the project: {self.path!r}")
        if self.op == "write":
            if self.content is None or self.find is not None or self.replace is not None:
                raise ValueError("write needs content and no find/replace")
        elif self.op == "patch":
            if self.find is None or self.replace is None or self.content is not None:
                raise ValueError("patch needs find and replace and no content")
        else:  # delete
            if self.content is not None or self.find is not None or self.replace is not None:
                raise ValueError("delete takes only a path")
        return self


class FileOpsPlan(BaseModel):
    operations: list[FileOp] = Field(min_length=1)


PROMPT = """You are editing a small Flutter project. Current file lib/main.dart:

```dart
import 'package:flutter/material.dart';

void main() => runApp(const MaterialApp(home: Text('Hello')));
```

Make exactly these three changes and return them as file operations:
1. In lib/main.dart, change the text 'Hello' to 'Welcome' (use a patch with find and replace).
2. Create lib/widgets/card.dart with a simple stateless Card widget that shows a title string (use a write with full file content).
3. Delete lib/old_screen.dart.

Use relative paths. Return only the operations."""

EXPECTED_OPS: frozenset[tuple[str, str]] = frozenset(
    {
        ("patch", "lib/main.dart"),
        ("write", "lib/widgets/card.dart"),
        ("delete", "lib/old_screen.dart"),
    }
)


def check_plan(data: dict[str, Any]) -> tuple[bool, bool, list[str]]:
    """Return (schema_valid, matches_expected, problems)."""
    problems: list[str] = []
    try:
        plan = FileOpsPlan.model_validate(data)
    except ValidationError as exc:
        problems.extend(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
        return False, False, problems
    got = {(op.op, op.path) for op in plan.operations}
    if len(plan.operations) != len(EXPECTED_OPS):
        problems.append(f"expected {len(EXPECTED_OPS)} operations, got {len(plan.operations)}")
    missing = EXPECTED_OPS - got
    extra = got - EXPECTED_OPS
    problems.extend(f"missing {op} {path}" for op, path in sorted(missing))
    problems.extend(f"unexpected {op} {path}" for op, path in sorted(extra))
    return True, not problems, problems
