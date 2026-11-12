import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:rutas_cusco_mobile/core/network/api_client.dart';
import 'package:rutas_cusco_mobile/data/repositories/server_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/settings_repository.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  test('ServerRepository guarda caché y cae a saved cuando luego queda sin conexión', () async {
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();
    final settings = SettingsRepository(prefs);

    var online = true;
    final apiClient = ApiClient(
      baseUrl: 'https://rutas-cusco-unsaac.onrender.com',
      httpClient: MockClient((request) async {
        if (!online) {
          throw const SocketException('Network unreachable');
        }
        if (request.url.path == '/api/v1/health') {
          return http.Response(jsonEncode({'ok': true}), 200);
        }
        if (request.url.path == '/api/v1/version') {
          return http.Response(
            jsonEncode({
              'name': 'Rutas mínimas en Cusco',
              'version': '1.5.0',
              'api_version': '1.5.0',
              'data_version': '2026-10-28',
              'docs_version': '2026-11-06',
              'generator_version': '1.0.0',
              'web_build': true,
            }),
            200,
          );
        }
        if (request.url.path == '/api/v1/catalog') {
          return http.Response(
            jsonEncode({
              'networks': [
                {'kind': 'center', 'label': 'Centro', 'available': true}
              ],
              'queues': ['binary_heap', '4ary_heap', 'fibonacci_heap'],
              'example': 'Seis nodos ilustrativos',
              'provider_keys': {'openweathermap': false, 'tomtom': false},
              'limits': {'experiment_size_min': 5, 'experiment_size_max': 200},
            }),
            200,
          );
        }
        return http.Response('{}', 404);
      }),
    );

    final repo = ServerRepository(
      apiClient: apiClient,
      settingsRepository: settings,
    );

    await repo.initialize();
    expect(repo.state, ServerLoadState.ready);
    expect(repo.version?.apiVersion, '1.5.0');
    expect(repo.limits.experimentSizeMin, 5);
    expect(repo.isVersionCompatible, isTrue);

    online = false;
    await repo.refreshStatus();
    expect(repo.state, ServerLoadState.saved);
    expect(repo.isUsingSavedFallback, isTrue);
    expect(repo.catalog?.networks.first.kind, 'center');
  });

  test('ServerRepository reporta offline si nunca hubo caché previa', () async {
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();
    final repo = ServerRepository(
      apiClient: ApiClient(
        baseUrl: 'https://rutas-cusco-unsaac.onrender.com',
        httpClient: MockClient((_) async => throw const SocketException('Offline')),
      ),
      settingsRepository: SettingsRepository(prefs),
    );

    await repo.initialize();
    expect(repo.state, ServerLoadState.offline);
    expect(repo.errorMessage, isNotNull);
  });
}
