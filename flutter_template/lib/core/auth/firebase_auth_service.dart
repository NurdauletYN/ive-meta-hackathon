import 'auth_service.dart';
import 'firebase_gateway.dart';

class FirebaseAuthService implements AuthService {
  FirebaseAuthService(this._gateway);

  final FirebaseAuthGateway _gateway;

  @override
  bool get isDemo => false;

  @override
  bool get isSignedIn => _gateway.isSignedIn;

  @override
  Future<void> signUp({required String email, required String password}) =>
      _gateway.signUp(email: email, password: password);

  @override
  Future<void> signIn({required String email, required String password}) =>
      _gateway.signIn(email: email, password: password);

  @override
  Future<void> signOut() => _gateway.signOut();

  @override
  Future<void> deleteAccount() => _gateway.deleteCurrentUser();
}
