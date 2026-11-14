import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/services/device_files_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/state_views.dart';
import '../../data/examples/example_catalog.dart';
import '../../data/models/editable_graph.dart';
import '../../data/repositories/instance_repository.dart';
import '../../data/repositories/server_repository.dart';
import 'widgets/editor_tab.dart';
import 'widgets/examples_tab.dart';
import 'widgets/import_generate_tab.dart';

class InstancesScreen extends StatefulWidget {
  const InstancesScreen({super.key});

  @override
  State<InstancesScreen> createState() => _InstancesScreenState();
}

class _InstancesScreenState extends State<InstancesScreen>
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

  void _showSnack(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _selectAndValidate(BundledExample ex) async {
    final repo = context.read<InstanceRepository>();
    repo.selectBundledExample(ex, validateRemote: false);
    final preview = await repo.validateActiveWithServer();
    if (!mounted) return;
    if (preview != null) {
      _showSnack(
        'Validada en el servidor: ${preview.nodes} nodos, ${preview.edges} aristas.',
      );
    } else if (repo.validationError != null) {
      _showSnack('Validación: ${repo.validationError}');
    }
  }

  Future<void> _duplicateToDraft(BundledExample ex) async {
    final repo = context.read<InstanceRepository>();
    await repo.duplicateExampleToDraft(ex);
    if (!mounted) return;
    _tabController.animateTo(1);
    _showSnack('Copia guardada como borrador en el dispositivo.');
  }

  Future<void> _saveCurrentDraft() async {
    final repo = context.read<InstanceRepository>();
    final active = repo.active;
    final graph = active?.editableGraph;
    if (graph == null) return;
    await repo.saveDraftGraph(
      graph,
      existingId: active?.savedRecordId,
      isValidServer: repo.lastPreview != null && repo.validationError == null,
    );
    _showSnack('Borrador guardado en la base interna del dispositivo.');
  }

  Future<void> _validateCurrent() async {
    final repo = context.read<InstanceRepository>();
    final preview = await repo.validateActiveWithServer();
    if (!mounted) return;
    if (preview != null) {
      _showSnack(
        'Válida en el servidor (${preview.nodes} nodos, ${preview.edges} aristas).',
      );
    }
  }

  Future<void> _exportAndShareCurrent() async {
    final repo = context.read<InstanceRepository>();
    final files = context.read<DeviceFilesService>();
    try {
      final jsonText = await repo.exportActiveCompleteJson();
      final title = repo.active?.title ?? 'instancia_cusco';
      if (!mounted) return;
      final choice = await showModalBottomSheet<String>(
        context: context,
        builder: (context) => SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.share_outlined),
                title: const Text('Compartir archivo JSON completo'),
                subtitle: const Text(
                  'Conserva todas las aristas, tipos de ID y atributos viales',
                ),
                onTap: () => Navigator.pop(context, 'share'),
              ),
              ListTile(
                leading: const Icon(Icons.copy_outlined),
                title: const Text('Copiar JSON al portapapeles'),
                onTap: () => Navigator.pop(context, 'copy'),
              ),
            ],
          ),
        ),
      );
      if (choice == 'share') {
        await files.shareTextFile(
          filename: '$title.json',
          content: jsonText,
          subject: 'Instancia: $title',
        );
      } else if (choice == 'copy') {
        await files.copyToClipboard(jsonText);
        _showSnack('JSON completo copiado al portapapeles.');
      }
    } catch (err) {
      _showSnack('No se pudo exportar: $err');
    }
  }

  Future<void> _onImportParsed(EditableGraph graph, String sourceKind) async {
    final repo = context.read<InstanceRepository>();
    await repo.saveDraftGraph(graph, sourceKind: 'imported_$sourceKind');
    if (!mounted) return;
    _tabController.animateTo(1);
    _showSnack('Instancia importada y guardada en tu biblioteca local.');
  }

  Future<void> _onGenerateOfficial({
    required String generator,
    required int seed,
    required int nodes,
    required int rows,
    required int cols,
  }) async {
    final repo = context.read<InstanceRepository>();
    try {
      final saved = await repo.generateOfficialAndSave(
        generator: generator,
        seed: seed,
        nodes: nodes,
        rows: rows,
        cols: cols,
      );
      if (!mounted) return;
      _tabController.animateTo(1);
      _showSnack(
        'Red generada (${saved.nodesCount} nodos, ${saved.edgesCount} aristas) con semilla $seed.',
      );
    } catch (err) {
      _showSnack('No se pudo generar: $err');
    }
  }

  @override
  Widget build(BuildContext context) {
    final repo = context.watch<InstanceRepository>();
    final serverRepo = context.watch<ServerRepository>();
    final files = context.read<DeviceFilesService>();
    final active = repo.active;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Instancias y ejemplos'),
        actions: [
          IconButton(
            tooltip: 'Crear grafo nuevo vacío',
            icon: const Icon(Icons.add_box_outlined),
            onPressed: () async {
              const blank = EditableGraph(
                name: 'Nuevo grafo',
                directed: true,
                metric: 'weight',
                nodes: [
                  EditableNode(id: 'A'),
                  EditableNode(id: 'B'),
                ],
                edges: [EditableEdge(origin: 'A', destination: 'B', weight: 1)],
              );
              await repo.saveDraftGraph(blank, sourceKind: 'draft');
              if (!mounted) return;
              _tabController.animateTo(1);
            },
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: AppTheme.maroon,
          indicatorColor: AppTheme.maroon,
          tabs: const [
            Tab(text: 'Ejemplos'),
            Tab(text: 'Editor'),
            Tab(text: 'Importar / Generar'),
          ],
        ),
      ),
      body: Column(
        children: [
          if (active != null) _ActiveInstanceSummary(repo: repo),
          if (repo.validationError != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
              child: ErrorStateBanner(
                message: repo.validationError!,
                onRetry: _validateCurrent,
              ),
            ),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                ExamplesTab(
                  examples: repo.examples,
                  activeTitle: active?.title,
                  onSelectExample: _selectAndValidate,
                  onDuplicateToDraft: _duplicateToDraft,
                ),
                EditorTab(
                  graph: active?.editableGraph,
                  localErrors: repo.localValidationErrors,
                  onChanged: repo.updateActiveEditableGraph,
                  onSaveDraft: _saveCurrentDraft,
                  onValidateServer: _validateCurrent,
                  onExportJson: _exportAndShareCurrent,
                ),
                ImportGenerateTab(
                  limits: serverRepo.limits,
                  generating: repo.generating,
                  onImportParsed: _onImportParsed,
                  onPickFile: () async {
                    final picked = await files.pickGraphFile();
                    return picked?.content;
                  },
                  onGenerateOfficial: _onGenerateOfficial,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ActiveInstanceSummary extends StatelessWidget {
  const _ActiveInstanceSummary({required this.repo});

  final InstanceRepository repo;

  @override
  Widget build(BuildContext context) {
    final active = repo.active!;
    final preview = repo.lastPreview;
    final graph = active.editableGraph;
    final nodesCount = preview?.nodes ?? graph?.nodes.length;
    final edgesCount = preview?.edges ?? graph?.edges.length;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: const BoxDecoration(
        color: AppTheme.surfaceWhite,
        border: Border(bottom: BorderSide(color: AppTheme.border)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Activa: ${active.title}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    color: AppTheme.ink,
                  ),
                ),
                Text(
                  [
                    if (nodesCount != null && edgesCount != null)
                      '$nodesCount nodos · $edgesCount aristas',
                    if (preview != null)
                      'Validada en el servidor (${preview.metric})'
                    else
                      'Sin validar en servidor aún',
                  ].join(' · '),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          if (repo.validating)
            const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: AppTheme.maroon,
              ),
            )
          else
            TextButton(
              onPressed: () => repo.validateActiveWithServer(),
              child: const Text('Validar'),
            ),
        ],
      ),
    );
  }
}
