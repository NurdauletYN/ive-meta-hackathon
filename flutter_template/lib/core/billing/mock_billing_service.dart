import 'billing_service.dart';
import 'offering_product.dart';

class MockBillingService implements BillingService {
  final Set<String> _owned = {};

  @override
  bool get isDemo => true;

  @override
  Future<List<OfferingProduct>> offerings() async {
    return const [
      OfferingProduct(
        id: 'rocket_plus_monthly',
        title: 'Plus monthly',
        priceLabel: r'$4.99 / month',
      ),
    ];
  }

  @override
  Future<void> purchase(String productId) async {
    _owned.add(productId);
  }

  @override
  Future<void> restorePurchases() async {
    _owned.add('restored');
  }
}
