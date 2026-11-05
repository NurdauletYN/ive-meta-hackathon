# Preflight checks

Deterministic verifiers run by `harness gate` before a Flutter project ships. Each check returns **PASS**, **FAIL**, or **WARN** with optional file/line evidence. `harness gate` also runs `flutter analyze` and `flutter test`.

These checks encode **general knowledge** of common mobile store expectations. The guideline column below is mapped from **secondary sources** (public write-ups of the App Store Review Guidelines, not Apple’s current official text). **The mapping needs verification against Apple’s current guidelines. It is not legal advice.** Preflight pass rates are not Apple rejection rates.

Checks search **all of `lib/`** (and `test/` for smoke). They do not require capsule paths, so `--mode bare` uses the same rules.

| ID | What it looks for | Related guideline (unverified, secondary sources) |
| --- | --- | --- |
| `privacy_link` | `/privacy` link on a settings-like screen **and** a paywall-like screen | 5.1.1 Data Collection and Storage |
| `terms_link` | `/terms` link on a settings-like screen **and** a paywall-like screen | 3.1.2 (legal / business terms around paid features) |
| `account_deletion` | In-app account deletion control anywhere under `lib/` | 5.1.1(v) Account Deletion |
| `restore_purchases` | Restore purchases control anywhere under `lib/` | 3.1.1 / 3.1.2 restore completed transactions |
| `subscription_disclosure` | Auto-renew/cancel wording or `SubscriptionDisclosure` next to a purchase CTA | 3.1.2 Subscriptions |
| `no_placeholders` | No lorem ipsum, TODO, or default Flutter demo strings | 2.1 App Completeness / 4.0 Design |
| `wcag_contrast` | Pairs in any `lib/**/design_tokens.json` meet WCAG AA 4.5:1 | 4.0 Design (accessibility is not a numbered store pass) |
| `interactive_home` | **WARN** if `extraFeatureRoutes()` has a screen with no `StatefulWidget` / `setState` | 4.2 Minimum Functionality |
| `smoke_tests_pass` | A `test/*_test.dart` with `test` / `testWidgets`; gate also runs `flutter test` | 2.1 App Completeness |
| `account_deletion_erases_data` | `deleteAccount()` clears in-memory user data (`.clear()` or `= null`); capsule has a behavioral Flutter test | 5.1.1(v) Account Deletion |
| `home_not_webview` | **FAIL** if a home-named screen renders `WebView` / `WebViewWidget` as main content | 4.2 Minimum Functionality (web wrapper) |
| `remote_code` | **WARN** on `eval(`, `javascript:`, `Isolate.spawnUri`, `dart:mirrors`, `WebAssembly.instantiate` | 2.5.2 Software Requirements (remote code) |
| `no_raw_material` | **FAIL** if generated features use ListTile, Scaffold, AppBar, FilterChip, Colors.*, etc. | 4.0 Design |
| `kit_usage` | **WARN** if generated extra screens use fewer than 4 distinct kit widget types | 4.0 Design |
| `not_text_only` | **WARN** if generated extra screens are Text/ListTile lists without cards and emoji or icons | 4.0 Design / 4.2 Minimum Functionality |

There are **15** checks: the original 12, `no_raw_material` (FAIL), and the two WARN kit checks. `kit_usage` and `not_text_only` never FAIL.

Fixtures under `tests/fixtures/preflight/` include a passing project and one failing tree per FAIL check. `remote_code` is WARN-only. `test_relocated_layout_still_passes` moves files off capsule paths and still expects PASS.
