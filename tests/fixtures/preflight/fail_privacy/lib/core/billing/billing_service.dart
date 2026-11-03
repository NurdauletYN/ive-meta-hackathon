abstract class BillingService {
  Future<void> purchase(String productId);
  Future<void> restorePurchases();
}
