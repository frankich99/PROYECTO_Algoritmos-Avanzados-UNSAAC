import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/state_views.dart';
import '../../../data/models/editable_graph.dart';

class EditorTab extends StatefulWidget {
  const EditorTab({
    super.key,
    required this.graph,
    required this.localErrors,
    required this.onChanged,
    required this.onSaveDraft,
    required this.onValidateServer,
    required this.onExportJson,
  });

  final EditableGraph? graph;
  final List<String> localErrors;
  final void Function(EditableGraph updated) onChanged;
  final VoidCallback onSaveDraft;
  final VoidCallback onValidateServer;
  final VoidCallback onExportJson;

  @override
  State<EditorTab> createState() => _EditorTabState();
}

class _EditorTabState extends State<EditorTab> {
  late TextEditingController _nameController;
  String? _lastGraphName;

  @override
  void initState() {
    super.initState();
    _lastGraphName = widget.graph?.name;
    _nameController = TextEditingController(text: widget.graph?.name ?? '');
  }

  @override
  void didUpdateWidget(covariant EditorTab oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.graph?.name != _lastGraphName &&
        widget.graph?.name != _nameController.text) {
      _lastGraphName = widget.graph?.name;
      _nameController.text = widget.graph?.name ?? '';
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _showNodeDialog({int? editIndex}) async {
    final g = widget.graph;
    if (g == null) return;
    final existing = editIndex != null ? g.nodes[editIndex] : null;
    final idCtrl = TextEditingController(text: existing?.idText ?? '');
    final nameCtrl = TextEditingController(text: existing?.name ?? '');
    final xCtrl = TextEditingController(
      text: existing?.x?.toString() ?? existing?.lon?.toString() ?? '',
    );
    final yCtrl = TextEditingController(
      text: existing?.y?.toString() ?? existing?.lat?.toString() ?? '',
    );
    String? error;

    final saved = await showDialog<EditableNode>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text(existing == null ? 'Agregar vértice' : 'Editar vértice'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: idCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Identificador (ej. A o 1)',
                  ),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: nameCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Nombre descriptivo (opcional)',
                  ),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: xCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          signed: true,
                          decimal: true,
                        ),
                        decoration: const InputDecoration(labelText: 'X / Lon'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: yCtrl,
                        keyboardType: const TextInputType.numberWithOptions(
                          signed: true,
                          decimal: true,
                        ),
                        decoration: const InputDecoration(labelText: 'Y / Lat'),
                      ),
                    ),
                  ],
                ),
                if (error != null) ...[
                  const SizedBox(height: 10),
                  Text(
                    error!,
                    style: const TextStyle(color: AppTheme.errorRed),
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () {
                final rawId = idCtrl.text.trim();
                if (rawId.isEmpty) {
                  setDialogState(() => error = 'Ingresa un identificador.');
                  return;
                }
                final duplicate = g.nodes.asMap().entries.any(
                      (entry) =>
                          entry.key != editIndex &&
                          entry.value.idText == rawId,
                    );
                if (duplicate) {
                  setDialogState(
                    () => error = 'Ya existe un vértice con el ID «$rawId».',
                  );
                  return;
                }
                final xVal = xCtrl.text.trim().isEmpty
                    ? null
                    : double.tryParse(xCtrl.text.trim());
                final yVal = yCtrl.text.trim().isEmpty
                    ? null
                    : double.tryParse(yCtrl.text.trim());
                if ((xCtrl.text.trim().isNotEmpty && xVal == null) ||
                    (yCtrl.text.trim().isNotEmpty && yVal == null)) {
                  setDialogState(
                    () => error = 'Las coordenadas deben ser numéricas.',
                  );
                  return;
                }

                final resolvedId = existing != null && existing.idText == rawId
                    ? existing.id
                    : g.resolveTypedId(rawId);
                Navigator.pop(
                  context,
                  EditableNode(
                    id: resolvedId,
                    name: nameCtrl.text.trim().isEmpty
                        ? null
                        : nameCtrl.text.trim(),
                    x: existing?.lon == null ? xVal : null,
                    y: existing?.lat == null ? yVal : null,
                    lon: existing?.lon != null ? xVal : null,
                    lat: existing?.lat != null ? yVal : null,
                  ),
                );
              },
              child: const Text('Guardar'),
            ),
          ],
        ),
      ),
    );

    if (saved == null) return;
    final nextNodes = List<EditableNode>.from(g.nodes);
    if (editIndex == null) {
      nextNodes.add(saved);
    } else {
      nextNodes[editIndex] = saved;
    }
    widget.onChanged(g.copyWith(nodes: nextNodes));
  }

  Future<void> _showEdgeDialog({int? editIndex}) async {
    final g = widget.graph;
    if (g == null) return;
    final existing = editIndex != null ? g.edges[editIndex] : null;
    final originCtrl = TextEditingController(
      text: existing?.origin.toString() ??
          (g.nodes.isNotEmpty ? g.nodes.first.idText : ''),
    );
    final destCtrl = TextEditingController(
      text: existing?.destination.toString() ??
          (g.nodes.length > 1 ? g.nodes[1].idText : ''),
    );
    final weightCtrl = TextEditingController(
      text: existing?.weight?.toString() ?? '1',
    );
    final lengthCtrl = TextEditingController(
      text: existing?.lengthM?.toString() ?? '',
    );
    final gradientCtrl = TextEditingController(
      text: existing?.gradientPct?.toString() ?? '0',
    );
    final streetCtrl = TextEditingController(
      text: existing?.streetName ?? '',
    );
    var streetType = existing?.streetType ?? 'calle_centro';
    var roadMode = existing?.isRoadEdge ?? g.isRoadBased;
    String? error;

    final saved = await showDialog<EditableEdge>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text(existing == null ? 'Agregar arista' : 'Editar arista'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: originCtrl,
                  decoration: const InputDecoration(labelText: 'Origen'),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: destCtrl,
                  decoration: const InputDecoration(labelText: 'Destino'),
                ),
                const SizedBox(height: 10),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Atributos viales (m / pendiente)'),
                  value: roadMode,
                  onChanged: (v) => setDialogState(() => roadMode = v),
                ),
                if (!roadMode)
                  TextField(
                    controller: weightCtrl,
                    keyboardType: const TextInputType.numberWithOptions(
                      signed: true,
                      decimal: true,
                    ),
                    decoration: const InputDecoration(labelText: 'Peso (>= 0)'),
                  )
                else ...[
                  TextField(
                    controller: lengthCtrl,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                      labelText: 'Longitud (m)',
                    ),
                  ),
                  const SizedBox(height: 10),
                  DropdownButtonFormField<String>(
                    initialValue: streetType,
                    decoration: const InputDecoration(labelText: 'Tipo de vía'),
                    items: const [
                      DropdownMenuItem(
                        value: 'avenida',
                        child: Text('Avenida (35 km/h)'),
                      ),
                      DropdownMenuItem(
                        value: 'calle_centro',
                        child: Text('Calle centro (15 km/h)'),
                      ),
                      DropdownMenuItem(
                        value: 'peatonal',
                        child: Text('Peatonal (8 km/h)'),
                      ),
                    ],
                    onChanged: (v) {
                      if (v != null) setDialogState(() => streetType = v);
                    },
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: gradientCtrl,
                    keyboardType: const TextInputType.numberWithOptions(
                      signed: true,
                      decimal: true,
                    ),
                    decoration: const InputDecoration(
                      labelText: 'Pendiente (%)',
                    ),
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: streetCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Nombre de calle (opcional)',
                    ),
                  ),
                ],
                if (error != null) ...[
                  const SizedBox(height: 10),
                  Text(
                    error!,
                    style: const TextStyle(color: AppTheme.errorRed),
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () {
                final uRaw = originCtrl.text.trim();
                final vRaw = destCtrl.text.trim();
                if (uRaw.isEmpty || vRaw.isEmpty) {
                  setDialogState(
                    () => error = 'Origen y destino son obligatorios.',
                  );
                  return;
                }
                final u = g.resolveTypedId(uRaw);
                final v = g.resolveTypedId(vRaw);
                if (roadMode) {
                  final len = double.tryParse(lengthCtrl.text.trim());
                  final grad = double.tryParse(gradientCtrl.text.trim()) ?? 0.0;
                  if (len == null || !len.isFinite || len < 0) {
                    setDialogState(
                      () => error = 'Ingresa una longitud >= 0 en metros.',
                    );
                    return;
                  }
                  Navigator.pop(
                    context,
                    EditableEdge(
                      origin: u,
                      destination: v,
                      lengthM: len,
                      streetType: streetType,
                      gradientPct: grad,
                      streetName: streetCtrl.text.trim().isEmpty
                          ? null
                          : streetCtrl.text.trim(),
                    ),
                  );
                } else {
                  final w = double.tryParse(weightCtrl.text.trim());
                  if (w == null || !w.isFinite || w < 0) {
                    setDialogState(
                      () => error = 'El peso debe ser un número finito >= 0.',
                    );
                    return;
                  }
                  Navigator.pop(
                    context,
                    EditableEdge(origin: u, destination: v, weight: w),
                  );
                }
              },
              child: const Text('Guardar'),
            ),
          ],
        ),
      ),
    );

    if (saved == null) return;
    final nextEdges = List<EditableEdge>.from(g.edges);
    if (editIndex == null) {
      nextEdges.add(saved);
    } else {
      nextEdges[editIndex] = saved;
    }

    final nextNodes = List<EditableNode>.from(g.nodes);
    final existingIds = nextNodes.map((n) => n.idText).toSet();
    for (final end in [saved.origin, saved.destination]) {
      if (existingIds.add(end.toString())) {
        nextNodes.add(EditableNode(id: end));
      }
    }
    widget.onChanged(g.copyWith(nodes: nextNodes, edges: nextEdges));
  }

  @override
  Widget build(BuildContext context) {
    final g = widget.graph;
    if (g == null) {
      return const EmptyStateView(
        icon: Icons.edit_off_outlined,
        title: 'Instancia de solo lectura',
        message:
            'Los snapshots OSM de Cusco no se editan celda por celda. Selecciona un ejemplo editable, crea un borrador o importa un archivo JSON/CSV/TXT.',
      );
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (widget.localErrors.isNotEmpty) ...[
          ErrorStateBanner(
            message:
                'Revisión local de formato: ${widget.localErrors.join(' · ')} (la validación definitiva la realiza FastAPI).',
          ),
          const SizedBox(height: 12),
        ],
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Propiedades del grafo',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: _nameController,
                  decoration: const InputDecoration(
                    labelText: 'Nombre de la instancia',
                  ),
                  onChanged: (val) => widget.onChanged(g.copyWith(name: val)),
                ),
                const SizedBox(height: 8),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Grafo dirigido'),
                  subtitle: Text(
                    g.directed
                        ? 'Cada arista va solo de origen → destino.'
                        : 'Las aristas se consideran en ambos sentidos.',
                  ),
                  value: g.directed,
                  onChanged: (v) => widget.onChanged(g.copyWith(directed: v)),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    FilledButton.icon(
                      onPressed: widget.onValidateServer,
                      icon: const Icon(Icons.verified_outlined, size: 18),
                      label: const Text('Validar con FastAPI'),
                    ),
                    OutlinedButton.icon(
                      onPressed: widget.onSaveDraft,
                      icon: const Icon(Icons.save_outlined, size: 18),
                      label: const Text('Guardar borrador'),
                    ),
                    OutlinedButton.icon(
                      onPressed: widget.onExportJson,
                      icon: const Icon(Icons.share_outlined, size: 18),
                      label: const Text('Exportar / Compartir'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 14),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Vértices (${g.nodes.length})',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ),
                    OutlinedButton.icon(
                      onPressed: () => _showNodeDialog(),
                      icon: const Icon(Icons.add, size: 18),
                      label: const Text('Agregar'),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                if (g.nodes.length > 80)
                  Text(
                    'Mostrando los primeros 80 de ${g.nodes.length} vértices para mantener fluidez táctil.',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                const SizedBox(height: 6),
                for (var i = 0; i < g.nodes.length && i < 80; i++)
                  ListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    leading: CircleAvatar(
                      radius: 16,
                      backgroundColor: AppTheme.maroonSoft,
                      child: Text(
                        g.nodes[i].idText.length > 3
                            ? '${i + 1}'
                            : g.nodes[i].idText,
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.maroon,
                        ),
                      ),
                    ),
                    title: Text(
                      g.nodes[i].name != null
                          ? '${g.nodes[i].idText} · ${g.nodes[i].name}'
                          : g.nodes[i].idText,
                    ),
                    subtitle: g.nodes[i].x != null
                        ? Text('(${g.nodes[i].x}, ${g.nodes[i].y})')
                        : g.nodes[i].lat != null
                            ? Text('lat ${g.nodes[i].lat}, lon ${g.nodes[i].lon}')
                            : null,
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          tooltip: 'Editar vértice',
                          icon: const Icon(Icons.edit_outlined, size: 20),
                          onPressed: () => _showNodeDialog(editIndex: i),
                        ),
                        IconButton(
                          tooltip: 'Quitar vértice',
                          icon: const Icon(Icons.delete_outline, size: 20),
                          onPressed: () {
                            final removedId = g.nodes[i].idText;
                            final nextNodes = List<EditableNode>.from(g.nodes)
                              ..removeAt(i);
                            final nextEdges = g.edges
                                .where((e) =>
                                    e.origin.toString() != removedId &&
                                    e.destination.toString() != removedId)
                                .toList();
                            widget.onChanged(
                              g.copyWith(nodes: nextNodes, edges: nextEdges),
                            );
                          },
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 14),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Aristas (${g.edges.length})',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ),
                    OutlinedButton.icon(
                      onPressed: () => _showEdgeDialog(),
                      icon: const Icon(Icons.add, size: 18),
                      label: const Text('Agregar'),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                if (g.edges.length > 100)
                  Text(
                    'Mostrando las primeras 100 de ${g.edges.length} aristas; la exportación guarda todas.',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                const SizedBox(height: 6),
                for (var i = 0; i < g.edges.length && i < 100; i++)
                  ListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    title: Text(
                      '${g.edges[i].origin} ${g.directed ? '→' : '↔'} ${g.edges[i].destination}',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    subtitle: Text(
                      g.edges[i].isRoadEdge
                          ? '${g.edges[i].lengthM} m · ${g.edges[i].streetType ?? 'calle_centro'} (${g.edges[i].gradientPct ?? 0}%)${g.edges[i].streetName != null ? ' · ${g.edges[i].streetName}' : ''}'
                          : 'Peso: ${g.edges[i].weight}',
                      style: const TextStyle(
                        fontFeatures: AppTheme.tabularFigures,
                      ),
                    ),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          tooltip: 'Editar arista',
                          icon: const Icon(Icons.edit_outlined, size: 20),
                          onPressed: () => _showEdgeDialog(editIndex: i),
                        ),
                        IconButton(
                          tooltip: 'Quitar arista',
                          icon: const Icon(Icons.delete_outline, size: 20),
                          onPressed: () {
                            final nextEdges = List<EditableEdge>.from(g.edges)
                              ..removeAt(i);
                            widget.onChanged(g.copyWith(edges: nextEdges));
                          },
                        ),
                      ],
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
