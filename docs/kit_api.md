# Kit API

Import `package:rocket_capsule/core/kit/kit.dart`. Protected: do not edit `lib/core/kit`. All sizes, colors, radii, spacing, and type come from tokens (`KitTokens.of(context)` + `ColorScheme`). No raw hex, no magic padding.

**Tabs:** `FeatureRoute(path, label, builder, icon: '🔧', tab: true)`. First `extraFeatureRoutes()` entry is home at `/` and `/home`. Up to 4 tabs feed `RocketScaffold` bottom navigation.

Widgets:
- `RocketScaffold({title, body, actions, floatingActionButton, showBottomNav})`
- `HeroHeader({title, subtitle, emoji, icon})` — token gradient
- `SectionTitle(text)`
- `ItemCard({emoji, icon, title, subtitle, trailing, onTap})` — tinted circle leading
- `ChipRow({labels, selected, onSelected})`
- `KitBadge({label})` / `PriceTag({text})`
- `StatTile({label, value, emoji})`
- `EmptyState({title, body, emoji})`
- `PrimaryButton({label, onPressed})` / `SecondaryButton({label, onPressed})`
- `AppTextField({controller, label, hint, obscureText})`
- `QuantityStepper({value, onChanged, min, max})`
- `showKitFormSheet(context, title: '…', child: …)`

Example (browse + in-memory list). Use kit widgets only for layout; seed 8–12 emoji items; add a detail/create screen and a profile/summary screen the same way.

```dart
RocketScaffold(
  title: 'Library',
  body: ListView(children: [
    HeroHeader(title: 'Tools', subtitle: 'Borrow from the block', emoji: '🔧'),
    ChipRow(labels: const ['All', 'Hand'], selected: 'All', onSelected: (_) {}),
    ItemCard(emoji: '🔨', title: 'Hammer', subtitle: '16 oz', onTap: () {}),
  ]),
)
```
