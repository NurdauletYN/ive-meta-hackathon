import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../strings.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.homeTitle)),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(AppStrings.appName, style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => context.push('/paywall'),
              child: const Text(AppStrings.paywallTitle),
            ),
            TextButton(
              onPressed: () => context.push('/settings'),
              child: const Text(AppStrings.settingsTitle),
            ),
          ],
        ),
      ),
    );
  }
}
