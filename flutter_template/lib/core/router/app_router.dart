import 'package:go_router/go_router.dart';

import '../auth/auth_service.dart';
import '../auth/in_memory_auth_service.dart';
import '../billing/billing_service.dart';
import '../billing/mock_billing_service.dart';
import '../legal/privacy_screen.dart';
import '../legal/terms_screen.dart';
import '../onboarding/onboarding_screen.dart';
import '../paywall/paywall_screen.dart';
import '../settings/settings_screen.dart';
import '../../app/features/home/home_screen.dart';
import '../../app/features/registry.dart';

class AppRouter {
  AppRouter({AuthService? auth, BillingService? billing})
      : auth = auth ?? InMemoryAuthService(),
        billing = billing ?? MockBillingService();

  final AuthService auth;
  final BillingService billing;

  late final GoRouter router = GoRouter(
    routes: [
      GoRoute(path: '/', builder: (context, state) => const HomeScreen()),
      GoRoute(path: '/onboarding', builder: (context, state) => const OnboardingScreen()),
      GoRoute(
        path: '/settings',
        builder: (context, state) => SettingsScreen(auth: auth, billing: billing),
      ),
      GoRoute(
        path: '/paywall',
        builder: (context, state) => PaywallScreen(billing: billing),
      ),
      GoRoute(path: '/terms', builder: (context, state) => const TermsScreen()),
      GoRoute(path: '/privacy', builder: (context, state) => const PrivacyScreen()),
      ...extraFeatureRoutes().map(
        (feature) => GoRoute(
          path: feature.path,
          builder: (context, state) => feature.builder(context),
        ),
      ),
    ],
  );
}
