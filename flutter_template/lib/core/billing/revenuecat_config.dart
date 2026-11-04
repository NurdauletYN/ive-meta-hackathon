import 'revenuecat_config_stub.dart'
    if (dart.library.io) 'revenuecat_config_io.dart' as impl;

/// True when the user has supplied a RevenueCat public SDK key file.
/// Web has no dart:io file probe and stays on mock billing unless a test injects true.
bool revenueCatConfigPresent({String? projectRoot, String? publicApiKey}) {
  if ((publicApiKey ?? '').trim().isNotEmpty) {
    return true;
  }
  const fromDefine = String.fromEnvironment('REVENUECAT_API_KEY');
  if (fromDefine.trim().isNotEmpty) {
    return true;
  }
  return impl.revenueCatKeyFilePresent(projectRoot: projectRoot);
}

String? readRevenueCatPublicKey({String? projectRoot}) {
  const fromDefine = String.fromEnvironment('REVENUECAT_API_KEY');
  if (fromDefine.trim().isNotEmpty) {
    return fromDefine.trim();
  }
  return impl.readRevenueCatKeyFile(projectRoot: projectRoot);
}
