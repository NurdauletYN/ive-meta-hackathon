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
    expect(find.text('🔨'), findsOneWidget);
  });

  testWidgets('HeroHeader uses title and emoji', (tester) async {
    await tester.pumpWidget(
      _wrap(const HeroHeader(title: 'Library', subtitle: 'Borrow', emoji: '🧰')),
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
    await tester.tap(find.byIcon(Icons.add_circle_outline));
    await tester.pump();
    expect(find.text('3'), findsOneWidget);
  });

  test('token defaults match the documented scale', () {
    final tokens = KitTokens.fallback();
    expect(tokens.spacing.md, 16);
    expect(tokens.radii.md, 12);
    expect(tokens.typeScale.body, 16);
  });
}
