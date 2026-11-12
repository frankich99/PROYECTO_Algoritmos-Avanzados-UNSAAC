import 'instance_models.dart';

class BenchmarkRow {
  const BenchmarkRow({
    required this.nodes,
    required this.edges,
    required this.medianUs,
    required this.q1Us,
    required this.q3Us,
    this.sampleCount,
    this.instanceSeeds,
  });

  final int nodes;
  final int edges;
  final double medianUs;
  final double q1Us;
  final double q3Us;
  final int? sampleCount;
  final List<int>? instanceSeeds;

  factory BenchmarkRow.fromJson(Map<String, dynamic> json) {
    final rawSeeds = json['instance_seeds'] as List<dynamic>?;
    return BenchmarkRow(
      nodes: (json['nodes'] as num).toInt(),
      edges: (json['edges'] as num).toInt(),
      medianUs: (json['median_us'] as num).toDouble(),
      q1Us: (json['q1_us'] as num).toDouble(),
      q3Us: (json['q3_us'] as num).toDouble(),
      sampleCount: (json['sample_count'] as num?)?.toInt(),
      instanceSeeds: rawSeeds?.map((e) => (e as num).toInt()).toList(),
    );
  }
}

class BenchmarkSeries {
  const BenchmarkSeries({required this.scales, required this.data});

  final List<int> scales;
  final Map<String, List<BenchmarkRow>> data;

  factory BenchmarkSeries.fromJson(Map<String, dynamic> json) {
    final rawData = json['data'] as Map<String, dynamic>? ?? const {};
    final parsedData = <String, List<BenchmarkRow>>{};
    for (final entry in rawData.entries) {
      final list = (entry.value as List<dynamic>? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(BenchmarkRow.fromJson)
          .toList();
      parsedData[entry.key] = list;
    }
    return BenchmarkSeries(
      scales: (json['scales'] as List<dynamic>? ?? const [])
          .map((e) => (e as num).toInt())
          .toList(),
      data: parsedData,
    );
  }
}

class BenchmarkResponse {
  const BenchmarkResponse({
    required this.generatedAtUtc,
    required this.protocol,
    required this.environment,
    required this.profile,
    required this.results,
  });

  final String? generatedAtUtc;
  final Map<String, dynamic> protocol;
  final Map<String, dynamic>? environment;
  final String profile;
  final BenchmarkSeries results;

  factory BenchmarkResponse.fromJson(Map<String, dynamic> json) {
    return BenchmarkResponse(
      generatedAtUtc: json['generated_at_utc']?.toString(),
      protocol: Map<String, dynamic>.from(
        json['protocol'] as Map<String, dynamic>? ?? const {},
      ),
      environment: json['environment'] is Map<String, dynamic>
          ? Map<String, dynamic>.from(json['environment'] as Map<String, dynamic>)
          : null,
      profile: json['profile']?.toString() ?? 'sparse',
      results: BenchmarkSeries.fromJson(
        json['results'] as Map<String, dynamic>? ?? const {},
      ),
    );
  }
}

class ExperimentRequest {
  const ExperimentRequest({
    this.profile = 'sparse',
    this.sizes = const [30, 60, 100],
    this.seed = 42,
    this.runs = 5,
  });

  final String profile;
  final List<int> sizes;
  final int seed;
  final int runs;

  Map<String, dynamic> toJson() => {
        'profile': profile,
        'sizes': sizes,
        'seed': seed,
        'runs': runs,
      };
}

class ExperimentRow {
  const ExperimentRow({
    required this.nodes,
    required this.edges,
    required this.queue,
    required this.medianUs,
    required this.q1Us,
    required this.q3Us,
    required this.samplesUs,
    required this.instanceSeeds,
  });

  final int nodes;
  final int edges;
  final String queue;
  final double medianUs;
  final double q1Us;
  final double q3Us;
  final List<double> samplesUs;
  final List<int> instanceSeeds;

  factory ExperimentRow.fromJson(Map<String, dynamic> json) {
    return ExperimentRow(
      nodes: (json['nodes'] as num).toInt(),
      edges: (json['edges'] as num).toInt(),
      queue: json['queue']?.toString() ?? 'binary_heap',
      medianUs: (json['median_us'] as num).toDouble(),
      q1Us: (json['q1_us'] as num).toDouble(),
      q3Us: (json['q3_us'] as num).toDouble(),
      samplesUs: (json['samples_us'] as List<dynamic>? ?? const [])
          .map((e) => (e as num).toDouble())
          .toList(),
      instanceSeeds: (json['instance_seeds'] as List<dynamic>? ?? const [])
          .map((e) => (e as num).toInt())
          .toList(),
    );
  }
}

class ExperimentResponse {
  const ExperimentResponse({
    required this.kind,
    required this.profile,
    required this.generatedAtUtc,
    required this.protocol,
    required this.rows,
  });

  final String kind;
  final String profile;
  final String generatedAtUtc;
  final Map<String, dynamic> protocol;
  final List<ExperimentRow> rows;

  factory ExperimentResponse.fromJson(Map<String, dynamic> json) {
    return ExperimentResponse(
      kind: json['kind']?.toString() ?? 'session_experiment_not_canonical',
      profile: json['profile']?.toString() ?? 'sparse',
      generatedAtUtc: json['generated_at_utc']?.toString() ?? '',
      protocol: Map<String, dynamic>.from(
        json['protocol'] as Map<String, dynamic>? ?? const {},
      ),
      rows: (json['rows'] as List<dynamic>? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(ExperimentRow.fromJson)
          .toList(),
    );
  }
}

class WeatherObservation {
  const WeatherObservation({
    required this.temperatureC,
    required this.relativeHumidityPct,
    required this.precipitationMm,
    required this.visibilityM,
    required this.windGustsKmh,
    required this.observedAt,
    required this.timezone,
    required this.gridPoint,
    required this.source,
    required this.weatherCode,
    required this.weatherDescription,
    this.surfacePressureHpa,
  });

  final double temperatureC;
  final double relativeHumidityPct;
  final double precipitationMm;
  final double visibilityM;
  final double windGustsKmh;
  final String observedAt;
  final String timezone;
  final PointCoord gridPoint;
  final String source;
  final int weatherCode;
  final String weatherDescription;
  final double? surfacePressureHpa;

  factory WeatherObservation.fromJson(Map<String, dynamic> json) {
    return WeatherObservation(
      temperatureC: (json['temperature_c'] as num).toDouble(),
      relativeHumidityPct: (json['relative_humidity_pct'] as num).toDouble(),
      precipitationMm: (json['precipitation_mm'] as num).toDouble(),
      visibilityM: (json['visibility_m'] as num).toDouble(),
      windGustsKmh: (json['wind_gusts_kmh'] as num).toDouble(),
      observedAt: json['observed_at']?.toString() ?? '',
      timezone: json['timezone']?.toString() ?? 'America/Lima',
      gridPoint: PointCoord.fromJson(
        json['grid_point'] as Map<String, dynamic>,
      ),
      source: json['source']?.toString() ?? '',
      weatherCode: (json['weather_code'] as num?)?.toInt() ?? 0,
      weatherDescription: json['weather_description']?.toString() ?? '',
      surfacePressureHpa: (json['surface_pressure_hpa'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'temperature_c': temperatureC,
        'relative_humidity_pct': relativeHumidityPct,
        'precipitation_mm': precipitationMm,
        'visibility_m': visibilityM,
        'wind_gusts_kmh': windGustsKmh,
        'observed_at': observedAt,
        'timezone': timezone,
        'grid_point': gridPoint.toJson(),
        'source': source,
        'weather_code': weatherCode,
        'weather_description': weatherDescription,
        'surface_pressure_hpa': surfacePressureHpa,
      };
}

class TrafficFlow {
  const TrafficFlow({
    required this.currentSpeedKmh,
    required this.freeFlowSpeedKmh,
    required this.multiplier,
    this.confidence,
    this.roadClosure,
  });

  final double currentSpeedKmh;
  final double freeFlowSpeedKmh;
  final double multiplier;
  final double? confidence;
  final bool? roadClosure;

  factory TrafficFlow.fromJson(Map<String, dynamic> json) {
    return TrafficFlow(
      currentSpeedKmh: (json['current_speed_kmh'] as num).toDouble(),
      freeFlowSpeedKmh: (json['free_flow_speed_kmh'] as num).toDouble(),
      multiplier: (json['multiplier'] as num).toDouble(),
      confidence: (json['confidence'] as num?)?.toDouble(),
      roadClosure: json['road_closure'] as bool?,
    );
  }
}

class ConditionsResponse {
  const ConditionsResponse({
    required this.kind,
    required this.requested,
    required this.fetchedAtUtc,
    this.multiplier,
    this.contributions,
    this.observation,
    this.flow,
  });

  final String kind;
  final PointCoord requested;
  final String fetchedAtUtc;
  final double? multiplier;
  final Map<String, double>? contributions;
  final WeatherObservation? observation;
  final TrafficFlow? flow;

  factory ConditionsResponse.fromJson(Map<String, dynamic> json) {
    final rawContrib = json['contributions'] as Map<String, dynamic>?;
    return ConditionsResponse(
      kind: json['kind']?.toString() ?? '',
      requested: PointCoord.fromJson(
        json['requested'] as Map<String, dynamic>,
      ),
      fetchedAtUtc: json['fetched_at_utc']?.toString() ?? '',
      multiplier: (json['multiplier'] as num?)?.toDouble(),
      contributions: rawContrib?.map(
        (key, value) => MapEntry(key, (value as num).toDouble()),
      ),
      observation: json['observation'] is Map<String, dynamic>
          ? WeatherObservation.fromJson(
              json['observation'] as Map<String, dynamic>,
            )
          : null,
      flow: json['flow'] is Map<String, dynamic>
          ? TrafficFlow.fromJson(json['flow'] as Map<String, dynamic>)
          : null,
    );
  }
}
