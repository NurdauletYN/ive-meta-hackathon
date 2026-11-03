import 'package:flutter/material.dart';

import '../../app/strings.dart';
import 'markdown_screen.dart';

class PrivacyScreen extends StatelessWidget {
  const PrivacyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const MarkdownLegalScreen(
      title: AppStrings.privacyLabel,
      assetPath: 'assets/legal/privacy.md',
    );
  }
}
