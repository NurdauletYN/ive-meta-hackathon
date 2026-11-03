"""Tests for protected-path guard."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from harness.guard import GuardViolation, validate_operations

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "flutter_template"


def test_rejects_protected_path_write() -> None:
    violations = validate_operations(
        TEMPLATE,
        [{"op": "write", "path": "lib/core/router/app_router.dart", "content": "// hack", "find": None, "replace": None}],
    )
    assert any(v.code == "protected_path" for v in violations)


def test_allows_editable_path_write() -> None:
    violations = validate_operations(
        TEMPLATE,
        [{"op": "write", "path": "lib/app/features/home/home_screen.dart", "content": "// ok", "find": None, "replace": None}],
    )
    assert violations == []


def test_rejects_traversal_and_absolute() -> None:
    for path in ("/etc/passwd", "../outside.dart"):
        violations = validate_operations(
            TEMPLATE,
            [{"op": "write", "path": path, "content": "x", "find": None, "replace": None}],
        )
        assert violations and violations[0].code == "invalid_op"


def test_rejects_binary_and_oversize(tmp_path: Path) -> None:
    manifest = {"protected_paths": [], "editable_paths": ["lib/**"]}
    project = tmp_path / "proj"
    project.mkdir()
    (project / "capsule.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    big = "a" * 300_000
    violations = validate_operations(
        project,
        [{"op": "write", "path": "lib/huge.dart", "content": big, "find": None, "replace": None}],
    )
    assert any(v.code == "oversize" for v in violations)
    violations = validate_operations(
        project,
        [{"op": "write", "path": "lib/bin.dart", "content": "a\x00b", "find": None, "replace": None}],
    )
    assert any(v.code == "binary_content" for v in violations)


def test_delete_on_protected_path() -> None:
    violations = validate_operations(TEMPLATE, [{"op": "delete", "path": "lib/core/auth/auth_service.dart"}])
    assert any(v.code == "protected_path" for v in violations)


def test_rejects_path_outside_build_allowlist() -> None:
    violations = validate_operations(
        TEMPLATE,
        [{"op": "write", "path": "lib/app/theme_loader.dart", "content": "// no", "find": None, "replace": None}],
        allowed_prefixes=["lib/app/features/**", "lib/app/strings.dart"],
    )
    assert any(v.code == "not_editable" for v in violations)
