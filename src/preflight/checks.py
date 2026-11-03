"""Individual preflight checks (deterministic, file/line evidence)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .types import CheckResult, CheckStatus

PrivacyTermsCtx = tuple[Path, str]


def _read(project: Path, rel: str) -> PrivacyTermsCtx | None:
    path = project / rel
    if not path.is_file():
        return None
    return path, path.read_text(encoding="utf-8", errors="replace")


def _line_of(text: str, needle: str) -> int | None:
    for index, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return index
    return None


def check_privacy_links(project: Path) -> CheckResult:
    check_id = "privacy_link"
    for rel in ("lib/core/settings/settings_screen.dart", "lib/core/paywall/paywall_screen.dart"):
        ctx = _read(project, rel)
        if ctx is None:
            return CheckResult(check_id, CheckStatus.FAIL, f"missing {rel}", rel, 1)
        path, text = ctx
        if "privacy" not in text.lower() or "/privacy" not in text:
            return CheckResult(check_id, CheckStatus.FAIL, "privacy route/link not found", str(path.relative_to(project)), 1)
    return CheckResult(check_id, CheckStatus.PASS, "privacy link present in settings and paywall")


def check_terms_links(project: Path) -> CheckResult:
    check_id = "terms_link"
    for rel in ("lib/core/settings/settings_screen.dart", "lib/core/paywall/paywall_screen.dart"):
        ctx = _read(project, rel)
        if ctx is None:
            return CheckResult(check_id, CheckStatus.FAIL, f"missing {rel}", rel, 1)
        path, text = ctx
        if "terms" not in text.lower() or "/terms" not in text:
            return CheckResult(check_id, CheckStatus.FAIL, "terms route/link not found", str(path.relative_to(project)), 1)
    return CheckResult(check_id, CheckStatus.PASS, "terms link present in settings and paywall")


def check_account_deletion(project: Path) -> CheckResult:
    check_id = "account_deletion"
    rel = "lib/core/settings/settings_screen.dart"
    ctx = _read(project, rel)
    if ctx is None:
        return CheckResult(check_id, CheckStatus.FAIL, f"missing {rel}", rel, 1)
    path, text = ctx
    if "deleteAccount" not in text and "Delete account" not in text:
        return CheckResult(check_id, CheckStatus.FAIL, "delete account control not found", str(path.relative_to(project)), 1)
    line = _line_of(text, "Delete account") or _line_of(text, "deleteAccount")
    return CheckResult(check_id, CheckStatus.PASS, "account deletion reachable from settings", str(path.relative_to(project)), line)


def check_restore_purchases(project: Path) -> CheckResult:
    check_id = "restore_purchases"
    rel = "lib/core/settings/settings_screen.dart"
    ctx = _read(project, rel)
    if ctx is None:
        return CheckResult(check_id, CheckStatus.FAIL, f"missing {rel}", rel, 1)
    path, text = ctx
    if "restorePurchases" not in text and "Restore purchases" not in text:
        return CheckResult(check_id, CheckStatus.FAIL, "restore purchases control not found", str(path.relative_to(project)), 1)
    line = _line_of(text, "Restore purchases") or _line_of(text, "restorePurchases")
    return CheckResult(check_id, CheckStatus.PASS, "restore purchases control present", str(path.relative_to(project)), line)


def check_subscription_disclosure(project: Path) -> CheckResult:
    check_id = "subscription_disclosure"
    rel = "lib/core/paywall/paywall_screen.dart"
    ctx = _read(project, rel)
    if ctx is None:
        return CheckResult(check_id, CheckStatus.FAIL, f"missing {rel}", rel, 1)
    path, text = ctx
    if "SubscriptionDisclosure" not in text:
        return CheckResult(check_id, CheckStatus.FAIL, "SubscriptionDisclosure widget not used on paywall", str(path.relative_to(project)), 1)
    if not any(token in text for token in ("Subscribe", "Purchase", "subscribeLabel")):
        return CheckResult(check_id, CheckStatus.FAIL, "purchase CTA not found near disclosure", str(path.relative_to(project)), 1)
    line = _line_of(text, "SubscriptionDisclosure")
    return CheckResult(check_id, CheckStatus.PASS, "subscription disclosure beside purchase CTA", str(path.relative_to(project)), line)


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


def _contrast_ratio(fg: str, bg: str) -> float:
    l1 = _relative_luminance(_hex_to_rgb(fg))
    l2 = _relative_luminance(_hex_to_rgb(bg))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def check_wcag_contrast(project: Path) -> CheckResult:
    check_id = "wcag_contrast"
    rel = "lib/app/design_tokens.json"
    path = project / rel
    if not path.is_file():
        return CheckResult(check_id, CheckStatus.FAIL, "design_tokens.json missing", rel, 1)
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs = data.get("contrast_pairs") or []
    if not pairs:
        return CheckResult(check_id, CheckStatus.FAIL, "contrast_pairs empty", rel, 1)
    for pair in pairs:
        ratio = _contrast_ratio(pair["foreground"], pair["background"])
        if ratio < 4.5:
            return CheckResult(
                check_id,
                CheckStatus.FAIL,
                f"contrast {ratio:.2f} below WCAG AA 4.5 for {pair.get('name', 'pair')}",
                rel,
                1,
            )
    return CheckResult(check_id, CheckStatus.PASS, "design token text/background pairs meet WCAG AA")


ALL_CHECKS = (
    check_privacy_links,
    check_terms_links,
    check_account_deletion,
    check_restore_purchases,
    check_subscription_disclosure,
    check_no_placeholders,
    check_wcag_contrast,
)
