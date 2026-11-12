import 'package:flutter/material.dart';

import '../../core/widgets/state_views.dart';

class AnalysisScreen extends StatelessWidget {
  const AnalysisScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Comparar y experimentos')),
      body: const EmptyStateView(
        icon: Icons.analytics_outlined,
        title: 'Benchmark canónico, piloto y experimentos (Etapa 6)',
        message:
            'Mostrará las 1350 ejecuciones canónicas, el piloto de 18 tiempos y nuevos experimentos acotados en el backend.',
      ),
    );
  }
}
