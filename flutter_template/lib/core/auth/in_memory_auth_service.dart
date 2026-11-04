import 'auth_service.dart';

class InMemoryAuthService implements AuthService {
  String? _email;
  final Map<String, Object?> userData = <String, Object?>{};

  @override
  bool get isSignedIn => _email != null;

  @override
  Future<void> signIn({required String email, required String password}) async {
    if (email.isEmpty || password.isEmpty) {
      throw ArgumentError('email and password required');
    }
    _email = email;
  }

  @override
  Future<void> signOut() async {
    _email = null;
  }

  @override
  Future<void> deleteAccount() async {
    _email = null;
    userData.clear();
  }
}
