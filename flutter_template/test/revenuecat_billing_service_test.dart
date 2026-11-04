import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rocket_capsule/app/strings.dart';
import 'package:rocket_capsule/core/billing/billing_factory.dart';
import 'package:rocket_capsule/core/billing/mock_billing_service.dart';
import 'package:rocket_capsule/core/billing/offering_product.dart';
import 'package:rocket_capsule/core/billing/revenuecat_billing_service.dart';
import 'package:rocket_capsule/core/billing/revenuecat_gateway.dart';
import 'package:rocket_capsule/core/paywall/paywall_screen.dart';

class FakeRevenueCatGateway implements RevenueCatGateway {
  String? configuredKey;
  bool restored = false;
  final List<String> purchased = <String>[];
  List<OfferingProduct> packages = const [
    OfferingProduct(id: 'rocket_plus_monthly', title: 'Plus monthly', priceLabel: r'$4.99 / month'),
  ];

  @override
  Future<void> configure(String publicApiKey) async {
    configuredKey = publicApiKey;
  }

  @override
  Future<List<OfferingProduct>> getOfferings() async => packages;

  @override
  Future<void> purchase(String productId) async {
    purchased.add(productId);
  }

  @override
  Future<void> restorePurchases() async {
    restored = true;
  }
}

void main() {
  test('falls back to mock billing demo mode when no key is supplied', () {
    final billing = createBillingService(configPresent: false);
    expect(billing, isA<MockBillingService>());
    expect(billing.isDemo, isTrue);
  });

  test('uses RevenueCatBillingService with a fake gateway and no live calls', () async {
    final fake = FakeRevenueCatGateway();
    final billing = createBillingService(
      configPresent: true,
      publicApiKey: 'test_public_key_not_live',
      gateway: fake,
    );
    expect(billing, isA<RevenueCatBillingService>());
    expect(billing.isDemo, isFalse);
    final items = await billing.offerings();
    expect(fake.configuredKey, 'test_public_key_not_live');
    expect(items, isNotEmpty);
    expect(items.first.id, 'rocket_plus_monthly');
    await billing.purchase(items.first.id);
    expect(fake.purchased, ['rocket_plus_monthly']);
    await billing.restorePurchases();
    expect(fake.restored, isTrue);
  });

  testWidgets('paywall renders offerings and restore in demo mode', (tester) async {
    final billing = MockBillingService();
    await tester.pumpWidget(MaterialApp(home: PaywallScreen(billing: billing)));
    await tester.pumpAndSettle();
    expect(find.text(AppStrings.subscribeLabel), findsOneWidget);
    expect(find.text(AppStrings.restoreLabel), findsOneWidget);
    expect(find.textContaining('Plus monthly'), findsOneWidget);
    await tester.tap(find.text(AppStrings.restoreLabel));
    await tester.pumpAndSettle();
  });
}
