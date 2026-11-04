/// Local product photos (generated with Muse Image, bundled as assets).
/// Pass a key (`photo: 'shoe'`) or let `resolve` match words in the title.
class KitPhoto {
  KitPhoto._();

  static const prefix = 'lib/core/kit/photos/';

  static const List<String> names = [
    'shoe',
    'jacket',
    'hoodie',
    'shorts',
    'cleat',
    'coffee',
    'tool',
    'plant',
    'bag',
    'headphone',
    'burger',
    'salad',
    'pastry',
    'dumbbell',
    'bike',
    'book',
    'camera',
    'watch',
    'sunglasses',
    'skincare',
    'candle',
    'lamp',
    'suitcase',
    'guitar',
  ];

  static String path(String name) => '$prefix$name.jpg';

  static const shoe = '${prefix}shoe.jpg';
  static const jacket = '${prefix}jacket.jpg';
  static const hoodie = '${prefix}hoodie.jpg';
  static const shorts = '${prefix}shorts.jpg';
  static const cleat = '${prefix}cleat.jpg';
  static const coffee = '${prefix}coffee.jpg';
  static const tool = '${prefix}tool.jpg';
  static const plant = '${prefix}plant.jpg';
  static const bag = '${prefix}bag.jpg';
  static const headphone = '${prefix}headphone.jpg';

  static List<String> get all => [for (final n in names) path(n)];

  static const Map<String, String> _words = {
    'sneaker': 'shoe',
    'boost': 'shoe',
    'runner': 'shoe',
    'trainer': 'shoe',
    'adidas': 'shoe',
    'nike': 'shoe',
    'footwear': 'shoe',
    'coat': 'jacket',
    'windbreaker': 'jacket',
    'sweat': 'hoodie',
    'short': 'shorts',
    'soccer': 'cleat',
    'football': 'cleat',
    'boot': 'cleat',
    'mug': 'coffee',
    'cafe': 'coffee',
    'latte': 'coffee',
    'espresso': 'coffee',
    'hammer': 'tool',
    'wrench': 'tool',
    'saw': 'tool',
    'drill': 'tool',
    'hardware': 'tool',
    'garden': 'plant',
    'trowel': 'plant',
    'flower': 'plant',
    'leaf': 'plant',
    'pack': 'bag',
    'tote': 'bag',
    'purse': 'bag',
    'audio': 'headphone',
    'ear': 'headphone',
    'speaker': 'headphone',
    'music': 'headphone',
    'cheese': 'burger',
    'fries': 'burger',
    'pizza': 'burger',
    'meal': 'burger',
    'food': 'burger',
    'lunch': 'burger',
    'bowl': 'salad',
    'vegan': 'salad',
    'fruit': 'salad',
    'healthy': 'salad',
    'croissant': 'pastry',
    'bread': 'pastry',
    'cake': 'pastry',
    'bakery': 'pastry',
    'dessert': 'pastry',
    'weight': 'dumbbell',
    'gym': 'dumbbell',
    'strength': 'dumbbell',
    'workout': 'dumbbell',
    'fitness': 'dumbbell',
    'cycle': 'bike',
    'bicycle': 'bike',
    'ride': 'bike',
    'novel': 'book',
    'read': 'book',
    'library': 'book',
    'lens': 'camera',
    'photo': 'camera',
    'clock': 'watch',
    'time': 'watch',
    'glasses': 'sunglasses',
    'shades': 'sunglasses',
    'serum': 'skincare',
    'beauty': 'skincare',
    'cream': 'skincare',
    'cosmetic': 'skincare',
    'wax': 'candle',
    'scent': 'candle',
    'home': 'lamp',
    'light': 'lamp',
    'decor': 'lamp',
    'travel': 'suitcase',
    'luggage': 'suitcase',
    'trip': 'suitcase',
    'flight': 'suitcase',
    'ukulele': 'guitar',
    'instrument': 'guitar',
  };

  static String resolve({String? photo, String title = ''}) {
    final explicit = (photo ?? '').trim().toLowerCase();
    if (explicit.isNotEmpty) {
      if (explicit.startsWith(prefix)) return explicit;
      if (names.contains(explicit)) return path(explicit);
      final mapped = _words[explicit];
      if (mapped != null) return path(mapped);
    }
    final text = title.toLowerCase();
    for (final name in names) {
      if (text.contains(name)) return path(name);
    }
    for (final entry in _words.entries) {
      if (text.contains(entry.key)) return path(entry.value);
    }
    if (title.isEmpty) return shoe;
    return path(names[title.hashCode.abs() % names.length]);
  }
}
