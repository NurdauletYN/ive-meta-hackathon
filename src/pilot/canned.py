"""Canned FakePilot scripts so the local UI can run offline."""

from __future__ import annotations

from .fake import FakePilot


def _write(path: str, content: str) -> dict:
    return {"op": "write", "path": path, "content": content, "find": None, "replace": None}


def _tokens(primary: str, *, radius: float, typography: str) -> dict:
    return {
        "colors": {
            "primary": primary,
            "on_primary": "#FFFFFF",
            "surface": "#F5F7FA",
            "on_surface": "#1A1A1A",
        },
        "contrast_pairs": [
            {"name": "body", "foreground": "#1A1A1A", "background": "#F5F7FA"},
            {"name": "cta", "foreground": "#FFFFFF", "background": primary},
        ],
        "corner_radius": radius,
        "typography": typography,
    }


def _direction(name: str, primary: str, *, radius: float, typography: str) -> dict:
    return {
        "name": name,
        "rationale": f"{name} direction for the gallery.",
        "tokens": _tokens(primary, radius=radius, typography=typography),
    }


DIRECTIONS = {
    "directions": [
        _direction("Harbor", "#1565C0", radius=8, typography="default"),
        _direction("Ember", "#C62828", radius=16, typography="compact"),
        _direction("Grove", "#2E7D32", radius=24, typography="expressive"),
    ]
}

APP_SPEC = {
    "app_name": "Tool Library",
    "bundle_id": "com.example.toollib",
    "onboarding": [
        {"title": "Share", "body": "List tools neighbors can borrow."},
        {"title": "Borrow", "body": "Request a tool and pick it up."},
        {"title": "Return", "body": "Mark it back when you are done."},
    ],
    "paywall_title": "Plus",
    "paywall_body": "Unlimited borrows for your block.",
    "paywall_cta": "Subscribe",
    "screens": [
        {"id": "catalog", "purpose": "browse tools", "fields": [{"name": "title", "type": "string"}]},
        {"id": "create", "purpose": "list a tool", "fields": [{"name": "title", "type": "string"}]},
        {"id": "profile", "purpose": "borrower summary", "fields": [{"name": "name", "type": "string"}]},
    ],
    "data_models": [{"name": "Tool", "fields": [{"name": "title", "type": "string"}]}],
}

STORE_DART = """class ToolItem {
  ToolItem({required this.emoji, required this.title, required this.subtitle, required this.category, this.listed = true});
  final String emoji;
  final String title;
  final String subtitle;
  final String category;
  bool listed;
}

class CatalogStore {
  CatalogStore._();
  static final CatalogStore instance = CatalogStore._();
  ToolItem? selected;
  final List<ToolItem> items = [
    ToolItem(emoji: '🔨', title: 'Claw hammer', subtitle: '16 oz steel', category: 'Hand'),
    ToolItem(emoji: '🪛', title: 'Screwdriver set', subtitle: 'Phillips and flat', category: 'Hand'),
    ToolItem(emoji: '🔧', title: 'Adjustable wrench', subtitle: '10 inch', category: 'Hand'),
    ToolItem(emoji: '🪚', title: 'Hand saw', subtitle: 'Wood, 20 inch', category: 'Hand'),
    ToolItem(emoji: '📏', title: 'Tape measure', subtitle: '25 ft', category: 'Measure'),
    ToolItem(emoji: '🪜', title: 'Step ladder', subtitle: '6 ft aluminum', category: 'Yard'),
    ToolItem(emoji: '🔌', title: 'Work light', subtitle: 'LED, clamp', category: 'Power'),
    ToolItem(emoji: '🧰', title: 'Toolbox', subtitle: 'Empty, 20 inch', category: 'Hand'),
    ToolItem(emoji: '🪴', title: 'Garden trowel', subtitle: 'Steel blade', category: 'Yard'),
    ToolItem(emoji: '🪵', title: 'Clamps', subtitle: 'Pair of bar clamps', category: 'Hand'),
  ];
}
"""

CATALOG_DART = """import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:rocket_capsule/core/kit/kit.dart';
import 'catalog_store.dart';

class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key});
  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  String filter = 'All';

  @override
  Widget build(BuildContext context) {
    final store = CatalogStore.instance;
    final labels = ['All', 'Hand', 'Yard', 'Power', 'Measure'];
    final shown = [for (final item in store.items) if (filter == 'All' || item.category == filter) item];
    KitProduct product(ToolItem item) => KitProduct(
          id: item.title,
          title: item.title,
          subtitle: item.subtitle,
          photo: 'tool',
          category: item.category,
          badge: item.category,
        );
    return RocketScaffold(
      body: KitShopScreen(
        heroTitle: 'Block library',
        heroSubtitle: 'Borrow a tool, return it this week.',
        heroPhoto: 'tool',
        heroAction: 'Browse all',
        filters: labels,
        selectedFilter: filter,
        onFilter: (value) => setState(() => filter = value),
        items: [for (final item in shown) product(item)],
        sectionTitle: 'Tools',
        onTap: (product) {
          store.selected = store.items.firstWhere((item) => item.title == product.id);
          context.go('/item');
        },
      ),
    );
  }
}
"""

CREATE_DART = """import 'package:flutter/material.dart';
import 'package:rocket_capsule/core/kit/kit.dart';
import 'catalog_store.dart';

class CreateScreen extends StatefulWidget {
  const CreateScreen({super.key});
  @override
  State<CreateScreen> createState() => _CreateScreenState();
}

class _CreateScreenState extends State<CreateScreen> {
  final title = TextEditingController();
  final detail = TextEditingController();
  int days = 3;

  @override
  void dispose() {
    title.dispose();
    detail.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final space = KitTokens.of(context).spacing;
    return RocketScaffold(
      title: 'List a tool',
      body: KitPage(
        children: [
          const HeroHeader(title: 'Share from your shed', subtitle: 'Neighbors will see this today.', emoji: '✏️'),
          SizedBox(height: space.md),
          AppTextField(controller: title, label: 'Tool', hint: 'Impact driver'),
          SizedBox(height: space.md),
          AppTextField(controller: detail, label: 'Notes', hint: 'Battery included'),
          SectionTitle('Loan length'),
          QuantityStepper(value: days, onChanged: (value) => setState(() => days = value), min: 1, max: 14),
          PrimaryButton(
            label: 'Publish',
            onPressed: () {
              final name = title.text.trim();
              if (name.isEmpty) return;
              setState(() {
                CatalogStore.instance.items.insert(0, ToolItem(emoji: '🛠️', title: name, subtitle: detail.text.trim().isEmpty ? '$days day loan' : detail.text.trim(), category: 'Hand'));
                title.clear();
                detail.clear();
              });
            },
          ),
        ],
      ),
    );
  }
}
"""

ITEM_DART = """import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:rocket_capsule/core/kit/kit.dart';
import 'catalog_store.dart';

class ItemScreen extends StatefulWidget {
  const ItemScreen({super.key});
  @override
  State<ItemScreen> createState() => _ItemScreenState();
}

class _ItemScreenState extends State<ItemScreen> {
  int days = 2;

  @override
  Widget build(BuildContext context) {
    final item = CatalogStore.instance.selected;
    if (item == null) {
      return const RocketScaffold(body: EmptyState(title: 'Pick a tool', body: 'Open browse and choose one.', emoji: '🔎'));
    }
    return RocketScaffold(
      body: KitDetailScreen(
        item: KitProduct(id: item.title, title: item.title, subtitle: item.subtitle, photo: 'tool', category: item.category),
        quantity: days,
        onQuantity: (value) => setState(() => days = value),
        primaryLabel: item.listed ? 'Request borrow' : 'Returned',
        onPrimary: () => setState(() => item.listed = !item.listed),
        secondaryLabel: 'Back to browse',
        onSecondary: () => context.go('/browse'),
        notes: [
          ListRow(title: item.category, subtitle: 'Free for $days day${days == 1 ? '' : 's'}', emoji: item.emoji),
        ],
      ),
    );
  }
}
"""

PROFILE_DART = """import 'package:flutter/material.dart';
import 'package:rocket_capsule/core/kit/kit.dart';
import 'catalog_store.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});
  @override
  Widget build(BuildContext context) {
    final store = CatalogStore.instance;
    return RocketScaffold(
      body: KitProfileScreen(
        title: 'Your shelf',
        subtitle: 'What you share on this block.',
        photo: 'tool',
        stats: [
          StatTile(label: 'Listed', value: '${store.items.length}', emoji: '📦'),
          StatTile(label: 'Open', value: '${store.items.where((item) => item.listed).length}', emoji: '✅'),
        ],
        rows: [
          for (final item in store.items.take(6))
            ListRow(title: item.title, subtitle: item.category, emoji: item.emoji),
        ],
      ),
    );
  }
}
"""

REGISTRY_DART = """import 'package:flutter/material.dart';
import 'browse/catalog_screen.dart';
import 'browse/create_screen.dart';
import 'browse/item_screen.dart';
import 'browse/profile_screen.dart';

class FeatureRoute {
  const FeatureRoute({
    required this.path,
    required this.label,
    required this.builder,
    this.icon = '•',
    this.tab = false,
  });

  final String path;
  final String label;
  final WidgetBuilder builder;
  final String icon;
  final bool tab;
}

List<FeatureRoute> extraFeatureRoutes() {
  return [
    FeatureRoute(path: '/browse', label: 'Browse', icon: '🧰', tab: true, builder: (c) => const CatalogScreen()),
    FeatureRoute(path: '/new', label: 'List', icon: '✏️', tab: true, builder: (c) => const CreateScreen()),
    FeatureRoute(path: '/item', label: 'Item', icon: '🔎', tab: false, builder: (c) => const ItemScreen()),
    FeatureRoute(path: '/profile', label: 'You', icon: '👤', tab: true, builder: (c) => const ProfileScreen()),
  ];
}
"""

FILE_OPS = {
    "operations": [
        _write("lib/app/features/browse/catalog_store.dart", STORE_DART),
        _write("lib/app/features/browse/catalog_screen.dart", CATALOG_DART),
        _write("lib/app/features/browse/create_screen.dart", CREATE_DART),
        _write("lib/app/features/browse/item_screen.dart", ITEM_DART),
        _write("lib/app/features/browse/profile_screen.dart", PROFILE_DART),
        _write("lib/app/features/registry.dart", REGISTRY_DART),
    ]
}

BARE_OPS = {
    "operations": [
        _write(
            "lib/main.dart",
            "import 'package:flutter/material.dart';\n\n"
            "void main() {\n"
            "  runApp(const MaterialApp(home: Text('Tool Library')));\n"
            "}\n",
        )
    ]
}


def canned_pilot() -> FakePilot:
    """Fresh queues for one design + one harness build + one bare build."""
    fake = FakePilot(cached_tokens=64)
    fake.enqueue("design", DIRECTIONS)
    fake.enqueue("spec", APP_SPEC, APP_SPEC)
    fake.enqueue("file_ops", FILE_OPS, FILE_OPS, BARE_OPS, FILE_OPS)
    return fake
