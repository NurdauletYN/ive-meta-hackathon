import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rocket_capsule/core/kit/kit.dart';
import 'package:rocket_capsule/core/router/app_router.dart';

const tourPaths = [
  '/onboarding',
  '/signup',
  '/home',
  '/paywall',
  '/settings',
  '/privacy',
  '/terms',
];

void main() {
  testWidgets('router table includes the preview-tour hash routes', (tester) async {
    final router = AppRouter().router;
    await tester.pumpWidget(
      MaterialApp.router(
        routerConfig: router,
        theme: ThemeData(extensions: [KitTokens.fallback()]),
      ),
    );
    expect(router.routeInformationProvider.value.uri.path, '/onboarding');
    for (final path in tourPaths) {
      router.go(path);
      await tester.pump();
      expect(router.routeInformationProvider.value.uri.path, path);
    }
  });
}
