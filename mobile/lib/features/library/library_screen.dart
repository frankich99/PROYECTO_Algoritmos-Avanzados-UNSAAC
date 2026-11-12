import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/services/device_files_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/state_views.dart';
import '../../data/local/app_database.dart';
import '../../data/repositories/instance_repository.dart';

class LibraryScreen extends StatelessWidget {
  const LibraryScreen({super.key});

  String _sourceLabel(SavedInstanceRecord r) {
    if (r.generatorMetaJson != null) {
      try {
        final meta = jsonDecode(r.generatorMetaJson!) as Map<String, dynamic>;
        return 'Generado (${meta['generator']} · semilla ${meta['seed']})';
      } catch (_) {}
    }
    if (r.sourceKind == 'example_copy') return 'Copia editable de ejemplo';
    if (r.sourceKind.startsWith('imported')) return 'Archivo / texto importado';
    return 'Borrador local';
  }

  @override
  Widget build(BuildContext context) {
    final repo = context.watch<InstanceRepository>();
    final files = context.read<DeviceFilesService>();
    final items = repo.savedInstances;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Biblioteca del dispositivo'),
        actions: [
          IconButton(
            tooltip: 'Recargar biblioteca local',
            icon: const Icon(Icons.refresh),
            onPressed: repo.refreshSavedInstances,
          ),
        ],
      ),
      body: items.isEmpty
          ? EmptyStateView(
              icon: Icons.bookmarks_outlined,
              title: 'Sin borradores guardados aún',
              message:
                  'Todo se guarda en la base interna SQLite del dispositivo (sin servidor externo). Duplica un ejemplo, importa un archivo o genera una red para verla aquí.',
              action: FilledButton.icon(
                onPressed: () => context.go('/instancias'),
                icon: const Icon(Icons.hub_outlined),
                label: const Text('Ir a Instancias'),
              ),
            )
          : ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: items.length,
              separatorBuilder: (_, _) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final record = items[index];
                final isSelected = repo.active?.savedRecordId == record.id;
                return Card(
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(
                      color: isSelected ? AppTheme.gold : AppTheme.border,
                      width: isSelected ? 2 : 1,
                    ),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Wrap(
                          spacing: 8,
                          runSpacing: 6,
                          children: [
                            SavedDataBadge(label: _sourceLabel(record)),
                            if (record.isValidServer)
                              const SavedDataBadge(
                                label: 'Validado en FastAPI',
                              ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          record.name,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${record.nodesCount} vértices · ${record.edgesCount} aristas · ${record.directed ? 'Dirigido' : 'No dirigido'} · Métrica ${record.metric}',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                        const SizedBox(height: 10),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            FilledButton.icon(
                              onPressed: () {
                                repo.openSavedRecord(record);
                                context.go('/instancias');
                              },
                              icon: const Icon(Icons.edit_outlined, size: 18),
                              label: const Text('Abrir en Editor'),
                            ),
                            OutlinedButton.icon(
                              onPressed: () async {
                                await files.shareTextFile(
                                  filename: '${record.name}.json',
                                  content: record.payloadJson,
                                  subject: 'Instancia ${record.name}',
                                );
                              },
                              icon: const Icon(Icons.share_outlined, size: 18),
                              label: const Text('Compartir JSON'),
                            ),
                            OutlinedButton.icon(
                              onPressed: () async {
                                await repo.deleteSavedRecord(record.id);
                                if (context.mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text(
                                        'Instancia eliminada del dispositivo.',
                                      ),
                                    ),
                                  );
                                }
                              },
                              icon: const Icon(Icons.delete_outline, size: 18),
                              label: const Text('Eliminar'),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}
