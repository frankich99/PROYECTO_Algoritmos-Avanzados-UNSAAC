import 'package:flutter_test/flutter_test.dart';
import 'package:rutas_cusco_mobile/data/models/evidence_models.dart';
import 'package:rutas_cusco_mobile/data/models/instance_models.dart';
import 'package:rutas_cusco_mobile/data/models/route_models.dart';
import 'package:rutas_cusco_mobile/data/repositories/docs_repository.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('DocsRepository carga evidencias, documentos y conserva autoría real de Git', () async {
    final docs = DocsRepository();
    await docs.initialize();

    expect(docs.evidence, isNotNull);
    expect(docs.evidence!.pythonPassed, greaterThan(0));
    expect(docs.evidence!.commits, isNotEmpty);
    expect(docs.evidence!.pilotRows, isNotEmpty);

    // Verifica que DeliveryCommit conserva el autor tal cual figura en el JSON.
    expect(docs.evidence!.commits.first.hash, isNotEmpty);
    expect(docs.evidence!.commits.first.author, isNotEmpty);

    final realAuthorCommit = DeliveryCommit.fromJson({
      'hash': 'abc1234',
      'date': '2026-11-12',
      'author': 'Noe Choquenaira',
      'subject': 'Prueba autor real',
    });
    expect(realAuthorCommit.author, 'Noe Choquenaira');

    for (final entry in DocsRepository.bundledDocs) {
      final text = docs.docContent(entry.id);
      expect(
        text,
        isNotNull,
        reason: 'Documento ${entry.id} debe cargarse offline',
      );
      expect(text!.trim().isNotEmpty, isTrue);
    }
    expect(
      DocsRepository.bundledDocs.map((entry) => entry.id),
      isNot(contains('bitacora_github')),
    );
    expect(docs.docContent('bitacora_github'), isNull);
  });

  test(
    'RouteRequest serializa escenarios climáticos y horarios según contrato',
    () {
      const req = RouteRequest(
        instance: InstanceSpec(kind: 'center'),
        metric: 'time',
        source: 1008097623,
        target: 995446309,
        algorithm: 'astar',
        queue: '4ary_heap',
        scenario: ScenarioSpec(
          weather: 'historical',
          trafficMode: 'simulated',
          trafficHour: 8.5,
        ),
      );
      final json = req.toJson();
      expect(json['source'], 1008097623);
      expect(json['algorithm'], 'astar');
      expect(json['queue'], '4ary_heap');
      final scen = json['scenario'] as Map<String, dynamic>;
      expect(scen['weather'], 'historical');
      expect(scen['traffic_mode'], 'simulated');
      expect(scen['traffic_hour'], 8.5);
    },
  );
}
