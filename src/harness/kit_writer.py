"""Write kit screen files from AppCatalog JSON. The model never emits layout Dart."""

from __future__ import annotations

from pathlib import Path

from pilot.schemas import AppCatalog, CatalogProduct

KIT_PHOTO_KEYS = (
    "shoe",
    "jacket",
    "hoodie",
    "shorts",
    "cleat",
    "coffee",
    "tool",
    "plant",
    "bag",
    "headphone",
    "burger",
    "salad",
    "pastry",
    "dumbbell",
    "bike",
    "book",
    "camera",
    "watch",
    "sunglasses",
    "skincare",
    "candle",
    "lamp",
    "suitcase",
    "guitar",
)


def _sanitize_photo(key: str | None, *, title: str = "") -> str:
    raw = (key or "").strip().lower()
    if raw in KIT_PHOTO_KEYS:
        return raw
    text = f"{raw} {title}".lower()
    for name in KIT_PHOTO_KEYS:
        if name in text:
            return name
    return "shoe"


def _dq(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'").replace("$", "\\$") + "'"


def _opt_str(value: str | None) -> str:
    if value is None or not str(value).strip():
        return "null"
    return _dq(str(value).strip())


def _product_field(name: str, value: str | None) -> str:
    if value is None or not str(value).strip():
        return ""
    return f", {name}: {_opt_str(str(value).strip())}"


def _product_ctor(item: CatalogProduct) -> str:
    photo = _sanitize_photo(item.photo, title=item.title)
    return (
        "    KitProduct("
        f"id: {_dq(item.id)}, title: {_dq(item.title)}"
        f"{_product_field('subtitle', item.subtitle)}"
        f"{_product_field('price', item.price)}"
        f", photo: {_dq(photo)}"
        f"{_product_field('category', item.category)}"
        f"{_product_field('badge', item.badge)}"
        f"{_product_field('emoji', item.emoji)}"
        "),\n"
    )


def _filters(catalog: AppCatalog) -> list[str]:
    labels = ["All"]
    seen = {"all"}
    for item in catalog.products:
        cat = (item.category or "Other").strip() or "Other"
        key = cat.lower()
        if key not in seen:
            seen.add(key)
            labels.append(cat)
    return labels


def write_app_catalog(project: Path, catalog: AppCatalog) -> None:
    """Emit store + browse/detail/profile screens and registry under lib/app/features/app/."""
    app_dir = project / "lib" / "app" / "features" / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    products = "".join(_product_ctor(item) for item in catalog.products)
    hero_photo = _sanitize_photo(catalog.shop_hero_photo, title=catalog.shop_hero_title)
    profile_photo = _sanitize_photo(catalog.profile_photo, title=catalog.profile_title)
    detail_path = catalog.detail_path.strip() or "/item"
    if not detail_path.startswith("/"):
        detail_path = f"/{detail_path}"
    filter_labels = _filters(catalog)

    store = f"""import 'package:flutter/material.dart';

import '../../../core/kit/kit.dart';

class AppStore {{
  AppStore._();
  static final AppStore instance = AppStore._();

  KitProduct? selected;
  int detailQuantity = 1;
  String filter = 'All';
  final search = TextEditingController();
  final favorites = <String>{{}};

  final List<KitProduct> products = [
{products}  ];

  List<KitProduct> visible() {{
    final query = search.text.trim().toLowerCase();
    return [
      for (final item in products)
        if ((filter == 'All' || (item.category ?? '') == filter) &&
            (query.isEmpty ||
                item.title.toLowerCase().contains(query) ||
                (item.subtitle ?? '').toLowerCase().contains(query)))
          KitProduct(
            id: item.id,
            title: item.title,
            subtitle: item.subtitle,
            price: item.price,
            photo: item.photo,
            badge: item.badge,
            category: item.category,
            emoji: item.emoji,
            favorite: favorites.contains(item.id),
          ),
    ];
  }}

  void toggleFavorite(String id) {{
    if (favorites.contains(id)) {{
      favorites.remove(id);
    }} else {{
      favorites.add(id);
    }}
  }}
}}
"""

    filter_literals = ", ".join(_dq(label) for label in filter_labels)
    browse = f"""import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/kit/kit.dart';
import 'app_store.dart';

class BrowseScreen extends StatefulWidget {{
  const BrowseScreen({{super.key}});

  @override
  State<BrowseScreen> createState() => _BrowseScreenState();
}}

class _BrowseScreenState extends State<BrowseScreen> {{
  @override
  Widget build(BuildContext context) {{
    final store = AppStore.instance;
    return RocketScaffold(
      body: KitShopScreen(
        heroTitle: {_dq(catalog.shop_hero_title)},
        heroSubtitle: {_opt_str(catalog.shop_hero_subtitle)},
        heroPhoto: {_dq(hero_photo)},
        heroAction: {_opt_str(catalog.shop_hero_action)},
        search: store.search,
        searchHint: {_opt_str(catalog.search_hint or 'Search')},
        filters: const [{filter_literals}],
        selectedFilter: store.filter,
        onFilter: (value) => setState(() => store.filter = value),
        items: store.visible(),
        sectionTitle: {_dq(catalog.section_title)},
        onTap: (item) {{
          store.selected = store.products.firstWhere((p) => p.id == item.id);
          store.detailQuantity = 1;
          context.go({_dq(detail_path)});
        }},
        onFavorite: (item) => setState(() => store.toggleFavorite(item.id)),
      ),
    );
  }}
}}
"""

    detail = f"""import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/kit/kit.dart';
import 'app_store.dart';

class DetailScreen extends StatefulWidget {{
  const DetailScreen({{super.key}});

  @override
  State<DetailScreen> createState() => _DetailScreenState();
}}

class _DetailScreenState extends State<DetailScreen> {{
  @override
  Widget build(BuildContext context) {{
    final store = AppStore.instance;
    final item = store.selected;
    if (item == null) {{
      return const RocketScaffold(
        body: EmptyState(title: 'Pick an item', body: 'Browse the shop first.', emoji: '🔎'),
      );
    }}
    return RocketScaffold(
      body: KitDetailScreen(
        item: item,
        quantity: store.detailQuantity,
        onQuantity: (value) => setState(() => store.detailQuantity = value),
        primaryLabel: {_dq(catalog.detail_primary_label)},
        onPrimary: () => setState(() => store.toggleFavorite(item.id)),
        secondaryLabel: {_dq(catalog.detail_secondary_label)},
        onSecondary: () => context.go('/browse'),
        notes: [
          if (item.category != null)
            ListRow(title: item.category!, subtitle: item.subtitle ?? '', emoji: item.emoji ?? '✨'),
        ],
      ),
    );
  }}
}}
"""

    profile = f"""import 'package:flutter/material.dart';

import '../../../core/kit/kit.dart';
import 'app_store.dart';

class ProfileScreen extends StatelessWidget {{
  const ProfileScreen({{super.key}});

  @override
  Widget build(BuildContext context) {{
    final store = AppStore.instance;
    return RocketScaffold(
      body: KitProfileScreen(
        title: {_dq(catalog.profile_title)},
        subtitle: {_opt_str(catalog.profile_subtitle)},
        photo: {_dq(profile_photo)},
        stats: [
          StatTile(label: 'Items', value: '${{store.products.length}}', emoji: '📦'),
          StatTile(label: 'Saved', value: '${{store.favorites.length}}', emoji: '❤️'),
        ],
        rows: [
          for (final item in store.products.take(6))
            ListRow(
              title: item.title,
              subtitle: item.price ?? item.subtitle ?? '',
              emoji: item.emoji ?? '•',
            ),
        ],
      ),
    );
  }}
}}
"""

    registry = f"""import 'package:flutter/material.dart';

import 'app/browse_screen.dart';
import 'app/detail_screen.dart';
import 'app/profile_screen.dart';

class FeatureRoute {{
  const FeatureRoute({{
    required this.path,
    required this.label,
    required this.builder,
    this.icon = '•',
    this.tab = false,
  }});

  final String path;
  final String label;
  final WidgetBuilder builder;
  final String icon;
  final bool tab;
}}

List<FeatureRoute> extraFeatureRoutes() {{
  return [
    FeatureRoute(
      path: '/browse',
      label: {_dq(catalog.browse_label)},
      icon: {_dq(catalog.browse_icon)},
      tab: true,
      builder: (context) => const BrowseScreen(),
    ),
    FeatureRoute(
      path: {_dq(detail_path)},
      label: 'Detail',
      icon: '🔎',
      tab: false,
      builder: (context) => const DetailScreen(),
    ),
    FeatureRoute(
      path: '/profile',
      label: {_dq(catalog.profile_label)},
      icon: {_dq(catalog.profile_icon)},
      tab: true,
      builder: (context) => const ProfileScreen(),
    ),
  ];
}}
"""

    (app_dir / "app_store.dart").write_text(store, encoding="utf-8")
    (app_dir / "browse_screen.dart").write_text(browse, encoding="utf-8")
    (app_dir / "detail_screen.dart").write_text(detail, encoding="utf-8")
    (app_dir / "profile_screen.dart").write_text(profile, encoding="utf-8")
    registry_path = project / "lib" / "app" / "features" / "registry.dart"
    registry_path.write_text(registry, encoding="utf-8")
