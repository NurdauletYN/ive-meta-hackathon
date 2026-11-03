"""Write the spec's app name into visible titles. Harness-side; the Pilot does not do this."""

from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

from pilot.schemas import AppSpec

_ROCKET = re.compile(r"Rocket Capsule|rocket_capsule", re.I)


def dart_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def apply_branding(project: Path, spec: AppSpec) -> None:
    name = spec.app_name.strip() or "App"
    _patch_strings(project / "lib" / "app" / "strings.dart", name)
    _patch_main(project / "lib" / "main.dart", name)
    _patch_web_index(project / "web" / "index.html", name)
    _patch_manifest(project / "web" / "manifest.json", name)


def _patch_strings(path: Path, name: str) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    quoted = dart_string(name)
    text = re.sub(r"static const appName = '[^']*';", f"static const appName = {quoted};", text)
    text = re.sub(r"static const homeTitle = '[^']*';", f"static const homeTitle = {quoted};", text)
    path.write_text(text, encoding="utf-8")


def _patch_main(path: Path, name: str) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if "AppStrings.appName" in text:
        path.write_text(text, encoding="utf-8")
        return
    text = text.replace("title: 'Rocket Capsule'", f"title: {dart_string(name)}")
    path.write_text(text, encoding="utf-8")


def _patch_web_index(path: Path, name: str) -> None:
    if not path.is_file():
        return
    safe = escape(name, quote=True)
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<title>[^<]*</title>", f"<title>{safe}</title>", text)
    text = re.sub(
        r'<meta name="apple-mobile-web-app-title" content="[^"]*"',
        f'<meta name="apple-mobile-web-app-title" content="{safe}"',
        text,
    )
    text = re.sub(
        r'<meta name="description" content="[^"]*"',
        f'<meta name="description" content="{safe}"',
        text,
    )
    path.write_text(text, encoding="utf-8")


def _patch_manifest(path: Path, name: str) -> None:
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    data["name"] = name
    data["short_name"] = name[:12]
    data["description"] = name
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def visible_rocket_capsule(project: Path) -> list[str]:
    """Paths under lib/app, lib/main.dart, and web/ that still show the template name."""
    hits: list[str] = []
    candidates = [project / "lib" / "main.dart", project / "web" / "index.html", project / "web" / "manifest.json"]
    app = project / "lib" / "app"
    if app.is_dir():
        candidates.extend(sorted(app.rglob("*")))
    for path in candidates:
        if not path.is_file() or path.suffix not in {".dart", ".html", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if _ROCKET.search(text):
            hits.append(str(path.relative_to(project)))
    return hits
