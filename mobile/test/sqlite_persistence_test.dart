import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:rutas_cusco_mobile/core/network/api_client.dart';
import 'package:rutas_cusco_mobile/data/local/app_database.dart';
import 'package:rutas_cusco_mobile/data/repositories/instance_repository.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  sqfliteFfiInit();

  test('SQLite interno guarda copias editables, redes generadas completas y sobrevive recarga', () async {
    final db = AppDatabase(
      factory: databaseFactoryFfi,
      customPath: inMemoryDatabasePath,
    );
    addTearDown(db.close);

    final mockClient = ApiClient(
      baseUrl: 'https://rutas-cusco-unsaac.onrender.com',
      httpClient: MockClient((request) async {
        if (request.url.path == '/api/v1/instances/export') {
          return http.Response(
            jsonEncode({
              'format': 'rutas-cusco-instance-v1',
              'api_version': '1.5.0',
              'generator_version': '1.0.0',
              'nodes': 5,
              'edges': 8,
              'metric': 'weight',
              'instance': {
                'name': 'sparse_n5_m8_s0',
                'directed': true,
                'metric': 'weight',
                'source': 'N0',
                'nodes': ['N0', 'N1', 'N2', 'N3', 'N4'],
                'edges': [
                  {'origin': 'N0', 'destination': 'N1', 'weight': 10},
                  {'origin': 'N1', 'destination': 'N2', 'weight': 12},
                  {'origin': 'N2', 'destination': 'N3', 'weight': 14},
                  {'origin': 'N3', 'destination': 'N4', 'weight': 16},
                  {'origin': 'N0', 'destination': 'N2', 'weight': 25},
                  {'origin': 'N1', 'destination': 'N3', 'weight': 30},
                  {'origin': 'N2', 'destination': 'N4', 'weight': 35},
                  {'origin': 'N0', 'destination': 'N4', 'weight': 70},
                ],
                'metadata': {
                  'generator': 'sparse',
                  'generator_version': '1.0.0',
                  'seed': 0,
                  'nodes': 5,
                },
              },
            }),
            200,
          );
        }
        return http.Response('{}', 404);
      }),
    );

    final repo = InstanceRepository(apiClient: mockClient, database: db);
    await repo.initialize();

    final cusco = repo.examples.firstWhere((e) => e.id == 'cusco_didactico_6');
    final copy = await repo.duplicateExampleToDraft(cusco);
    expect(copy.sourceKind, 'example_copy');
    expect(copy.nodesCount, 6);
    expect(copy.edgesCount, 9);

    final generated = await repo.generateOfficialAndSave(
      generator: 'sparse',
      seed: 0,
      nodes: 5,
    );
    expect(generated.sourceKind, 'generated');
    expect(generated.nodesCount, 5);
    expect(generated.edgesCount, 8);
    expect(generated.isValidServer, isTrue);
    expect(generated.generatorMetaJson, contains('"seed":0'));

    // Simula reapertura de la app leyendo desde la misma BD SQLite local.
    final repoReloaded = InstanceRepository(apiClient: mockClient, database: db);
    await repoReloaded.initialize();
    expect(repoReloaded.savedInstances.length, 2);

    await repoReloaded.deleteSavedRecord(copy.id);
    expect(repoReloaded.savedInstances.length, 1);
  });
}
