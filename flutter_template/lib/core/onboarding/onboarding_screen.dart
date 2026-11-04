import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({super.key});

  Future<Map<String, String>> _loadSlots() async {
    final raw = await rootBundle.loadString('assets/onboarding/onboarding.json');
    final json = jsonDecode(raw) as Map<String, dynamic>;
    final slots = json['slots'] as Map<String, dynamic>;
    return slots.map((key, value) => MapEntry(key, value as String));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Onboarding')),
      body: FutureBuilder<Map<String, String>>(
        future: _loadSlots(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final slots = snapshot.data!;
          return Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(slots['hero_title'] ?? '', style: Theme.of(context).textTheme.headlineMedium),
                const SizedBox(height: 12),
                Text(slots['hero_body'] ?? ''),
                const Spacer(),
                FilledButton(
                  onPressed: () => context.go('/signup'),
                  child: const Text('Continue'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
