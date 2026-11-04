# Kit API

Import `package:rocket_capsule/core/kit/kit.dart`. Protected: do not edit `lib/core/kit`. Colors and sizes come from the theme and `KitTokens.of(context)`; never hardcode them. Never use ListTile, CircleAvatar, FilterChip, Card, AppBar, or a raw Scaffold: the kit has a widget for each. The theme may be dark: never assume a white background.

**Tabs:** `FeatureRoute(path, label, builder, icon: '🔧', tab: true)`. First extra route is home. Keep `final bool tab` and `final String icon`.

**Every screen** is `RocketScaffold(title:, body: KitPage(children: [...]))`. Open with one `HeroHeader` (add `photo:` and `actionLabel:` on the home screen), then `SectionHeader` blocks. Stack at least 3 different kit widgets per screen.

| Widget | Use |
|---|---|
| `HeroHeader(title, subtitle, emoji/icon/photo, actionLabel, onAction)` | gradient banner, the first child |
| `FeaturedRow(children: [FeaturedCard(title, subtitle, photo, badge, price, onTap)])` | horizontal carousel of big photo cards |
| `SectionHeader(title, actionLabel, onAction)` | heading with "See all" |
| `ProductGrid(children: [ProductCard(title, subtitle, price, photo, badge, favorite, onFavorite, onTap)])` | 2-column catalog |
| `ItemCard(title, subtitle, price, photo/emoji/icon, trailing, onTap)` | one photo row |
| `ChipRow(labels, selected, onSelected)` / `SegmentedTabs(labels, selected, onSelected)` | filters / 2-4 way switch |
| `ListSection(title, children: [ListRow(title, subtitle, emoji/icon, trailing, onTap, destructive)])` | settings, details, menus (use instead of ListTile) |
| `StatRow(children: [StatTile(label, value, emoji)])` / `ProgressRing(value 0..1, label, caption)` | numbers, goals |
| `AppTextField(controller, label, hint, isSearch)` | inputs |
| `PrimaryButton(label, onPressed)` / `SecondaryButton` | pill buttons |
| `QuantityStepper`, `CartBar`, `KitBadge`, `PriceTag`, `EmptyState`, `showKitFormSheet` | small pieces |

**Photos:** `photo:` takes `shoe jacket hoodie shorts cleat coffee tool plant bag headphone burger salad pastry dumbbell bike book camera watch sunglasses skincare candle lamp suitcase guitar`; with no `photo:` it matches words in the title. Pick the closest key. No network images. Money goes in `price:`.

Catalog home:

```dart
RocketScaffold(
  title: 'Shop',
  body: KitPage(children: [
    HeroHeader(title: 'New season', subtitle: 'Fresh drops for the track.', photo: 'shoe', actionLabel: 'Shop now', onAction: () {}),
    SectionHeader('Featured', actionLabel: 'See all'),
    FeaturedRow(children: [
      FeaturedCard(photo: 'jacket', title: 'Track jacket', subtitle: 'Lightweight', badge: 'New', price: '\$70', onTap: () {}),
      FeaturedCard(photo: 'hoodie', title: 'Heavy hoodie', subtitle: 'Warm', price: '\$85', onTap: () {}),
    ]),
    AppTextField(controller: search, isSearch: true),
    ChipRow(labels: const ['All', 'Running', 'Soccer'], selected: 'All', onSelected: (_) {}),
    ProductGrid(children: [
      ProductCard(photo: 'shoe', title: 'Ultraboost', subtitle: 'Running', price: '\$190', favorite: false, onFavorite: () {}, onTap: () {}),
      ProductCard(photo: 'cleat', title: 'Pro cleats', subtitle: 'Soccer', price: '\$120', badge: 'Sale', onTap: () {}),
    ]),
  ]),
)
```

Tracker or profile screen:

```dart
KitPage(children: [
  HeroHeader(title: 'Today', subtitle: '3 of 5 done', emoji: '🔥'),
  Center(child: ProgressRing(value: 0.6, caption: 'of goal')),
  StatRow(children: [StatTile(label: 'Streak', value: '12', emoji: '🔥'), StatTile(label: 'Best', value: '21', emoji: '🏆')]),
  SegmentedTabs(labels: const ['Day', 'Week'], selected: 'Day', onSelected: (_) {}),
  ListSection(title: 'Habits', children: [
    ListRow(title: 'Morning run', subtitle: '5 km', emoji: '🏃', trailing: Switch(value: true, onChanged: (_) {})),
    ListRow(title: 'Read', subtitle: '20 pages', emoji: '📖', onTap: () {}),
  ]),
])
```
