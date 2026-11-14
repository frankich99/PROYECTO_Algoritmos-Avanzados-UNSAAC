import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../../core/network/request_guard.dart';
import '../models/analysis_models.dart';
import '../models/instance_models.dart';
import 'settings_repository.dart';

class ConditionsRepository extends ChangeNotifier {
  ConditionsRepository({
    required this.apiClient,
    required this.settingsRepository,
  });

  final ApiClient apiClient;
  final SettingsRepository settingsRepository;
  final RequestGuard _guard = RequestGuard();

  ConditionsResponse? _liveWeather;
  ConditionsResponse? _savedWeather;
  ConditionsResponse? _liveTraffic;
  bool _loading = false;
  String? _errorMessage;
  bool _rememberKeys = false;
  Map<String, String> _personalKeys = {
    'openweathermap': '',
    'tomtom': '',
  };
  bool _initialized = false;

  ConditionsResponse? get liveWeather => _liveWeather;
  ConditionsResponse? get savedWeather => _savedWeather;
  ConditionsResponse? get liveTraffic => _liveTraffic;
  bool get loading => _loading;
  String? get errorMessage => _errorMessage;
  bool get rememberKeys => _rememberKeys;
  String keyFor(String provider) => _personalKeys[provider] ?? '';

  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;
    _rememberKeys = await settingsRepository.loadRememberProviderKeys();
    _personalKeys = await settingsRepository.loadProviderKeys();
    final rawWeather = await settingsRepository.loadSavedWeatherJson();
    if (rawWeather != null && rawWeather.isNotEmpty) {
      try {
        _savedWeather = ConditionsResponse.fromJson(
          jsonDecode(rawWeather) as Map<String, dynamic>,
        );
      } catch (_) {}
    }
    notifyListeners();
  }

  static bool samePoint(PointCoord? a, PointCoord? b) {
    if (a == null || b == null) return false;
    return (a.lat - b.lat).abs() <= 0.00001 && (a.lon - b.lon).abs() <= 0.00001;
  }

  Future<void> updatePersonalKey(String provider, String value) async {
    _personalKeys = {..._personalKeys, provider: value};
    await settingsRepository.saveProviderKeys(
      remember: _rememberKeys,
      keys: _personalKeys,
    );
    notifyListeners();
  }

  Future<void> setRememberKeys(bool value) async {
    _rememberKeys = value;
    await settingsRepository.saveProviderKeys(
      remember: value,
      keys: _personalKeys,
    );
    notifyListeners();
  }

  Future<void> forgetKeys() async {
    _rememberKeys = false;
    _personalKeys = {'openweathermap': '', 'tomtom': ''};
    await settingsRepository.forgetProviderKeys();
    notifyListeners();
  }

  Future<ConditionsResponse?> fetchCondition({
    required PointCoord point,
    required String provider,
  }) async {
    final token = _guard.nextToken();
    _loading = true;
    _errorMessage = null;
    notifyListeners();

    final personalKey = (_personalKeys[provider] ?? '').trim();
    final body = <String, dynamic>{
      'point': point.toJson(),
      'provider': provider,
      if (provider != 'open-meteo' && personalKey.isNotEmpty) 'key': personalKey,
    };

    try {
      final json = await apiClient.postJson('/conditions', body: body);
      if (!_guard.isCurrent(token)) return null;
      final parsed = ConditionsResponse.fromJson(json);
      if (provider == 'tomtom') {
        _liveTraffic = parsed;
      } else {
        _liveWeather = parsed;
      }
      _loading = false;
      _errorMessage = null;
      notifyListeners();
      return parsed;
    } on ApiException catch (err) {
      if (!_guard.isCurrent(token)) return null;
      _loading = false;
      _errorMessage = err.message;
      notifyListeners();
      return null;
    }
  }

  Future<void> saveLiveWeatherLocally() async {
    final current = _liveWeather;
    if (current?.observation == null) return;
    _savedWeather = current;
    final payload = {
      'kind': current!.kind,
      'requested': current.requested.toJson(),
      'fetched_at_utc': current.fetchedAtUtc,
      'multiplier': current.multiplier,
      'contributions': current.contributions,
      'observation': current.observation!.toJson(),
    };
    await settingsRepository.saveWeatherJson(jsonEncode(payload));
    notifyListeners();
  }

  Future<void> forgetSavedWeather() async {
    _savedWeather = null;
    await settingsRepository.forgetSavedWeather();
    notifyListeners();
  }
}
