import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'app/strings.dart';
import 'app/theme_loader.dart';
import 'core/auth/auth_factory.dart';
import 'core/auth/auth_service.dart';
import 'core/auth/firebase_config.dart';
import 'core/auth/live_firebase_gateway.dart';
import 'core/router/app_router.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final theme = await AppTheme.load();
  final AuthService auth;
  if (firebaseConfigPresent()) {
    await Firebase.initializeApp();
    auth = createAuthService(
      configPresent: true,
      gateway: LiveFirebaseAuthGateway(FirebaseAuth.instance),
    );
  } else {
    auth = createAuthService(configPresent: false);
  }
  final appRouter = AppRouter(auth: auth);
  runApp(RocketCapsuleApp(router: appRouter.router, theme: theme.data));
}

class RocketCapsuleApp extends StatelessWidget {
  const RocketCapsuleApp({super.key, required this.router, required this.theme});

  final GoRouter router;
  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: AppStrings.appName,
      theme: theme,
      routerConfig: router,
    );
  }
}
