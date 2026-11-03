# Preflight checks

Deterministic verifiers run by `harness gate` before a Flutter project ships. Each check returns **PASS**, **FAIL**, or **WARN** with optional file and line evidence.

These checks encode **general knowledge** of common mobile store expectations (privacy/terms links, account deletion, restore purchases, subscription disclosures, obvious placeholder copy, readable contrast). They are **not legal advice** and have **not** been verified line-by-line against current Apple App Store or Google Play guidelines. Treat failures as engineering signals and confirm requirements with official documentation before submission.

Checks search **all of `lib/`**. They do not require capsule paths such as `lib/core/settings/settings_screen.dart`, so a blank (`--mode bare`) project is scored with the same rules as the capsule.

| ID | What it looks for |
| --- | --- |
| `privacy_link` | `/privacy` link on a settings-like screen **and** a paywall-like screen |
| `terms_link` | `/terms` link on a settings-like screen **and** a paywall-like screen |
| `account_deletion` | In-app account deletion control anywhere under `lib/` |
| `restore_purchases` | Restore purchases control anywhere under `lib/` |
| `subscription_disclosure` | Auto-renew/cancel wording or `SubscriptionDisclosure` next to a purchase CTA on a paywall-like screen |
| `no_placeholders` | No lorem ipsum, TODO, or default Flutter demo strings |
| `wcag_contrast` | Pairs in any `lib/**/design_tokens.json` meet WCAG AA 4.5:1 |
| `interactive_home` | **WARN** (not FAIL) if `extraFeatureRoutes()` has a screen with no `StatefulWidget` / `setState` |

Fixtures under `tests/fixtures/preflight/` include a passing project and one failing tree per check. `test_relocated_layout_still_passes` moves those files off capsule paths and still expects PASS.
