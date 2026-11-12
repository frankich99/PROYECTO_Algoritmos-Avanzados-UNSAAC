import 'instance_models.dart';

class ScenarioSpec {
  const ScenarioSpec({
    this.weather = 'none',
    this.weatherProvider = 'open-meteo',
    this.weatherKey,
    this.weatherObservation,
    this.weatherRequestPoint,
    this.trafficHour,
    this.trafficMode,
    this.trafficLive = false,
    this.trafficLiveKey,
  });

  final String weather;
  final String weatherProvider;
  final String? weatherKey;
  final Map<String, dynamic>? weatherObservation;
  final PointCoord? weatherRequestPoint;
  final double? trafficHour;
  final String? trafficMode;
  final bool trafficLive;
  final String? trafficLiveKey;

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{
      'weather': weather,
      'weather_provider': weatherProvider,
      'traffic_live': trafficLive,
    };
    if (weatherKey != null && weatherKey!.isNotEmpty) {
      map['weather_key'] = weatherKey;
    }
    if (weatherObservation != null) {
      map['weather_observation'] = weatherObservation;
    }
    if (weatherRequestPoint != null) {
      map['weather_request_point'] = weatherRequestPoint!.toJson();
    }
    if (trafficHour != null) map['traffic_hour'] = trafficHour;
    if (trafficMode != null) map['traffic_mode'] = trafficMode;
    if (trafficLiveKey != null && trafficLiveKey!.isNotEmpty) {
      map['traffic_live_key'] = trafficLiveKey;
    }
    return map;
  }
}

class RouteRequest {
  const RouteRequest({
    required this.instance,
    this.metric = 'time',
    this.source,
    this.target,
    this.sourcePoint,
    this.targetPoint,
    this.algorithm = 'dijkstra',
    this.queue = 'binary_heap',
    this.compare = true,
    this.scenario = const ScenarioSpec(),
  });

  final InstanceSpec instance;
  final String metric;
  final Object? source;
  final Object? target;
  final PointCoord? sourcePoint;
  final PointCoord? targetPoint;
  final String algorithm;
  final String queue;
  final bool compare;
  final ScenarioSpec scenario;

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{
      'instance': instance.toJson(),
      'metric': metric,
      'algorithm': algorithm,
      'queue': queue,
      'compare': compare,
      'scenario': scenario.toJson(),
    };
    if (source != null) map['source'] = source;
    if (target != null) map['target'] = target;
    if (sourcePoint != null) map['source_point'] = sourcePoint!.toJson();
    if (targetPoint != null) map['target_point'] = targetPoint!.toJson();
    return map;
  }
}

class RouteEdgeDetail {
  const RouteEdgeDetail({
    required this.from,
    required this.to,
    required this.cost,
    this.lengthM,
    this.timeSec,
    this.street,
  });

  final Object from;
  final Object to;
  final double cost;
  final double? lengthM;
  final double? timeSec;
  final String? street;

  factory RouteEdgeDetail.fromJson(Map<String, dynamic> json) {
    return RouteEdgeDetail(
      from: json['from'] as Object,
      to: json['to'] as Object,
      cost: (json['cost'] as num).toDouble(),
      lengthM: (json['length_m'] as num?)?.toDouble(),
      timeSec: (json['time_sec'] as num?)?.toDouble(),
      street: json['street']?.toString(),
    );
  }
}

class RouteRow {
  const RouteRow({
    required this.algorithm,
    required this.queue,
    required this.cost,
    required this.path,
    required this.edges,
    required this.lengthM,
    required this.timeSec,
    required this.pathGeometry,
    required this.expanded,
    required this.relaxations,
    required this.decreaseKey,
    required this.elapsedMsSingleRun,
  });

  final String algorithm;
  final String queue;
  final double? cost;
  final List<Object> path;
  final List<RouteEdgeDetail> edges;
  final double? lengthM;
  final double? timeSec;
  final List<List<double>> pathGeometry;
  final int expanded;
  final int relaxations;
  final int decreaseKey;
  final double elapsedMsSingleRun;

  bool get isReachable => cost != null && path.isNotEmpty;

  factory RouteRow.fromJson(Map<String, dynamic> json) {
    final rawGeometry = (json['path_geometry'] as List<dynamic>? ?? const [])
        .whereType<List<dynamic>>()
        .map((pair) => [
              (pair[0] as num).toDouble(),
              (pair[1] as num).toDouble(),
            ])
        .toList();
    return RouteRow(
      algorithm: json['algorithm']?.toString() ?? 'dijkstra',
      queue: json['queue']?.toString() ?? 'binary_heap',
      cost: (json['cost'] as num?)?.toDouble(),
      path: (json['path'] as List<dynamic>? ?? const [])
          .whereType<Object>()
          .toList(),
      edges: (json['edges'] as List<dynamic>? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(RouteEdgeDetail.fromJson)
          .toList(),
      lengthM: (json['length_m'] as num?)?.toDouble(),
      timeSec: (json['time_sec'] as num?)?.toDouble(),
      pathGeometry: rawGeometry,
      expanded: (json['expanded'] as num).toInt(),
      relaxations: (json['relaxations'] as num).toInt(),
      decreaseKey: (json['decrease_key'] as num).toInt(),
      elapsedMsSingleRun: (json['elapsed_ms_single_run'] as num).toDouble(),
    );
  }
}

class RouteSnap {
  const RouteSnap({
    required this.requested,
    required this.node,
    required this.snapped,
    required this.offsetMApprox,
  });

  final PointCoord requested;
  final Object node;
  final PointCoord snapped;
  final double offsetMApprox;

  factory RouteSnap.fromJson(Map<String, dynamic> json) {
    return RouteSnap(
      requested: PointCoord.fromJson(
        json['requested'] as Map<String, dynamic>,
      ),
      node: json['node'] as Object,
      snapped: PointCoord.fromJson(json['snapped'] as Map<String, dynamic>),
      offsetMApprox: (json['offset_m_approx'] as num).toDouble(),
    );
  }
}

class RouteResponse {
  const RouteResponse({
    required this.network,
    required this.coverage,
    required this.nodesCount,
    required this.edgesCount,
    required this.metric,
    required this.unit,
    required this.source,
    required this.target,
    required this.sourceSnap,
    required this.targetSnap,
    required this.result,
    required this.comparisons,
    required this.pathCoords,
    required this.scenario,
    required this.geometryQuality,
    required this.warning,
  });

  final String network;
  final String coverage;
  final int nodesCount;
  final int edgesCount;
  final String metric;
  final String unit;
  final Object source;
  final Object target;
  final RouteSnap? sourceSnap;
  final RouteSnap? targetSnap;
  final RouteRow result;
  final List<RouteRow> comparisons;
  final List<List<double>> pathCoords;
  final Map<String, dynamic> scenario;
  final String geometryQuality;
  final String? warning;

  factory RouteResponse.fromJson(Map<String, dynamic> json) {
    final counts = json['counts'] as Map<String, dynamic>? ?? const {};
    final rawPathCoords = (json['path_coords'] as List<dynamic>? ?? const [])
        .whereType<List<dynamic>>()
        .map((pair) => [
              (pair[0] as num).toDouble(),
              (pair[1] as num).toDouble(),
            ])
        .toList();
    return RouteResponse(
      network: json['network']?.toString() ?? '',
      coverage: json['coverage']?.toString() ?? 'center',
      nodesCount: (counts['nodes'] as num?)?.toInt() ?? 0,
      edgesCount: (counts['edges'] as num?)?.toInt() ?? 0,
      metric: json['metric']?.toString() ?? 'time',
      unit: json['unit']?.toString() ?? 'peso',
      source: json['source'] as Object,
      target: json['target'] as Object,
      sourceSnap: json['source_snap'] is Map<String, dynamic>
          ? RouteSnap.fromJson(json['source_snap'] as Map<String, dynamic>)
          : null,
      targetSnap: json['target_snap'] is Map<String, dynamic>
          ? RouteSnap.fromJson(json['target_snap'] as Map<String, dynamic>)
          : null,
      result: RouteRow.fromJson(json['result'] as Map<String, dynamic>),
      comparisons: (json['comparisons'] as List<dynamic>? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(RouteRow.fromJson)
          .toList(),
      pathCoords: rawPathCoords,
      scenario: Map<String, dynamic>.from(
        json['scenario'] as Map<String, dynamic>? ?? const {},
      ),
      geometryQuality: json['geometry_quality']?.toString() ?? 'abstract',
      warning: json['warning']?.toString(),
    );
  }
}
