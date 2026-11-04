import 'package:purchases_flutter/purchases_flutter.dart';

import 'offering_product.dart';
import 'revenuecat_gateway.dart';

/// Real RevenueCat Purchases. Not used unless a public SDK key file is present.
/// Unverified until a sandbox purchase completes on a real device.
class LiveRevenueCatGateway implements RevenueCatGateway {
  bool _configured = false;

  @override
  Future<void> configure(String publicApiKey) async {
    if (_configured) {
      return;
    }
    await Purchases.configure(PurchasesConfiguration(publicApiKey));
    _configured = true;
  }

  @override
  Future<List<OfferingProduct>> getOfferings() async {
    final offerings = await Purchases.getOfferings();
    final current = offerings.current;
    if (current == null) {
      return const [];
    }
    return [
      for (final package in current.availablePackages)
        OfferingProduct(
          id: package.storeProduct.identifier,
          title: package.storeProduct.title,
          priceLabel: package.storeProduct.priceString,
        ),
    ];
  }

  @override
  Future<void> purchase(String productId) async {
    final offerings = await Purchases.getOfferings();
    Package? match;
    for (final package in offerings.current?.availablePackages ?? const <Package>[]) {
      if (package.storeProduct.identifier == productId || package.identifier == productId) {
        match = package;
        break;
      }
    }
    if (match == null) {
      throw StateError('No RevenueCat package matches the product id.');
    }
    await Purchases.purchase(PurchaseParams.package(match));
  }

  @override
  Future<void> restorePurchases() => Purchases.restorePurchases();
}

RevenueCatGateway? createLiveRevenueCatGateway() => LiveRevenueCatGateway();
