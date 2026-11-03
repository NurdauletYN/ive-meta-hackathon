"""Harness writes spec.app_name into visible titles."""

from __future__ import annotations

import shutil
from pathlib import Path

from harness.branding import apply_branding, visible_rocket_capsule
from pilot.schemas import AppSpec

ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / "flutter_template"


def _spec(name: str = "Brewly") -> AppSpec:
    return AppSpec.model_validate(
        {
            "app_name": name,
            "bundle_id": "com.example.brewly",
            "onboarding": [
                {"title": "A", "body": "a"},
                {"title": "B", "body": "b"},
                {"title": "C", "body": "c"},
            ],
            "paywall_title": "Plus",
            "paywall_body": "body",
            "paywall_cta": "Go",
            "screens": [{"id": "menu", "purpose": "list", "fields": [{"name": "title", "type": "string"}]}],
            "data_models": [{"name": "Item", "fields": [{"name": "title", "type": "string"}]}],
        }
    )


def test_apply_branding_removes_visible_rocket_capsule(tmp_path: Path) -> None:
    dest = tmp_path / "project"
    shutil.copytree(CAPSULE, dest, ignore=shutil.ignore_patterns("build", ".dart_tool"))
    apply_branding(dest, _spec("Brewly"))
    strings = (dest / "lib" / "app" / "strings.dart").read_text(encoding="utf-8")
    assert "appName = 'Brewly'" in strings
    assert "homeTitle = 'Brewly'" in strings
    assert "Rocket Capsule" not in strings
    html = (dest / "web" / "index.html").read_text(encoding="utf-8")
    assert "<title>Brewly</title>" in html
    assert "rocket_capsule" not in html.lower()
    assert 'content="Brewly"' in html
    manifest = (dest / "web" / "manifest.json").read_text(encoding="utf-8")
    assert "Brewly" in manifest
    main = (dest / "lib" / "main.dart").read_text(encoding="utf-8")
    assert "AppStrings.appName" in main
    assert visible_rocket_capsule(dest) == []


def test_apply_branding_escapes_quotes(tmp_path: Path) -> None:
    dest = tmp_path / "project"
    shutil.copytree(CAPSULE, dest, ignore=shutil.ignore_patterns("build", ".dart_tool"))
    apply_branding(dest, _spec("Bob's List"))
    strings = (dest / "lib" / "app" / "strings.dart").read_text(encoding="utf-8")
    assert r"Bob\'s List" in strings
