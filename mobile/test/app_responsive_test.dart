import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:rutas_cusco_mobile/core/network/api_client.dart';
import 'package:rutas_cusco_mobile/core/services/device_files_service.dart';
import 'package:rutas_cusco_mobile/core/services/location_service.dart';
import 'package:rutas_cusco_mobile/core/widgets/app_select_field.dart';
import 'package:rutas_cusco_mobile/data/local/app_database.dart';
import 'package:rutas_cusco_mobile/data/repositories/analysis_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/conditions_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/docs_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/instance_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/route_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/server_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/settings_repository.dart';
import 'package:rutas_cusco_mobile/features/routes/routes_screen.dart';
import 'package:rutas_cusco_mobile/features/library/library_screen.dart';
import 'package:rutas_cusco_mobile/main.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

Future<
  (
    ServerRepository,
    InstanceRepository,
    RouteRepository,
    ConditionsRepository,
    AnalysisRepository,
    DocsRepository,
    AppDatabase,
  )
>
_readyDeps(SharedPreferences prefs) async {
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
      if (request.url.path == '/api/v1/catalog') {
        return http.Response(
          jsonEncode({
            'networks': [
              {'kind': 'center', 'label': 'Centro OSM', 'available': true},
            ],
            'queues': ['binary_heap', '4ary_heap', 'fibonacci_heap'],
            'example': 'Seis nodos ilustrativos',
            'provider_keys': {'openweathermap': false, 'tomtom': false},
            'limits': {'experiment_size_min': 5, 'experiment_size_max': 200},
          }),
          200,
        );
      }
      return http.Response('Offline', 503);
    }),
  );
  final settingsRepo = SettingsRepository(prefs);
  final serverRepo = ServerRepository(
    apiClient: client,
    settingsRepository: settingsRepo,
  );
  final instanceRepo = InstanceRepository(apiClient: client, database: db);
  final routeRepo = RouteRepository(apiClient: client, database: db);
  final condRepo = ConditionsRepository(
    apiClient: client,
    settingsRepository: settingsRepo,
  );
  final analysisRepo = AnalysisRepository(apiClient: client, database: db);
  final docsRepo = DocsRepository();
  await Future.wait([
    serverRepo.initialize(),
    instanceRepo.initialize(),
    routeRepo.initialize(),
    condRepo.initialize(),
    analysisRepo.initialize(),
    docsRepo.initialize(),
  ]);
  return (
    serverRepo,
    instanceRepo,
    routeRepo,
    condRepo,
    analysisRepo,
    docsRepo,
    db,
  );
}

void main() {
  testWidgets(
    'Teléfono pequeño usa NavigationBar, navega a Instancias y escala texto sin desbordar',
    (tester) async {
      SharedPreferences.setMockInitialValues({});
      final prefs = await SharedPreferences.getInstance();
      final (sRepo, iRepo, rRepo, cRepo, aRepo, dRepo, db) =
          await tester.runAsync(() => _readyDeps(prefs))
              as (
                ServerRepository,
                InstanceRepository,
                RouteRepository,
                ConditionsRepository,
                AnalysisRepository,
                DocsRepository,
                AppDatabase,
              );
      addTearDown(() => tester.runAsync(db.close));

      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);
      tester.platformDispatcher.textScaleFactorTestValue = 1.4;
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);

      await tester.pumpWidget(
        RutasCuscoApp(
          serverRepository: sRepo,
          settingsRepository: SettingsRepository(prefs),
          instanceRepository: iRepo,
          routeRepository: rRepo,
          conditionsRepository: cRepo,
          analysisRepository: aRepo,
          docsRepository: dRepo,
          deviceFilesService: DeviceFilesService(),
          locationService: LocationService(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(NavigationBar), findsOneWidget);
      expect(find.byType(NavigationRail), findsNothing);

      await tester.tap(find.text('Instancias'));
      await tester.pumpAndSettle();
      expect(find.text('Grafo introductorio de 3 nodos'), findsOneWidget);

      await tester.tap(find.text('Ajustes'));
      await tester.pumpAndSettle();
      expect(find.text('Servicio disponible'), findsOneWidget);
      expect(find.text('Bitácora GitHub'), findsNothing);
      expect(find.byType(TextField), findsNothing);

      await tester.tap(find.text('Biblioteca'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('Referencia'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Referencia'));
      await tester.pumpAndSettle();
      expect(find.text('Cobertura de los mapas'), findsOneWidget);
      expect(find.textContaining('Bitácora'), findsNothing);
      await tester.scrollUntilVisible(
        find.text('Compartir PDF'),
        300,
        scrollable: find
            .descendant(
              of: find.byType(LibraryScreen),
              matching: find.byWidgetPredicate(
                (widget) =>
                    widget is Scrollable &&
                    widget.axisDirection == AxisDirection.down,
              ),
            )
            .last,
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);

      await tester.tap(find.text('Análisis'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('Banco canónico y piloto'));
      await tester.tap(find.text('Banco canónico y piloto'));
      await tester.pumpAndSettle();
      expect(find.byType(Table), findsNothing);

      await tester.tap(find.text('Rutas'));
      await tester.pumpAndSettle();
      final routesVerticalScroll = find.descendant(
        of: find.byType(RoutesScreen),
        matching: find.byWidgetPredicate(
          (w) => w is Scrollable && w.axisDirection == AxisDirection.down,
        ),
      );
      final queueField = find.ancestor(
        of: find.text('Cola de prioridad'),
        matching: find.byType(AppSelectField<String>),
      );
      await tester.drag(routesVerticalScroll.first, const Offset(0, -350));
      await tester.pumpAndSettle();
      final center = tester.getCenter(queueField);
      expect(center.dy, inInclusiveRange(80.0, 760.0));
      await tester.tap(queueField);
      await tester.pumpAndSettle();
      expect(find.byType(BottomSheet), findsOneWidget);
      final textsInSheet = tester
          .widgetList<Text>(
            find.descendant(
              of: find.byType(BottomSheet),
              matching: find.byType(Text),
            ),
          )
          .map((t) => t.data)
          .toList();
      expect(textsInSheet, contains('Cola de prioridad'));
      expect(textsInSheet, contains('4-aria (D-ary Heap, d=4)'));
      await tester.ensureVisible(find.text('4-aria (D-ary Heap, d=4)'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('4-aria (D-ary Heap, d=4)'));
      await tester.pumpAndSettle();
      expect(find.byType(BottomSheet), findsNothing);
      expect(find.text('4-aria (D-ary Heap, d=4)'), findsOneWidget);
    },
  );

  testWidgets('Tableta usa NavigationRail adaptativo y vista en dos columnas', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();
    final (sRepo, iRepo, rRepo, cRepo, aRepo, dRepo, db) =
        await tester.runAsync(() => _readyDeps(prefs))
            as (
              ServerRepository,
              InstanceRepository,
              RouteRepository,
              ConditionsRepository,
              AnalysisRepository,
              DocsRepository,
              AppDatabase,
            );
    addTearDown(() => tester.runAsync(db.close));

    tester.view.physicalSize = const Size(1100, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      RutasCuscoApp(
        serverRepository: sRepo,
        settingsRepository: SettingsRepository(prefs),
        instanceRepository: iRepo,
        routeRepository: rRepo,
        conditionsRepository: cRepo,
        analysisRepository: aRepo,
        docsRepository: dRepo,
        deviceFilesService: DeviceFilesService(),
        locationService: LocationService(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(NavigationRail), findsOneWidget);
    expect(find.byType(NavigationBar), findsNothing);
    expect(find.text('UNSAAC · Cusco'), findsOneWidget);

    await tester.tap(find.text('Análisis'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Banco canónico y piloto'));
    await tester.pumpAndSettle();
    expect(find.byType(Table), findsAtLeastNWidgets(1));
  });
}
