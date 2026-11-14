class DeliveryCommit {
  const DeliveryCommit({
    required this.hash,
    required this.date,
    required this.author,
    required this.subject,
  });

  final String hash;
  final String date;
  final String author;
  final String subject;

  factory DeliveryCommit.fromJson(Map<String, dynamic> json) {
    return DeliveryCommit(
      hash: json['hash']?.toString() ?? '',
      date: json['date']?.toString() ?? '',
      author: json['author']?.toString() ?? '',
      subject: json['subject']?.toString() ?? '',
    );
  }
}

class DeliveryContributor {
  const DeliveryContributor({required this.name, required this.count});

  final String name;
  final int count;

  factory DeliveryContributor.fromJson(Map<String, dynamic> json) {
    return DeliveryContributor(
      name: json['name']?.toString() ?? '',
      count: (json['count'] as num?)?.toInt() ?? 0,
    );
  }
}

class DeliveryPilotRow {
  const DeliveryPilotRow({
    required this.profile,
    required this.nodes,
    required this.edges,
    required this.queue,
    required this.medianUs,
    required this.q1Us,
    required this.q3Us,
    required this.sampleCount,
  });

  final String profile;
  final int nodes;
  final int edges;
  final String queue;
  final double medianUs;
  final double q1Us;
  final double q3Us;
  final int sampleCount;

  factory DeliveryPilotRow.fromJson(Map<String, dynamic> json) {
    return DeliveryPilotRow(
      profile: json['profile']?.toString() ?? '',
      nodes: (json['nodes'] as num?)?.toInt() ?? 0,
      edges: (json['edges'] as num?)?.toInt() ?? 0,
      queue: json['queue']?.toString() ?? '',
      medianUs: (json['median_us'] as num?)?.toDouble() ?? 0,
      q1Us: (json['q1_us'] as num?)?.toDouble() ?? 0,
      q3Us: (json['q3_us'] as num?)?.toDouble() ?? 0,
      sampleCount: (json['sample_count'] as num?)?.toInt() ?? 0,
    );
  }
}

class DeliveryEvidence {
  const DeliveryEvidence({
    required this.generatedAtUtc,
    required this.gitHead,
    required this.gitBranch,
    required this.pythonPassed,
    required this.pythonFailed,
    required this.webPassed,
    required this.webTotal,
    required this.pilotGeneratedAtUtc,
    required this.pilotRows,
    required this.contributors,
    required this.commits,
  });

  final String generatedAtUtc;
  final String gitHead;
  final String gitBranch;
  final int pythonPassed;
  final int pythonFailed;
  final int webPassed;
  final int webTotal;
  final String pilotGeneratedAtUtc;
  final List<DeliveryPilotRow> pilotRows;
  final List<DeliveryContributor> contributors;
  final List<DeliveryCommit> commits;

  factory DeliveryEvidence.fromJson(Map<String, dynamic> json) {
    final git = json['git'] as Map<String, dynamic>? ?? const {};
    final tests = json['tests'] as Map<String, dynamic>? ?? const {};
    final py = tests['python'] as Map<String, dynamic>? ?? const {};
    final web = tests['web'] as Map<String, dynamic>? ?? const {};
    final pilot = json['pilot'] as Map<String, dynamic>? ?? const {};

    return DeliveryEvidence(
      generatedAtUtc: json['generated_at_utc']?.toString() ?? '',
      gitHead: git['head']?.toString() ?? '',
      gitBranch: git['branch']?.toString() ?? '',
      pythonPassed: (py['passed'] as num?)?.toInt() ?? 0,
      pythonFailed: (py['failed'] as num?)?.toInt() ?? 0,
      webPassed: (web['passed'] as num?)?.toInt() ?? 0,
      webTotal: (web['total'] as num?)?.toInt() ?? 0,
      pilotGeneratedAtUtc: pilot['generated_at_utc']?.toString() ?? '',
      pilotRows: (pilot['rows'] as List<dynamic>? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(DeliveryPilotRow.fromJson)
          .toList(),
      contributors: (json['contributors'] as List<dynamic>? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(DeliveryContributor.fromJson)
          .toList(),
      commits: (json['commits'] as List<dynamic>? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(DeliveryCommit.fromJson)
          .toList(),
    );
  }
}
