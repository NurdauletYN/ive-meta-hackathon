class CatalogScreen extends StatefulWidget {
  const CatalogScreen();
  State createState() => _S();
}
class _S extends State {
  Widget build(c) {
    return RocketScaffold(
      title: 'Browse',
      body: ListView(children: const [
        HeroHeader(title: 'Tools', emoji: '🧰'),
        ItemCard(emoji: '🔨', title: 'Hammer', subtitle: '16 oz'),
        PrimaryButton(label: 'Add'),
        ChipRow(labels: ['All'], selected: 'All', onSelected: null),
      ]),
    );
  }
}
