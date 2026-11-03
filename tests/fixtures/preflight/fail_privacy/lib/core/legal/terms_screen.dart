import 'package:flutter/material.dart';

import '../../app/strings.dart';
import 'markdown_screen.dart';

class TermsScreen extends StatelessWidget {
  const TermsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const MarkdownLegalScreen(
      title: AppStrings.termsLabel,
      assetPath: 'assets/legal/terms.md',
    );
  }
}
