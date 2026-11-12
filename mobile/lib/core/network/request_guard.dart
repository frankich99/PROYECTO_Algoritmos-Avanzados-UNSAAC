/// Evita que una respuesta tardía sobrescriba una consulta más reciente
/// cuando el usuario cambia de instancia, origen/destino o pantalla.
class RequestGuard {
  int _latestToken = 0;

  int nextToken() {
    _latestToken += 1;
    return _latestToken;
  }

  bool isCurrent(int token) => token == _latestToken;

  void invalidateAll() {
    _latestToken += 1;
  }
}
