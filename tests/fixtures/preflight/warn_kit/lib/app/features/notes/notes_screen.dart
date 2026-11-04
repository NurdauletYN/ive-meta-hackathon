class NotesScreen extends StatefulWidget {
  const NotesScreen();
  State createState() => _S();
}
class _S extends State {
  Widget build(c) {
    return ListView(children: const [Text('alpha'), Text('beta'), Text('gamma')]);
  }
}
