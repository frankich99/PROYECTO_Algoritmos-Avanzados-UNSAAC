import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:rutas_cusco_mobile/core/network/api_client.dart';
import 'package:rutas_cusco_mobile/core/services/device_files_service.dart';
import 'package:rutas_cusco_mobile/core/services/location_service.dart';
import 'package:rutas_cusco_mobile/data/local/app_database.dart';
import 'package:rutas_cusco_mobile/data/models/instance_models.dart';
import 'package:rutas_cusco_mobile/data/models/route_models.dart';
import 'package:rutas_cusco_mobile/data/repositories/analysis_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/conditions_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/docs_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/instance_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/route_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/server_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/settings_repository.dart';
import 'package:rutas_cusco_mobile/main.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

Map<String, dynamic> _sampleSolvePayload() => {
      'network': 'cusco_manual_time',
      'coverage': 'example',
      'counts': {'nodes': 6, 'edges': 9},
      'metric': 'time',
      'unit': 's',
      'source': 'A',
      'target': 'F',
      'source_snap': null,
      'target_snap': null,
      'result': {
        'algorithm': 'dijkstra',
        'queue': 'binary_heap',
        'cost': 144.45,
        'path': ['A', 'C', 'F'],
        'edges': [
          {
            'from': 'A',
            'to': 'C',
            'cost': 108.0,
            'length_m': 450.0,
            'time_sec': 108.0,
            'street': 'Calle Loreto',
          },
          {
            'from': 'C',
            'to': 'F',
            'cost': 36.45,
            'length_m': 350.0,
            'time_sec': 36.45,
            'street': 'Calle Ahuacpinta',
          },
        ],
        'length_m': 800.0,
        'time_sec': 144.45,
        'path_geometry': [],
        'expanded': 4,
        'relaxations': 6,
        'decrease_key': 1,
        'elapsed_ms_single_run': 0.142,
      },
      'comparisons': [
        {
          'algorithm': 'dijkstra',
          'queue': 'binary_heap',
          'cost': 144.45,
          'path': ['A', 'C', 'F'],
          'edges': [],
          'length_m': 800.0,
          'time_sec': 144.45,
          'path_geometry': [],
          'expanded': 4,
          'relaxations': 6,
          'decrease_key': 1,
          'elapsed_ms_single_run': 0.142,
        },
        {
          'algorithm': 'dijkstra',
          'queue': '4ary_heap',
          'cost': 144.45,
          'path': ['A', 'C', 'F'],
          'edges': [],
          'length_m': 800.0,
          'time_sec': 144.45,
          'path_geometry': [],
          'expanded': 4,
          'relaxations': 6,
          'decrease_key': 1,
          'elapsed_ms_single_run': 0.155,
        },
        {
          'algorithm': 'dijkstra',
          'queue': 'fibonacci_heap',
          'cost': 144.45,
          'path': ['A', 'C', 'F'],
          'edges': [],
          'length_m': 800.0,
          'time_sec': 144.45,
          'path_geometry': [],
          'expanded': 4,
          'relaxations': 6,
          'decrease_key': 1,
          'elapsed_ms_single_run': 0.21,
        },
        {
          'algorithm': 'astar',
          'queue': 'binary_heap',
          'cost': 144.45,
          'path': ['A', 'C', 'F'],
          'edges': [],
          'length_m': 800.0,
          'time_sec': 144.45,
          'path_geometry': [],
          'expanded': 3,
          'relaxations': 4,
          'decrease_key': 0,
          'elapsed_ms_single_run': 0.118,
        },
      ],
      'path_coords': [
        [0.0, 0.0],
        [180.0, -250.0],
        [350.0, -420.0],
      ],
      'scenario': {'kind': 'nominal', 'factor': 1.0},
      'geometry_quality': 'abstract',
      'warning': null,
    };

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  sqfliteFfiInit();

  test('RouteRepository resuelve ruta, separa tiempos y guarda/recupera en SQLite local', () async {
    final db = AppDatabase(
      factory: databaseFactoryFfiNoIsolate,
      customPath: inMemoryDatabasePath,
    );
    addTearDown(db.close);

    final client = ApiClient(
      baseUrl: 'https://rutas-cusco-unsaac.onrender.com',
      httpClient: MockClient((request) async {
        if (request.url.path == '/api/v1/routes/solve') {
          return http.Response(jsonEncode(_sampleSolvePayload()), 200);
        }
        return http.Response('{}', 404);
      }),
    );

    final repo = RouteRepository(apiClient: client, database: db);
    await repo.initialize();

    final resp = await repo.solveRoute(
      const RouteRequest(
        instance: InstanceSpec(kind: 'example'),
        source: 'A',
        target: 'F',
        metric: 'time',
      ),
    );

    expect(resp, isNotNull);
    expect(resp!.result.cost, 144.45);
    expect(resp.comparisons.length, 4);
    expect(repo.lastRequestLatencyMs, isNotNull);
    expect(repo.isSavedOfflineView, isFalse);

    final saved = await repo.saveCurrentRoute();
    expect(saved.cost, 144.45);

    final reloaded = RouteRepository(apiClient: client, database: db);
    await reloaded.initialize();
    expect(reloaded.savedRoutes.length, 1);

    reloaded.openSavedRoute(reloaded.savedRoutes.first);
    expect(reloaded.isSavedOfflineView, isTrue);
    expect(reloaded.currentResponse?.result.path, ['A', 'C', 'F']);

    await reloaded.deleteSavedRoute(saved.id);
    expect(reloaded.savedRoutes, isEmpty);
  });

  testWidgets('Flujo completo en Rutas: valida, calcula, muestra 4 comparaciones y lista accesible', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();

    final (serverRepo, instRepo, routeRepo, condRepo, analysisRepo, docsRepo, db) =
        await tester.runAsync(() async {
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
          if (request.url.path == '/api/v1/catalog') {
            return http.Response(
              jsonEncode({
                'networks': [
                  {'kind': 'center', 'label': 'Centro OSM', 'available': true}
                ],
                'queues': ['binary_heap', '4ary_heap', 'fibonacci_heap'],
                'example': 'Seis nodos ilustrativos',
                'provider_keys': {'openweathermap': false, 'tomtom': false},
                'limits': {},
              }),
              200,
            );
          }
          if (request.url.path == '/api/v1/instances/validate') {
            return http.Response(
              jsonEncode({
                'valid': true,
                'name': 'cusco_manual_time',
                'nodes': 6,
                'edges': 9,
                'ids': ['A', 'B', 'C', 'D', 'E', 'F'],
                'coords': {
                  'A': [0.0, 0.0],
                  'B': [-120.0, -10.0],
                  'C': [180.0, -250.0],
                  'D': [-310.0, -80.0],
                  'E': [-480.0, -320.0],
                  'F': [350.0, -420.0],
                },
                'metric': 'time',
                'geographic': false,
                'display_edges': [
                  ['A', 'B', 44.82],
                  ['A', 'C', 108.0],
                  ['C', 'F', 36.45],
                ],
                'display_limited': false,
              }),
              200,
            );
          }
          if (request.url.path == '/api/v1/routes/solve') {
            return http.Response(jsonEncode(_sampleSolvePayload()), 200);
          }
          return http.Response('{}', 404);
        }),
      );

      final settingsRepo = SettingsRepository(prefs);
      final sRepo = ServerRepository(
        apiClient: client,
        settingsRepository: settingsRepo,
      );
      final iRepo = InstanceRepository(apiClient: client, database: db);
      final rRepo = RouteRepository(apiClient: client, database: db);
      final cRepo = ConditionsRepository(
        apiClient: client,
        settingsRepository: settingsRepo,
      );
      final aRepo = AnalysisRepository(apiClient: client, database: db);
      final dRepo = DocsRepository();
      await Future.wait([
        sRepo.initialize(),
        iRepo.initialize(),
        rRepo.initialize(),
        cRepo.initialize(),
        aRepo.initialize(),
        dRepo.initialize(),
      ]);
      return (sRepo, iRepo, rRepo, cRepo, aRepo, dRepo, db);
    }) as (
      ServerRepository,
      InstanceRepository,
      RouteRepository,
      ConditionsRepository,
      AnalysisRepository,
      DocsRepository,
      AppDatabase
    );

    addTearDown(() => tester.runAsync(db.close));

    tester.view.physicalSize = const Size(420, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      RutasCuscoApp(
        serverRepository: serverRepo,
        settingsRepository: SettingsRepository(prefs),
        instanceRepository: instRepo,
        routeRepository: routeRepo,
        conditionsRepository: condRepo,
        analysisRepository: analysisRepo,
        docsRepository: docsRepo,
        deviceFilesService: DeviceFilesService(),
        locationService: LocationService(),
      ),
    );
    await tester.pumpAndSettle();

    final solveButton = find.text('Calcular y contrastar');
    await tester.scrollUntilVisible(
      solveButton,
      200,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();
    await tester.tap(solveButton);
    await tester.pumpAndSettle();

    expect(find.text('144.45 s'), findsWidgets);
    expect(find.text('Comparación equivalente (4 ejecuciones)'), findsOneWidget);
    expect(find.text('A → C → F'), findsOneWidget);
    expect(find.text('Vista en lista del recorrido (2 tramos)'), findsOneWidget);

    await tester.scrollUntilVisible(
      find.text('Guardar en biblioteca'),
      250,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Guardar en biblioteca'));
    await tester.pumpAndSettle();

    expect(routeRepo.savedRoutes.length, 1);
  });
}
