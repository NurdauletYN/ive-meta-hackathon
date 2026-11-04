import 'package:flutter_test/flutter_test.dart';
import 'package:rocket_capsule/core/auth/auth_factory.dart';
import 'package:rocket_capsule/core/auth/firebase_auth_service.dart';
import 'package:rocket_capsule/core/auth/firebase_gateway.dart';
import 'package:rocket_capsule/core/auth/in_memory_auth_service.dart';

class FakeFirebaseAuthGateway implements FirebaseAuthGateway {
  String? email;
  bool deleted = false;

  @override
  bool get isSignedIn => email != null;

  @override
  Future<void> signUp({required String email, required String password}) async {
    this.email = email;
  }

  @override
  Future<void> signIn({required String email, required String password}) async {
    this.email = email;
  }

  @override
  Future<void> signOut() async {
    email = null;
  }

  @override
  Future<void> deleteCurrentUser() async {
    deleted = true;
    email = null;
  }
}

void main() {
  test('falls back to in-memory demo auth when config is missing', () {
    final auth = createAuthService(configPresent: false);
    expect(auth, isA<InMemoryAuthService>());
    expect(auth.isDemo, isTrue);
  });

  test('uses FirebaseAuthService when config is present (fake gateway, no live calls)', () async {
    final fake = FakeFirebaseAuthGateway();
    final auth = createAuthService(configPresent: true, gateway: fake);
    expect(auth, isA<FirebaseAuthService>());
    expect(auth.isDemo, isFalse);
    await auth.signUp(email: 'a@b.c', password: 'secret');
    expect(auth.isSignedIn, isTrue);
    await auth.deleteAccount();
    expect(fake.deleted, isTrue);
    expect(auth.isSignedIn, isFalse);
  });
}
