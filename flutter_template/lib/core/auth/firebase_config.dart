import 'firebase_config_stub.dart'
    if (dart.library.io) 'firebase_config_io.dart' as impl;

/// True when the user has supplied Firebase config files next to the project.
/// Web has no dart:io file probe and stays demo unless a test injects true.
bool firebaseConfigPresent({String? projectRoot}) =>
    impl.firebaseConfigPresent(projectRoot: projectRoot);
