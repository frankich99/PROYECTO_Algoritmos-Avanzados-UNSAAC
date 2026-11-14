import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/network/request_guard.dart';
import '../local/app_database.dart';
import '../models/route_models.dart';

class RouteRepository extends ChangeNotifier {
  RouteRepository({
    required this.apiClient,
    required this.database,
  });

  final ApiClient apiClient;
  final AppDatabase database;
  final RequestGuard _guard = RequestGuard();

  RouteRequest? _lastRequest;
  RouteResponse? _currentResponse;
  Map<String, dynamic>? _rawResponseJson;
  int? _lastRequestLatencyMs;
  bool _isSavedOfflineView = false;
  bool _loading = false;
  bool _slowWakeup = false;
  String? _errorMessage;
  bool _isOfflineError = false;
  List<SavedRouteRecord> _savedRoutes = const [];
  bool _initialized = false;

  RouteRequest? get lastRequest => _lastRequest;
  RouteResponse? get currentResponse => _currentResponse;
  Map<String, dynamic>? get rawResponseJson => _rawResponseJson;
  int? get lastRequestLatencyMs => _lastRequestLatencyMs;
  bool get isSavedOfflineView => _isSavedOfflineView;
  bool get loading => _loading;
  bool get slowWakeup => _slowWakeup;
  String? get errorMessage => _errorMessage;
  bool get isOfflineError => _isOfflineError;
  List<SavedRouteRecord> get savedRoutes => _savedRoutes;

  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;
    await refreshSavedRoutes();
  }

  Future<void> refreshSavedRoutes() async {
    _savedRoutes = await database.listRoutes();
    notifyListeners();
  }

  void clearCurrentResult() {
    _guard.invalidateAll();
    _currentResponse = null;
    _rawResponseJson = null;
    _lastRequest = null;
    _lastRequestLatencyMs = null;
    _isSavedOfflineView = false;
    _loading = false;
    _slowWakeup = false;
    _errorMessage = null;
    _isOfflineError = false;
    notifyListeners();
  }

  Future<RouteResponse?> solveRoute(RouteRequest request) async {
    final token = _guard.nextToken();
    _loading = true;
    _slowWakeup = false;
    _errorMessage = null;
    _isOfflineError = false;
    _isSavedOfflineView = false;
    _lastRequest = request;
    notifyListeners();

    final stopwatch = Stopwatch()..start();
    try {
      final json = await apiClient.postJson(
        '/routes/solve',
        body: request.toJson(),
        onSlowRequest: () {
          if (!_guard.isCurrent(token)) return;
          _slowWakeup = true;
          notifyListeners();
        },
      );
      stopwatch.stop();
      if (!_guard.isCurrent(token)) return null;

      final parsed = RouteResponse.fromJson(json);
      _currentResponse = parsed;
      _rawResponseJson = json;
      _lastRequestLatencyMs = stopwatch.elapsedMilliseconds;
      _loading = false;
      _slowWakeup = false;
      _errorMessage = null;
      _isOfflineError = false;
      notifyListeners();
      return parsed;
    } on ApiException catch (err) {
      stopwatch.stop();
      if (!_guard.isCurrent(token)) return null;
      _loading = false;
      _slowWakeup = false;
      _errorMessage = err.message;
      _isOfflineError = err.isNetworkRelated;
      notifyListeners();
      return null;
    }
  }

  Future<SavedRouteRecord> saveCurrentRoute({String? customTitle}) async {
    final resp = _currentResponse;
    final raw = _rawResponseJson;
    if (resp == null || raw == null) {
      throw StateError('No hay resultado calculado para guardar.');
    }
    final now = DateTime.now().toUtc().toIso8601String();
    final title = customTitle?.trim().isNotEmpty == true
        ? customTitle!.trim()
        : '${resp.network}: ${resp.source} → ${resp.target}';
    final record = SavedRouteRecord(
      id: 'route_${DateTime.now().microsecondsSinceEpoch}',
      title: title,
      instanceName: resp.network,
      metric: resp.metric,
      unit: resp.unit,
      sourceLabel: resp.source.toString(),
      targetLabel: resp.target.toString(),
      cost: resp.result.cost,
      requestJson: jsonEncode(_lastRequest?.toJson() ?? const {}),
      responseJson: const JsonEncoder.withIndent('  ').convert(raw),
      createdAt: now,
    );
    await database.upsertRoute(record);
    await refreshSavedRoutes();
    return record;
  }

  void openSavedRoute(SavedRouteRecord record) {
    _guard.invalidateAll();
    final decoded = jsonDecode(record.responseJson) as Map<String, dynamic>;
    _rawResponseJson = decoded;
    _currentResponse = RouteResponse.fromJson(decoded);
    _lastRequestLatencyMs = null;
    _isSavedOfflineView = true;
    _loading = false;
    _slowWakeup = false;
    _errorMessage = null;
    _isOfflineError = false;
    notifyListeners();
  }

  Future<void> deleteSavedRoute(String id) async {
    await database.deleteRoute(id);
    await refreshSavedRoutes();
  }

  String exportCurrentResultJson() {
    if (_rawResponseJson == null) {
      throw StateError('No hay resultado disponible para exportar.');
    }
    return const JsonEncoder.withIndent('  ').convert(_rawResponseJson);
  }
}
