/// Configuración centralizada de entornos, URL de backend y versiones esperadas.
class AppConfig {
  const AppConfig._();

  static const String appTitle = 'Rutas mínimas en Cusco';
  static const String appSubtitle = 'UNSAAC · Algoritmos Avanzados';
  static const String expectedApiVersion = '1.5.0';

  /// Producción en Render (Plan Free: puede tardar unos segundos al despertar).
  static const String productionBaseUrl = 'https://rutas-cusco-unsaac.onrender.com';

  /// Emulador Android hacia servidor FastAPI corriendo en el host local.
  static const String androidEmulatorLocalUrl = 'http://10.0.2.2:8000';

  static const String configuredBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: productionBaseUrl,
  );

  static const String environment = String.fromEnvironment(
    'APP_ENV',
    defaultValue: 'prod',
  );

  static const Duration standardTimeout = Duration(seconds: 45);
  static const Duration healthTimeout = Duration(seconds: 35);
  static const Duration slowWarningThreshold = Duration(seconds: 4);

  /// Normaliza una URL base quitando barras finales.
  static String normalizeBaseUrl(String raw) {
    final trimmed = raw.trim();
    if (trimmed.isEmpty) {
      return productionBaseUrl;
    }
    return trimmed.replaceAll(RegExp(r'/+$'), '');
  }

  /// Detecta si el usuario escribió localhost/127.0.0.1 en un teléfono o emulador.
  static bool isLoopbackHost(String url) {
    final uri = Uri.tryParse(url);
    if (uri == null) return false;
    final host = uri.host.toLowerCase();
    return host == 'localhost' || host == '127.0.0.1' || host == '::1';
  }
}
