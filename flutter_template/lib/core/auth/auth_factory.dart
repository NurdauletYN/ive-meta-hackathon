import 'auth_service.dart';
import 'firebase_auth_service.dart';
import 'firebase_config.dart';
import 'firebase_gateway.dart';
import 'in_memory_auth_service.dart';

/// Picks Firebase only when user-supplied config files exist. Never calls a network from here.
AuthService createAuthService({
  bool? configPresent,
  FirebaseAuthGateway? gateway,
  String? projectRoot,
}) {
  final present = configPresent ?? firebaseConfigPresent(projectRoot: projectRoot);
  if (present) {
    final gw = gateway;
    if (gw == null) {
      throw StateError(
        'Firebase config is present but no gateway was provided. '
        'Wire a real FirebaseAuthGateway only in a live app with initializeApp.',
      );
    }
    return FirebaseAuthService(gw);
  }
  return InMemoryAuthService();
}
