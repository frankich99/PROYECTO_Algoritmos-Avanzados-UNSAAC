import 'dart:convert';

import '../../core/config/app_config.dart';

class EditableNode {
  const EditableNode({
    required this.id,
    this.name,
    this.x,
    this.y,
    this.lon,
    this.lat,
  });

  /// Conserva el tipo original (int o String) para interoperabilidad exacta con FastAPI.
  final Object id;
  final String? name;
  final double? x;
  final double? y;
  final double? lon;
  final double? lat;

  String get idText => id.toString();

  EditableNode copyWith({
    Object? id,
    String? name,
    double? x,
    double? y,
    double? lon,
    double? lat,
  }) {
    return EditableNode(
      id: id ?? this.id,
      name: name ?? this.name,
      x: x ?? this.x,
      y: y ?? this.y,
      lon: lon ?? this.lon,
      lat: lat ?? this.lat,
    );
  }

  dynamic toJson() {
    final hasExtra =
        name != null || x != null || y != null || lon != null || lat != null;
    if (!hasExtra) return id;
    final map = <String, dynamic>{'id': id};
    if (name != null && name!.isNotEmpty) map['name'] = name;
    if (x != null && y != null) {
      map['x'] = x;
      map['y'] = y;
    }
    if (lon != null && lat != null) {
      map['lon'] = lon;
      map['lat'] = lat;
    }
    return map;
  }
}

class EditableEdge {
  const EditableEdge({
    required this.origin,
    required this.destination,
    this.weight,
    this.lengthM,
    this.streetType,
    this.gradientPct,
    this.streetName,
    this.travelTimeSec,
  });

  final Object origin;
  final Object destination;
  final double? weight;
  final double? lengthM;
  final String? streetType;
  final double? gradientPct;
  final String? streetName;
  final double? travelTimeSec;

  bool get isRoadEdge => lengthM != null;

  EditableEdge copyWith({
    Object? origin,
    Object? destination,
    double? weight,
    double? lengthM,
    String? streetType,
    double? gradientPct,
    String? streetName,
    double? travelTimeSec,
  }) {
    return EditableEdge(
      origin: origin ?? this.origin,
      destination: destination ?? this.destination,
      weight: weight ?? this.weight,
      lengthM: lengthM ?? this.lengthM,
      streetType: streetType ?? this.streetType,
      gradientPct: gradientPct ?? this.gradientPct,
      streetName: streetName ?? this.streetName,
      travelTimeSec: travelTimeSec ?? this.travelTimeSec,
    );
  }

  Map<String, dynamic> toJson() {
    if (isRoadEdge) {
      final map = <String, dynamic>{
        'origin': origin,
        'destination': destination,
        'length_m': lengthM,
        'street_type': streetType ?? 'calle_centro',
        'gradient_pct': gradientPct ?? 0.0,
      };
      if (streetName != null && streetName!.isNotEmpty) {
        map['street_name'] = streetName;
      }
      if (travelTimeSec != null) {
        map['travel_time_sec'] = travelTimeSec;
      }
      return map;
    }
    final w = weight ?? 1.0;
    return {
      'origin': origin,
      'destination': destination,
      'weight': w == w.roundToDouble() ? w.toInt() : w,
    };
  }
}

/// Representación editable en memoria y serializable sin pérdida entre JSON,
/// lista de aristas CSV/TXT y el contrato de `python/src/io/graph_io.py`.
class EditableGraph {
  const EditableGraph({
    required this.name,
    required this.directed,
    required this.metric,
    this.defaultSource,
    required this.nodes,
    required this.edges,
    this.metadata = const {},
  });

  final String name;
  final bool directed;
  final String metric;
  final Object? defaultSource;
  final List<EditableNode> nodes;
  final List<EditableEdge> edges;
  final Map<String, dynamic> metadata;

  bool get isRoadBased =>
      edges.isNotEmpty && edges.every((edge) => edge.isRoadEdge);

  EditableGraph copyWith({
    String? name,
    bool? directed,
    String? metric,
    Object? defaultSource,
    bool clearDefaultSource = false,
    List<EditableNode>? nodes,
    List<EditableEdge>? edges,
    Map<String, dynamic>? metadata,
  }) {
    return EditableGraph(
      name: name ?? this.name,
      directed: directed ?? this.directed,
      metric: metric ?? this.metric,
      defaultSource:
          clearDefaultSource ? null : (defaultSource ?? this.defaultSource),
      nodes: nodes ?? this.nodes,
      edges: edges ?? this.edges,
      metadata: metadata ?? this.metadata,
    );
  }

  /// Resuelve un texto ingresado por el usuario respetando el tipo (int vs String)
  /// de un nodo existente si coincide, o conservando String si es nuevo.
  Object resolveTypedId(String raw) {
    final trimmed = raw.trim();
    for (final node in nodes) {
      if (node.id.toString() == trimmed) return node.id;
    }
    return trimmed;
  }

  static Object? _validId(dynamic raw) {
    if (raw is bool || raw == null) return null;
    if (raw is int) return raw;
    if (raw is String && raw.trim().isNotEmpty) return raw;
    return null;
  }

  static double? _finiteDouble(dynamic raw) {
    if (raw is bool || raw == null) return null;
    if (raw is num) {
      final d = raw.toDouble();
      return d.isFinite ? d : null;
    }
    if (raw is String) {
      final parsed = double.tryParse(raw.trim());
      return (parsed != null && parsed.isFinite) ? parsed : null;
    }
    return null;
  }

  factory EditableGraph.fromJsonMap(
    Map<String, dynamic> data, {
    String fallbackName = 'instancia_movil',
  }) {
    if (!data.containsKey('edges') || data['edges'] is! List) {
      throw const FormatException("El JSON debe contener una lista 'edges'.");
    }

    final parsedNodes = <EditableNode>[];
    final declaredIds = <String>{};
    final rawNodes = data['nodes'];
    if (rawNodes != null) {
      if (rawNodes is! List) {
        throw const FormatException("'nodes' debe ser una lista.");
      }
      for (var i = 0; i < rawNodes.length; i++) {
        final item = rawNodes[i];
        if (item is Map<String, dynamic>) {
          final id = _validId(item['id']);
          if (id == null) {
            throw FormatException(
              'Vértice #${i + 1}: falta un identificador texto o entero válido.',
            );
          }
          declaredIds.add(id.toString());
          parsedNodes.add(
            EditableNode(
              id: id,
              name: item['name']?.toString(),
              x: _finiteDouble(item['x']),
              y: _finiteDouble(item['y']),
              lon: _finiteDouble(item['lon']),
              lat: _finiteDouble(item['lat']),
            ),
          );
        } else {
          final id = _validId(item);
          if (id == null) {
            throw FormatException(
              'Vértice #${i + 1}: identificador debe ser texto o entero.',
            );
          }
          declaredIds.add(id.toString());
          parsedNodes.add(EditableNode(id: id));
        }
      }
    }

    final rawEdges = data['edges'] as List<dynamic>;
    final parsedEdges = <EditableEdge>[];
    for (var i = 0; i < rawEdges.length; i++) {
      final item = rawEdges[i];
      if (item is List && item.length == 3) {
        final u = _validId(item[0]);
        final v = _validId(item[1]);
        final w = _finiteDouble(item[2]);
        if (u == null || v == null || w == null) {
          throw FormatException(
            'Arista #${i + 1}: formato [origen, destino, peso] inválido.',
          );
        }
        parsedEdges.add(EditableEdge(origin: u, destination: v, weight: w));
        if (rawNodes == null) {
          for (final end in [u, v]) {
            if (declaredIds.add(end.toString())) {
              parsedNodes.add(EditableNode(id: end));
            }
          }
        }
      } else if (item is Map<String, dynamic>) {
        final u = _validId(item['origin'] ?? item['u'] ?? item['from']);
        final v = _validId(item['destination'] ?? item['v'] ?? item['to']);
        if (u == null || v == null) {
          throw FormatException(
            "Arista #${i + 1}: faltan 'origin'/'destination' válidos.",
          );
        }
        final lengthM = _finiteDouble(item['length_m']);
        final weight = _finiteDouble(item['weight']);
        final travelTime = _finiteDouble(item['travel_time_sec']);
        if (lengthM == null && weight == null && travelTime == null) {
          throw FormatException(
            "Arista #${i + 1}: falta 'weight' o 'length_m' numérico finito.",
          );
        }
        parsedEdges.add(
          EditableEdge(
            origin: u,
            destination: v,
            weight: weight ?? travelTime,
            lengthM: lengthM,
            streetType: item['street_type']?.toString(),
            gradientPct: _finiteDouble(item['gradient_pct']),
            streetName: item['street_name']?.toString(),
            travelTimeSec: travelTime,
          ),
        );
        if (rawNodes == null) {
          for (final end in [u, v]) {
            if (declaredIds.add(end.toString())) {
              parsedNodes.add(EditableNode(id: end));
            }
          }
        }
      } else {
        throw FormatException('Arista #${i + 1}: estructura no reconocida.');
      }
    }

    return EditableGraph(
      name: data['name']?.toString().trim().isNotEmpty == true
          ? data['name'].toString()
          : fallbackName,
      directed: data['directed'] != false,
      metric: data['metric']?.toString() ?? 'weight',
      defaultSource: _validId(data['source']),
      nodes: parsedNodes,
      edges: parsedEdges,
      metadata: data['metadata'] is Map<String, dynamic>
          ? Map<String, dynamic>.from(data['metadata'] as Map<String, dynamic>)
          : const {},
    );
  }

  factory EditableGraph.fromJsonString(
    String rawJson, {
    String fallbackName = 'instancia_movil',
  }) {
    final decoded = jsonDecode(rawJson);
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException(
        "El JSON debe ser un objeto con las claves 'nodes' y 'edges'.",
      );
    }
    return EditableGraph.fromJsonMap(decoded, fallbackName: fallbackName);
  }

  /// Parsea texto plano o CSV compatible con `parse_edge_list` de Python.
  factory EditableGraph.fromEdgeListText(
    String rawText, {
    String name = 'lista_importada',
  }) {
    final lines = rawText.split(RegExp(r'\r?\n'));
    var directed = true;
    String? source;
    final extraNodes = <String>[];
    final edges = <EditableEdge>[];
    final seenIds = <String>{};
    final nodes = <EditableNode>[];
    var checkedHeader = false;

    for (var i = 0; i < lines.length; i++) {
      final noComment = lines[i].split('#').first.trim();
      if (noComment.isEmpty) continue;
      final lower = noComment.toLowerCase();
      if (lower == 'undirected' ||
          lower == 'no_dirigido' ||
          lower == 'nodirigido') {
        directed = false;
        continue;
      }
      if (lower == 'directed' || lower == 'dirigido') {
        directed = true;
        continue;
      }

      final firstSpace = noComment.indexOf(' ');
      if (firstSpace > 0) {
        final head = noComment.substring(0, firstSpace).toLowerCase();
        final rest = noComment.substring(firstSpace + 1).trim();
        if ((head == 'node' || head == 'nodo') && rest.isNotEmpty) {
          extraNodes.addAll(rest.split(RegExp(r'\s+')));
          continue;
        }
        if ((head == 'source' || head == 'origen') && rest.isNotEmpty) {
          source = rest;
          continue;
        }
      }

      if (!checkedHeader) {
        checkedHeader = true;
        final headerParts = noComment
            .replaceAll(',', ' ')
            .replaceAll(';', ' ')
            .split(RegExp(r'\s+'))
            .map((e) => e.trim().toLowerCase())
            .toList();
        if (headerParts.length == 3 &&
            ((headerParts[0] == 'origin' &&
                    headerParts[1] == 'destination' &&
                    headerParts[2] == 'weight') ||
                (headerParts[0] == 'origen' &&
                    headerParts[1] == 'destino' &&
                    headerParts[2] == 'peso') ||
                (headerParts[0] == 'from' &&
                    headerParts[1] == 'to' &&
                    headerParts[2] == 'weight') ||
                (headerParts[0] == 'u' &&
                    headerParts[1] == 'v' &&
                    headerParts[2] == 'w'))) {
          continue;
        }
      }

      final parts = noComment
          .replaceAll(',', ' ')
          .replaceAll(';', ' ')
          .replaceAll('|', ' ')
          .split(RegExp(r'\s+'))
          .where((e) => e.isNotEmpty)
          .toList();
      if (parts.length != 3) {
        throw FormatException(
          'Línea ${i + 1}: se esperaban 3 campos «origen destino peso» y hay ${parts.length}.',
        );
      }
      final w = double.tryParse(parts[2]);
      if (w == null || !w.isFinite) {
        throw FormatException(
          'Línea ${i + 1}: el peso «${parts[2]}» no es numérico finito.',
        );
      }
      for (final end in [parts[0], parts[1]]) {
        if (seenIds.add(end)) {
          nodes.add(EditableNode(id: end));
        }
      }
      edges.add(EditableEdge(origin: parts[0], destination: parts[1], weight: w));
    }

    for (final extra in extraNodes) {
      if (seenIds.add(extra)) {
        nodes.add(EditableNode(id: extra));
      }
    }

    if (nodes.isEmpty && edges.isEmpty) {
      throw const FormatException('La lista de aristas está vacía.');
    }

    return EditableGraph(
      name: name,
      directed: directed,
      metric: 'weight',
      defaultSource: source,
      nodes: nodes,
      edges: edges,
    );
  }

  Map<String, dynamic> toJsonMap() {
    final map = <String, dynamic>{
      'name': name,
      'directed': directed,
      'metric': isRoadBased ? metric : 'weight',
      'nodes': nodes.map((n) => n.toJson()).toList(),
      'edges': edges.map((e) => e.toJson()).toList(),
    };
    if (defaultSource != null) {
      map['source'] = defaultSource;
    }
    if (metadata.isNotEmpty) {
      map['metadata'] = metadata;
    }
    return map;
  }

  String toPrettyJson() => const JsonEncoder.withIndent('  ').convert(toJsonMap());

  /// Exporta como lista de aristas cuando no hay atributos viales complejos.
  String toEdgeListText() {
    final buffer = StringBuffer();
    buffer.writeln('# $name');
    buffer.writeln(directed ? 'directed' : 'undirected');
    if (defaultSource != null) {
      buffer.writeln('source $defaultSource');
    }
    final connected = <String>{};
    for (final edge in edges) {
      connected.add(edge.origin.toString());
      connected.add(edge.destination.toString());
    }
    for (final node in nodes) {
      if (!connected.contains(node.idText)) {
        buffer.writeln('node ${node.idText}');
      }
    }
    for (final edge in edges) {
      final cost = edge.travelTimeSec ?? edge.lengthM ?? edge.weight ?? 1.0;
      buffer.writeln('${edge.origin} ${edge.destination} $cost');
    }
    return buffer.toString();
  }

  /// Validación local rápida de formato antes de enviar a FastAPI.
  /// No reemplaza la validación definitiva del servidor.
  List<String> validateLocally({
    int maxNodes = 5000,
    int maxEdges = 30000,
    int maxPayloadBytes = 2000000,
  }) {
    final errors = <String>[];
    if (nodes.isEmpty) {
      errors.add('El grafo debe tener al menos un vértice.');
      return errors;
    }
    if (nodes.length > maxNodes) {
      errors.add('Supera el límite de $maxNodes vértices (${nodes.length}).');
    }
    if (edges.length > maxEdges) {
      errors.add('Supera el límite de $maxEdges aristas (${edges.length}).');
    }

    final seen = <String>{};
    final duplicated = <String>{};
    for (final node in nodes) {
      final key = node.idText.trim();
      if (key.isEmpty) {
        errors.add('Hay un vértice con identificador vacío.');
      } else if (!seen.add(key)) {
        duplicated.add(key);
      }
    }
    if (duplicated.isNotEmpty) {
      errors.add(
        'Identificadores de vértice repetidos: ${duplicated.join(', ')}.',
      );
    }

    for (var i = 0; i < edges.length; i++) {
      final e = edges[i];
      if (!seen.contains(e.origin.toString())) {
        errors.add(
          'Arista #${i + 1}: el origen «${e.origin}» no está declarado en los vértices.',
        );
      }
      if (!seen.contains(e.destination.toString())) {
        errors.add(
          'Arista #${i + 1}: el destino «${e.destination}» no está declarado en los vértices.',
        );
      }
      if (e.isRoadEdge) {
        if ((e.lengthM ?? -1) < 0) {
          errors.add(
            'Arista #${i + 1} (${e.origin}→${e.destination}): longitud negativa (${e.lengthM}).',
          );
        }
      } else {
        final w = e.weight;
        if (w == null || !w.isFinite) {
          errors.add(
            'Arista #${i + 1} (${e.origin}→${e.destination}): el peso debe ser finito.',
          );
        } else if (w < 0) {
          errors.add(
            'Arista #${i + 1} (${e.origin}→${e.destination}): peso negativo ($w). Dijkstra requiere pesos >= 0.',
          );
        }
      }
    }

    if (defaultSource != null && !seen.contains(defaultSource.toString())) {
      errors.add(
        'El origen por defecto «$defaultSource» no existe en los vértices.',
      );
    }

    final bytes = utf8.encode(jsonEncode(toJsonMap())).length;
    if (bytes > maxPayloadBytes) {
      errors.add(
        'El tamaño serializado (${(bytes / 1024).toStringAsFixed(0)} KB) supera el límite de ${(maxPayloadBytes / 1000000).toStringAsFixed(1)} MB (${AppConfig.appTitle}).',
      );
    }

    return errors;
  }
}
