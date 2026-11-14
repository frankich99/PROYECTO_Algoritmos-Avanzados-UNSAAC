import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../core/services/device_files_service.dart';
import '../../core/services/location_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_select_field.dart';
import '../../core/widgets/state_views.dart';
import '../../data/models/instance_models.dart';
import '../../data/models/route_models.dart';
import '../../data/repositories/conditions_repository.dart';
import '../../data/repositories/instance_repository.dart';
import '../../data/repositories/route_repository.dart';
import '../../data/repositories/server_repository.dart';
import 'widgets/conditions_panel.dart';
import 'widgets/cusco_map_view.dart';
import 'widgets/graph_canvas.dart';
import 'widgets/node_picker_sheet.dart';

class RoutesScreen extends StatefulWidget {
  const RoutesScreen({super.key});

  @override
  State<RoutesScreen> createState() => _RoutesScreenState();
}

class _RoutesScreenState extends State<RoutesScreen> {
  String _algorithm = 'dijkstra';
  String _queue = 'binary_heap';
  String _metric = 'time';

  Object? _selectedSource;
  Object? _selectedTarget;
  PointCoord? _sourcePoint;
  PointCoord? _targetPoint;

  String _pickMode = 'source';
  String _viewMode = 'grafo';
  bool _showNodes = true;
  bool _showNames = true;
  bool _showWeights = true;
  bool _showNetwork = true;
  bool _onlyRoute = false;
  bool _lockSelection = false;
  bool _gpsLoading = false;
  String? _gpsError;
  double? _gpsAccuracyM;
  String? _syncedInstanceKey;
  ConditionsSelection _conditions = const ConditionsSelection();

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final instRepo = context.read<InstanceRepository>();
    final active = instRepo.active;
    final preview = instRepo.lastPreview;
    final key = '${active?.title}|${preview?.nodes}|${preview?.edges}';
    if (_syncedInstanceKey != key) {
      _syncedInstanceKey = key;
      _syncDefaults(active, preview);
    }
  }

  void _syncDefaults(ActiveInstanceContext? active, InstancePreview? preview) {
    _sourcePoint = null;
    _targetPoint = null;
    _gpsError = null;
    _gpsAccuracyM = null;
    if (preview != null && preview.ids.isNotEmpty) {
      _selectedSource =
          _findMatchingId(preview.ids, active?.suggestedSource) ??
          preview.ids.first;
      _selectedTarget =
          _findMatchingId(preview.ids, active?.suggestedTarget) ??
          (preview.ids.length > 1 ? preview.ids.last : preview.ids.first);
      _viewMode = preview.geographic ? 'mapa' : 'grafo';
      _metric = preview.metric == 'distance' ? 'distance' : 'time';
    } else if (active?.editableGraph != null &&
        active!.editableGraph!.nodes.isNotEmpty) {
      final nodes = active.editableGraph!.nodes;
      _selectedSource = active.suggestedSource ?? nodes.first.id;
      _selectedTarget =
          active.suggestedTarget ??
          (nodes.length > 1 ? nodes.last.id : nodes.first.id);
      _viewMode = 'grafo';
      _metric = active.preferredMetric;
    } else {
      _selectedSource = active?.suggestedSource;
      _selectedTarget = active?.suggestedTarget;
      _viewMode = 'grafo';
    }
    _onlyRoute = false;
  }

  Object? _findMatchingId(List<Object> ids, Object? candidate) {
    if (candidate == null) return null;
    for (final id in ids) {
      if (id.toString() == candidate.toString()) return id;
    }
    return null;
  }

  Future<void> _selectQuickNetwork(String exampleId) async {
    final instRepo = context.read<InstanceRepository>();
    final found = instRepo.examples.where((e) => e.id == exampleId).toList();
    if (found.isEmpty) return;
    instRepo.selectBundledExample(found.first, validateRemote: false);
    final preview = await instRepo.validateActiveWithServer(metric: _metric);
    if (!mounted) return;
    setState(() {
      _syncDefaults(instRepo.active, preview);
    });
  }

  void _swapEndpoints() {
    setState(() {
      final tmpNode = _selectedSource;
      _selectedSource = _selectedTarget;
      _selectedTarget = tmpNode;

      final tmpPoint = _sourcePoint;
      _sourcePoint = _targetPoint;
      _targetPoint = tmpPoint;
    });
  }

  Future<void> _useMyLocation() async {
    setState(() {
      _gpsLoading = true;
      _gpsError = null;
    });
    try {
      final res = await context.read<LocationService>().getCurrentCuscoPoint();
      if (!mounted) return;
      setState(() {
        _sourcePoint = res.point;
        _selectedSource = null;
        _gpsAccuracyM = res.accuracyM;
        _gpsLoading = false;
      });
    } catch (err) {
      if (!mounted) return;
      setState(() {
        _gpsLoading = false;
        _gpsError = err.toString().replaceFirst('Bad state: ', '');
      });
    }
  }

  PointCoord _currentQueryPoint(InstancePreview? preview) {
    if (_sourcePoint != null) return _sourcePoint!;
    if (preview != null && preview.geographic && _selectedSource != null) {
      final pair = preview.coords[_selectedSource.toString()];
      if (pair != null && pair.length >= 2) {
        return PointCoord(lat: pair[1], lon: pair[0]);
      }
    }
    return const PointCoord(lat: -13.5165, lon: -71.9788);
  }

  Future<void> _solve() async {
    final instRepo = context.read<InstanceRepository>();
    final routeRepo = context.read<RouteRepository>();
    final condRepo = context.read<ConditionsRepository>();
    final active = instRepo.active;
    if (active == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Elige primero una instancia en Instancias.'),
        ),
      );
      return;
    }

    var preview = instRepo.lastPreview;
    preview ??= await instRepo.validateActiveWithServer(metric: _metric);

    final isAbstract =
        (preview?.metric ?? active.editableGraph?.metric) == 'weight';
    final isGeographic = preview?.geographic ?? false;
    final scenario = (!isAbstract && _metric == 'time')
        ? _conditions.toScenarioSpec(
            condRepo: condRepo,
            queryPoint: _currentQueryPoint(preview),
            isGeographic: isGeographic,
          )
        : const ScenarioSpec();

    final req = RouteRequest(
      instance: active.spec,
      metric: _metric,
      source: _sourcePoint == null ? _selectedSource : null,
      target: _targetPoint == null ? _selectedTarget : null,
      sourcePoint: _sourcePoint,
      targetPoint: _targetPoint,
      algorithm: _algorithm,
      queue: _queue,
      compare: true,
      scenario: scenario,
    );

    final solved = await routeRepo.solveRoute(req);
    if (!mounted || solved == null) return;
    setState(() {
      _selectedSource = solved.source;
      _selectedTarget = solved.target;
    });
  }

  Future<void> _saveRoute() async {
    final routeRepo = context.read<RouteRepository>();
    try {
      await routeRepo.saveCurrentRoute();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Resultado guardado en la base interna del dispositivo.',
          ),
        ),
      );
    } catch (err) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('No se pudo guardar: $err')));
    }
  }

  Future<void> _shareRoute() async {
    final routeRepo = context.read<RouteRepository>();
    final files = context.read<DeviceFilesService>();
    final resp = routeRepo.currentResponse;
    if (resp == null) return;
    try {
      final json = routeRepo.exportCurrentResultJson();
      await files.shareTextFile(
        filename: 'ruta_${resp.source}_a_${resp.target}.json',
        content: json,
        subject: 'Ruta ${resp.source} → ${resp.target} (${resp.network})',
      );
    } catch (err) {
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text('No se pudo compartir: $err')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final instRepo = context.watch<InstanceRepository>();
    final routeRepo = context.watch<RouteRepository>();
    final serverRepo = context.watch<ServerRepository>();

    final active = instRepo.active;
    final preview = instRepo.lastPreview;
    final route = routeRepo.currentResponse;
    final ids =
        preview?.ids ??
        active?.editableGraph?.nodes.map((n) => n.id).toList() ??
        const <Object>[];
    final isGeographic = preview?.geographic ?? false;
    final isAbstractWeights =
        (preview?.metric ?? active?.editableGraph?.metric) == 'weight';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Rutas en Cusco'),
        actions: [
          IconButton(
            tooltip: 'Elegir otra instancia',
            icon: const Icon(Icons.hub_outlined),
            onPressed: () => context.go('/instancias'),
          ),
        ],
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final twoPane = constraints.maxWidth >= 900;
          final controlsPane = _buildControlsCard(
            context,
            active: active,
            preview: preview,
            ids: ids,
            isGeographic: isGeographic,
            isAbstractWeights: isAbstractWeights,
            routeLoading: routeRepo.loading,
            slowWakeup: routeRepo.slowWakeup,
            urbanAvailable:
                serverRepo.catalog?.networks.any(
                  (n) => n.kind == 'urban' && n.available,
                ) ??
                false,
          );
          final mainPane = _buildVisualizationAndResults(
            context,
            instRepo: instRepo,
            routeRepo: routeRepo,
            preview: preview,
            route: route,
            isGeographic: isGeographic,
          );

          if (twoPane) {
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  width: 400,
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(16),
                    child: controlsPane,
                  ),
                ),
                const VerticalDivider(width: 1),
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(16),
                    child: mainPane,
                  ),
                ),
              ],
            );
          }

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [controlsPane, const SizedBox(height: 16), mainPane],
          );
        },
      ),
    );
  }

  Widget _buildControlsCard(
    BuildContext context, {
    required ActiveInstanceContext? active,
    required InstancePreview? preview,
    required List<Object> ids,
    required bool isGeographic,
    required bool isAbstractWeights,
    required bool routeLoading,
    required bool slowWakeup,
    required bool urbanAvailable,
  }) {
    final textScale = MediaQuery.textScalerOf(context).scale(1);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    active?.title ?? 'Sin instancia seleccionada',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                TextButton(
                  onPressed: () => context.go('/instancias'),
                  child: const Text('Cambiar'),
                ),
              ],
            ),
            if (active != null)
              Text(
                active.sourceDescription,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            const SizedBox(height: 10),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  ActionChip(
                    avatar: const Icon(Icons.location_city, size: 16),
                    label: const Text('Cusco OSM 1,5 km'),
                    onPressed: () => _selectQuickNetwork('osm_centro_1500m'),
                  ),
                  const SizedBox(width: 8),
                  if (urbanAvailable) ...[
                    ActionChip(
                      avatar: const Icon(Icons.map_outlined, size: 16),
                      label: const Text('Ampliada 3 km'),
                      onPressed: () =>
                          _selectQuickNetwork('osm_ampliado_3000m'),
                    ),
                    const SizedBox(width: 8),
                  ],
                  ActionChip(
                    avatar: const Icon(Icons.school_outlined, size: 16),
                    label: const Text('6 nodos Cusco'),
                    onPressed: () => _selectQuickNetwork('cusco_didactico_6'),
                  ),
                ],
              ),
            ),
            const Divider(height: 22),
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Origen y destino',
                    style: Theme.of(context).textTheme.titleSmall
                        ?.copyWith(fontWeight: FontWeight.w700),
                  ),
                ),
                TextButton.icon(
                  onPressed: _swapEndpoints,
                  icon: const Icon(Icons.swap_vert, size: 18),
                  label: const Text('Invertir'),
                ),
              ],
            ),
            const SizedBox(height: 6),
            _NodeSelectorTile(
              label: 'Origen',
              value: _sourcePoint != null
                  ? 'Coordenadas: ${_sourcePoint!.lat.toStringAsFixed(5)}, ${_sourcePoint!.lon.toStringAsFixed(5)}'
                  : (_selectedSource != null
                        ? 'Nodo $_selectedSource'
                        : 'Seleccionar origen'),
              accentColor: AppTheme.gold,
              onClearPoint: _sourcePoint != null
                  ? () => setState(() => _sourcePoint = null)
                  : null,
              onTap: ids.isEmpty
                  ? null
                  : () async {
                      final picked = await showNodePickerSheet(
                        context: context,
                        title: 'Seleccionar origen',
                        ids: ids,
                        current: _selectedSource,
                      );
                      if (picked != null && mounted) {
                        setState(() {
                          _selectedSource = picked;
                          _sourcePoint = null;
                        });
                      }
                    },
            ),
            const SizedBox(height: 10),
            _NodeSelectorTile(
              label: 'Destino',
              value: _targetPoint != null
                  ? 'Coordenadas: ${_targetPoint!.lat.toStringAsFixed(5)}, ${_targetPoint!.lon.toStringAsFixed(5)}'
                  : (_selectedTarget != null
                        ? 'Nodo $_selectedTarget'
                        : 'Seleccionar destino'),
              accentColor: AppTheme.maroon,
              onClearPoint: _targetPoint != null
                  ? () => setState(() => _targetPoint = null)
                  : null,
              onTap: ids.isEmpty
                  ? null
                  : () async {
                      final picked = await showNodePickerSheet(
                        context: context,
                        title: 'Seleccionar destino',
                        ids: ids,
                        current: _selectedTarget,
                      );
                      if (picked != null && mounted) {
                        setState(() {
                          _selectedTarget = picked;
                          _targetPoint = null;
                        });
                      }
                    },
            ),
            if (isGeographic) ...[
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _gpsLoading ? null : _useMyLocation,
                      icon: const Icon(Icons.my_location, size: 17),
                      label: Text(
                        _gpsLoading ? 'GPS…' : 'Mi ubicación',
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () {
                        setState(() {
                          _sourcePoint = const PointCoord(
                            lat: -13.5165,
                            lon: -71.9788,
                          );
                          _selectedSource = null;
                          _gpsError = null;
                        });
                      },
                      icon: const Icon(
                        Icons.account_balance_outlined,
                        size: 17,
                      ),
                      label: const Text(
                        'Centro Cusco',
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                ],
              ),
              if (_gpsAccuracyM != null)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    'GPS fijado (precisión ±${_gpsAccuracyM!.toStringAsFixed(0)} m).',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              if (_gpsError != null)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    _gpsError!,
                    style: const TextStyle(color: AppTheme.errorRed),
                  ),
                ),
            ],
            const Divider(height: 22),
            Text(
              'Algoritmo, cola y métrica',
              style: Theme.of(context).textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 10),
            if (textScale <= 1.2) ...[
              SizedBox(
                width: double.infinity,
                child: SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(
                      value: 'dijkstra',
                      label: Text('Dijkstra'),
                      icon: Icon(Icons.account_tree_outlined, size: 17),
                    ),
                    ButtonSegment(
                      value: 'astar',
                      label: Text('A* consistente'),
                      icon: Icon(Icons.explore_outlined, size: 17),
                    ),
                  ],
                  selected: {_algorithm},
                  onSelectionChanged: (s) =>
                      setState(() => _algorithm = s.first),
                ),
              ),
              const SizedBox(height: 10),
            ] else ...[
              AppSelectField<String>(
                label: 'Algoritmo',
                value: _algorithm,
                leadingIcon: Icons.account_tree_outlined,
                options: const [
                  SelectOption(
                    value: 'dijkstra',
                    label: 'Dijkstra',
                    subtitle: 'Garantiza optimalidad con pesos >= 0',
                  ),
                  SelectOption(
                    value: 'astar',
                    label: 'A* consistente',
                    subtitle: 'Poda mediante heurística euclidiana admisible',
                  ),
                ],
                onChanged: (v) => setState(() => _algorithm = v),
              ),
              const SizedBox(height: 10),
            ],
            AppSelectField<String>(
              label: 'Cola de prioridad',
              value: _queue,
              leadingIcon: Icons.layers_outlined,
              options: const [
                SelectOption(
                  value: 'binary_heap',
                  label: 'Binaria (Binary Heap)',
                  subtitle: 'O((V + E) log V) en peor caso',
                  icon: Icons.filter_2,
                ),
                SelectOption(
                  value: '4ary_heap',
                  label: '4-aria (D-ary Heap, d=4)',
                  subtitle: 'Menor altura de árbol y buena localidad',
                  icon: Icons.filter_4,
                ),
                SelectOption(
                  value: 'fibonacci_heap',
                  label: 'Fibonacci Heap',
                  subtitle: 'Decrease-Key O(1) amortizado',
                  icon: Icons.all_inclusive,
                ),
              ],
              onChanged: (v) => setState(() => _queue = v),
            ),
            const SizedBox(height: 10),
            AppSelectField<String>(
              label: 'Métrica de costo',
              value: _metric,
              leadingIcon: Icons.straighten_outlined,
              helperText: isAbstractWeights
                  ? 'Pesos abstractos: se calcula sobre «peso» sin unidad física.'
                  : null,
              options: const [
                SelectOption(
                  value: 'time',
                  label: 'Tiempo de viaje (segundos)',
                  subtitle: 'Permite ajustar clima y horario en redes viales',
                  icon: Icons.schedule,
                ),
                SelectOption(
                  value: 'distance',
                  label: 'Distancia vial (metros)',
                  subtitle: 'Longitud acumulada nominal sin factores',
                  icon: Icons.straighten,
                ),
              ],
              onChanged: (v) => setState(() => _metric = v),
            ),
            const SizedBox(height: 12),
            ConditionsPanel(
              selection: _conditions,
              onChanged: (next) => setState(() => _conditions = next),
              metric: _metric,
              isAbstractWeights: isAbstractWeights,
              isGeographic: isGeographic,
              queryPoint: _currentQueryPoint(preview),
            ),
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: routeLoading ? null : _solve,
                icon: routeLoading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.alt_route),
                label: Text(
                  routeLoading
                      ? (slowWakeup
                            ? 'Despertando servidor…'
                            : 'Calculando ruta…')
                      : 'Calcular y contrastar',
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVisualizationAndResults(
    BuildContext context, {
    required InstanceRepository instRepo,
    required RouteRepository routeRepo,
    required InstancePreview? preview,
    required RouteResponse? route,
    required bool isGeographic,
  }) {
    final canOnlyRoute = route?.result.path.isNotEmpty ?? false;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    if (isGeographic)
                      ChoiceChip(
                        label: const Text('Mapa'),
                        selected: _viewMode == 'mapa',
                        selectedColor: AppTheme.maroonSoft,
                        onSelected: (_) => setState(() => _viewMode = 'mapa'),
                      ),
                    ChoiceChip(
                      label: const Text('Grafo'),
                      selected: _viewMode == 'grafo',
                      selectedColor: AppTheme.maroonSoft,
                      onSelected: (_) => setState(() => _viewMode = 'grafo'),
                    ),
                    FilterChip(
                      label: const Text('Nodos'),
                      selected: _showNodes,
                      onSelected: (v) => setState(() => _showNodes = v),
                    ),
                    FilterChip(
                      label: const Text('Nombres/ID'),
                      selected: _showNames,
                      onSelected: (v) => setState(() => _showNames = v),
                    ),
                    FilterChip(
                      label: const Text('Red'),
                      selected: _showNetwork,
                      onSelected: (v) => setState(() => _showNetwork = v),
                    ),
                    FilterChip(
                      label: const Text('Pesos'),
                      selected: _showWeights,
                      onSelected: (v) => setState(() => _showWeights = v),
                    ),
                    FilterChip(
                      label: const Text('Solo recorrido'),
                      selected: _onlyRoute && canOnlyRoute,
                      onSelected: canOnlyRoute
                          ? (v) => setState(() => _onlyRoute = v)
                          : null,
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                if (preview == null)
                  SizedBox(
                    height: 200,
                    child: EmptyStateView(
                      icon: Icons.hub_outlined,
                      title: 'Sin vista previa validada',
                      message: 'Pulsa «Calcular y contrastar» o valida la instancia para dibujar los nodos y aristas.',
                      action: OutlinedButton(
                        onPressed: instRepo.validating
                            ? null
                            : () => instRepo.validateActiveWithServer(
                                metric: _metric,
                              ),
                        child: const Text('Validar ahora'),
                      ),
                    ),
                  )
                else if (_viewMode == 'mapa' && isGeographic)
                  CuscoMapView(
                    preview: preview,
                    route: route,
                    showNodes: _showNodes,
                    showNames: _showNames,
                    showWeights: _showWeights,
                    showNetwork: _showNetwork,
                    onlyRoute: _onlyRoute,
                    lockSelection: _lockSelection,
                    pickMode: _pickMode,
                    sourcePoint: _sourcePoint,
                    targetPoint: _targetPoint,
                    onPickModeChanged: (mode) =>
                        setState(() => _pickMode = mode),
                    onToggleLock: () =>
                        setState(() => _lockSelection = !_lockSelection),
                    onPickPoint: (point) {
                      setState(() {
                        if (_pickMode == 'source') {
                          _sourcePoint = point;
                          _selectedSource = null;
                        } else {
                          _targetPoint = point;
                          _selectedTarget = null;
                        }
                      });
                    },
                  )
                else
                  GraphCanvas(
                    preview: preview,
                    route: route,
                    showNodes: _showNodes,
                    showNames: _showNames,
                    showWeights: _showWeights,
                    showNetwork: _showNetwork,
                    onlyRoute: _onlyRoute,
                    lockSelection: _lockSelection,
                    pickMode: _pickMode,
                    onPickModeChanged: (mode) =>
                        setState(() => _pickMode = mode),
                    onToggleLock: () =>
                        setState(() => _lockSelection = !_lockSelection),
                    onPickNode: (nodeId) {
                      setState(() {
                        if (_pickMode == 'source') {
                          _selectedSource = nodeId;
                          _sourcePoint = null;
                        } else {
                          _selectedTarget = nodeId;
                          _targetPoint = null;
                        }
                      });
                    },
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        if (routeRepo.loading)
          LoadingStateView(
            title: 'Calculando ruta…',
            subtitle: 'Ejecutando Dijkstra (3 colas) y A* sobre la misma red.',
            showWakeupNotice: routeRepo.slowWakeup,
          )
        else if (routeRepo.errorMessage != null)
          ErrorStateBanner(
            message: routeRepo.errorMessage!,
            isOffline: routeRepo.isOfflineError,
            onRetry: _solve,
          )
        else if (route == null)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'Elige origen y destino y pulsa «Calcular y contrastar» para obtener costo, recorrido, comparación de colas y métricas.',
              ),
            ),
          )
        else
          _RouteResultCard(
            route: route,
            isSavedOffline: routeRepo.isSavedOfflineView,
            requestLatencyMs: routeRepo.lastRequestLatencyMs,
            onSave: _saveRoute,
            onShare: _shareRoute,
          ),
      ],
    );
  }
}

class _NodeSelectorTile extends StatelessWidget {
  const _NodeSelectorTile({
    required this.label,
    required this.value,
    required this.accentColor,
    this.onTap,
    this.onClearPoint,
  });

  final String label;
  final String value;
  final Color accentColor;
  final VoidCallback? onTap;
  final VoidCallback? onClearPoint;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: Icon(Icons.circle, size: 12, color: accentColor),
          suffixIcon: onClearPoint != null
              ? IconButton(
                  tooltip: 'Volver a elegir nodo por ID',
                  icon: const Icon(Icons.close, size: 18),
                  onPressed: onClearPoint,
                )
              : const Icon(Icons.search),
        ),
        child: Text(
          value,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            fontWeight: FontWeight.w600,
            fontFeatures: AppTheme.tabularFigures,
          ),
        ),
      ),
    );
  }
}

class _RouteResultCard extends StatelessWidget {
  const _RouteResultCard({
    required this.route,
    required this.isSavedOffline,
    required this.requestLatencyMs,
    required this.onSave,
    required this.onShare,
  });

  final RouteResponse route;
  final bool isSavedOffline;
  final int? requestLatencyMs;
  final VoidCallback onSave;
  final VoidCallback onShare;

  String _queueName(String q) {
    switch (q) {
      case 'binary_heap':
        return 'Binaria';
      case '4ary_heap':
        return '4-aria';
      case 'fibonacci_heap':
        return 'Fibonacci';
      default:
        return q;
    }
  }

  @override
  Widget build(BuildContext context) {
    final res = route.result;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              spacing: 8,
              runSpacing: 6,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Text(
                  'Resultado de la consulta',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                if (isSavedOffline)
                  const SavedDataBadge(
                    label: 'Resultado guardado · sin conexión',
                  ),
              ],
            ),
            const SizedBox(height: 8),
            if (route.warning != null) ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppTheme.warnBg,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  route.warning!,
                  style: const TextStyle(fontSize: 13, color: AppTheme.ink),
                ),
              ),
              const SizedBox(height: 10),
            ],
            if (!res.isReachable)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.warnBg,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: AppTheme.gold.withValues(alpha: 0.45),
                  ),
                ),
                child: const Text(
                  'No existe camino dirigido entre el origen y el destino seleccionados (costo: null). Revisa el sentido de las aristas o prueba otro destino.',
                ),
              )
            else ...[
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: [
                  _MetricTile(
                    label: 'Costo óptimo',
                    value: '${res.cost!.toStringAsFixed(2)} ${route.unit}',
                    highlight: true,
                  ),
                  if (res.lengthM != null)
                    _MetricTile(
                      label: 'Distancia',
                      value: '${res.lengthM!.toStringAsFixed(1)} m',
                    ),
                  if (res.timeSec != null)
                    _MetricTile(
                      label: 'Tiempo vial',
                      value: '${res.timeSec!.toStringAsFixed(2)} s',
                    ),
                  _MetricTile(label: 'Expandidos', value: '${res.expanded}'),
                  _MetricTile(
                    label: 'Relajaciones',
                    value: '${res.relaxations}',
                  ),
                  _MetricTile(
                    label: 'Decrease-Key',
                    value: '${res.decreaseKey}',
                  ),
                  _MetricTile(
                    label: 'Solver servidor',
                    value: '${res.elapsedMsSingleRun.toStringAsFixed(3)} ms',
                  ),
                  if (requestLatencyMs != null)
                    _MetricTile(
                      label: 'Solicitud total (red)',
                      value: '$requestLatencyMs ms',
                    ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                'Secuencia (${res.path.length} vértices, ${res.edges.length} aristas):',
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 4),
              SelectableText(
                res.path.join(' → '),
                style: const TextStyle(fontFeatures: AppTheme.tabularFigures),
              ),
            ],
            if (route.sourceSnap != null)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  'Origen ajustado al nodo ${route.sourceSnap!.node} (~${route.sourceSnap!.offsetMApprox} m).',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            if (route.targetSnap != null)
              Padding(
                padding: const EdgeInsets.only(top: 2),
                child: Text(
                  'Destino ajustado al nodo ${route.targetSnap!.node} (~${route.targetSnap!.offsetMApprox} m).',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            if ((route.scenario['kind']?.toString() ?? 'nominal') != 'nominal')
              Container(
                width: double.infinity,
                margin: const EdgeInsets.only(top: 10),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppTheme.goldSoft,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: AppTheme.gold.withValues(alpha: 0.4),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Escenario uniforme aplicado: factor ×${route.scenario['factor']}',
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 12.5,
                      ),
                    ),
                    if (route.scenario['weather_source'] != null)
                      Text(
                        'Clima: ${route.scenario['weather_source']} · ${route.scenario['weather_observed_at'] ?? ''} (factor ×${route.scenario['weather_factor']})',
                        style: const TextStyle(fontSize: 12),
                      ),
                    if (route.scenario['traffic_source'] != null)
                      Text(
                        'Tráfico: ${route.scenario['traffic_source']} · ${route.scenario['traffic_level'] ?? ''} (factor ×${route.scenario['traffic_factor']})',
                        style: const TextStyle(fontSize: 12),
                      ),
                  ],
                ),
              ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                if (!isSavedOffline)
                  FilledButton.icon(
                    onPressed: onSave,
                    icon: const Icon(Icons.bookmark_add_outlined, size: 18),
                    label: const Text('Guardar en biblioteca'),
                  ),
                OutlinedButton.icon(
                  onPressed: onShare,
                  icon: const Icon(Icons.share_outlined, size: 18),
                  label: const Text('Compartir JSON'),
                ),
              ],
            ),
            if (route.comparisons.isNotEmpty) ...[
              const SizedBox(height: 16),
              Text(
                'Comparación equivalente (4 ejecuciones)',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 6),
              for (final row in route.comparisons)
                ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  title: Text(
                    '${row.algorithm == 'astar' ? 'A*' : 'Dijkstra'} · ${_queueName(row.queue)}',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Text(
                    'Exp: ${row.expanded} · Relaj: ${row.relaxations} · DK: ${row.decreaseKey} · Solver: ${row.elapsedMsSingleRun.toStringAsFixed(3)} ms',
                    style: const TextStyle(
                      fontFeatures: AppTheme.tabularFigures,
                    ),
                  ),
                  trailing: Text(
                    row.cost == null
                        ? 'null'
                        : '${row.cost!.toStringAsFixed(2)} ${route.unit}',
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      color: AppTheme.maroon,
                      fontFeatures: AppTheme.tabularFigures,
                    ),
                  ),
                ),
            ],
            if (res.edges.isNotEmpty) ...[
              const SizedBox(height: 10),
              ExpansionTile(
                tilePadding: EdgeInsets.zero,
                title: Text(
                  'Vista en lista del recorrido (${res.edges.length} tramos)',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                children: [
                  for (var i = 0; i < res.edges.length; i++)
                    ListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      leading: Text(
                        '${i + 1}.',
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          fontFeatures: AppTheme.tabularFigures,
                        ),
                      ),
                      title: Text(
                        '${res.edges[i].from} → ${res.edges[i].to}${res.edges[i].street != null ? ' · ${res.edges[i].street}' : ''}',
                      ),
                      trailing: Text(
                        '${res.edges[i].cost.toStringAsFixed(2)} ${route.unit}',
                        style: const TextStyle(
                          fontFeatures: AppTheme.tabularFigures,
                        ),
                      ),
                    ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _MetricTile extends StatelessWidget {
  const _MetricTile({
    required this.label,
    required this.value,
    this.highlight = false,
  });

  final String label;
  final String value;
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: highlight ? AppTheme.maroonSoft : AppTheme.paper,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: highlight
              ? AppTheme.maroon.withValues(alpha: 0.4)
              : AppTheme.border,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(fontSize: 11.5, color: AppTheme.mutedInk),
          ),
          const SizedBox(height: 2),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.w700,
              color: highlight ? AppTheme.maroon : AppTheme.ink,
              fontFeatures: AppTheme.tabularFigures,
            ),
          ),
        ],
      ),
    );
  }
}
