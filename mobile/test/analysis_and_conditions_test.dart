import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:rutas_cusco_mobile/core/network/api_client.dart';
import 'package:rutas_cusco_mobile/data/local/app_database.dart';
import 'package:rutas_cusco_mobile/data/models/catalog_models.dart';
import 'package:rutas_cusco_mobile/data/models/instance_models.dart';
import 'package:rutas_cusco_mobile/data/repositories/analysis_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/conditions_repository.dart';
import 'package:rutas_cusco_mobile/data/repositories/settings_repository.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  sqfliteFfiInit();

  test('AnalysisRepository carga benchmark canónico y piloto desde assets sin conexión', () async {
    final db = AppDatabase(
      factory: databaseFactoryFfiNoIsolate,
      customPath: inMemoryDatabasePath,
    );
    addTearDown(db.close);

    final offlineClient = ApiClient(
      baseUrl: 'https://rutas-cusco-unsaac.onrender.com',
      httpClient: MockClient((_) async => throw const SocketException('Offline')),
    );

    final repo = AnalysisRepository(apiClient: offlineClient, database: db);
    await repo.initialize();

    expect(repo.benchmarkFromOfflineBundle, isTrue);
    expect(repo.canonicalBenchmark, isNotNull);
    expect(repo.canonicalBenchmark!.results.scales.length, 5);
    expect(repo.pilotSeries, isNotNull);
    expect(repo.pilotSeries!.scales, [100]);
  });

  test('AnalysisRepository valida límites 5-200 y guarda experimento de sesión en SQLite', () async {
    const limits = ApiLimits();
    final valid = AnalysisRepository.parseExperimentInputs(
      profile: 'sparse',
      sizesText: '5, 30, 200',
      seedText: '0',
      runsText: '2',
      limits: limits,
    );
    expect(valid.sizes, [5, 30, 200]);
    expect(valid.seed, 0);
    expect(valid.runs, 2);

    for (final bad in ['4', '201', '30, 30', '5, 10, 15, 20, 25', '']) {
      expect(
        () => AnalysisRepository.parseExperimentInputs(
          profile: 'dense',
          sizesText: bad,
          seedText: '42',
          runsText: '5',
          limits: limits,
        ),
        throwsFormatException,
      );
    }

    final db = AppDatabase(
      factory: databaseFactoryFfiNoIsolate,
      customPath: inMemoryDatabasePath,
    );
    addTearDown(db.close);

    final client = ApiClient(
      baseUrl: 'https://rutas-cusco-unsaac.onrender.com',
      httpClient: MockClient((request) async {
        if (request.url.path == '/api/v1/experiments') {
          return http.Response(
            jsonEncode({
              'kind': 'session_experiment_not_canonical',
              'profile': 'sparse',
              'generated_at_utc': '2026-11-12T10:00:00+00:00',
              'protocol': {
                'runs_per_instance': 2,
                'instances_per_size': 2,
                'warmup': 2,
                'clock': 'perf_counter_ns',
                'gc': 'normal',
                'timing_scope': 'solo solver',
              },
              'rows': [
                {
                  'nodes': 10,
                  'edges': 40,
                  'queue': 'binary_heap',
                  'median_us': 45.2,
                  'q1_us': 41.0,
                  'q3_us': 49.0,
                  'samples_us': [41.0, 44.0, 46.4, 49.0],
                  'instance_seeds': [310, 311],
                },
              ],
            }),
            200,
          );
        }
        return http.Response('{}', 404);
      }),
    );

    final repo = AnalysisRepository(apiClient: client, database: db);
    final res = await repo.runExperiment(valid);
    expect(res, isNotNull);
    expect(res!.kind, 'session_experiment_not_canonical');
    expect(repo.lastExperimentLatencyMs, isNotNull);
    expect(repo.savedExperiments.length, 1);
  });

  test('ConditionsRepository guarda lectura meteorológica local, verifica punto y olvida claves', () async {
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();
    final settings = SettingsRepository(prefs);

    final client = ApiClient(
      baseUrl: 'https://rutas-cusco-unsaac.onrender.com',
      httpClient: MockClient((request) async {
        if (request.url.path == '/api/v1/conditions') {
          return http.Response(
            jsonEncode({
              'kind': 'model_weather_not_station',
              'requested': {'lat': -13.5165, 'lon': -71.9788},
              'fetched_at_utc': '2026-11-12T10:00:00+00:00',
              'multiplier': 1.07,
              'contributions': {'lluvia': 0.05, 'visibilidad': 0.02},
              'observation': {
                'temperature_c': 14.0,
                'relative_humidity_pct': 70.0,
                'precipitation_mm': 2.5,
                'visibility_m': 8000.0,
                'wind_gusts_kmh': 20.0,
                'observed_at': '2026-11-12T05:00',
                'timezone': 'America/Lima',
                'grid_point': {'lat': -13.5, 'lon': -71.97},
                'source': 'Open-Meteo',
                'weather_code': 61,
                'weather_description': 'Lluvia ligera',
                'surface_pressure_hpa': 651.0,
              },
            }),
            200,
          );
        }
        return http.Response('{}', 404);
      }),
    );

    final condRepo = ConditionsRepository(
      apiClient: client,
      settingsRepository: settings,
    );
    await condRepo.initialize();

    final res = await condRepo.fetchCondition(
      point: const PointCoord(lat: -13.5165, lon: -71.9788),
      provider: 'open-meteo',
    );
    expect(res, isNotNull);
    await condRepo.saveLiveWeatherLocally();
    expect(
      ConditionsRepository.samePoint(
        condRepo.savedWeather?.requested,
        const PointCoord(lat: -13.5165, lon: -71.9788),
      ),
      isTrue,
    );
    expect(
      ConditionsRepository.samePoint(
        condRepo.savedWeather?.requested,
        const PointCoord(lat: -13.52, lon: -71.9788),
      ),
      isFalse,
    );

    await condRepo.setRememberKeys(true);
    await condRepo.updatePersonalKey('tomtom', 'clave-demo');
    expect(condRepo.keyFor('tomtom'), 'clave-demo');
    await condRepo.forgetKeys();
    expect(condRepo.keyFor('tomtom'), '');
    expect(condRepo.rememberKeys, isFalse);
  });
}
