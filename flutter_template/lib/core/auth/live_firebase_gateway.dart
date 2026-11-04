import 'package:firebase_auth/firebase_auth.dart';

import 'firebase_gateway.dart';

/// Real Firebase Auth. Not used unless config files exist and initializeApp ran.
/// Unverified on a device in this repository.
class LiveFirebaseAuthGateway implements FirebaseAuthGateway {
  LiveFirebaseAuthGateway(this._auth);

  final FirebaseAuth _auth;

  @override
  bool get isSignedIn => _auth.currentUser != null;

  @override
  Future<void> signUp({required String email, required String password}) async {
    await _auth.createUserWithEmailAndPassword(email: email, password: password);
  }

  @override
  Future<void> signIn({required String email, required String password}) async {
    await _auth.signInWithEmailAndPassword(email: email, password: password);
  }

  @override
  Future<void> signOut() => _auth.signOut();

  @override
  Future<void> deleteCurrentUser() async {
    final user = _auth.currentUser;
    if (user == null) {
      return;
    }
    await user.delete();
  }
}
