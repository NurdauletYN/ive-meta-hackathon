# Kit API

Import `package:rocket_capsule/core/kit/kit.dart`. Protected: do not edit `lib/core/kit`. Colors and sizes come from the theme; never hardcode them. Never use ListTile, CircleAvatar, FilterChip, Card, AppBar, NavigationBar, or a raw Scaffold.

v0 and Lovable do not invent page chrome. They fill design-system **screens** with data. Do the same: pass `KitProduct`s into `KitShopScreen` / `KitDetailScreen` / `KitProfileScreen`. Do not place ProductGrid, ChipRow, or HeroHeader yourself on shop/detail/profile. `RocketScaffold` has no AppBar; omit `title:` on those screens.

**Tabs:** `FeatureRoute(path, label, builder, icon: '🔧', tab: true)`. First extra route is home. Keep `final bool tab` and `final String icon`. Navigate with `context.go`, never `Navigator.push`.

**Photos:** `photo:` takes `shoe jacket hoodie shorts cleat coffee tool plant bag headphone burger salad pastry dumbbell bike book camera watch sunglasses skincare candle lamp suitcase guitar`. Money goes in `price:`. No network images.

Shop (write this, not a custom layout):

```dart
RocketScaffold(
  body: KitShopScreen(
    heroTitle: 'New season',
    heroSubtitle: 'Fresh drops',
    heroPhoto: 'shoe',
    heroAction: 'Shop now',
    search: search,
    filters: const ['All', 'Running', 'Soccer'],
    selectedFilter: 'All',
    onFilter: (value) {},
    items: const [
      KitProduct(id: '1', title: 'Ultraboost', subtitle: 'Running', price: '\$190', photo: 'shoe', favorite: false),
      KitProduct(id: '2', title: 'Pro cleats', subtitle: 'Soccer', price: '\$120', photo: 'cleat', badge: 'Sale'),
    ],
    onTap: (item) {},
    onFavorite: (item) {},
  ),
)
```

Detail and profile:

```dart
RocketScaffold(body: KitDetailScreen(
  item: product,
  quantity: 1,
  onQuantity: (value) {},
  primaryLabel: 'Add to bag',
  onPrimary: () {},
  notes: [ListRow(title: 'Shipping', subtitle: '2 days', emoji: '🚚')],
))

RocketScaffold(body: KitProfileScreen(
  title: 'You',
  subtitle: 'Member',
  photo: 'watch',
  stats: [StatTile(label: 'Orders', value: '3', emoji: '📦')],
  rows: [ListRow(title: 'Favorites', emoji: '❤️', onTap: () {})],
))
```

Forms (create/list) may use `KitPage` + `HeroHeader` + `AppTextField` + `PrimaryButton`. Auth, paywall, settings, onboarding already exist in `lib/core`.
