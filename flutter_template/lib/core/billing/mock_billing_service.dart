import 'billing_service.dart';

class MockBillingService implements BillingService {
  final Set<String> _owned = {};

  @override
  Future<void> purchase(String productId) async {
    _owned.add(productId);
  }

  @override
  Future<void> restorePurchases() async {
    _owned.add('restored');
  }
}
