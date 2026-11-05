"""Individual preflight checks (deterministic, file/line evidence).

Checks search all of `lib/**` so a blank (bare) project can pass without copying
capsule path names. Settings-like and paywall-like files are detected by filename
or content, not by `lib/core/...`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .types import CheckResult, CheckStatus

DartFile = tuple[Path, str]


def _lib_dart(project: Path) -> list[DartFile]:
    lib = project / "lib"
    if not lib.is_dir():
        return []
    out: list[DartFile] = []
    for path in sorted(lib.rglob("*.dart")):
        out.append((path, path.read_text(encoding="utf-8", errors="replace")))
    return out


def _line_of(text: str, needle: str) -> int | None:
    for index, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return index
    return None


def _rel(project: Path, path: Path) -> str:
    return str(path.relative_to(project))


def _is_settings_like(path: Path, text: str) -> bool:
    if "settings" in path.name.lower():
        return True
    if "router" in path.name.lower() or "service" in path.name.lower():
        return False
    return "settingsTitle" in text or "deleteAccountLabel" in text or "restoreLabel" in text


def _is_paywall_like(path: Path, text: str) -> bool:
    if "paywall" in path.name.lower():
        return True
    if "router" in path.name.lower():
        return False
    lowered = text.lower()
    return (
        "SubscriptionDisclosure" in text
        or "subscribeLabel" in text
        or ("subscribe" in lowered and "purchase" in lowered)
    )


def _group(files: list[DartFile], pred) -> list[DartFile]:
    return [item for item in files if pred(*item)]


def _has_route_or_word(text: str, route: str, word: str) -> bool:
    return route in text and word.lower() in text.lower()


def check_privacy_links(project: Path) -> CheckResult:
    check_id = "privacy_link"
    files = _lib_dart(project)
    if not files:
        return CheckResult(check_id, CheckStatus.FAIL, "lib/ missing", "lib", 1)
    settings = _group(files, _is_settings_like)
    paywall = _group(files, _is_paywall_like)
    if not settings:
        return CheckResult(check_id, CheckStatus.FAIL, "no settings-like Dart file under lib/", "lib", 1)
    if not paywall:
        return CheckResult(check_id, CheckStatus.FAIL, "no paywall-like Dart file under lib/", "lib", 1)
    settings_hit = next((p for p, t in settings if _has_route_or_word(t, "/privacy", "privacy")), None)
    paywall_hit = next((p for p, t in paywall if _has_route_or_word(t, "/privacy", "privacy")), None)
    if settings_hit is None or paywall_hit is None:
        missing = "settings" if settings_hit is None else "paywall"
        sample = settings[0][0] if settings_hit is None else paywall[0][0]
        return CheckResult(
            check_id,
            CheckStatus.FAIL,
            f"privacy route/link not found on a {missing} screen",
            _rel(project, sample),
            1,
        )
    return CheckResult(check_id, CheckStatus.PASS, "privacy link present in settings and paywall")


def check_terms_links(project: Path) -> CheckResult:
    check_id = "terms_link"
    files = _lib_dart(project)
    if not files:
        return CheckResult(check_id, CheckStatus.FAIL, "lib/ missing", "lib", 1)
    settings = _group(files, _is_settings_like)
    paywall = _group(files, _is_paywall_like)
    if not settings:
        return CheckResult(check_id, CheckStatus.FAIL, "no settings-like Dart file under lib/", "lib", 1)
    if not paywall:
        return CheckResult(check_id, CheckStatus.FAIL, "no paywall-like Dart file under lib/", "lib", 1)
    settings_hit = next((p for p, t in settings if _has_route_or_word(t, "/terms", "terms")), None)
    paywall_hit = next((p for p, t in paywall if _has_route_or_word(t, "/terms", "terms")), None)
    if settings_hit is None or paywall_hit is None:
        missing = "settings" if settings_hit is None else "paywall"
        sample = settings[0][0] if settings_hit is None else paywall[0][0]
        return CheckResult(
            check_id,
            CheckStatus.FAIL,
            f"terms route/link not found on a {missing} screen",
            _rel(project, sample),
            1,
        )
    return CheckResult(check_id, CheckStatus.PASS, "terms link present in settings and paywall")


_CALL_DELETE = re.compile(r"\.\s*deleteAccount\s*\(")
_CALL_RESTORE = re.compile(r"\.\s*restorePurchases\s*\(")


def check_account_deletion(project: Path) -> CheckResult:
    check_id = "account_deletion"
    files = _lib_dart(project)
    if not files:
        return CheckResult(check_id, CheckStatus.FAIL, "lib/ missing", "lib", 1)
    for path, text in files:
        if "service" in path.name.lower():
            continue
        if "Delete account" in text or _CALL_DELETE.search(text):
            line = _line_of(text, "Delete account") or _line_of(text, "deleteAccount")
            return CheckResult(
                check_id,
                CheckStatus.PASS,
                "account deletion reachable from the app",
                _rel(project, path),
                line,
            )
    return CheckResult(check_id, CheckStatus.FAIL, "delete account control not found under lib/", "lib", 1)


def check_restore_purchases(project: Path) -> CheckResult:
    check_id = "restore_purchases"
    files = _lib_dart(project)
    if not files:
        return CheckResult(check_id, CheckStatus.FAIL, "lib/ missing", "lib", 1)
    for path, text in files:
        if "service" in path.name.lower():
            continue
        if "Restore purchases" in text or _CALL_RESTORE.search(text):
            line = _line_of(text, "Restore purchases") or _line_of(text, "restorePurchases")
            return CheckResult(
                check_id,
                CheckStatus.PASS,
                "restore purchases control present",
                _rel(project, path),
                line,
            )
    return CheckResult(check_id, CheckStatus.FAIL, "restore purchases control not found under lib/", "lib", 1)


_DISCLOSURE_HINTS = (
    "SubscriptionDisclosure",
    "auto-renew",
    "auto renew",
    "automatically renew",
    "cancel anytime",
    "cancel at any time",
)
_PURCHASE_HINTS = ("Subscribe", "Purchase", "subscribeLabel")


def check_subscription_disclosure(project: Path) -> CheckResult:
    check_id = "subscription_disclosure"
    files = _lib_dart(project)
    paywall = _group(files, _is_paywall_like)
    if not paywall:
        return CheckResult(check_id, CheckStatus.FAIL, "no paywall-like Dart file under lib/", "lib", 1)
    for path, text in paywall:
        lowered = text.lower()
        has_disclosure = any(hint.lower() in lowered or hint in text for hint in _DISCLOSURE_HINTS)
        has_cta = any(token in text for token in _PURCHASE_HINTS)
        if has_disclosure and has_cta:
            line = _line_of(text, "SubscriptionDisclosure") or _line_of(text.lower(), "auto-renew") or 1
            return CheckResult(
                check_id,
                CheckStatus.PASS,
                "subscription disclosure beside purchase CTA",
                _rel(project, path),
                line,
            )
    sample = paywall[0][0]
    return CheckResult(
        check_id,
        CheckStatus.FAIL,
        "paywall missing disclosure (auto-renew/cancel) next to a purchase CTA",
        _rel(project, sample),
        1,
    )


PLACEHOLDER_PATTERNS = (
    re.compile(r"lorem\s+ipsum", re.I),
    re.compile(r"\bTODO\b"),
    re.compile(r"Flutter Demo Home Page"),
    re.compile(r"You have pushed the button this many times"),
)


def check_no_placeholders(project: Path) -> CheckResult:
    check_id = "no_placeholders"
    lib = project / "lib"
    if not lib.is_dir():
        return CheckResult(check_id, CheckStatus.FAIL, "lib/ missing", "lib", 1)
    for dart in lib.rglob("*.dart"):
        text = dart.read_text(encoding="utf-8", errors="replace")
        for pattern in PLACEHOLDER_PATTERNS:
            match = pattern.search(text)
            if match:
                line = text.count("\n", 0, match.start()) + 1
                return CheckResult(
                    check_id,
                    CheckStatus.FAIL,
                    f"placeholder pattern {pattern.pattern!r}",
                    str(dart.relative_to(project)),
                    line,
                )
    return CheckResult(check_id, CheckStatus.PASS, "no placeholder strings detected")


def _hex_to_rgb(value: str) -> tuple[float, float, float]:
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(value)
    r = int(value[0:2], 16) / 255.0
    g = int(value[2:4], 16) / 255.0
    b = int(value[4:6], 16) / 255.0
    return r, g, b


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    def linear(channel: float) -> float:
        return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)


def contrast_ratio(fg: str, bg: str) -> float:
    l1 = _relative_luminance(_hex_to_rgb(fg))
    l2 = _relative_luminance(_hex_to_rgb(bg))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _find_tokens_file(project: Path) -> Path | None:
    lib = project / "lib"
    if not lib.is_dir():
        return None
    matches = sorted(lib.rglob("design_tokens.json"))
    return matches[0] if matches else None


def check_wcag_contrast(project: Path) -> CheckResult:
    check_id = "wcag_contrast"
    path = _find_tokens_file(project)
    if path is None:
        return CheckResult(check_id, CheckStatus.FAIL, "design_tokens.json missing under lib/", "lib", 1)
    rel = _rel(project, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs = data.get("contrast_pairs") or []
    if not pairs:
        return CheckResult(check_id, CheckStatus.FAIL, "contrast_pairs empty", rel, 1)
    for pair in pairs:
        ratio = contrast_ratio(pair["foreground"], pair["background"])
        if ratio < 4.5:
            return CheckResult(
                check_id,
                CheckStatus.FAIL,
                f"contrast {ratio:.2f} below WCAG AA 4.5 for {pair.get('name', 'pair')}",
                rel,
                1,
            )
    return CheckResult(check_id, CheckStatus.PASS, "design token text/background pairs meet WCAG AA")


_STATEFUL = re.compile(
    r"\bStatefulWidget\b|\bsetState\s*\(|\bChangeNotifier\b|\bValueNotifier\b"
)


def check_interactive_home(project: Path) -> CheckResult:
    """WARN when a generated extra feature exists but has no in-memory state."""
    check_id = "interactive_home"
    registry = None
    for path, text in _lib_dart(project):
        if path.name == "registry.dart" and "extraFeatureRoutes" in text:
            registry = (path, text)
            break
    if registry is None:
        return CheckResult(check_id, CheckStatus.PASS, "no extra feature registry")
    path, text = registry
    if "FeatureRoute(" not in text:
        return CheckResult(check_id, CheckStatus.PASS, "no generated extra features")
    features_dir = path.parent
    for dart_path, src in _lib_dart(project):
        try:
            dart_path.relative_to(features_dir)
        except ValueError:
            continue
        if dart_path.name in {"registry.dart", "home_screen.dart"}:
            continue
        if _STATEFUL.search(src):
            line = _line_of(src, "StatefulWidget") or _line_of(src, "setState") or 1
            return CheckResult(
                check_id,
                CheckStatus.PASS,
                "generated feature has in-memory state",
                _rel(project, dart_path),
                line,
            )
    return CheckResult(
        check_id,
        CheckStatus.WARN,
        "generated home screen has no StatefulWidget or setState",
        _rel(project, path),
        _line_of(text, "extraFeatureRoutes") or 1,
    )


def check_smoke_tests_pass(project: Path) -> CheckResult:
    check_id = "smoke_tests_pass"
    tests = list((project / "test").rglob("*_test.dart")) if (project / "test").is_dir() else []
    for path in tests:
        text = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"\btest\s*\(|\btestWidgets\s*\(", text):
            return CheckResult(
                check_id,
                CheckStatus.PASS,
                "smoke test file present (gate also runs flutter test)",
                _rel(project, path),
                _line_of(text, "test(") or _line_of(text, "testWidgets(") or 1,
            )
    return CheckResult(check_id, CheckStatus.FAIL, "no test/*_test.dart with test() or testWidgets()", "test", 1)


_DELETE_ACCOUNT = re.compile(
    r"deleteAccount\s*\([^)]*\)\s*(?:async\s*)?\{(.*?)\n\}",
    re.S,
)


def check_account_deletion_erases_data(project: Path) -> CheckResult:
    check_id = "account_deletion_erases_data"
    for path, text in _lib_dart(project):
        match = _DELETE_ACCOUNT.search(text)
        if not match:
            continue
        body = match.group(1)
        if ".clear(" in body or re.search(r"=\s*null", body):
            return CheckResult(
                check_id,
                CheckStatus.PASS,
                "deleteAccount clears in-memory user data",
                _rel(project, path),
                text[: match.start()].count("\n") + 1,
            )
        return CheckResult(
            check_id,
            CheckStatus.FAIL,
            "deleteAccount does not clear in-memory data",
            _rel(project, path),
            text[: match.start()].count("\n") + 1,
        )
    return CheckResult(check_id, CheckStatus.FAIL, "no deleteAccount implementation under lib/", "lib", 1)


_WEBVIEW = re.compile(r"\bWebViewWidget\b|\bWebView\b|\bInAppWebView\b|webview_flutter")


def check_home_not_webview(project: Path) -> CheckResult:
    check_id = "home_not_webview"
    for path, text in _lib_dart(project):
        homeish = "home" in path.name.lower() or "HomeScreen" in text
        if not homeish:
            continue
        match = _WEBVIEW.search(text)
        if match:
            return CheckResult(
                check_id,
                CheckStatus.FAIL,
                "home renders a WebView as main content",
                _rel(project, path),
                text[: match.start()].count("\n") + 1,
            )
    return CheckResult(check_id, CheckStatus.PASS, "home is not a WebView")


_REMOTE = re.compile(
    r"\beval\s*\(|javascript:|Isolate\.spawnUri|dart:mirrors|WebAssembly\.instantiate"
)


def check_remote_code(project: Path) -> CheckResult:
    check_id = "remote_code"
    for path, text in _lib_dart(project):
        match = _REMOTE.search(text)
        if match:
            return CheckResult(
                check_id,
                CheckStatus.WARN,
                "dynamic remote code or eval-like pattern",
                _rel(project, path),
                text[: match.start()].count("\n") + 1,
            )
    return CheckResult(check_id, CheckStatus.PASS, "no eval-like remote code patterns")


KIT_WIDGETS = (
    "RocketScaffold",
    "KitPage",
    "HeroHeader",
    "SectionTitle",
    "ItemCard",
    "ProductCard",
    "ProductGrid",
    "ChipRow",
    "KitBadge",
    "PriceTag",
    "CartBar",
    "KitShopScreen",
    "KitDetailScreen",
    "KitProfileScreen",
    "FeaturedRow",
    "FeaturedCard",
    "SectionHeader",
    "ListSection",
    "ListRow",
    "SegmentedTabs",
    "ProgressRing",
    "StatRow",
    "StatTile",
    "EmptyState",
    "PrimaryButton",
    "SecondaryButton",
    "AppTextField",
    "QuantityStepper",
    "showKitFormSheet",
)

_EMOJI = re.compile(
    r"[\U0001F300-\U0001FAFF]|[\u2600-\u27BF]|Icons\.\w+"
)


def _generated_feature_files(project: Path) -> list[DartFile]:
    registry = None
    for path, text in _lib_dart(project):
        if path.name == "registry.dart" and "extraFeatureRoutes" in text:
            registry = (path, text)
            break
    if registry is None or "FeatureRoute(" not in registry[1]:
        return []
    features_dir = registry[0].parent
    out: list[DartFile] = []
    for dart_path, src in _lib_dart(project):
        try:
            dart_path.relative_to(features_dir)
        except ValueError:
            continue
        if dart_path.name in {"registry.dart", "home_screen.dart"}:
            continue
        out.append((dart_path, src))
    return out


def check_kit_usage(project: Path) -> CheckResult:
    check_id = "kit_usage"
    files = _generated_feature_files(project)
    if not files:
        return CheckResult(check_id, CheckStatus.PASS, "no generated extra features")
    found: list[str] = []
    sample = files[0]
    for name in KIT_WIDGETS:
        for path, text in files:
            if re.search(rf"\b{name}\b", text):
                found.append(name)
                sample = (path, text)
                break
    if len(found) >= 4:
        return CheckResult(
            check_id,
            CheckStatus.PASS,
            f"generated screens use {len(found)} kit widget types",
            _rel(project, sample[0]),
            _line_of(sample[1], found[0]) or 1,
        )
    return CheckResult(
        check_id,
        CheckStatus.WARN,
        f"generated screens use {len(found)} kit widget types (want at least 4)",
        _rel(project, sample[0]),
        1,
    )


def check_no_raw_material(project: Path) -> CheckResult:
    from harness.kitlint import kit_violations

    check_id = "no_raw_material"
    issues = kit_violations(project, limit=5)
    if not issues:
        return CheckResult(check_id, CheckStatus.PASS, "generated screens use kit blocks only")
    first = issues[0]
    rel, rest = first.split(" ", 1)
    line = 1
    if ":" in rel:
        path_part, line_part = rel.rsplit(":", 1)
        rel = path_part
        if line_part.isdigit():
            line = int(line_part)
    return CheckResult(check_id, CheckStatus.FAIL, rest, rel, line)


def check_not_text_only(project: Path) -> CheckResult:
    check_id = "not_text_only"
    files = _generated_feature_files(project)
    if not files:
        return CheckResult(check_id, CheckStatus.PASS, "no generated extra features")
    joined = "\n".join(text for _, text in files)
    has_card = (
        "ItemCard" in joined
        or "HeroHeader" in joined
        or "ProductCard" in joined
        or "KitShopScreen" in joined
        or "KitDetailScreen" in joined
        or "FeaturedCard" in joined
    )
    has_icon = _EMOJI.search(joined) is not None
    if has_card and has_icon:
        path, text = files[0]
        needle = "ItemCard" if "ItemCard" in text else ("HeroHeader" if "HeroHeader" in text else "")
        return CheckResult(
            check_id,
            CheckStatus.PASS,
            "generated screens include cards and emoji or icons",
            _rel(project, path),
            (_line_of(text, needle) if needle else 1) or 1,
        )
    path, _text = files[0]
    return CheckResult(
        check_id,
        CheckStatus.WARN,
        "generated screens look like text lists (need cards plus emoji or icons)",
        _rel(project, path),
        1,
    )


ALL_CHECKS = (
    check_privacy_links,
    check_terms_links,
    check_account_deletion,
    check_restore_purchases,
    check_subscription_disclosure,
    check_no_placeholders,
    check_wcag_contrast,
    check_interactive_home,
    check_smoke_tests_pass,
    check_account_deletion_erases_data,
    check_home_not_webview,
    check_remote_code,
    check_no_raw_material,
    check_kit_usage,
    check_not_text_only,
)
