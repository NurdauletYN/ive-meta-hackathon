import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rocket_capsule/core/kit/kit.dart';

Widget _wrap(Widget child) {
  return MaterialApp(
    theme: ThemeData(extensions: [KitTokens.fallback()]),
    home: Scaffold(body: child),
  );
}

void main() {
  testWidgets('ItemCard shows emoji, title and subtitle', (tester) async {
    await tester.pumpWidget(
      _wrap(const ItemCard(emoji: '🔨', title: 'Hammer', subtitle: '16 oz')),
    );
    expect(find.text('Hammer'), findsOneWidget);
    expect(find.text('16 oz'), findsOneWidget);
    expect(find.byType(Image), findsOneWidget);
  });

  testWidgets('ItemCard shows a price', (tester) async {
    await tester.pumpWidget(
      _wrap(const ItemCard(emoji: '👟', title: 'Runner', price: '\$89')),
    );
    expect(find.text('\$89'), findsOneWidget);
  });

  testWidgets('ProductCard shows photo layout copy', (tester) async {
    await tester.pumpWidget(
      _wrap(
        const SizedBox(
          width: 180,
          height: 280,
          child: ProductCard(
            photo: 'shoe',
            title: 'Ultraboost',
            subtitle: 'Running',
            price: '\$190',
          ),
        ),
      ),
    );
    expect(find.text('Ultraboost'), findsOneWidget);
    expect(find.text('\$190'), findsOneWidget);
  });

  testWidgets('ChipRow has no checkmark', (tester) async {
    await tester.pumpWidget(
      _wrap(
        ChipRow(
          labels: const ['All', 'Gym'],
          selected: 'All',
          onSelected: (_) {},
        ),
      ),
    );
    expect(find.text('All'), findsOneWidget);
    expect(find.byIcon(Icons.check), findsNothing);
  });

  testWidgets('HeroHeader uses title and emoji', (tester) async {
    await tester.pumpWidget(
      _wrap(
        const HeroHeader(title: 'Library', subtitle: 'Borrow', emoji: '🧰'),
      ),
    );
    expect(find.text('Library'), findsOneWidget);
    expect(find.text('Borrow'), findsOneWidget);
    expect(find.text('🧰'), findsOneWidget);
  });

  testWidgets('QuantityStepper changes value', (tester) async {
    var value = 2;
    await tester.pumpWidget(
      _wrap(
        StatefulBuilder(
          builder: (context, setState) {
            return QuantityStepper(
              value: value,
              onChanged: (next) => setState(() => value = next),
            );
          },
        ),
      ),
    );
    expect(find.text('2'), findsOneWidget);
    await tester.tap(find.byIcon(Icons.add));
    await tester.pump();
    expect(find.text('3'), findsOneWidget);
  });

  test('KitPhoto maps titles to local assets', () {
    expect(KitPhoto.resolve(title: 'Ultraboost shoes'), KitPhoto.shoe);
    expect(KitPhoto.resolve(photo: 'jacket'), KitPhoto.jacket);
    expect(KitPhoto.resolve(title: 'Claw hammer'), KitPhoto.tool);
  });

  testWidgets('ListSection groups ListRows and taps', (tester) async {
    var tapped = false;
    await tester.pumpWidget(
      _wrap(
        ListSection(
          title: 'Account',
          children: [
            ListRow(title: 'Privacy', emoji: '🔒', onTap: () => tapped = true),
            const ListRow(title: 'Delete', emoji: '🗑️', destructive: true),
          ],
        ),
      ),
    );
    expect(find.text('ACCOUNT'), findsOneWidget);
    await tester.tap(find.text('Privacy'));
    expect(tapped, isTrue);
  });

  testWidgets('SegmentedTabs reports the tapped label', (tester) async {
    var picked = 'Day';
    await tester.pumpWidget(
      _wrap(
        StatefulBuilder(
          builder: (context, setState) => SegmentedTabs(
            labels: const ['Day', 'Week'],
            selected: picked,
            onSelected: (value) => setState(() => picked = value),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Week'));
    await tester.pumpAndSettle();
    expect(picked, 'Week');
  });

  testWidgets('ProgressRing, StatRow and SectionHeader render', (tester) async {
    await tester.pumpWidget(
      _wrap(
        ListView(
          children: [
            const SectionHeader('Today', actionLabel: 'See all'),
            const ProgressRing(value: 0.6, caption: 'of goal'),
            const StatRow(
              children: [
                StatTile(label: 'Streak', value: '12'),
                StatTile(label: 'Best', value: '21'),
              ],
            ),
          ],
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Today'), findsOneWidget);
    expect(find.text('60%'), findsOneWidget);
    expect(find.text('Streak'), findsOneWidget);
  });

  testWidgets('FeaturedRow shows FeaturedCard copy and badge', (tester) async {
    await tester.pumpWidget(
      _wrap(
        const FeaturedRow(
          children: [
            FeaturedCard(
              photo: 'jacket',
              title: 'Track jacket',
              subtitle: 'Light',
              badge: 'New',
              price: '\$70',
            ),
          ],
        ),
      ),
    );
    expect(find.text('Track jacket'), findsOneWidget);
    expect(find.text('New'), findsOneWidget);
    expect(find.text('\$70'), findsOneWidget);
  });

  testWidgets('ProductCard favorite toggles icon and calls back', (
    tester,
  ) async {
    var taps = 0;
    await tester.pumpWidget(
      _wrap(
        SizedBox(
          width: 180,
          height: 260,
          child: ProductCard(
            title: 'Cap',
            favorite: false,
            onFavorite: () => taps++,
          ),
        ),
      ),
    );
    await tester.tap(find.byIcon(Icons.favorite_border));
    expect(taps, 1);
  });

  test('every KitPhoto name has an asset path and resolves', () {
    for (final name in KitPhoto.names) {
      expect(KitPhoto.resolve(photo: name), KitPhoto.path(name));
    }
    expect(KitPhoto.resolve(title: 'Cold brew latte'), KitPhoto.coffee);
    expect(KitPhoto.resolve(title: 'City bicycle'), KitPhoto.path('bike'));
  });

  testWidgets('KitShopScreen lays out hero, featured, grid from products', (
    tester,
  ) async {
    await tester.pumpWidget(
      _wrap(
        SizedBox(
          width: 400,
          height: 800,
          child: KitShopScreen(
            heroTitle: 'Drops',
            heroPhoto: 'shoe',
            items: const [
              KitProduct(
                id: '1',
                title: 'Ultraboost',
                subtitle: 'Run',
                price: '\$190',
                photo: 'shoe',
              ),
              KitProduct(
                id: '2',
                title: 'Cleats',
                price: '\$120',
                photo: 'cleat',
              ),
            ],
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Drops'), findsOneWidget);
    expect(find.text('Ultraboost'), findsWidgets);
    expect(find.byType(HeroHeader), findsOneWidget);
    expect(find.byType(FeaturedRow), findsOneWidget);
    expect(find.byType(ProductGrid), findsOneWidget);
  });

  testWidgets('KitAuthScreen shows fields without an AppBar', (tester) async {
    await tester.pumpWidget(
      _wrap(
        KitAuthScreen(
          title: 'Create your account',
          subtitle: 'Email and password',
          email: TextEditingController(),
          password: TextEditingController(),
          primaryLabel: 'Create account',
          onPrimary: () {},
          switchLabel: 'Sign in',
          onSwitch: () {},
        ),
      ),
    );
    expect(find.text('Create your account'), findsOneWidget);
    expect(find.byType(AppBar), findsNothing);
  });

  test('token defaults match the documented scale', () {
    final tokens = KitTokens.fallback();
    expect(tokens.spacing.md, 16);
    expect(tokens.radii.md, 12);
    expect(tokens.typeScale.body, 16);
  });
}
