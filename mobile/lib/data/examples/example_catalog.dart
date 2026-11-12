import 'dart:convert';

import 'package:flutter/services.dart';

import '../models/editable_graph.dart';
import '../models/instance_models.dart';

class BundledExample {
  const BundledExample({
    required this.id,
    required this.title,
    required this.category,
    required this.kind,
    required this.format,
    required this.directed,
    required this.metric,
    required this.nodesCount,
    required this.edgesCount,
    required this.description,
    required this.learningGoal,
    required this.sourceInfo,
    required this.weightsMeaning,
    required this.coordsMeaning,
    this.suggestedSource,
    this.suggestedTarget,
    this.expectedCost,
    required this.expectedUnit,
    this.expectedPath,
    required this.validExpected,
    this.expectedError,
    this.payloadJson,
    this.payloadText,
  });

  final String id;
  final String title;
  final String category;
  final String kind;
  final String format;
  final bool directed;
  final String metric;
  final int nodesCount;
  final int edgesCount;
  final String description;
  final String learningGoal;
  final String sourceInfo;
  final String weightsMeaning;
  final String coordsMeaning;
  final Object? suggestedSource;
  final Object? suggestedTarget;
  final double? expectedCost;
  final String expectedUnit;
  final List<Object>? expectedPath;
  final bool validExpected;
  final String? expectedError;
  final Map<String, dynamic>? payloadJson;
  final String? payloadText;

  bool get isEditable => format == 'json' || format == 'text';
  bool get isServerSnapshot => format == 'server_snapshot';

  InstanceSpec toInstanceSpec() {
    if (kind == 'example') {
      return const InstanceSpec(kind: 'example');
    }
    if (kind == 'center' || kind == 'urban') {
      return InstanceSpec(kind: kind);
    }
    if (kind == 'text' && payloadText != null) {
      return InstanceSpec(kind: 'text', text: payloadText);
    }
    return InstanceSpec(kind: 'custom', data: payloadJson);
  }

  EditableGraph? toEditableGraph() {
    if (payloadJson != null) {
      return EditableGraph.fromJsonMap(payloadJson!, fallbackName: title);
    }
    if (payloadText != null) {
      return EditableGraph.fromEdgeListText(payloadText!, name: title);
    }
    return null;
  }

  factory BundledExample.fromJson(Map<String, dynamic> json) {
    return BundledExample(
      id: json['id'].toString(),
      title: json['title'].toString(),
      category: json['category'].toString(),
      kind: json['kind'].toString(),
      format: json['format'].toString(),
      directed: json['directed'] != false,
      metric: json['metric'].toString(),
      nodesCount: (json['nodes_count'] as num).toInt(),
      edgesCount: (json['edges_count'] as num).toInt(),
      description: json['description'].toString(),
      learningGoal: json['learning_goal'].toString(),
      sourceInfo: json['source_info'].toString(),
      weightsMeaning: json['weights_meaning'].toString(),
      coordsMeaning: json['coords_meaning'].toString(),
      suggestedSource: json['suggested_source'],
      suggestedTarget: json['suggested_target'],
      expectedCost: (json['expected_cost'] as num?)?.toDouble(),
      expectedUnit: json['expected_unit']?.toString() ?? 'peso',
      expectedPath: (json['expected_path'] as List<dynamic>?)
          ?.whereType<Object>()
          .toList(),
      validExpected: json['valid_expected'] != false,
      expectedError: json['expected_error']?.toString(),
      payloadJson: json['payload_json'] is Map<String, dynamic>
          ? Map<String, dynamic>.from(
              json['payload_json'] as Map<String, dynamic>,
            )
          : null,
      payloadText: json['payload_text']?.toString(),
    );
  }
}

class ExampleCatalogLoader {
  static const String assetPath = 'assets/examples/catalog.json';

  static Future<List<BundledExample>> loadFromBundle([AssetBundle? bundle]) async {
    final targetBundle = bundle ?? rootBundle;
    final raw = await targetBundle.loadString(assetPath);
    final decoded = jsonDecode(raw) as Map<String, dynamic>;
    final list = decoded['examples'] as List<dynamic>? ?? const [];
    return list
        .whereType<Map<String, dynamic>>()
        .map(BundledExample.fromJson)
        .toList();
  }
}
