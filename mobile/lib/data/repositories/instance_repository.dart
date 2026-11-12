import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/network/request_guard.dart';
import '../examples/example_catalog.dart';
import '../local/app_database.dart';
import '../models/editable_graph.dart';
import '../models/instance_models.dart';

class ActiveInstanceContext {
  const ActiveInstanceContext({
    required this.title,
    required this.spec,
    this.editableGraph,
    this.savedRecordId,
    this.suggestedSource,
    this.suggestedTarget,
    this.preferredMetric = 'time',
    this.sourceDescription = '',
  });

  final String title;
  final InstanceSpec spec;
  final EditableGraph? editableGraph;
  final String? savedRecordId;
  final Object? suggestedSource;
  final Object? suggestedTarget;
  final String preferredMetric;
  final String sourceDescription;
}

class InstanceRepository extends ChangeNotifier {
  InstanceRepository({
    required this.apiClient,
    required this.database,
    this.assetBundle,
  });

  final ApiClient apiClient;
  final AppDatabase database;
  final AssetBundle? assetBundle;
  final RequestGuard _guard = RequestGuard();

  List<BundledExample> _examples = const [];
  List<SavedInstanceRecord> _savedInstances = const [];
  ActiveInstanceContext? _active;
  InstancePreview? _lastPreview;
  bool _validating = false;
  bool _generating = false;
  String? _validationError;
  List<String> _localValidationErrors = const [];
  bool _initialized = false;

  List<BundledExample> get examples => _examples;
  List<SavedInstanceRecord> get savedInstances => _savedInstances;
  ActiveInstanceContext? get active => _active;
  InstancePreview? get lastPreview => _lastPreview;
  bool get validating => _validating;
  bool get generating => _generating;
  String? get validationError => _validationError;
  List<String> get localValidationErrors => _localValidationErrors;

  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;
    await Future.wait([
      _loadBundledExamples(),
      refreshSavedInstances(),
    ]);
    if (_active == null && _examples.isNotEmpty) {
      selectBundledExample(_examples.first, validateRemote: false);
    }
  }

  Future<void> _loadBundledExamples() async {
    _examples = await ExampleCatalogLoader.loadFromBundle(assetBundle);
    notifyListeners();
  }

  Future<void> refreshSavedInstances() async {
    _savedInstances = await database.listInstances();
    notifyListeners();
  }

  void selectBundledExample(
    BundledExample example, {
    bool validateRemote = false,
  }) {
    final graph = example.toEditableGraph();
    _active = ActiveInstanceContext(
      title: example.title,
      spec: example.toInstanceSpec(),
      editableGraph: graph,
      suggestedSource: example.suggestedSource,
      suggestedTarget: example.suggestedTarget,
      preferredMetric: example.metric == 'distance' ? 'distance' : 'time',
      sourceDescription: example.sourceInfo,
    );
    _localValidationErrors = graph?.validateLocally() ?? const [];
    _validationError = null;
    _lastPreview = null;
    notifyListeners();
    if (validateRemote) {
      validateActiveWithServer();
    }
  }

  /// Crea un borrador editable en SQLite local sin alterar el ejemplo original.
  Future<SavedInstanceRecord> duplicateExampleToDraft(
    BundledExample example,
  ) async {
    final graph = example.toEditableGraph();
    if (graph == null) {
      throw StateError(
        'Los snapshots OSM de solo lectura no se editan directamente en tabla.',
      );
    }
    final copyGraph = graph.copyWith(name: '${graph.name} (copia)');
    return saveDraftGraph(
      copyGraph,
      sourceKind: 'example_copy',
    );
  }

  Future<SavedInstanceRecord> saveDraftGraph(
    EditableGraph graph, {
    String? existingId,
    String sourceKind = 'draft',
    Map<String, dynamic>? generatorMeta,
    bool isValidServer = false,
  }) async {
    final now = DateTime.now().toUtc().toIso8601String();
    final id = existingId ?? 'inst_${DateTime.now().microsecondsSinceEpoch}';
    final record = SavedInstanceRecord(
      id: id,
      name: graph.name.trim().isEmpty ? 'Borrador sin nombre' : graph.name.trim(),
      sourceKind: sourceKind,
      format: 'json',
      metric: graph.isRoadBased ? graph.metric : 'weight',
      directed: graph.directed,
      payloadJson: graph.toPrettyJson(),
      generatorMetaJson: generatorMeta == null ? null : jsonEncode(generatorMeta),
      nodesCount: graph.nodes.length,
      edgesCount: graph.edges.length,
      isValidServer: isValidServer,
      createdAt: now,
      updatedAt: now,
    );
    await database.upsertInstance(record);
    await refreshSavedInstances();

    _active = ActiveInstanceContext(
      title: record.name,
      spec: InstanceSpec(kind: 'custom', data: graph.toJsonMap()),
      editableGraph: graph,
      savedRecordId: record.id,
      suggestedSource: graph.defaultSource ??
          (graph.nodes.isNotEmpty ? graph.nodes.first.id : null),
      suggestedTarget: graph.nodes.length > 1 ? graph.nodes.last.id : null,
      preferredMetric: record.metric == 'distance' ? 'distance' : 'time',
      sourceDescription: 'Guardado en base interna del dispositivo',
    );
    _localValidationErrors = graph.validateLocally();
    notifyListeners();
    return record;
  }

  void openSavedRecord(
    SavedInstanceRecord record, {
    bool validateRemote = false,
  }) {
    final graph = EditableGraph.fromJsonString(
      record.payloadJson,
      fallbackName: record.name,
    );
    _active = ActiveInstanceContext(
      title: record.name,
      spec: InstanceSpec(kind: 'custom', data: graph.toJsonMap()),
      editableGraph: graph,
      savedRecordId: record.id,
      suggestedSource: graph.defaultSource ??
          (graph.nodes.isNotEmpty ? graph.nodes.first.id : null),
      suggestedTarget: graph.nodes.length > 1 ? graph.nodes.last.id : null,
      preferredMetric: record.metric == 'distance' ? 'distance' : 'time',
      sourceDescription: 'Guardado localmente (${record.sourceKind})',
    );
    _localValidationErrors = graph.validateLocally();
    _validationError = null;
    _lastPreview = null;
    notifyListeners();
    if (validateRemote) {
      validateActiveWithServer();
    }
  }

  Future<void> deleteSavedRecord(String id) async {
    await database.deleteInstance(id);
    if (_active?.savedRecordId == id) {
      _active = ActiveInstanceContext(
        title: _active!.title,
        spec: _active!.spec,
        editableGraph: _active!.editableGraph,
        suggestedSource: _active!.suggestedSource,
        suggestedTarget: _active!.suggestedTarget,
        preferredMetric: _active!.preferredMetric,
        sourceDescription: 'Borrador eliminado de biblioteca',
      );
    }
    await refreshSavedInstances();
  }

  void updateActiveEditableGraph(EditableGraph updated) {
    _active = ActiveInstanceContext(
      title: updated.name,
      spec: InstanceSpec(kind: 'custom', data: updated.toJsonMap()),
      editableGraph: updated,
      savedRecordId: _active?.savedRecordId,
      suggestedSource: updated.defaultSource ??
          (updated.nodes.isNotEmpty ? updated.nodes.first.id : null),
      suggestedTarget:
          updated.nodes.length > 1 ? updated.nodes.last.id : null,
      preferredMetric:
          updated.isRoadBased && updated.metric == 'distance' ? 'distance' : 'time',
      sourceDescription: _active?.sourceDescription ?? 'Editor móvil',
    );
    _localValidationErrors = updated.validateLocally();
    _validationError = null;
    notifyListeners();
  }

  Future<InstancePreview?> validateActiveWithServer({String? metric}) async {
    final current = _active;
    if (current == null) return null;

    final token = _guard.nextToken();
    _validating = true;
    _validationError = null;
    notifyListeners();

    final queryMetric = metric ?? current.preferredMetric;
    try {
      final json = await apiClient.postJson(
        '/instances/validate',
        queryParameters: {'metric': queryMetric},
        body: current.spec.toJson(),
      );
      if (!_guard.isCurrent(token)) return null;
      final preview = InstancePreview.fromJson(json);
      _lastPreview = preview;
      _validating = false;
      _validationError = null;
      notifyListeners();
      return preview;
    } on ApiException catch (err) {
      if (!_guard.isCurrent(token)) return null;
      _validating = false;
      _validationError = err.message;
      _lastPreview = null;
      notifyListeners();
      return null;
    }
  }

  /// Genera una instancia oficial en FastAPI y la descarga completa (sin truncar
  /// aristas) vía `/instances/export`, guardándola en SQLite local con su semilla.
  Future<SavedInstanceRecord> generateOfficialAndSave({
    required String generator,
    required int seed,
    int nodes = 30,
    int rows = 5,
    int cols = 5,
  }) async {
    final token = _guard.nextToken();
    _generating = true;
    _validationError = null;
    notifyListeners();

    final spec = InstanceSpec(
      kind: 'generated',
      generator: generator,
      seed: seed,
      nodes: nodes,
      rows: rows,
      cols: cols,
    );

    try {
      final exportJson = await apiClient.postJson(
        '/instances/export',
        queryParameters: const {'metric': 'time'},
        body: spec.toJson(),
      );
      if (!_guard.isCurrent(token)) {
        throw const ApiException(
          kind: ApiErrorKind.cancelled,
          message: 'Generación reemplazada por otra solicitud.',
        );
      }

      final exported = ExportedInstance.fromJson(exportJson);
      final graph = EditableGraph.fromJsonMap(
        exported.instance,
        fallbackName: '${generator}_s$seed',
      );
      final meta = {
        'generator': generator,
        'generator_version': exported.generatorVersion,
        'seed': seed,
        if (generator == 'grid') ...{'rows': rows, 'cols': cols} else 'nodes': nodes,
      };
      final saved = await saveDraftGraph(
        graph,
        sourceKind: 'generated',
        generatorMeta: meta,
        isValidServer: true,
      );
      _generating = false;
      notifyListeners();
      return saved;
    } catch (err) {
      _generating = false;
      if (err is ApiException) {
        _validationError = err.message;
      }
      notifyListeners();
      rethrow;
    }
  }

  /// Obtiene el JSON completo exportable (desde el grafo en memoria o vía
  /// `/instances/export` para snapshots y otros tipos).
  Future<String> exportActiveCompleteJson() async {
    final current = _active;
    if (current == null) {
      throw StateError('No hay instancia activa para exportar.');
    }
    if (current.editableGraph != null) {
      return current.editableGraph!.toPrettyJson();
    }
    final json = await apiClient.postJson(
      '/instances/export',
      queryParameters: {'metric': current.preferredMetric},
      body: current.spec.toJson(),
    );
    final exported = ExportedInstance.fromJson(json);
    return const JsonEncoder.withIndent('  ').convert(exported.instance);
  }
}
