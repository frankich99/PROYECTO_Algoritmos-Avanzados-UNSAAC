import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/network/request_guard.dart';
import '../local/app_database.dart';
import '../models/analysis_models.dart';
import '../models/catalog_models.dart';

class AnalysisRepository extends ChangeNotifier {
  AnalysisRepository({
    required this.apiClient,
    required this.database,
    this.assetBundle,
  });

  final ApiClient apiClient;
  final AppDatabase database;
  final AssetBundle? assetBundle;
  final RequestGuard _benchGuard = RequestGuard();
  final RequestGuard _expGuard = RequestGuard();

  String _profile = 'sparse';
  BenchmarkResponse? _canonicalBenchmark;
  bool _benchmarkFromOfflineBundle = false;
  Map<String, dynamic>? _rawCanonicalJson;
  BenchmarkSeries? _pilotSparse;
  BenchmarkSeries? _pilotDense;
  String? _pilotGeneratedAtUtc;
  Map<String, dynamic>? _pilotProtocol;
  bool _loadingBenchmark = false;
  String? _benchmarkError;

  ExperimentResponse? _currentExperiment;
  Map<String, dynamic>? _rawExperimentJson;
  int? _lastExperimentLatencyMs;
  bool _runningExperiment = false;
  String? _experimentError;
  List<SavedExperimentRecord> _savedExperiments = const [];
  bool _initialized = false;

  String get profile => _profile;
  BenchmarkResponse? get canonicalBenchmark => _canonicalBenchmark;
  bool get benchmarkFromOfflineBundle => _benchmarkFromOfflineBundle;
  Map<String, dynamic>? get rawCanonicalJson => _rawCanonicalJson;
  BenchmarkSeries? get pilotSeries =>
      _profile == 'sparse' ? _pilotSparse : _pilotDense;
  String? get pilotGeneratedAtUtc => _pilotGeneratedAtUtc;
  Map<String, dynamic>? get pilotProtocol => _pilotProtocol;
  bool get loadingBenchmark => _loadingBenchmark;
  String? get benchmarkError => _benchmarkError;

  ExperimentResponse? get currentExperiment => _currentExperiment;
  Map<String, dynamic>? get rawExperimentJson => _rawExperimentJson;
  int? get lastExperimentLatencyMs => _lastExperimentLatencyMs;
  bool get runningExperiment => _runningExperiment;
  String? get experimentError => _experimentError;
  List<SavedExperimentRecord> get savedExperiments => _savedExperiments;

  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;
    await Future.wait([
      refreshSavedExperiments(),
      loadBenchmarks(profile: _profile),
    ]);
  }

  Future<void> refreshSavedExperiments() async {
    _savedExperiments = await database.listExperiments();
    notifyListeners();
  }

  Future<void> loadBenchmarks({String? profile}) async {
    final targetProfile = profile ?? _profile;
    _profile = targetProfile;
    final token = _benchGuard.nextToken();
    _loadingBenchmark = true;
    _benchmarkError = null;
    notifyListeners();

    try {
      final results = await Future.wait([
        apiClient.getJson('/benchmarks/$targetProfile'),
        apiClient.getJson('/benchmarks/pilot/summary'),
      ]);
      if (!_benchGuard.isCurrent(token)) return;
      _rawCanonicalJson = results[0];
      _canonicalBenchmark = BenchmarkResponse.fromJson(results[0]);
      _benchmarkFromOfflineBundle = false;
      _applyPilotMap(results[1]);
      _loadingBenchmark = false;
      notifyListeners();
    } on ApiException catch (err) {
      if (!_benchGuard.isCurrent(token)) return;
      final loadedOffline = await _loadBundledOffline(targetProfile);
      _loadingBenchmark = false;
      if (loadedOffline) {
        _benchmarkFromOfflineBundle = true;
        _benchmarkError = null;
      } else {
        _benchmarkError = err.message;
      }
      notifyListeners();
    }
  }

  Future<bool> _loadBundledOffline(String targetProfile) async {
    try {
      final bundle = assetBundle ?? rootBundle;
      final benchRaw = jsonDecode(
        await bundle.loadString('assets/data/benchmark_results.json'),
      ) as Map<String, dynamic>;
      final pilotRaw = jsonDecode(
        await bundle.loadString('assets/data/pilot_benchmark_results.json'),
      ) as Map<String, dynamic>;

      final profiles = benchRaw['profiles'] as Map<String, dynamic>? ?? const {};
      final selected = profiles[targetProfile];
      if (selected is! Map<String, dynamic>) return false;

      final adapted = {
        'generated_at_utc': benchRaw['generated_at_utc'],
        'protocol': benchRaw['protocol'] ?? const {},
        'environment': benchRaw['environment'],
        'profile': targetProfile,
        'results': selected,
      };
      _rawCanonicalJson = adapted;
      _canonicalBenchmark = BenchmarkResponse.fromJson(adapted);
      _applyPilotMap(pilotRaw);
      return true;
    } catch (_) {
      return false;
    }
  }

  void _applyPilotMap(Map<String, dynamic> pilotRaw) {
    _pilotGeneratedAtUtc = pilotRaw['generated_at_utc']?.toString();
    _pilotProtocol = Map<String, dynamic>.from(
      pilotRaw['protocol'] as Map<String, dynamic>? ?? const {},
    );
    final profiles = pilotRaw['profiles'] as Map<String, dynamic>? ?? const {};
    if (profiles['sparse'] is Map<String, dynamic>) {
      _pilotSparse = BenchmarkSeries.fromJson(
        profiles['sparse'] as Map<String, dynamic>,
      );
    }
    if (profiles['dense'] is Map<String, dynamic>) {
      _pilotDense = BenchmarkSeries.fromJson(
        profiles['dense'] as Map<String, dynamic>,
      );
    }
  }

  /// Valida parámetros de experimento contra los límites compartidos del servidor.
  static ExperimentRequest parseExperimentInputs({
    required String profile,
    required String sizesText,
    required String seedText,
    required String runsText,
    required ApiLimits limits,
  }) {
    int parseIntRange(String raw, String label, int min, int max) {
      final trimmed = raw.trim();
      final val = int.tryParse(trimmed);
      if (val == null || val < min || val > max) {
        throw FormatException('$label: introduce un entero entre $min y $max.');
      }
      return val;
    }

    final tokens = sizesText
        .split(',')
        .map((e) => e.trim())
        .where((e) => e.isNotEmpty)
        .toList();
    if (tokens.isEmpty || tokens.length > limits.experimentSizesMaxCount) {
      throw FormatException(
        'Usa entre 1 y ${limits.experimentSizesMaxCount} tamaños separados por comas.',
      );
    }
    final parsedSizes = tokens
        .map((t) => parseIntRange(
              t,
              'Tamaño',
              limits.experimentSizeMin,
              limits.experimentSizeMax,
            ))
        .toList();
    if (parsedSizes.toSet().length != parsedSizes.length) {
      throw const FormatException('Los tamaños no deben repetirse.');
    }

    final seed = parseIntRange(
      seedText,
      'Semilla',
      limits.seedMin,
      limits.seedMax,
    );
    final runs = parseIntRange(
      runsText,
      'Repeticiones',
      limits.experimentRunsMin,
      limits.experimentRunsMax,
    );

    return ExperimentRequest(
      profile: profile,
      sizes: parsedSizes,
      seed: seed,
      runs: runs,
    );
  }

  Future<ExperimentResponse?> runExperiment(ExperimentRequest request) async {
    if (_runningExperiment) return null;
    final token = _expGuard.nextToken();
    _runningExperiment = true;
    _experimentError = null;
    notifyListeners();

    final sw = Stopwatch()..start();
    try {
      final json = await apiClient.postJson(
        '/experiments',
        body: request.toJson(),
      );
      sw.stop();
      if (!_expGuard.isCurrent(token)) return null;
      final parsed = ExperimentResponse.fromJson(json);
      _rawExperimentJson = json;
      _currentExperiment = parsed;
      _lastExperimentLatencyMs = sw.elapsedMilliseconds;
      _runningExperiment = false;
      _experimentError = null;

      final record = SavedExperimentRecord(
        id: 'exp_${DateTime.now().microsecondsSinceEpoch}',
        profile: parsed.profile,
        seed: request.seed,
        runs: request.runs,
        responseJson: const JsonEncoder.withIndent('  ').convert(json),
        createdAt: DateTime.now().toUtc().toIso8601String(),
      );
      await database.upsertExperiment(record);
      await refreshSavedExperiments();
      notifyListeners();
      return parsed;
    } on ApiException catch (err) {
      sw.stop();
      if (!_expGuard.isCurrent(token)) return null;
      _runningExperiment = false;
      _experimentError = err.message;
      notifyListeners();
      return null;
    }
  }

  void openSavedExperiment(SavedExperimentRecord record) {
    final decoded = jsonDecode(record.responseJson) as Map<String, dynamic>;
    _rawExperimentJson = decoded;
    _currentExperiment = ExperimentResponse.fromJson(decoded);
    _lastExperimentLatencyMs = null;
    _experimentError = null;
    notifyListeners();
  }

  Future<void> deleteSavedExperiment(String id) async {
    await database.deleteExperiment(id);
    await refreshSavedExperiments();
  }
}
