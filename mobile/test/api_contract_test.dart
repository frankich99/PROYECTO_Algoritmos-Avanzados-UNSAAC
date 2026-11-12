import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:rutas_cusco_mobile/core/config/app_config.dart';
import 'package:rutas_cusco_mobile/core/network/api_client.dart';
import 'package:rutas_cusco_mobile/core/network/api_exception.dart';
import 'package:rutas_cusco_mobile/core/network/request_guard.dart';
import 'package:rutas_cusco_mobile/data/models/catalog_models.dart';
import 'package:rutas_cusco_mobile/data/models/instance_models.dart';
import 'package:rutas_cusco_mobile/data/models/route_models.dart';
import 'package:rutas_cusco_mobile/data/models/version_info.dart';

void main() {
  group('ApiClient y contrato FastAPI', () {
    test('interpreta version, catalog y limits unificados', () async {
      final client = ApiClient(
        baseUrl: 'https://rutas-cusco-unsaac.onrender.com/',
        httpClient: MockClient((request) async {
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
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          }
          if (request.url.path == '/api/v1/catalog') {
            return http.Response(
              jsonEncode({
                'networks': [
                  {'kind': 'center', 'label': 'Centro OSM', 'available': true},
                  {'kind': 'urban', 'label': 'Ampliada OSM', 'available': true},
                ],
                'queues': ['binary_heap', '4ary_heap', 'fibonacci_heap'],
                'example': 'Seis nodos ilustrativos',
                'provider_keys': {'openweathermap': false, 'tomtom': false},
                'limits': {
                  'max_nodes': 5000,
                  'max_edges': 30000,
                  'max_payload_bytes': 2000000,
                  'display_max_nodes': 1200,
                  'display_max_edges': 3000,
                  'generator_nodes_min': 2,
                  'generator_nodes_max': 500,
                  'generator_grid_min': 1,
                  'generator_grid_max': 30,
                  'experiment_sizes_max_count': 4,
                  'experiment_size_min': 5,
                  'experiment_size_max': 200,
                  'experiment_runs_min': 2,
                  'experiment_runs_max': 10,
                  'seed_min': 0,
                  'seed_max': 2147483647,
                },
              }),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          }
          return http.Response('Not found', 404);
        }),
      );

      final version = VersionInfo.fromJson(await client.getJson('/version'));
      final catalog = CatalogInfo.fromJson(await client.getJson('/catalog'));

      expect(version.apiVersion, '1.5.0');
      expect(version.dataVersion, '2026-10-28');
      expect(catalog.networks.length, 2);
      expect(catalog.limits.experimentSizeMin, 5);
      expect(catalog.limits.experimentSizeMax, 200);
      expect(catalog.limits.displayMaxEdges, 3000);
    });

    test('distingue destino inalcanzable (cost null) de costo cero y conserva IDs mixtos', () {
      final unreachable = RouteResponse.fromJson({
        'network': 'custom',
        'coverage': 'custom',
        'counts': {'nodes': 2, 'edges': 0},
        'metric': 'time',
        'unit': 'peso',
        'source': 1008097623,
        'target': 'Z',
        'source_snap': null,
        'target_snap': null,
        'result': {
          'algorithm': 'dijkstra',
          'queue': 'binary_heap',
          'cost': null,
          'path': [],
          'edges': [],
          'length_m': null,
          'time_sec': null,
          'path_geometry': [],
          'expanded': 1,
          'relaxations': 0,
          'decrease_key': 0,
          'elapsed_ms_single_run': 0.05,
        },
        'comparisons': [],
        'path_coords': [],
        'scenario': {'kind': 'nominal', 'factor': 1.0},
        'geometry_quality': 'abstract',
        'warning': null,
      });

      expect(unreachable.source, 1008097623);
      expect(unreachable.source, isA<int>());
      expect(unreachable.target, 'Z');
      expect(unreachable.result.cost, isNull);
      expect(unreachable.result.isReachable, isFalse);

      final point = PointCoord.fromLonLatList([-71.9788, -13.5165]);
      expect(point.lon, -71.9788);
      expect(point.lat, -13.5165);
    });

    test('traduce errores 422 Pydantic, 5xx y SocketException con mensaje claro', () async {
      final validationClient = ApiClient(
        baseUrl: AppConfig.productionBaseUrl,
        httpClient: MockClient((_) async {
          return http.Response(
            jsonEncode({
              'detail': [
                {'msg': 'Input should be greater than or equal to 2'}
              ]
            }),
            422,
          );
        }),
      );

      await expectLater(
        validationClient.postJson('/routes/solve', body: {}),
        throwsA(
          isA<ApiException>()
              .having((e) => e.kind, 'kind', ApiErrorKind.validation)
              .having((e) => e.message, 'message',
                  contains('greater than or equal to 2')),
        ),
      );

      final offlineLoopbackClient = ApiClient(
        baseUrl: 'http://127.0.0.1:8000',
        httpClient: MockClient((_) async {
          throw const SocketException('Connection refused');
        }),
      );

      await expectLater(
        offlineLoopbackClient.getJson('/health'),
        throwsA(
          isA<ApiException>()
              .having((e) => e.kind, 'kind', ApiErrorKind.offline)
              .having((e) => e.message, 'message', contains('localhost apunta al propio dispositivo')),
        ),
      );
    });

    test('RequestGuard descarta tokens vencidos', () {
      final guard = RequestGuard();
      final t1 = guard.nextToken();
      final t2 = guard.nextToken();
      expect(guard.isCurrent(t1), isFalse);
      expect(guard.isCurrent(t2), isTrue);
      guard.invalidateAll();
      expect(guard.isCurrent(t2), isFalse);
    });
  });
}
