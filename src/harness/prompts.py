"""Byte-identical capsule API prefix. Keep this string stable across spec and build calls."""

from pathlib import Path

# Do not reformat: prefix bytes are part of the cache-hit experiment.
KIT_API = (Path(__file__).resolve().parents[2] / "docs" / "kit_api.md").read_text(encoding="utf-8")

CAPSULE_PREFIX = (
    """You are the Pilot for the Rocket Flutter capsule.

Capsule API (do not invent other paths):
- Protected (never write): lib/core/** and capsule.manifest.json.
- Editable: lib/app/features/** and lib/app/strings.dart (and lib/app/design_tokens.json is applied by the harness, not by you).
- Extra screens MUST be registered in lib/app/features/registry.dart via extraFeatureRoutes(). The core router already reads that list. Keep the FeatureRoute class with `final bool tab` (default false) and `final String icon`. First entry is home at / and /home. Mark up to 4 routes tab: true with an emoji icon for bottom navigation.
- Auth: AuthService.deleteAccount(). Billing: BillingService.purchase / restorePurchases. Do not reimplement those services.
- Settings, paywall, terms, privacy, onboarding scaffolds already exist in lib/core. Do not recreate them.
- File operations JSON: op write|patch|delete, relative path, content/find/replace (null when unused). One patch replaces the first match only. Bare mode only.
- Harness build/improve: you return AppCatalog JSON (products + hero/profile copy + tab labels). The harness writes KitShopScreen / KitDetailScreen / KitProfileScreen Dart; never emit layout Dart for those screens.
- Design is the product. Do not invent page chrome (no AppBar, NavigationBar, ListTile, CircleAvatar, FilterChip, Card, raw Scaffold, Colors.*, Color(0x...), Navigator.push). Kit blocks only. Seed 8 to 12 products with believable names, prices, and KitPhoto keys. Local photos only. Follow the examples below.

Rules: no TODO, no lorem ipsum, no default Flutter demo strings. Dart 3 null-safety. Do not edit pubspec.yaml.

"""
    + KIT_API
)

BARE_REQUIREMENTS = """Build a Flutter app from a blank project.

Requirements in plain words:
- Email/password auth with in-app account deletion.
- Onboarding (three short screens of copy).
- Paywall with a subscription disclosure next to the purchase CTA (price, period, auto-renew, cancel wording).
- Restore purchases control.
- Terms and Privacy screens linked from settings and from the paywall.
- A settings screen that reaches delete-account, restore-purchases, privacy, and terms.

You get a blank Flutter project. There is no scaffold and no protected-path list. pubspec.yaml is locked (do not change dependencies). Use the same file-operations JSON (write/patch/delete). No TODO, no lorem ipsum, no default Flutter demo strings.

Preflight searches all of lib/ (paths need not match the capsule). Put privacy and terms links on both a settings-named screen and a paywall-named screen; put auto-renew/cancel wording next to the purchase CTA; write lib/app/design_tokens.json with WCAG AA contrast_pairs.
"""
