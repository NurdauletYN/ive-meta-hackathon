/// Narrow Firebase Auth surface so tests can inject a fake. No live calls here.
abstract class FirebaseAuthGateway {
  Future<void> signUp({required String email, required String password});
  Future<void> signIn({required String email, required String password});
  Future<void> signOut();
  Future<void> deleteCurrentUser();
  bool get isSignedIn;
}
