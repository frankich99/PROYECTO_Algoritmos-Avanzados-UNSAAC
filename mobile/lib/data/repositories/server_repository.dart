import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../../core/config/app_config.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/network/request_guard.dart';
import '../models/catalog_models.dart';
import '../models/version_info.dart';
import 'settings_repository.dart';

enum ServerLoadState { initial, loading, ready, empty, offline, error, saved }

class ServerRepository extends ChangeNotifier {
  ServerRepository({required this.apiClient, required this.settingsRepository});

  final ApiClient apiClient;
  final SettingsRepository settingsRepository;
  final RequestGuard _guard = RequestGuard();

  ServerLoadState _state = ServerLoadState.initial;
  VersionInfo? _version;
  CatalogInfo? _catalog;
  String? _errorMessage;
  bool _slowWakeup = false;
  DateTime? _lastSyncedAt;
  bool _initialized = false;

  ServerLoadState get state => _state;
  VersionInfo? get version => _version;
  CatalogInfo? get catalog => _catalog;
  ApiLimits get limits => _catalog?.limits ?? const ApiLimits();
  String? get errorMessage => _errorMessage;
  bool get slowWakeup => _slowWakeup;
  DateTime? get lastSyncedAt => _lastSyncedAt;
  String get baseUrl => apiClient.baseUrl;
  bool get isUsingSavedFallback => _state == ServerLoadState.saved;

  bool get isVersionCompatible {
    final current = _version?.apiVersion;
    if (current == null || current.isEmpty) return true;
    final expectedMajor = AppConfig.expectedApiVersion.split('.').first;
    final currentMajor = current.split('.').first;
    return expectedMajor == currentMajor;
  }

  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;
    final savedUrl = await settingsRepository.loadBaseUrl();
    apiClient.updateBaseUrl(savedUrl);
    await _restoreCachedMetadata();
    await refreshStatus();
  }

  Future<void> _restoreCachedMetadata() async {
    final cachedVersion = await settingsRepository.loadCachedVersionJson();
    final cachedCatalog = await settingsRepository.loadCachedCatalogJson();
    if (cachedVersion != null) {
      try {
        _version = VersionInfo.fromJson(
          jsonDecode(cachedVersion) as Map<String, dynamic>,
        );
      } catch (_) {}
    }
    if (cachedCatalog != null) {
      try {
        _catalog = CatalogInfo.fromJson(
          jsonDecode(cachedCatalog) as Map<String, dynamic>,
        );
      } catch (_) {}
    }
    if (_catalog != null && _state == ServerLoadState.initial) {
      _state = ServerLoadState.saved;
      notifyListeners();
    }
  }

  Future<void> updateServerUrl(String url) async {
    final error = AppConfig.validateBaseUrl(url);
    if (error != null) throw ArgumentError(error);
    final normalized = AppConfig.normalizeBaseUrl(url);
    if (normalized != baseUrl) {
      _guard.invalidateAll();
      await settingsRepository.clearCachedServerMetadata();
      _catalog = null;
      _version = null;
      _lastSyncedAt = null;
      _state = ServerLoadState.initial;
    }
    await settingsRepository.saveBaseUrl(normalized);
    apiClient.updateBaseUrl(normalized);
    await refreshStatus();
  }

  Future<void> resetServerUrl() async {
    await updateServerUrl(AppConfig.configuredBaseUrl);
    await settingsRepository.resetBaseUrl();
  }

  Future<void> refreshStatus() async {
    if (_state == ServerLoadState.loading) return;
    final token = _guard.nextToken();
    _state = ServerLoadState.loading;
    _slowWakeup = false;
    _errorMessage = null;
    notifyListeners();

    try {
      final healthJson = await apiClient.getJson(
        '/health',
        timeout: AppConfig.healthTimeout,
        onSlowRequest: () {
          if (!_guard.isCurrent(token)) return;
          _slowWakeup = true;
          notifyListeners();
        },
      );
      if (!_guard.isCurrent(token)) return;
      final health = HealthStatus.fromJson(healthJson);
      if (!health.ok) {
        throw const ApiException(
          kind: ApiErrorKind.server,
          message: 'El backend respondió sin confirmación de salud.',
        );
      }

      final results = await Future.wait([
        apiClient.getJson('/version', timeout: AppConfig.standardTimeout),
        apiClient.getJson('/catalog', timeout: AppConfig.standardTimeout),
      ]);
      if (!_guard.isCurrent(token)) return;

      final versionMap = results[0];
      final catalogMap = results[1];
      _version = VersionInfo.fromJson(versionMap);
      _catalog = CatalogInfo.fromJson(catalogMap);
      _lastSyncedAt = DateTime.now();
      _slowWakeup = false;
      _errorMessage = null;
      _state = (_catalog!.networks.isEmpty && _catalog!.queues.isEmpty)
          ? ServerLoadState.empty
          : ServerLoadState.ready;

      await settingsRepository.saveCachedVersionJson(jsonEncode(versionMap));
      await settingsRepository.saveCachedCatalogJson(jsonEncode(catalogMap));
      if (!_guard.isCurrent(token)) return;
      notifyListeners();
    } on ApiException catch (err) {
      if (!_guard.isCurrent(token)) return;
      _slowWakeup = false;
      _errorMessage = err.message;
      if (_catalog != null && err.isNetworkRelated) {
        _state = ServerLoadState.saved;
      } else if (err.isNetworkRelated) {
        _state = ServerLoadState.offline;
      } else {
        _state = ServerLoadState.error;
      }
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _guard.invalidateAll();
    super.dispose();
  }
}
