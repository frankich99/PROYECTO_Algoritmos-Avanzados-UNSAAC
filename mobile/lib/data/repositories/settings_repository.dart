import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../../core/config/app_config.dart';

class SettingsRepository {
  SettingsRepository([SharedPreferences? prefs]) : _prefs = prefs;

  static const String _serverUrlKey = 'rutas_server_base_url';
  static const String _cachedCatalogKey = 'rutas_cached_catalog_json';
  static const String _cachedVersionKey = 'rutas_cached_version_json';
  static const String _savedWeatherKey = 'rutas_saved_weather_json';
  static const String _rememberKeysKey = 'rutas_remember_provider_keys';
  static const String _providerKeysKey = 'rutas_provider_keys_json';

  SharedPreferences? _prefs;

  Future<SharedPreferences> _ensurePrefs() async {
    return _prefs ??= await SharedPreferences.getInstance();
  }

  Future<String> loadBaseUrl() async {
    final prefs = await _ensurePrefs();
    final stored = prefs.getString(_serverUrlKey);
    if (stored == null || stored.trim().isEmpty) {
      return AppConfig.configuredBaseUrl;
    }
    return AppConfig.normalizeBaseUrl(stored);
  }

  Future<void> saveBaseUrl(String url) async {
    final prefs = await _ensurePrefs();
    await prefs.setString(_serverUrlKey, AppConfig.normalizeBaseUrl(url));
  }

  Future<void> resetBaseUrl() async {
    final prefs = await _ensurePrefs();
    await prefs.remove(_serverUrlKey);
  }

  Future<String?> loadCachedCatalogJson() async {
    final prefs = await _ensurePrefs();
    return prefs.getString(_cachedCatalogKey);
  }

  Future<void> saveCachedCatalogJson(String raw) async {
    final prefs = await _ensurePrefs();
    await prefs.setString(_cachedCatalogKey, raw);
  }

  Future<String?> loadCachedVersionJson() async {
    final prefs = await _ensurePrefs();
    return prefs.getString(_cachedVersionKey);
  }

  Future<void> saveCachedVersionJson(String raw) async {
    final prefs = await _ensurePrefs();
    await prefs.setString(_cachedVersionKey, raw);
  }

  Future<void> clearCachedServerMetadata() async {
    final prefs = await _ensurePrefs();
    await prefs.remove(_cachedCatalogKey);
    await prefs.remove(_cachedVersionKey);
  }

  Future<String?> loadSavedWeatherJson() async {
    final prefs = await _ensurePrefs();
    return prefs.getString(_savedWeatherKey);
  }

  Future<void> saveWeatherJson(String raw) async {
    final prefs = await _ensurePrefs();
    await prefs.setString(_savedWeatherKey, raw);
  }

  Future<void> forgetSavedWeather() async {
    final prefs = await _ensurePrefs();
    await prefs.remove(_savedWeatherKey);
  }

  Future<bool> loadRememberProviderKeys() async {
    final prefs = await _ensurePrefs();
    return prefs.getBool(_rememberKeysKey) ?? false;
  }

  Future<Map<String, String>> loadProviderKeys() async {
    final prefs = await _ensurePrefs();
    final remember = prefs.getBool(_rememberKeysKey) ?? false;
    if (!remember) return {'openweathermap': '', 'tomtom': ''};
    final raw = prefs.getString(_providerKeysKey);
    if (raw == null || raw.isEmpty) {
      return {'openweathermap': '', 'tomtom': ''};
    }
    try {
      final decoded = jsonDecode(raw) as Map<String, dynamic>;
      return {
        'openweathermap': decoded['openweathermap']?.toString() ?? '',
        'tomtom': decoded['tomtom']?.toString() ?? '',
      };
    } catch (_) {
      return {'openweathermap': '', 'tomtom': ''};
    }
  }

  Future<void> saveProviderKeys({
    required bool remember,
    required Map<String, String> keys,
  }) async {
    final prefs = await _ensurePrefs();
    await prefs.setBool(_rememberKeysKey, remember);
    if (remember) {
      await prefs.setString(_providerKeysKey, jsonEncode(keys));
    } else {
      await prefs.remove(_providerKeysKey);
    }
  }

  Future<void> forgetProviderKeys() async {
    final prefs = await _ensurePrefs();
    await prefs.remove(_rememberKeysKey);
    await prefs.remove(_providerKeysKey);
  }
}
