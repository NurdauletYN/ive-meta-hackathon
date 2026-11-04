import 'dart:io';

const _fileNames = [
  'revenuecat_api_key.txt',
  'lib/revenuecat_key.dart',
];

bool revenueCatKeyFilePresent({String? projectRoot}) {
  return (readRevenueCatKeyFile(projectRoot: projectRoot) ?? '').isNotEmpty;
}

String? readRevenueCatKeyFile({String? projectRoot}) {
  final base = projectRoot ?? Directory.current.path;
  for (final rel in _fileNames) {
    final file = File('$base/$rel');
    if (!file.existsSync()) {
      continue;
    }
    final text = file.readAsStringSync();
    if (rel.endsWith('.dart')) {
      final match = RegExp(
        r"revenueCatPublicApiKey\s*=\s*'([^']+)'",
      ).firstMatch(text);
      final value = match?.group(1)?.trim();
      if (value != null && value.isNotEmpty) {
        return value;
      }
      continue;
    }
    for (final line in text.split('\n')) {
      final value = line.trim();
      if (value.isEmpty || value.startsWith('#')) {
        continue;
      }
      return value;
    }
  }
  return null;
}
