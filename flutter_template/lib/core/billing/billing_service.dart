import 'offering_product.dart';

abstract class BillingService {
  Future<void> purchase(String productId);
  Future<void> restorePurchases();
  Future<List<OfferingProduct>> offerings();
  bool get isDemo;
}
