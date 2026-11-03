import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'app/strings.dart';
import 'app/theme_loader.dart';
import 'core/router/app_router.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final theme = await AppTheme.load();
  final appRouter = AppRouter();
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
