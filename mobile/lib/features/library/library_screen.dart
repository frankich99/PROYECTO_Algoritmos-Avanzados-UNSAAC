import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/services/device_files_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/responsive_data_view.dart';
import '../../core/widgets/state_views.dart';
import '../../data/local/app_database.dart';
import '../../data/repositories/docs_repository.dart';
import '../../data/repositories/instance_repository.dart';
import '../../data/repositories/route_repository.dart';
import 'widgets/reference_sections.dart';

class LibraryScreen extends StatefulWidget {
  const LibraryScreen({super.key});

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

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
    final instRepo = context.watch<InstanceRepository>();
    final routeRepo = context.watch<RouteRepository>();
    final docsRepo = context.watch<DocsRepository>();
    final files = context.read<DeviceFilesService>();
    final instances = instRepo.savedInstances;
    final routes = routeRepo.savedRoutes;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Biblioteca'),
        actions: [
          IconButton(
            tooltip: 'Recargar biblioteca local',
            icon: const Icon(Icons.refresh),
            onPressed: () {
              instRepo.refreshSavedInstances();
              routeRepo.refreshSavedRoutes();
            },
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          labelColor: AppTheme.maroon,
          indicatorColor: AppTheme.maroon,
          tabs: [
            Tab(text: 'Instancias (${instances.length})'),
            Tab(text: 'Rutas (${routes.length})'),
            const Tab(text: 'Referencia'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          instances.isEmpty
              ? EmptyStateView(
                  icon: Icons.bookmarks_outlined,
                  title: 'Sin borradores guardados aún',
                  message: 'Duplica un ejemplo, importa un archivo o guarda un grafo. Tus borradores quedan en este dispositivo.',
                  action: FilledButton.icon(
                    onPressed: () => context.go('/instancias'),
                    icon: const Icon(Icons.hub_outlined),
                    label: const Text('Ir a Instancias'),
                  ),
                )
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: instances.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final record = instances[index];
                    final isSelected =
                        instRepo.active?.savedRecordId == record.id;
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
                                    label: 'Validado en el servidor',
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
                                    instRepo.openSavedRecord(record);
                                    context.go('/instancias');
                                  },
                                  icon: const Icon(
                                    Icons.edit_outlined,
                                    size: 18,
                                  ),
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
                                  icon: const Icon(
                                    Icons.share_outlined,
                                    size: 18,
                                  ),
                                  label: const Text('Compartir JSON'),
                                ),
                                OutlinedButton.icon(
                                  onPressed: () async {
                                    await instRepo.deleteSavedRecord(record.id);
                                    if (context.mounted) {
                                      ScaffoldMessenger.of(context)
                                          .showSnackBar(
                                            const SnackBar(
                                              content: Text(
                                                'Instancia eliminada del dispositivo.',
                                              ),
                                            ),
                                          );
                                    }
                                  },
                                  icon: const Icon(
                                    Icons.delete_outline,
                                    size: 18,
                                  ),
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
          routes.isEmpty
              ? EmptyStateView(
                  icon: Icons.alt_route_outlined,
                  title: 'Sin rutas guardadas aún',
                  message: 'Calcula una ruta y pulsa «Guardar en biblioteca» para consultarla después incluso sin conexión a Internet.',
                  action: FilledButton.icon(
                    onPressed: () => context.go('/rutas'),
                    icon: const Icon(Icons.alt_route),
                    label: const Text('Ir a Rutas'),
                  ),
                )
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: routes.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final r = routes[index];
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SavedDataBadge(
                              label: 'Resultado guardado · sin conexión',
                            ),
                            const SizedBox(height: 8),
                            Text(
                              r.title,
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              r.cost == null
                                  ? '${r.instanceName} · Sin camino dirigido (null)'
                                  : '${r.instanceName} · Costo: ${r.cost!.toStringAsFixed(2)} ${r.unit}',
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                            const SizedBox(height: 10),
                            Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: [
                                FilledButton.icon(
                                  onPressed: () {
                                    routeRepo.openSavedRoute(r);
                                    context.go('/rutas');
                                  },
                                  icon: const Icon(
                                    Icons.visibility_outlined,
                                    size: 18,
                                  ),
                                  label: const Text('Ver en Rutas'),
                                ),
                                OutlinedButton.icon(
                                  onPressed: () async {
                                    await files.shareTextFile(
                                      filename:
                                          'ruta_${r.sourceLabel}_${r.targetLabel}.json',
                                      content: r.responseJson,
                                      subject: r.title,
                                    );
                                  },
                                  icon: const Icon(
                                    Icons.share_outlined,
                                    size: 18,
                                  ),
                                  label: const Text('Compartir JSON'),
                                ),
                                OutlinedButton.icon(
                                  onPressed: () async {
                                    await routeRepo.deleteSavedRoute(r.id);
                                    if (context.mounted) {
                                      ScaffoldMessenger.of(
                                        context,
                                      ).showSnackBar(
                                        const SnackBar(
                                          content: Text(
                                            'Ruta eliminada del dispositivo.',
                                          ),
                                        ),
                                      );
                                    }
                                  },
                                  icon: const Icon(
                                    Icons.delete_outline,
                                    size: 18,
                                  ),
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
          _OfflineDocsTab(docsRepo: docsRepo, files: files),
        ],
      ),
    );
  }
}

class _OfflineDocsTab extends StatelessWidget {
  const _OfflineDocsTab({required this.docsRepo, required this.files});

  final DocsRepository docsRepo;
  final DeviceFilesService files;

  void _openDocSheet(BuildContext context, BundledDocEntry entry) {
    final text = docsRepo.docContent(entry.id) ?? 'Documento no disponible.';
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.85,
        minChildSize: 0.5,
        maxChildSize: 0.96,
        builder: (context, controller) => Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 8, 8),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          entry.title,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        Text(
                          'Actualizado: ${entry.updatedLabel}',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    tooltip: 'Compartir documento',
                    icon: const Icon(Icons.share_outlined),
                    onPressed: () => files.shareTextFile(
                      filename: '${entry.id}.md',
                      content: text,
                      subject: entry.title,
                    ),
                  ),
                  IconButton(
                    tooltip: 'Cerrar documento',
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: SingleChildScrollView(
                controller: controller,
                padding: const EdgeInsets.all(16),
                child: SelectableText(
                  text,
                  style: const TextStyle(fontSize: 13.5, height: 1.45),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const SavedDataBadge(label: 'Referencia incluida · sin conexión'),
        const SizedBox(height: 12),
        ReferenceSections(docs: docsRepo),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Complejidad temporal y espacial',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 6),
                const Text(
                  'V = vértices, E = aristas, n = elementos en cola. Se separa el núcleo algorítmico de la reconstrucción de caminos.',
                ),
                const SizedBox(height: 8),
                const ResponsiveDataView(
                  headers: [
                    'Cola',
                    'Insertar',
                    'Extraer mín.',
                    'Decrease-Key',
                    'Tipo de cota',
                  ],
                  rows: [
                    ResponsiveRowItem(
                      title: 'Cola Binaria',
                      badge: 'Peor caso',
                      mobileColumns: [1, 2, 3],
                      cells: [
                        'Binaria',
                        'O(log n)',
                        'O(log n)',
                        'O(log n)',
                        'Peor caso',
                      ],
                    ),
                    ResponsiveRowItem(
                      title: 'Cola 4-aria (d = 4)',
                      badge: 'Peor caso',
                      mobileColumns: [1, 2, 3],
                      cells: [
                        '4-aria',
                        'O(log₄ n)',
                        'O(4 log₄ n)',
                        'O(log₄ n)',
                        'Peor caso',
                      ],
                    ),
                    ResponsiveRowItem(
                      title: 'Fibonacci Heap',
                      badge: 'Amortizada',
                      mobileColumns: [1, 2, 3],
                      cells: [
                        'Fibonacci',
                        'O(1)',
                        'O(log n)',
                        'O(1)',
                        'Amortizada',
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                const Text(
                  '• Dijkstra binario/4-ario: O((V + E) log V), espacio O(V).\n'
                  '• Dijkstra Fibonacci: O(E + V log V) amortizado, espacio O(V).\n'
                  '• A* consistente: misma cota según cola; si h = 0 no obtiene ventaja heurística.\n'
                  '• Grafo en memoria: O(V + E). Reconstruir todos los caminos puede requerir O(V²).',
                  style: TextStyle(fontSize: 13, height: 1.4),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Modelo de costos y límites',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 6),
                const Text(
                  '• Penalización por pendiente positiva: 1 + 2.5 × max(0, pendiente % / 100).\n'
                  '• Jerarquía ilustrativa: avenida 35 km/h, calle_centro 15 km/h, peatonal 8 km/h.\n'
                  '• Los grafos de pesos genéricos muestran «peso» y no acreditan segundos ni metros.\n'
                  '• Clima y tráfico aplican un factor uniforme sobre toda la red: alteran el costo total, pero preservan la ruta óptima nominal.',
                  style: TextStyle(fontSize: 13, height: 1.4),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Documentos técnicos incluidos',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 6),
                for (final doc in DocsRepository.bundledDocs)
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(
                      Icons.description_outlined,
                      color: AppTheme.maroon,
                    ),
                    title: Text(doc.title),
                    subtitle: Text('${doc.subtitle} · ${doc.updatedLabel}'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => _openDocSheet(context, doc),
                  ),
                const Divider(),
                const ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(
                    Icons.picture_as_pdf_outlined,
                    color: AppTheme.maroon,
                  ),
                  title: Text('Informe final UNSAAC'),
                  subtitle: Text(
                    'PDF incluido. Usa un visor del teléfono para leerlo.',
                  ),
                ),
                Align(
                  alignment: Alignment.centerLeft,
                  child: FilledButton.tonalIcon(
                    onPressed: () => files.shareAssetBinary(
                      assetPath: 'assets/docs/informe_final_unsaac.pdf',
                      outputFilename: 'informe_final_unsaac.pdf',
                      subject: 'Informe final UNSAAC - Rutas mínimas en Cusco',
                    ),
                    icon: const Icon(Icons.share_outlined, size: 18),
                    label: const Text('Compartir PDF'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
