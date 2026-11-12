class NetworkOption {
  const NetworkOption({
    required this.kind,
    required this.label,
    required this.available,
  });

  final String kind;
  final String label;
  final bool available;

  factory NetworkOption.fromJson(Map<String, dynamic> json) {
    return NetworkOption(
      kind: json['kind']?.toString() ?? 'center',
      label: json['label']?.toString() ?? '',
      available: json['available'] == true,
    );
  }
}

class ProviderKeysStatus {
  const ProviderKeysStatus({
    required this.openweathermap,
    required this.tomtom,
  });

  final bool openweathermap;
  final bool tomtom;

  factory ProviderKeysStatus.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const ProviderKeysStatus(openweathermap: false, tomtom: false);
    }
    return ProviderKeysStatus(
      openweathermap: json['openweathermap'] == true,
      tomtom: json['tomtom'] == true,
    );
  }
}

class ApiLimits {
  const ApiLimits({
    this.maxNodes = 5000,
    this.maxEdges = 30000,
    this.maxPayloadBytes = 2000000,
    this.displayMaxNodes = 1200,
    this.displayMaxEdges = 3000,
    this.generatorNodesMin = 2,
    this.generatorNodesMax = 500,
    this.generatorGridMin = 1,
    this.generatorGridMax = 30,
    this.experimentSizesMaxCount = 4,
    this.experimentSizeMin = 5,
    this.experimentSizeMax = 200,
    this.experimentRunsMin = 2,
    this.experimentRunsMax = 10,
    this.seedMin = 0,
    this.seedMax = 2147483647,
  });

  final int maxNodes;
  final int maxEdges;
  final int maxPayloadBytes;
  final int displayMaxNodes;
  final int displayMaxEdges;
  final int generatorNodesMin;
  final int generatorNodesMax;
  final int generatorGridMin;
  final int generatorGridMax;
  final int experimentSizesMaxCount;
  final int experimentSizeMin;
  final int experimentSizeMax;
  final int experimentRunsMin;
  final int experimentRunsMax;
  final int seedMin;
  final int seedMax;

  factory ApiLimits.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const ApiLimits();
    int readInt(String key, int fallback) =>
        (json[key] as num?)?.toInt() ?? fallback;
    return ApiLimits(
      maxNodes: readInt('max_nodes', 5000),
      maxEdges: readInt('max_edges', 30000),
      maxPayloadBytes: readInt('max_payload_bytes', 2000000),
      displayMaxNodes: readInt('display_max_nodes', 1200),
      displayMaxEdges: readInt('display_max_edges', 3000),
      generatorNodesMin: readInt('generator_nodes_min', 2),
      generatorNodesMax: readInt('generator_nodes_max', 500),
      generatorGridMin: readInt('generator_grid_min', 1),
      generatorGridMax: readInt('generator_grid_max', 30),
      experimentSizesMaxCount: readInt('experiment_sizes_max_count', 4),
      experimentSizeMin: readInt('experiment_size_min', 5),
      experimentSizeMax: readInt('experiment_size_max', 200),
      experimentRunsMin: readInt('experiment_runs_min', 2),
      experimentRunsMax: readInt('experiment_runs_max', 10),
      seedMin: readInt('seed_min', 0),
      seedMax: readInt('seed_max', 2147483647),
    );
  }
}

class CatalogInfo {
  const CatalogInfo({
    required this.networks,
    required this.queues,
    required this.example,
    required this.providerKeys,
    required this.limits,
  });

  final List<NetworkOption> networks;
  final List<String> queues;
  final String example;
  final ProviderKeysStatus providerKeys;
  final ApiLimits limits;

  factory CatalogInfo.fromJson(Map<String, dynamic> json) {
    final rawNetworks = (json['networks'] as List<dynamic>? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(NetworkOption.fromJson)
        .toList();
    final rawQueues = (json['queues'] as List<dynamic>? ?? const [])
        .map((e) => e.toString())
        .toList();
    return CatalogInfo(
      networks: rawNetworks,
      queues: rawQueues,
      example: json['example']?.toString() ?? '',
      providerKeys: ProviderKeysStatus.fromJson(
        json['provider_keys'] as Map<String, dynamic>?,
      ),
      limits: ApiLimits.fromJson(json['limits'] as Map<String, dynamic>?),
    );
  }
}
