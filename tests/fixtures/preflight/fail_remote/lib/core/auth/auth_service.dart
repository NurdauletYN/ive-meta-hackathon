abstract class AuthService {
  Future<void> signIn({required String email, required String password});
  Future<void> signOut();
  Future<void> deleteAccount();
  bool get isSignedIn;
}
