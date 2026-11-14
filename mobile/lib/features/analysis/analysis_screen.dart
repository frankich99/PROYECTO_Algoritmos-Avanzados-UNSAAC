import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/services/device_files_service.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/app_select_field.dart';
import '../../core/widgets/responsive_data_view.dart';
import '../../core/widgets/state_views.dart';
import '../../data/local/app_database.dart';
import '../../data/models/analysis_models.dart';
import '../../data/models/route_models.dart';
import '../../data/repositories/analysis_repository.dart';
import '../../data/repositories/route_repository.dart';
import '../../data/repositories/server_repository.dart';
import 'widgets/benchmark_chart.dart';

class AnalysisScreen extends StatefulWidget {
  const AnalysisScreen({super.key});

  @override
  State<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen>
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Comparar y experimentos'),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          labelColor: AppTheme.maroon,
          indicatorColor: AppTheme.maroon,
          tabs: const [
            Tab(text: 'Comparar'),
            Tab(text: 'Banco canónico y piloto'),
            Tab(text: 'Experimentos'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          _CompareRoutesTab(),
          _CanonicalBenchmarksTab(),
          _ExperimentsTab(),
        ],
      ),
    );
  }
}

class _CompareRoutesTab extends StatefulWidget {
  const _CompareRoutesTab();

  @override
  State<_CompareRoutesTab> createState() => _CompareRoutesTabState();
}

class _CompareRoutesTabState extends State<_CompareRoutesTab> {
  String? _leftId;
  String? _rightId;

  @override
  Widget build(BuildContext context) {
    final routeRepo = context.watch<RouteRepository>();
    final active = routeRepo.currentResponse;
    final saved = routeRepo.savedRoutes;

    SavedRouteRecord? pickById(String? id) {
      if (id == null) return null;
      for (final r in saved) {
        if (r.id == id) return r;
      }
      return null;
    }

    final left = pickById(_leftId) ?? (saved.isNotEmpty ? saved.first : null);
    final right = pickById(_rightId) ?? (saved.length > 1 ? saved[1] : null);

    final incompatibleUnits =
        left != null && right != null && left.unit != right.unit;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Contraste de la consulta activa',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 6),
                if (active == null)
                  const Text(
                    'Calcula una ruta en la pestaña Rutas para comparar aquí Dijkstra (3 colas) y A*.',
                  )
                else ...[
                  Text(
                    '${active.network} · ${active.source} → ${active.target} (${active.unit})',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  const SizedBox(height: 8),
                  for (final row in active.comparisons)
                    _ComparisonRowTile(row: row, unit: active.unit),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Comparar consultas guardadas en SQLite',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 6),
                if (saved.length < 2)
                  const Text(
                    'Guarda al menos dos rutas en biblioteca para compararlas lado a lado.',
                  )
                else ...[
                  AppSelectField<String>(
                    label: 'Consulta A',
                    value: left?.id ?? saved.first.id,
                    leadingIcon: Icons.looks_one_outlined,
                    options: [
                      for (final r in saved)
                        SelectOption(
                          value: r.id,
                          label: r.title,
                          subtitle: r.cost == null
                              ? '${r.instanceName} · null'
                              : '${r.instanceName} · ${r.cost!.toStringAsFixed(2)} ${r.unit}',
                        ),
                    ],
                    onChanged: (v) => setState(() => _leftId = v),
                  ),
                  const SizedBox(height: 10),
                  AppSelectField<String>(
                    label: 'Consulta B',
                    value: right?.id ?? saved[1].id,
                    leadingIcon: Icons.looks_two_outlined,
                    options: [
                      for (final r in saved)
                        SelectOption(
                          value: r.id,
                          label: r.title,
                          subtitle: r.cost == null
                              ? '${r.instanceName} · null'
                              : '${r.instanceName} · ${r.cost!.toStringAsFixed(2)} ${r.unit}',
                        ),
                    ],
                    onChanged: (v) => setState(() => _rightId = v),
                  ),
                  const SizedBox(height: 12),
                  if (incompatibleUnits)
                    const ErrorStateBanner(
                      message: 'Unidades incompatibles: no compares directamente segundos (s), metros (m) o pesos abstractos (peso) sin convertir el contexto.',
                    )
                  else if (left != null && right != null)
                    _SideBySideSavedComparison(left: left, right: right),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _ComparisonRowTile extends StatelessWidget {
  const _ComparisonRowTile({required this.row, required this.unit});

  final RouteRow row;
  final String unit;

  String _queueName(String q) {
    switch (q) {
      case 'binary_heap':
        return 'Binary Heap';
      case '4ary_heap':
        return '4-ary Heap';
      case 'fibonacci_heap':
        return 'Fibonacci Heap';
      default:
        return q;
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListTile(
      dense: true,
      contentPadding: EdgeInsets.zero,
      title: Text(
        '${row.algorithm == 'astar' ? 'A*' : 'Dijkstra'} · ${_queueName(row.queue)}',
        style: const TextStyle(fontWeight: FontWeight.w600),
      ),
      subtitle: Text(
        'Exp: ${row.expanded} · Relaj: ${row.relaxations} · DK: ${row.decreaseKey} · Solver: ${row.elapsedMsSingleRun.toStringAsFixed(3)} ms',
        style: const TextStyle(fontFeatures: AppTheme.tabularFigures),
      ),
      trailing: Text(
        row.cost == null ? 'null' : '${row.cost!.toStringAsFixed(2)} $unit',
        style: const TextStyle(
          fontWeight: FontWeight.w700,
          color: AppTheme.maroon,
          fontFeatures: AppTheme.tabularFigures,
        ),
      ),
    );
  }
}

class _SideBySideSavedComparison extends StatelessWidget {
  const _SideBySideSavedComparison({required this.left, required this.right});

  final SavedRouteRecord left;
  final SavedRouteRecord right;

  @override
  Widget build(BuildContext context) {
    final diff = (left.cost != null && right.cost != null)
        ? (right.cost! - left.cost!)
        : null;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.paper,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'A: ${left.title} → ${left.cost?.toStringAsFixed(2) ?? 'null'} ${left.unit}',
            style: const TextStyle(fontFeatures: AppTheme.tabularFigures),
          ),
          const SizedBox(height: 4),
          Text(
            'B: ${right.title} → ${right.cost?.toStringAsFixed(2) ?? 'null'} ${right.unit}',
            style: const TextStyle(fontFeatures: AppTheme.tabularFigures),
          ),
          if (diff != null) ...[
            const SizedBox(height: 6),
            Text(
              'Diferencia (B − A): ${diff >= 0 ? '+' : ''}${diff.toStringAsFixed(2)} ${left.unit}',
              style: const TextStyle(
                fontWeight: FontWeight.w700,
                color: AppTheme.maroon,
                fontFeatures: AppTheme.tabularFigures,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _CanonicalBenchmarksTab extends StatelessWidget {
  const _CanonicalBenchmarksTab();

  @override
  Widget build(BuildContext context) {
    final repo = context.watch<AnalysisRepository>();
    final files = context.read<DeviceFilesService>();
    final bench = repo.canonicalBenchmark;
    final pilot = repo.pilotSeries;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 8,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            ChoiceChip(
              label: const Text('Perfil disperso (E = 4V)'),
              selected: repo.profile == 'sparse',
              selectedColor: AppTheme.maroonSoft,
              onSelected: (_) => repo.loadBenchmarks(profile: 'sparse'),
            ),
            ChoiceChip(
              label: const Text('Perfil denso (8% aristas)'),
              selected: repo.profile == 'dense',
              selectedColor: AppTheme.maroonSoft,
              onSelected: (_) => repo.loadBenchmarks(profile: 'dense'),
            ),
            if (repo.benchmarkFromOfflineBundle)
              const SavedDataBadge(label: 'Snapshot incluido · sin conexión'),
          ],
        ),
        const SizedBox(height: 12),
        if (repo.loadingBenchmark)
          const LoadingStateView(title: 'Cargando mediciones canónicas…')
        else if (repo.benchmarkError != null)
          ErrorStateBanner(
            message: repo.benchmarkError!,
            onRetry: () => repo.loadBenchmarks(profile: repo.profile),
          )
        else if (bench != null) ...[
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Banco canónico (1350 ejecuciones · solo lectura)',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Fecha: ${bench.generatedAtUtc ?? '2026-10-28'} · Estadístico primario: mediana y dispersión IQR (Q1–Q3). No se mezcla con experimentos de sesión.',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  const SizedBox(height: 12),
                  BenchmarkChart.fromSeries(bench.results),
                  const SizedBox(height: 14),
                  _SeriesDataTable(series: bench.results),
                  const SizedBox(height: 10),
                  if (repo.rawCanonicalJson != null)
                    OutlinedButton.icon(
                      onPressed: () {
                        files.shareTextFile(
                          filename: 'benchmark_${repo.profile}.json',
                          content: const JsonEncoder.withIndent('  ')
                              .convert(repo.rawCanonicalJson),
                          subject: 'Benchmark canónico (${repo.profile})',
                        );
                      },
                      icon: const Icon(Icons.share_outlined, size: 18),
                      label: const Text('Exportar / Compartir JSON'),
                    ),
                ],
              ),
            ),
          ),
          if (pilot != null) ...[
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Piloto metodológico (18 muestras · separado)',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Fecha: ${repo.pilotGeneratedAtUtc ?? '2026-11-04'}. No se agrega al banco de 1350 ni permite decidir un ganador.',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    const SizedBox(height: 10),
                    _SeriesDataTable(series: pilot),
                  ],
                ),
              ),
            ),
          ],
        ],
      ],
    );
  }
}

class _SeriesDataTable extends StatelessWidget {
  const _SeriesDataTable({required this.series});

  final BenchmarkSeries series;

  @override
  Widget build(BuildContext context) {
    final rows = <ResponsiveRowItem>[];
    for (final q in const ['binary_heap', '4ary_heap', 'fibonacci_heap']) {
      final qLabel = BenchmarkChart.queueLabels[q] ?? q;
      for (final item in (series.data[q] ?? const <BenchmarkRow>[])) {
        final iqr =
            '${item.q1Us.toStringAsFixed(1)}–${item.q3Us.toStringAsFixed(1)}';
        rows.add(
          ResponsiveRowItem(
            title: 'V = ${item.nodes} · E = ${item.edges}',
            badge: qLabel,
            mobileColumns: const [3, 4],
            cells: [
              '${item.nodes}',
              '${item.edges}',
              qLabel,
              item.medianUs.toStringAsFixed(1),
              iqr,
            ],
          ),
        );
      }
    }

    return ResponsiveDataView(
      headers: const ['V', 'E', 'Cola', 'Mediana (µs)', 'IQR Q1–Q3'],
      rows: rows,
    );
  }
}

class _ExperimentsTab extends StatefulWidget {
  const _ExperimentsTab();

  @override
  State<_ExperimentsTab> createState() => _ExperimentsTabState();
}

class _ExperimentsTabState extends State<_ExperimentsTab> {
  String _profile = 'sparse';
  final _sizesCtrl = TextEditingController(text: '30, 60, 100');
  final _seedCtrl = TextEditingController(text: '42');
  final _runsCtrl = TextEditingController(text: '5');
  String? _formError;

  @override
  void dispose() {
    _sizesCtrl.dispose();
    _seedCtrl.dispose();
    _runsCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final serverRepo = context.read<ServerRepository>();
    final analysisRepo = context.read<AnalysisRepository>();
    try {
      final request = AnalysisRepository.parseExperimentInputs(
        profile: _profile,
        sizesText: _sizesCtrl.text,
        seedText: _seedCtrl.text,
        runsText: _runsCtrl.text,
        limits: serverRepo.limits,
      );
      setState(() => _formError = null);
      await analysisRepo.runExperiment(request);
    } on FormatException catch (err) {
      setState(() => _formError = err.message);
    }
  }

  @override
  Widget build(BuildContext context) {
    final analysisRepo = context.watch<AnalysisRepository>();
    final serverRepo = context.watch<ServerRepository>();
    final files = context.read<DeviceFilesService>();
    final limits = serverRepo.limits;
    final exp = analysisRepo.currentExperiment;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Nuevo experimento de sesión (no canónico)',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 4),
                Text(
                  'Requiere conexión. Ejecuta 2 redes por tamaño en el servidor. Separa el tiempo de cálculo (µs) del tiempo total de la solicitud (ms).',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 12),
                AppSelectField<String>(
                  label: 'Perfil experimental',
                  value: _profile,
                  leadingIcon: Icons.analytics_outlined,
                  options: const [
                    SelectOption(
                      value: 'sparse',
                      label: 'Disperso (E = 4V)',
                      subtitle:
                          'Grado promedio acotado, similar a redes viales',
                    ),
                    SelectOption(
                      value: 'dense',
                      label: 'Denso (8% aristas posibles)',
                      subtitle: 'Mayor densidad de aristas y decrease-key',
                    ),
                  ],
                  onChanged: (v) => setState(() => _profile = v),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: _sizesCtrl,
                  decoration: InputDecoration(
                    labelText:
                        'Tamaños (${limits.experimentSizeMin}–${limits.experimentSizeMax}, máx. ${limits.experimentSizesMaxCount})',
                  ),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _seedCtrl,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(
                          labelText:
                              'Semilla (${limits.seedMin}–${limits.seedMax})',
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: _runsCtrl,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(
                          labelText:
                              'Repeticiones (${limits.experimentRunsMin}–${limits.experimentRunsMax})',
                        ),
                      ),
                    ),
                  ],
                ),
                if (_formError != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    _formError!,
                    style: const TextStyle(color: AppTheme.errorRed),
                  ),
                ],
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: analysisRepo.runningExperiment ? null : _submit,
                  icon: analysisRepo.runningExperiment
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.science_outlined),
                  label: Text(
                    analysisRepo.runningExperiment
                        ? 'Ejecutando experimento…'
                        : 'Ejecutar experimento',
                  ),
                ),
              ],
            ),
          ),
        ),
        if (analysisRepo.experimentError != null) ...[
          const SizedBox(height: 12),
          ErrorStateBanner(
            message: analysisRepo.experimentError!,
            onRetry: _submit,
          ),
        ],
        if (exp != null) ...[
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SavedDataBadge(
                    label:
                        'Experimento de sesión · separado del banco canónico',
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Perfil ${exp.profile} · ${exp.generatedAtUtc}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  if (analysisRepo.lastExperimentLatencyMs != null)
                    Text(
                      'Tiempo solver reportado en µs (Python) · Duración total de solicitud en móvil: ${analysisRepo.lastExperimentLatencyMs} ms',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  const SizedBox(height: 12),
                  BenchmarkChart.fromExperimentRows(exp.rows),
                  const SizedBox(height: 12),
                  ResponsiveDataView(
                    headers: const [
                      'V',
                      'E',
                      'Cola',
                      'Mediana (µs)',
                      'Q1–Q3 (µs)',
                      'Semillas',
                    ],
                    rows: [
                      for (final r in exp.rows)
                        ResponsiveRowItem(
                          title: 'V = ${r.nodes} · E = ${r.edges}',
                          badge: BenchmarkChart.queueLabels[r.queue] ?? r.queue,
                          mobileColumns: const [3, 4, 5],
                          cells: [
                            '${r.nodes}',
                            '${r.edges}',
                            BenchmarkChart.queueLabels[r.queue] ?? r.queue,
                            r.medianUs.toStringAsFixed(1),
                            '${r.q1Us.toStringAsFixed(1)}–${r.q3Us.toStringAsFixed(1)}',
                            r.instanceSeeds.join(', '),
                          ],
                        ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  if (analysisRepo.rawExperimentJson != null)
                    OutlinedButton.icon(
                      onPressed: () {
                        files.shareTextFile(
                          filename: 'experimento_${exp.profile}.json',
                          content: const JsonEncoder.withIndent('  ')
                              .convert(analysisRepo.rawExperimentJson),
                          subject: 'Experimento de sesión (${exp.profile})',
                        );
                      },
                      icon: const Icon(Icons.share_outlined, size: 18),
                      label: const Text('Exportar muestras y protocolo'),
                    ),
                ],
              ),
            ),
          ),
        ],
        if (analysisRepo.savedExperiments.isNotEmpty) ...[
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Historial guardado en dispositivo (${analysisRepo.savedExperiments.length})',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 6),
                  for (final item in analysisRepo.savedExperiments)
                    ListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      title: Text(
                        'Perfil ${item.profile} · semilla ${item.seed} · ${item.runs} rep.',
                      ),
                      subtitle: Text(item.createdAt),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          TextButton(
                            onPressed: () =>
                                analysisRepo.openSavedExperiment(item),
                            child: const Text('Ver'),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete_outline, size: 18),
                            onPressed: () =>
                                analysisRepo.deleteSavedExperiment(item.id),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }
}
