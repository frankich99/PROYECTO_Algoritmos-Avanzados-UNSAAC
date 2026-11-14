import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import '../models/evidence_models.dart';

class BundledDocEntry {
  const BundledDocEntry({
    required this.id,
    required this.title,
    required this.subtitle,
    required this.assetPath,
    required this.updatedLabel,
  });

  final String id;
  final String title;
  final String subtitle;
  final String assetPath;
  final String updatedLabel;
}

class DocsRepository extends ChangeNotifier {
  DocsRepository({this.assetBundle});

  final AssetBundle? assetBundle;

  static const List<BundledDocEntry> bundledDocs = [
    BundledDocEntry(
      id: 'datos_y_modelo',
      title: 'Datos, unidades y alcance del modelo',
      subtitle: 'Diferencia entre ejemplo de 6 nodos, benchmark y snapshot OSM',
      assetPath: 'assets/docs/datos_y_modelo.md',
      updatedLabel: '05/11/2026',
    ),
    BundledDocEntry(
      id: 'segunda_entrega',
      title: 'Guía técnica de reproducción (Segunda entrega)',
      subtitle: 'Instalación, módulos, parámetros, formatos y pruebas',
      assetPath: 'assets/docs/segunda_entrega.md',
      updatedLabel: '06/11/2026',
    ),
    BundledDocEntry(
      id: 'contrato_movil_api',
      title: 'Contrato de compatibilidad Web, Móvil y API',
      subtitle: 'Límites, valores nulos, IDs mixtos y coordenadas',
      assetPath: 'assets/docs/contrato_movil_api.md',
      updatedLabel: '12/11/2026',
    ),
  ];

  DeliveryEvidence? _evidence;
  final Map<String, String> _loadedDocs = {};
  bool _initialized = false;

  DeliveryEvidence? get evidence => _evidence;
  String? docContent(String id) => _loadedDocs[id];

  Future<void> initialize() async {
    if (_initialized) return;
    _initialized = true;
    final bundle = assetBundle ?? rootBundle;
    try {
      final rawEvidence = await bundle.loadString(
        'assets/docs/delivery_evidence.json',
      );
      _evidence = DeliveryEvidence.fromJson(
        jsonDecode(rawEvidence) as Map<String, dynamic>,
      );
    } catch (_) {}

    for (final doc in bundledDocs) {
      try {
        _loadedDocs[doc.id] = await bundle.loadString(doc.assetPath);
      } catch (_) {}
    }
    notifyListeners();
  }
}
