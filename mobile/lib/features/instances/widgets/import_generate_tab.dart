import 'dart:math';

import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_select_field.dart';
import '../../../data/models/catalog_models.dart';
import '../../../data/models/editable_graph.dart';

class ImportGenerateTab extends StatefulWidget {
  const ImportGenerateTab({
    super.key,
    required this.limits,
    required this.generating,
    required this.onImportParsed,
    required this.onPickFile,
    required this.onGenerateOfficial,
  });

  final ApiLimits limits;
  final bool generating;
  final Future<void> Function(EditableGraph graph, String sourceLabel)
  onImportParsed;
  final Future<String?> Function() onPickFile;
  final Future<void> Function({
    required String generator,
    required int seed,
    required int nodes,
    required int rows,
    required int cols,
  })
  onGenerateOfficial;

  @override
  State<ImportGenerateTab> createState() => _ImportGenerateTabState();
}

class _ImportGenerateTabState extends State<ImportGenerateTab> {
  final _textCtrl = TextEditingController(
    text: 'directed\nsource A\nA B 4\nB C 2\nA C 9',
  );
  final _nameCtrl = TextEditingController(text: 'instancia_importada');
  String? _importError;

  String _generator = 'random';
  final _seedCtrl = TextEditingController(text: '42');
  final _nodesCtrl = TextEditingController(text: '30');
  final _rowsCtrl = TextEditingController(text: '5');
  final _colsCtrl = TextEditingController(text: '5');
  String? _genError;

  @override
  void dispose() {
    _textCtrl.dispose();
    _nameCtrl.dispose();
    _seedCtrl.dispose();
    _nodesCtrl.dispose();
    _rowsCtrl.dispose();
    _colsCtrl.dispose();
    super.dispose();
  }

  Future<void> _parseAndLoad() async {
    final raw = _textCtrl.text.trim();
    if (raw.isEmpty) {
      setState(() => _importError = 'Pega un JSON o lista de aristas.');
      return;
    }
    try {
      final fallback = _nameCtrl.text.trim().isEmpty
          ? 'instancia_importada'
          : _nameCtrl.text.trim();
      final EditableGraph graph;
      if (raw.startsWith('{')) {
        graph = EditableGraph.fromJsonString(raw, fallbackName: fallback);
      } else {
        graph = EditableGraph.fromEdgeListText(raw, name: fallback);
      }
      setState(() => _importError = null);
      await widget.onImportParsed(graph, raw.startsWith('{') ? 'json' : 'text');
    } on FormatException catch (err) {
      setState(() => _importError = err.message);
    } catch (err) {
      setState(() => _importError = err.toString());
    }
  }

  Future<void> _pickDeviceFile() async {
    try {
      final content = await widget.onPickFile();
      if (content == null) return;
      _textCtrl.text = content;
      await _parseAndLoad();
    } catch (err) {
      setState(() => _importError = err.toString());
    }
  }

  Future<void> _submitGenerate() async {
    final limits = widget.limits;
    final seed = int.tryParse(_seedCtrl.text.trim());
    if (seed == null || seed < limits.seedMin || seed > limits.seedMax) {
      setState(() {
        _genError =
            'Semilla: entero entre ${limits.seedMin} y ${limits.seedMax} (se admite 0).';
      });
      return;
    }

    if (_generator == 'grid') {
      final rows = int.tryParse(_rowsCtrl.text.trim());
      final cols = int.tryParse(_colsCtrl.text.trim());
      if (rows == null ||
          cols == null ||
          rows < limits.generatorGridMin ||
          rows > limits.generatorGridMax ||
          cols < limits.generatorGridMin ||
          cols > limits.generatorGridMax ||
          rows * cols < 2) {
        setState(() {
          _genError =
              'Filas y columnas entre ${limits.generatorGridMin} y ${limits.generatorGridMax}, con al menos 2 vértices.';
        });
        return;
      }
      setState(() => _genError = null);
      await widget.onGenerateOfficial(
        generator: 'grid',
        seed: seed,
        nodes: rows * cols,
        rows: rows,
        cols: cols,
      );
      return;
    }

    final nodes = int.tryParse(_nodesCtrl.text.trim());
    if (nodes == null ||
        nodes < limits.generatorNodesMin ||
        nodes > limits.generatorNodesMax) {
      setState(() {
        _genError =
            'Vértices: entero entre ${limits.generatorNodesMin} y ${limits.generatorNodesMax}.';
      });
      return;
    }
    setState(() => _genError = null);
    await widget.onGenerateOfficial(
      generator: _generator,
      seed: seed,
      nodes: nodes,
      rows: 5,
      cols: 5,
    );
  }

  @override
  Widget build(BuildContext context) {
    final limits = widget.limits;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Importar archivo o pegar JSON / CSV / TXT',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 6),
                Text(
                  'Admite JSON genérico o vial, listas «u v w» con directivas directed/undirected/source/node, y archivos CSV con cabecera.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _nameCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Nombre del borrador al importar',
                  ),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: _textCtrl,
                  maxLines: 6,
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 13),
                  decoration: const InputDecoration(
                    labelText: 'Contenido JSON o lista de aristas',
                    alignLabelWithHint: true,
                  ),
                ),
                if (_importError != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    _importError!,
                    style: const TextStyle(color: AppTheme.errorRed),
                  ),
                ],
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    FilledButton.icon(
                      onPressed: _parseAndLoad,
                      icon: const Icon(Icons.playlist_add_check, size: 18),
                      label: const Text('Cargar y guardar borrador'),
                    ),
                    OutlinedButton.icon(
                      onPressed: _pickDeviceFile,
                      icon: const Icon(Icons.folder_open_outlined, size: 18),
                      label: const Text('Elegir archivo del teléfono'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Generar una red',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 6),
                Text(
                  'Requiere conexión. La misma semilla y parámetros generan la misma red que en la web. El grafo completo se guarda en este dispositivo.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 12),
                AppSelectField<String>(
                  label: 'Perfil de red',
                  value: _generator,
                  leadingIcon: Icons.hub_outlined,
                  options: const [
                    SelectOption(
                      value: 'random',
                      label: 'Red local aleatoria',
                      subtitle: 'Árbol de conectividad más aristas locales',
                    ),
                    SelectOption(
                      value: 'grid',
                      label: 'Cuadrícula urbana',
                      subtitle: 'Malla filas × columnas con múltiples empates',
                    ),
                    SelectOption(
                      value: 'sparse',
                      label: 'Disperso (E ≈ 4V)',
                      subtitle: 'Baja densidad, representativo de redes viales',
                    ),
                    SelectOption(
                      value: 'dense',
                      label: 'Denso (8% aristas posibles)',
                      subtitle: 'Alta densidad para exigir decrease-key',
                    ),
                  ],
                  onChanged: (v) => setState(() => _generator = v),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _seedCtrl,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(
                          labelText:
                              'Semilla (${limits.seedMin}–${limits.seedMax})',
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    IconButton.outlined(
                      tooltip: 'Semilla aleatoria',
                      onPressed: () {
                        _seedCtrl.text = Random().nextInt(100000).toString();
                      },
                      icon: const Icon(Icons.casino_outlined),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                if (_generator == 'grid')
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _rowsCtrl,
                          keyboardType: TextInputType.number,
                          decoration: InputDecoration(
                            labelText:
                                'Filas (${limits.generatorGridMin}–${limits.generatorGridMax})',
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: TextField(
                          controller: _colsCtrl,
                          keyboardType: TextInputType.number,
                          decoration: InputDecoration(
                            labelText:
                                'Columnas (${limits.generatorGridMin}–${limits.generatorGridMax})',
                          ),
                        ),
                      ),
                    ],
                  )
                else
                  TextField(
                    controller: _nodesCtrl,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText:
                          'Vértices (${limits.generatorNodesMin}–${limits.generatorNodesMax})',
                    ),
                  ),
                if (_genError != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    _genError!,
                    style: const TextStyle(color: AppTheme.errorRed),
                  ),
                ],
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: widget.generating ? null : _submitGenerate,
                  icon: widget.generating
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.auto_graph, size: 18),
                  label: Text(
                    widget.generating
                        ? 'Generando y guardando…'
                        : 'Generar y guardar',
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
