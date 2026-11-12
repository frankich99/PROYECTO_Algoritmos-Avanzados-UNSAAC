import 'package:flutter_test/flutter_test.dart';
import 'package:rutas_cusco_mobile/data/examples/example_catalog.dart';
import 'package:rutas_cusco_mobile/data/models/editable_graph.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('Carga el catálogo completo de ejemplos incluidos y valida casos válidos e inválidos', () async {
    final examples = await ExampleCatalogLoader.loadFromBundle();
    expect(examples.length, 16);

    final validEditable = examples.where((e) => e.validExpected && e.isEditable);
    expect(validEditable.length, 11);

    for (final ex in validEditable) {
      final graph = ex.toEditableGraph();
      expect(graph, isNotNull, reason: 'Ejemplo editable ${ex.id} debe parsearse');
      expect(
        graph!.validateLocally(),
        isEmpty,
        reason: 'Ejemplo válido ${ex.id} no debe tener errores locales',
      );
    }

    final invalidExamples = examples.where((e) => !e.validExpected).toList();
    expect(invalidExamples.length, 3);
    for (final bad in invalidExamples) {
      final graph = bad.toEditableGraph();
      expect(graph, isNotNull);
      expect(
        graph!.validateLocally(),
        isNotEmpty,
        reason: 'Ejemplo inválido ${bad.id} debe detectar errores locales',
      );
    }
  });

  test('Importar -> editar -> exportar -> reimportar conserva IDs mixtos y atributos viales', () {
    const rawJson = '''
    {
      "name": "Cusco mixto",
      "directed": true,
      "metric": "time",
      "source": 1001,
      "nodes": [
        {"id": 1001, "name": "Plaza", "lon": -71.9788, "lat": -13.5165},
        {"id": "B", "name": "Qorikancha", "lon": -71.9755, "lat": -13.5190}
      ],
      "edges": [
        {
          "origin": 1001,
          "destination": "B",
          "length_m": 450.0,
          "street_type": "calle_centro",
          "gradient_pct": -2.0,
          "street_name": "Calle Loreto"
        }
      ]
    }
    ''';

    final graph = EditableGraph.fromJsonString(rawJson);
    expect(graph.nodes[0].id, 1001);
    expect(graph.nodes[0].id, isA<int>());
    expect(graph.nodes[1].id, 'B');
    expect(graph.isRoadBased, isTrue);

    final edited = graph.copyWith(
      nodes: [...graph.nodes, const EditableNode(id: 'C', name: 'Limacpampa')],
      edges: [
        ...graph.edges,
        const EditableEdge(
          origin: 'B',
          destination: 'C',
          lengthM: 350,
          streetType: 'avenida',
          gradientPct: 0.5,
        ),
      ],
    );

    final exportedText = edited.toPrettyJson();
    final reimported = EditableGraph.fromJsonString(exportedText);

    expect(reimported.nodes.length, 3);
    expect(reimported.nodes[0].id, 1001);
    expect(reimported.nodes[0].id, isA<int>());
    expect(reimported.edges.length, 2);
    expect(reimported.edges[0].lengthM, 450.0);
    expect(reimported.edges[0].streetName, 'Calle Loreto');
    expect(reimported.edges[1].streetType, 'avenida');
  });

  test('Importa CSV/TXT con cabecera y directivas y permite reexportar', () {
    const csv = '''
# Prueba CSV
undirected
source N1
origen,destino,peso
N1,N2,4
N2,N3,2.5
node N4
''';
    final graph = EditableGraph.fromEdgeListText(csv, name: 'malla_csv');
    expect(graph.directed, isFalse);
    expect(graph.defaultSource, 'N1');
    expect(graph.nodes.map((n) => n.idText), ['N1', 'N2', 'N3', 'N4']);
    expect(graph.edges.length, 2);
    expect(graph.validateLocally(), isEmpty);

    final roundTrip = EditableGraph.fromEdgeListText(graph.toEdgeListText());
    expect(roundTrip.directed, isFalse);
    expect(roundTrip.nodes.length, 4);
    expect(roundTrip.edges.length, 2);
  });
}
