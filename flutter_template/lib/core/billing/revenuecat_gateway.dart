import 'offering_product.dart';

/// Narrow Purchases surface so tests can inject a fake. No live calls here.
abstract class RevenueCatGateway {
  Future<void> configure(String publicApiKey);
  Future<List<OfferingProduct>> getOfferings();
  Future<void> purchase(String productId);
  Future<void> restorePurchases();
}
