import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:rutas_cusco_mobile/core/network/api_client.dart';
import 'package:rutas_cusco_mobile/core/services/device_files_service.dart';
import 'package:rutas_cusco_mobile/data/local/app_database.dart';
import 'package:rutas_cusco_mobile/data/repositories/instance_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/server_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/settings_repository.dart';
import 'package:rutas_cusco_mobile/main.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

Future<(ServerRepository, InstanceRepository, AppDatabase)> _readyDeps(
  SharedPreferences prefs,
) async {
  sqfliteFfiInit();
  final db = AppDatabase(
    factory: databaseFactoryFfiNoIsolate,
    customPath: inMemoryDatabasePath,
  );
  final client = ApiClient(
    baseUrl: 'https://rutas-cusco-unsaac.onrender.com',
    httpClient: MockClient((request) async {
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
      return http.Response(
        jsonEncode({
          'networks': [
            {'kind': 'center', 'label': 'Centro OSM', 'available': true}
          ],
          'queues': ['binary_heap', '4ary_heap', 'fibonacci_heap'],
          'example': 'Seis nodos ilustrativos',
          'provider_keys': {'openweathermap': false, 'tomtom': false},
          'limits': {'experiment_size_min': 5, 'experiment_size_max': 200},
        }),
        200,
      );
    }),
  );
  final serverRepo = ServerRepository(
    apiClient: client,
    settingsRepository: SettingsRepository(prefs),
  );
  final instanceRepo = InstanceRepository(
    apiClient: client,
    database: db,
  );
  await Future.wait([serverRepo.initialize(), instanceRepo.initialize()]);
  return (serverRepo, instanceRepo, db);
}

void main() {
  testWidgets('Teléfono pequeño usa NavigationBar, navega a Instancias y escala texto sin desbordar', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();
    final (serverRepo, instanceRepo, db) = await tester.runAsync(
      () => _readyDeps(prefs),
    ) as (ServerRepository, InstanceRepository, AppDatabase);
    addTearDown(() => tester.runAsync(db.close));

    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      MediaQuery(
        data: const MediaQueryData(textScaler: TextScaler.linear(1.4)),
        child: RutasCuscoApp(
          serverRepository: serverRepo,
          settingsRepository: SettingsRepository(prefs),
          instanceRepository: instanceRepo,
          deviceFilesService: DeviceFilesService(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.byType(NavigationRail), findsNothing);

    await tester.tap(find.text('Instancias'));
    await tester.pumpAndSettle();
    expect(find.text('Grafo introductorio de 3 nodos'), findsOneWidget);

    await tester.tap(find.text('Proyecto'));
    await tester.pumpAndSettle();
    expect(find.text('Estado del backend FastAPI'), findsOneWidget);
    expect(find.text('1.5.0'), findsOneWidget);
  });

  testWidgets('Tableta usa NavigationRail adaptativo y vista en dos columnas', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();
    final (serverRepo, instanceRepo, db) = await tester.runAsync(
      () => _readyDeps(prefs),
    ) as (ServerRepository, InstanceRepository, AppDatabase);
    addTearDown(() => tester.runAsync(db.close));

    tester.view.physicalSize = const Size(1100, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      RutasCuscoApp(
        serverRepository: serverRepo,
        settingsRepository: SettingsRepository(prefs),
        instanceRepository: instanceRepo,
        deviceFilesService: DeviceFilesService(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(NavigationRail), findsOneWidget);
    expect(find.byType(NavigationBar), findsNothing);
    expect(find.text('UNSAAC · Cusco'), findsOneWidget);
  });
}
