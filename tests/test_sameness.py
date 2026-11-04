"""Pairwise Jaccard sameness over lib/app tokens."""

from __future__ import annotations

from pathlib import Path

from harness.sameness import app_tokens, grams, iter_projects, jaccard, pairwise, render_sameness


def _app(root: Path, name: str, dart: str) -> Path:
    proj = root / name
    dest = proj / "lib" / "app"
    dest.mkdir(parents=True)
    (dest / "screen.dart").write_text(dart, encoding="utf-8")
    return proj


def test_identical_apps_jaccard_one(tmp_path: Path) -> None:
    src = "class NotesScreen extends StatefulWidget { void add() { setState(() {}); } }\n"
    a = _app(tmp_path, "a", src)
    b = _app(tmp_path, "b", src)
    ga, gb = grams(app_tokens(a)), grams(app_tokens(b))
    assert jaccard(ga, gb) == 1.0


def test_literals_stripped(tmp_path: Path) -> None:
    a = _app(tmp_path, "a", "class A { final x = 'hello world'; void run() { foo(); } }\n")
    b = _app(tmp_path, "b", "class A { final x = 'other text'; void run() { foo(); } }\n")
    assert "hello" not in app_tokens(a)
    assert jaccard(grams(app_tokens(a)), grams(app_tokens(b))) == 1.0


def test_pairwise_and_glob(tmp_path: Path) -> None:
    _app(tmp_path, "one", "class One { void a() { foo(); bar(); baz(); qux(); } }\n")
    _app(tmp_path, "two", "class Two { void a() { foo(); bar(); baz(); qux(); } }\n")
    projects = iter_projects("*", cwd=tmp_path)
    assert len(projects) == 2
    rows = pairwise(projects)
    assert len(rows) == 1
    md = render_sameness(rows)
    assert "Jaccard" in md
    assert "threshold" not in md.lower() or "no pass/fail threshold" in md
