class PointCoord {
  const PointCoord({required this.lat, required this.lon});

  final double lat;
  final double lon;

  factory PointCoord.fromJson(Map<String, dynamic> json) {
    return PointCoord(
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
    );
  }

  /// Convierte un par [lon, lat] del backend a PointCoord.
  factory PointCoord.fromLonLatList(List<dynamic> pair) {
    return PointCoord(
      lon: (pair[0] as num).toDouble(),
      lat: (pair[1] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {'lat': lat, 'lon': lon};
}

class InstanceSpec {
  const InstanceSpec({
    this.kind = 'center',
    this.data,
    this.text,
    this.generator = 'random',
    this.nodes = 30,
    this.seed = 42,
    this.rows = 5,
    this.cols = 5,
  });

  final String kind;
  final Map<String, dynamic>? data;
  final String? text;
  final String generator;
  final int nodes;
  final int seed;
  final int rows;
  final int cols;

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{
      'kind': kind,
      'generator': generator,
      'nodes': nodes,
      'seed': seed,
      'rows': rows,
      'cols': cols,
    };
    if (data != null) map['data'] = data;
    if (text != null) map['text'] = text;
    return map;
  }
}

class DisplayEdge {
  const DisplayEdge({
    required this.from,
    required this.to,
    required this.weight,
  });

  final Object from;
  final Object to;
  final double weight;

  factory DisplayEdge.fromList(List<dynamic> row) {
    return DisplayEdge(
      from: row[0] as Object,
      to: row[1] as Object,
      weight: (row[2] as num).toDouble(),
    );
  }
}

class InstancePreview {
  const InstancePreview({
    required this.valid,
    required this.name,
    required this.nodes,
    required this.edges,
    required this.ids,
    required this.coords,
    required this.metric,
    required this.geographic,
    required this.displayEdges,
    required this.displayLimited,
  });

  final bool valid;
  final String name;
  final int nodes;
  final int edges;

  /// Conserva el tipo original (String o int) para reenviar sin ambigüedades.
  final List<Object> ids;

  /// Coordenadas en orden [x/lon, y/lat] indexadas por String(id).
  final Map<String, List<double>> coords;
  final String metric;
  final bool geographic;
  final List<DisplayEdge> displayEdges;
  final bool displayLimited;

  factory InstancePreview.fromJson(Map<String, dynamic> json) {
    final rawCoords = json['coords'] as Map<String, dynamic>? ?? const {};
    final coords = <String, List<double>>{};
    for (final entry in rawCoords.entries) {
      final list = entry.value as List<dynamic>;
      coords[entry.key] = [
        (list[0] as num).toDouble(),
        (list[1] as num).toDouble(),
      ];
    }
    final rawIds = (json['ids'] as List<dynamic>? ?? const [])
        .whereType<Object>()
        .toList();
    final rawDisplay = (json['display_edges'] as List<dynamic>? ?? const [])
        .whereType<List<dynamic>>()
        .map(DisplayEdge.fromList)
        .toList();

    return InstancePreview(
      valid: json['valid'] == true,
      name: json['name']?.toString() ?? '',
      nodes: (json['nodes'] as num).toInt(),
      edges: (json['edges'] as num).toInt(),
      ids: rawIds,
      coords: coords,
      metric: json['metric']?.toString() ?? 'weight',
      geographic: json['geographic'] == true,
      displayEdges: rawDisplay,
      displayLimited: json['display_limited'] == true,
    );
  }
}

class ExportedInstance {
  const ExportedInstance({
    required this.format,
    required this.apiVersion,
    required this.generatorVersion,
    required this.nodes,
    required this.edges,
    required this.metric,
    required this.instance,
  });

  final String format;
  final String apiVersion;
  final String generatorVersion;
  final int nodes;
  final int edges;
  final String metric;
  final Map<String, dynamic> instance;

  factory ExportedInstance.fromJson(Map<String, dynamic> json) {
    return ExportedInstance(
      format: json['format']?.toString() ?? 'rutas-cusco-instance-v1',
      apiVersion: json['api_version']?.toString() ?? '',
      generatorVersion: json['generator_version']?.toString() ?? '',
      nodes: (json['nodes'] as num).toInt(),
      edges: (json['edges'] as num).toInt(),
      metric: json['metric']?.toString() ?? 'weight',
      instance: Map<String, dynamic>.from(
        json['instance'] as Map<String, dynamic>? ?? const {},
      ),
    );
  }
}
