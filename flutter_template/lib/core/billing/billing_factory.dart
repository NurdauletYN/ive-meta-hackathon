import 'billing_service.dart';
import 'mock_billing_service.dart';
import 'revenuecat_billing_service.dart';
import 'revenuecat_config.dart';
import 'revenuecat_gateway.dart';

/// Picks RevenueCat only when a user-supplied public key is present. Never calls a network from here.
BillingService createBillingService({
  bool? configPresent,
  RevenueCatGateway? gateway,
  String? publicApiKey,
  String? projectRoot,
}) {
  final key = (publicApiKey ?? readRevenueCatPublicKey(projectRoot: projectRoot) ?? '').trim();
  final present = configPresent ?? revenueCatConfigPresent(projectRoot: projectRoot, publicApiKey: key);
  if (!present) {
    return MockBillingService();
  }
  final gw = gateway;
  if (gw == null) {
    throw StateError(
      'RevenueCat key is present but no gateway was provided. '
      'Wire a live RevenueCatGateway only in a device/sandbox build.',
    );
  }
  if (key.isEmpty) {
    throw StateError('RevenueCat config is present but the public API key is empty.');
  }
  return RevenueCatBillingService(gw, publicApiKey: key);
}
