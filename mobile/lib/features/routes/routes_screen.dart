import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';
import '../../core/widgets/state_views.dart';

class RoutesScreen extends StatelessWidget {
  const RoutesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Rutas en Cusco')),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final twoPane = constraints.maxWidth >= 840;
          final panel = Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'ETAPA 5 · PRÓXIMAMENTE',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.1,
                      color: AppTheme.maroon,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Consulta de rutas, Dijkstra y A*',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Aquí se conectarán las instancias validadas, la selección de origen/destino, las tres colas de prioridad, el escenario climático/horario y el lienzo interactivo.',
                  ),
                ],
              ),
            ),
          );

          final preview = const EmptyStateView(
            icon: Icons.map_outlined,
            title: 'Base móvil lista para rutas y mapas',
            message:
                'En las siguientes etapas se integrarán el catálogo de ejemplos, el grafo táctil y las redes OSM.',
          );

          if (twoPane) {
            return Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(width: 360, child: panel),
                  const SizedBox(width: 16),
                  Expanded(child: Card(child: preview)),
                ],
              ),
            );
          }

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              panel,
              const SizedBox(height: 16),
              Card(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(minHeight: 220),
                  child: preview,
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
