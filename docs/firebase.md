# Firebase auth adapter (unverified)

`FirebaseAuthService` implements the capsule `AuthService` (sign up, sign in, sign out, `deleteAccount` via the real user delete). It is selected at startup **only** when user-supplied config files exist next to the Flutter project:

- `ios/Runner/GoogleService-Info.plist`
- `android/app/google-services.json`
- `lib/firebase_options.dart`

Those filenames are gitignored. Do not commit them. The harness never passes them to a Pilot.

If none of those files are present, the app uses `InMemoryAuthService` and Settings shows a **demo mode** label. That fallback is what `harness gate` exercises.

## What you must supply

1. A Firebase project with Email/Password auth enabled.
2. The iOS and/or Android config files from the Firebase console, placed at the paths above.
3. Optional: `flutterfire configure` output as `lib/firebase_options.dart` (still gitignored).
4. A live `FirebaseAuthGateway` wired in the iOS/Android runner after `Firebase.initializeApp`. This repository’s tests inject a **fake** gateway and make **no live calls**.

## Unverified

This adapter is **unverified** until it is run with a real Firebase project on a real device. Offline tests do not prove Apple or Google auth, token refresh, or account deletion on Firebase servers.
