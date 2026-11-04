import 'dart:io';

bool firebaseConfigPresent({String? projectRoot}) {
  final base = projectRoot ?? Directory.current.path;
  const names = [
    'ios/Runner/GoogleService-Info.plist',
    'android/app/google-services.json',
    'lib/firebase_options.dart',
  ];
  return names.any((rel) => File('$base/$rel').existsSync());
}
