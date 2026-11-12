import 'package:shared_preferences/shared_preferences.dart';

import '../../core/config/app_config.dart';

class SettingsRepository {
  SettingsRepository([SharedPreferences? prefs]) : _prefs = prefs;

  static const String _serverUrlKey = 'rutas_server_base_url';
  static const String _cachedCatalogKey = 'rutas_cached_catalog_json';
  static const String _cachedVersionKey = 'rutas_cached_version_json';

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
}
