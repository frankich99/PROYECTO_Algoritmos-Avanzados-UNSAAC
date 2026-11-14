import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:provider/provider.dart';
import 'package:rutas_cusco_mobile/core/config/app_config.dart';
import 'package:rutas_cusco_mobile/core/network/api_client.dart';
import 'package:rutas_cusco_mobile/core/theme/app_theme.dart';
import 'package:rutas_cusco_mobile/data/repositories/server_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/settings_repository.dart';
import 'package:rutas_cusco_mobile/features/settings/project_settings_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

http.Response _response(http.Request request, {String version = '1.5.0'}) {
  final body = switch (request.url.path) {
    '/api/v1/health' => <String, dynamic>{'ok': true},
    '/api/v1/version' => <String, dynamic>{'api_version': version},
    _ => <String, dynamic>{
      'networks': [
        {'kind': 'center', 'label': 'Centro OSM', 'available': true},
      ],
      'queues': ['binary_heap'],
    },
  };
  return http.Response(jsonEncode(body), 200);
}

Future<ServerRepository> _repository(
  Future<http.Response> Function(http.Request) handler,
) async {
  final prefs = await SharedPreferences.getInstance();
  final client = ApiClient(
    baseUrl: AppConfig.productionBaseUrl,
    httpClient: MockClient(handler),
  );
  addTearDown(client.dispose);
  final repo = ServerRepository(
    apiClient: client,
    settingsRepository: SettingsRepository(prefs),
  );
  addTearDown(repo.dispose);
  await repo.initialize();
  return repo;
}

Future<void> _showSettings(
  WidgetTester tester,
  ServerRepository repo, {
  Size size = const Size(390, 844),
  double scale = 1,
}) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    ChangeNotifierProvider.value(
      value: repo,
      child: MaterialApp(
        theme: AppTheme.light(),
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context)
              .copyWith(textScaler: TextScaler.linear(scale)),
          child: child!,
        ),
        home: const ProjectSettingsScreen(),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('URL base admite producción, emulador y servidor LAN', () {
    for (final url in [
      AppConfig.productionBaseUrl,
      AppConfig.androidEmulatorLocalUrl,
      'http://192.168.1.10:8000/',
      'https://example.org/rutas',
      'http://[::1]:8000',
    ]) {
      expect(AppConfig.validateBaseUrl(url), isNull, reason: url);
    }
  });

  test(
    'URL base rechaza esquemas, credenciales, puerto y sufijo API incorrectos',
    () {
      for (final url in [
        '',
        'rutas.local',
        'file:///data/rutas',
        'ftp://example.org',
        'https://',
        'https://example.org:99999',
        'https://example.org:abc',
        'https://user:secret@example.org',
        'https://example.org?q=1',
        'https://example.org#mapa',
        'https://example.org/api/v1/',
        'https://exam ple.org',
      ]) {
        expect(AppConfig.validateBaseUrl(url), isNotNull, reason: url);
      }
    },
  );

  test(
    'Sin conexión conserva catálogo del mismo servicio, no del nuevo',
    () async {
      var offline = false;
      final repo = await _repository((request) async {
        if (offline) throw const SocketException('offline');
        return _response(request);
      });
      expect(repo.state, ServerLoadState.ready);
      offline = true;
      await repo.refreshStatus();
      expect(repo.state, ServerLoadState.saved);
      expect(repo.catalog, isNotNull);
      await repo.updateServerUrl('http://192.168.1.20:8000');
      expect(repo.state, ServerLoadState.offline);
      expect(repo.catalog, isNull);
      expect(repo.version, isNull);
      expect(repo.lastSyncedAt, isNull);
      expect(await repo.settingsRepository.loadCachedCatalogJson(), isNull);
      expect(await repo.settingsRepository.loadCachedVersionJson(), isNull);
      expect(
        await repo.settingsRepository.loadBaseUrl(),
        'http://192.168.1.20:8000',
      );
    },
  );

  test(
    'Rechazar una URL no modifica la configuración ni inicia solicitudes',
    () async {
      var calls = 0;
      final repo = await _repository((request) async {
        calls++;
        return _response(request);
      });
      final before = calls;
      await expectLater(
        repo.updateServerUrl('ftp://invalid'),
        throwsArgumentError,
      );
      expect(calls, before);
      expect(repo.baseUrl, AppConfig.productionBaseUrl);
      expect(repo.state, ServerLoadState.ready);
    },
  );

  test('Reintentos simultáneos no duplican solicitudes', () async {
    Completer<http.Response>? pending;
    final entered = Completer<void>();
    var healthCalls = 0;
    final repo = await _repository((request) async {
      if (request.url.path.endsWith('/health')) {
        healthCalls++;
        if (pending != null) {
          entered.complete();
          return pending.future;
        }
      }
      return _response(request);
    });
    pending = Completer();
    final refresh = repo.refreshStatus();
    await entered.future;
    await repo.refreshStatus();
    expect(healthCalls, 2);
    pending.complete(http.Response('{"ok":true}', 200));
    await refresh;
    expect(repo.state, ServerLoadState.ready);
  });

  testWidgets(
    'Ajustes muestra ayuda, oculta datos técnicos y valida antes de guardar',
    (tester) async {
      var calls = 0;
      final repo = await _repository((request) async {
        calls++;
        return _response(request);
      });
      await _showSettings(tester, repo);
      expect(find.text('Servicio disponible'), findsOneWidget);
      expect(find.byType(TextField), findsNothing);
      expect(find.textContaining('Bitácora'), findsNothing);
      expect(find.textContaining('GitHub'), findsNothing);
      expect(find.text('Acerca de'), findsOneWidget);

      await tester.tap(find.text('Cómo se conectan los mapas'));
      await tester.pumpAndSettle();
      expect(find.text('Plano sin conexión'), findsOneWidget);
      expect(find.text('Calles OSM'), findsOneWidget);
      await tester.tap(find.text('Cómo se conectan los mapas'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('Conexión avanzada'));
      await tester.tap(find.text('Conexión avanzada'));
      await tester.pumpAndSettle();
      expect(find.byType(TextField), findsOneWidget);
      await tester.ensureVisible(find.byType(TextField));
      await tester.enterText(find.byType(TextField), 'ftp://invalid');
      await tester.ensureVisible(find.text('Guardar y comprobar'));
      final before = calls;
      await tester.tap(find.text('Guardar y comprobar'));
      await tester.pumpAndSettle();
      expect(
        find.text('Ingresa una dirección válida con https:// o http://.'),
        findsOneWidget,
      );
      expect(calls, before);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'Sin conexión explica límites y reintentar recupera el servicio',
    (tester) async {
      var offline = true;
      final repo = await _repository((request) async {
        if (offline) throw const SocketException('offline');
        return _response(request);
      });
      await _showSettings(tester, repo);
      expect(find.text('Sin conexión al servicio'), findsOneWidget);
      expect(find.text('Reintentar conexión'), findsOneWidget);
      offline = false;
      await tester.tap(find.text('Reintentar conexión'));
      await tester.pumpAndSettle();
      expect(find.text('Servicio disponible'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('Versión incompatible no se anuncia como servicio disponible', (
    tester,
  ) async {
    final repo = await _repository(
      (request) async => _response(request, version: '2.0.0'),
    );
    await _showSettings(tester, repo);
    expect(find.text('El servicio necesita revisión'), findsOneWidget);
    expect(find.text('Servicio disponible'), findsNothing);
  });

  testWidgets(
    'Servidor propio, restauración y emulador usan el cliente compartido',
    (tester) async {
      final hosts = <String>[];
      final repo = await _repository((request) async {
        hosts.add(request.url.host);
        return _response(request);
      });
      await _showSettings(tester, repo);
      await tester.ensureVisible(find.text('Conexión avanzada'));
      await tester.tap(find.text('Conexión avanzada'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.byType(TextField));
      await tester.enterText(
        find.byType(TextField),
        'http://192.168.1.20:8000',
      );
      await tester.ensureVisible(find.text('Guardar y comprobar'));
      await tester.tap(find.text('Guardar y comprobar'));
      await tester.pumpAndSettle();
      expect(repo.baseUrl, 'http://192.168.1.20:8000');
      expect(hosts.last, '192.168.1.20');
      expect(repo.state, ServerLoadState.ready);
      await tester.ensureVisible(
        find.text('Restablecer servicio del proyecto'),
      );
      await tester.tap(find.text('Restablecer servicio del proyecto'));
      await tester.pumpAndSettle();
      expect(repo.baseUrl, AppConfig.productionBaseUrl);
      expect(hosts.last, 'rutas-cusco-unsaac.onrender.com');
      await tester.ensureVisible(
        find.text('Usar servidor del emulador (10.0.2.2)'),
      );
      await tester.tap(find.text('Usar servidor del emulador (10.0.2.2)'));
      await tester.pumpAndSettle();
      expect(repo.baseUrl, AppConfig.androidEmulatorLocalUrl);
      expect(hosts.last, '10.0.2.2');
      expect(tester.takeException(), isNull);
    },
  );

  for (final (size, scale) in [
    (const Size(320, 700), 1.4),
    (const Size(390, 844), 2.0),
    (const Size(1100, 800), 1.4),
  ]) {
    testWidgets(
      'Ayuda y opciones sin desbordes a ${size.width} px y texto ×$scale',
      (tester) async {
        final repo = await _repository((request) async => _response(request));
        await _showSettings(tester, repo, size: size, scale: scale);
        for (final title in [
          'Qué puedes hacer sin internet',
          'Cómo se conectan los mapas',
          'Conexión avanzada',
        ]) {
          await tester.ensureVisible(find.text(title));
          await tester.tap(find.text(title));
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
        }
        await tester.ensureVisible(
          find.text('Usar servidor del emulador (10.0.2.2)'),
        );
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
      },
    );
  }
}
