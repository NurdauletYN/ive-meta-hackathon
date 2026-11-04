import 'billing_service.dart';
import 'offering_product.dart';
import 'revenuecat_gateway.dart';

class RevenueCatBillingService implements BillingService {
  RevenueCatBillingService(this._gateway, {required String publicApiKey})
      : _publicApiKey = publicApiKey;

  final RevenueCatGateway _gateway;
  final String _publicApiKey;
  Future<void>? _ready;

  Future<void> _ensureConfigured() {
    return _ready ??= _gateway.configure(_publicApiKey);
  }

  @override
  bool get isDemo => false;

  @override
  Future<List<OfferingProduct>> offerings() async {
    await _ensureConfigured();
    return _gateway.getOfferings();
  }

  @override
  Future<void> purchase(String productId) async {
    await _ensureConfigured();
    await _gateway.purchase(productId);
  }

  @override
  Future<void> restorePurchases() async {
    await _ensureConfigured();
    await _gateway.restorePurchases();
  }
}
