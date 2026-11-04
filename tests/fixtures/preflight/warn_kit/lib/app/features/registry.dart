List<FeatureRoute> extraFeatureRoutes() {
  return [FeatureRoute(path: '/notes', label: 'Notes', builder: (c) => const NotesScreen())];
}
