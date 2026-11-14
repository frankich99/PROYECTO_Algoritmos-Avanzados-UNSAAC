import 'package:flutter/material.dart';

import '../../../core/widgets/responsive_data_view.dart';
import '../../../data/repositories/docs_repository.dart';

class ReferenceSections extends StatelessWidget {
  const ReferenceSections({super.key, required this.docs});

  final DocsRepository docs;

  @override
  Widget build(BuildContext context) {
    final evidence = docs.evidence;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const ExpansionTile(
          tilePadding: EdgeInsets.zero,
          childrenPadding: EdgeInsets.only(bottom: 16),
          expandedCrossAxisAlignment: CrossAxisAlignment.start,
          title: Text('Cobertura de los mapas'),
          subtitle: Text('Alcance de las redes incluidas'),
          children: [
            Text(
              'Centro de Cusco: radio de 1,5 km alrededor de '
              '(-13.5165, -71.9788), 891 nodos y 2139 aristas. '
              'Snapshot OpenStreetMap del 28/10/2026.\n\n'
              'Red ampliada: radio de 3 km recortado por distancia de red, '
              '1938 nodos y 4753 aristas. Snapshot del 10/08/2026, '
              'con cobertura revisada.\n\n'
              'No representan toda la provincia. Las velocidades son '
              'supuestos del modelo, no mediciones de tráfico real.',
            ),
          ],
        ),
        ExpansionTile(
          tilePadding: EdgeInsets.zero,
          childrenPadding: const EdgeInsets.only(bottom: 16),
          expandedCrossAxisAlignment: CrossAxisAlignment.start,
          title: const Text('Verificación académica'),
          subtitle: const Text(
            'Registro histórico de pruebas y piloto de revisión',
          ),
          children: [
            if (evidence == null)
              const Text(
                'No se pudo cargar el registro incluido. Los documentos siguen disponibles.',
              )
            else ...[
              Text(
                'Registro incluido: ${evidence.generatedAtUtc}. '
                'No corresponde a una prueba ejecutada ahora en el teléfono.',
              ),
              const SizedBox(height: 8),
              Text(
                'Python: ${evidence.pythonPassed} pruebas aprobadas, '
                '${evidence.pythonFailed} fallidas. '
                'Web: ${evidence.webPassed} de ${evidence.webTotal} aprobadas. '
                'Estos conteos no son porcentajes de cobertura de código.',
              ),
              const SizedBox(height: 16),
              Text(
                'Piloto de revisión (120 tiempos)',
                style: Theme.of(context).textTheme.titleSmall,
              ),
              const SizedBox(height: 6),
              Text(
                'Medido: ${evidence.pilotGeneratedAtUtc}. '
                'Es un registro distinto del banco canónico y del piloto histórico de Análisis.',
              ),
              const SizedBox(height: 12),
              ResponsiveDataView(
                headers: const [
                  'Perfil',
                  'V / E',
                  'Cola',
                  'Mediana (µs)',
                  'Muestras',
                ],
                rows: [
                  for (final row in evidence.pilotRows)
                    ResponsiveRowItem(
                      title:
                          '${row.profile == 'sparse' ? 'Disperso' : 'Denso'} · ${row.nodes} nodos',
                      cells: [
                        row.profile == 'sparse' ? 'Disperso' : 'Denso',
                        '${row.nodes} / ${row.edges}',
                        row.queue,
                        row.medianUs.toStringAsFixed(2),
                        '${row.sampleCount}',
                      ],
                    ),
                ],
              ),
            ],
          ],
        ),
      ],
    );
  }
}
