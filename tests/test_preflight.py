"""Preflight check tests: golden pass project and one fail fixture per check."""

from __future__ import annotations

from pathlib import Path

import pytest
from preflight.checks import (
    ALL_CHECKS,
    check_account_deletion,
    check_account_deletion_erases_data,
    check_home_not_webview,
    check_interactive_home,
    check_kit_usage,
    check_no_placeholders,
    check_not_text_only,
    check_privacy_links,
    check_remote_code,
    check_restore_purchases,
    check_smoke_tests_pass,
    check_subscription_disclosure,
    check_terms_links,
    check_wcag_contrast,
)
from preflight.runner import run_preflight
from preflight.types import CheckStatus

FIX = Path(__file__).resolve().parent / "fixtures" / "preflight"
PASS = FIX / "pass"


def test_pass_project_all_checks_pass() -> None:
    results = run_preflight(PASS)
    assert len(results) == len(ALL_CHECKS)
    assert all(r.status == CheckStatus.PASS for r in results), [r for r in results if r.status != CheckStatus.PASS]


def test_relocated_layout_still_passes(tmp_path: Path) -> None:
    """Bare mode may put screens anywhere under lib/; capsule paths must not be required."""
    import shutil

    dest = tmp_path / "relocated"
    shutil.copytree(PASS, dest)
    lib = dest / "lib"
    (lib / "screens").mkdir(parents=True)
    shutil.move(lib / "core" / "settings" / "settings_screen.dart", lib / "screens" / "settings_page.dart")
    shutil.move(lib / "core" / "paywall" / "paywall_screen.dart", lib / "screens" / "paywall_page.dart")
    (lib / "theme").mkdir(parents=True)
    shutil.move(lib / "app" / "design_tokens.json", lib / "theme" / "design_tokens.json")
    results = run_preflight(dest)
    assert all(r.status == CheckStatus.PASS for r in results), [r for r in results if r.status != CheckStatus.PASS]


@pytest.mark.parametrize(
    ("fixture", "check_fn", "check_id"),
    [
        ("fail_privacy", check_privacy_links, "privacy_link"),
        ("fail_terms", check_terms_links, "terms_link"),
        ("fail_delete", check_account_deletion, "account_deletion"),
        ("fail_restore", check_restore_purchases, "restore_purchases"),
        ("fail_disclosure", check_subscription_disclosure, "subscription_disclosure"),
        ("fail_placeholder", check_no_placeholders, "no_placeholders"),
        ("fail_contrast", check_wcag_contrast, "wcag_contrast"),
        ("fail_smoke", check_smoke_tests_pass, "smoke_tests_pass"),
        ("fail_erase", check_account_deletion_erases_data, "account_deletion_erases_data"),
        ("fail_webview", check_home_not_webview, "home_not_webview"),
    ],
)
def test_fail_fixture_triggers_exactly_one_check(
    fixture: str, check_fn, check_id: str
) -> None:
    project = FIX / fixture
    target = check_fn(project)
    assert target.status == CheckStatus.FAIL
    assert target.check_id == check_id
    others = [c for c in ALL_CHECKS if c is not check_fn]
    for other in others:
        result = other(project)
        assert result.status == CheckStatus.PASS, (other.__name__, result)


def test_interactive_home_pass_without_registry() -> None:
    assert check_interactive_home(PASS).status == CheckStatus.PASS


def test_interactive_home_warns_when_feature_is_stateless(tmp_path: Path) -> None:
    features = tmp_path / "lib" / "app" / "features"
    (features / "notes").mkdir(parents=True)
    (features / "registry.dart").write_text(
        "List<FeatureRoute> extraFeatureRoutes() {\n"
        "  return [FeatureRoute(path: '/notes', label: 'Notes', builder: (c) => const NotesScreen())];\n"
        "}\n",
        encoding="utf-8",
    )
    (features / "notes" / "notes_screen.dart").write_text(
        "class NotesScreen extends StatelessWidget {\n"
        "  const NotesScreen();\n"
        "  Widget build(c) => const Text('static');\n"
        "}\n",
        encoding="utf-8",
    )
    result = check_interactive_home(tmp_path)
    assert result.status == CheckStatus.WARN
    assert result.check_id == "interactive_home"


def test_interactive_home_pass_when_stateful(tmp_path: Path) -> None:
    features = tmp_path / "lib" / "app" / "features"
    (features / "notes").mkdir(parents=True)
    (features / "registry.dart").write_text(
        "List<FeatureRoute> extraFeatureRoutes() {\n"
        "  return [FeatureRoute(path: '/notes', label: 'Notes', builder: (c) => const NotesScreen())];\n"
        "}\n",
        encoding="utf-8",
    )
    (features / "notes" / "notes_screen.dart").write_text(
        "class NotesScreen extends StatefulWidget {\n"
        "  State createState() => _S();\n"
        "}\nclass _S extends State {\n"
        "  void add() { setState(() {}); }\n"
        "}\n",
        encoding="utf-8",
    )
    result = check_interactive_home(tmp_path)
    assert result.status == CheckStatus.PASS


def test_remote_code_warns(tmp_path: Path) -> None:
    result = check_remote_code(FIX / "fail_remote")
    assert result.status == CheckStatus.WARN
    assert result.check_id == "remote_code"
    assert check_remote_code(PASS).status == CheckStatus.PASS


def test_kit_usage_and_not_text_only_pass_without_features() -> None:
    assert check_kit_usage(PASS).status == CheckStatus.PASS
    assert check_not_text_only(PASS).status == CheckStatus.PASS


def test_kit_usage_warns_on_text_lists() -> None:
    project = FIX / "warn_kit"
    kit = check_kit_usage(project)
    assert kit.status == CheckStatus.WARN
    assert kit.check_id == "kit_usage"
    text_only = check_not_text_only(project)
    assert text_only.status == CheckStatus.WARN
    assert text_only.check_id == "not_text_only"


def test_kit_ok_fixture_passes_kit_checks() -> None:
    project = FIX / "kit_ok"
    assert check_kit_usage(project).status == CheckStatus.PASS
    assert check_not_text_only(project).status == CheckStatus.PASS
