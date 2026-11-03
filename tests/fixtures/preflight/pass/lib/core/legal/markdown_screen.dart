import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

import '../../app/strings.dart';

class MarkdownLegalScreen extends StatelessWidget {
  const MarkdownLegalScreen({super.key, required this.title, required this.assetPath});

  final String title;
  final String assetPath;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: FutureBuilder<String>(
        future: DefaultAssetBundle.of(context).loadString(assetPath),
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final body = snapshot.data!.replaceAll('{{app_name}}', AppStrings.appName);
          return Markdown(data: body);
        },
      ),
    );
  }
}
