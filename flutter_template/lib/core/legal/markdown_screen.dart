import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

import '../../app/strings.dart';
import '../kit/kit.dart';

class MarkdownLegalScreen extends StatelessWidget {
  const MarkdownLegalScreen({
    super.key,
    required this.title,
    required this.assetPath,
  });

  final String title;
  final String assetPath;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return RocketScaffold(
      title: title,
      showBottomNav: false,
      body: FutureBuilder<String>(
        future: DefaultAssetBundle.of(context).loadString(assetPath),
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final body = snapshot.data!.replaceAll(
            '{{app_name}}',
            AppStrings.appName,
          );
          return Padding(
            padding: EdgeInsets.fromLTRB(
              tokens.spacing.md,
              0,
              tokens.spacing.md,
              tokens.spacing.lg,
            ),
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: scheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(tokens.radii.lg),
              ),
              child: Markdown(
                data: body,
                padding: EdgeInsets.all(tokens.spacing.md),
              ),
            ),
          );
        },
      ),
    );
  }
}
