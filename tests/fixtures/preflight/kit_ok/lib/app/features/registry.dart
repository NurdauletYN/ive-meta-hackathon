List<FeatureRoute> extraFeatureRoutes() {
  return [
    FeatureRoute(path: '/browse', label: 'Browse', icon: '🧰', tab: true, builder: (c) => const CatalogScreen()),
  ];
}
