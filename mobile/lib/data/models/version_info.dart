class HealthStatus {
  const HealthStatus({required this.ok});

  final bool ok;

  factory HealthStatus.fromJson(Map<String, dynamic> json) {
    return HealthStatus(ok: json['ok'] == true);
  }
}

class VersionInfo {
  const VersionInfo({
    required this.name,
    required this.version,
    required this.apiVersion,
    required this.dataVersion,
    required this.docsVersion,
    required this.generatorVersion,
    required this.webBuild,
  });

  final String name;
  final String version;
  final String apiVersion;
  final String dataVersion;
  final String docsVersion;
  final String generatorVersion;
  final bool webBuild;

  factory VersionInfo.fromJson(Map<String, dynamic> json) {
    final version = json['version']?.toString() ?? '0.0.0';
    return VersionInfo(
      name: json['name']?.toString() ?? 'Rutas mínimas en Cusco',
      version: version,
      apiVersion: json['api_version']?.toString() ?? version,
      dataVersion: json['data_version']?.toString() ?? '',
      docsVersion: json['docs_version']?.toString() ?? '',
      generatorVersion: json['generator_version']?.toString() ?? '',
      webBuild: json['web_build'] == true,
    );
  }
}
