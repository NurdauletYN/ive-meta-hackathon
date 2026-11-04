import 'package:flutter_test/flutter_test.dart';
import 'package:rocket_capsule/core/auth/in_memory_auth_service.dart';

void main() {
  test('deleteAccount clears in-memory data for that user', () async {
    final auth = InMemoryAuthService();
    await auth.signIn(email: 'user@example.com', password: 'secret');
    auth.userData['notes'] = ['keep'];
    await auth.deleteAccount();
    expect(auth.isSignedIn, isFalse);
    expect(auth.userData, isEmpty);
  });
}
