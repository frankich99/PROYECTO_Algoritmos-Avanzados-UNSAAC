import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../../../data/examples/example_catalog.dart';

class ExamplesTab extends StatefulWidget {
  const ExamplesTab({
    super.key,
    required this.examples,
    required this.activeTitle,
    required this.onSelectExample,
    required this.onDuplicateToDraft,
  });

  final List<BundledExample> examples;
  final String? activeTitle;
  final void Function(BundledExample example) onSelectExample;
  final Future<void> Function(BundledExample example) onDuplicateToDraft;

  @override
  State<ExamplesTab> createState() => _ExamplesTabState();
}

class _ExamplesTabState extends State<ExamplesTab> {
  String _category = 'all';

  static const _categories = [
    ('all', 'Todos'),
    ('didactic', 'Didácticos'),
    ('cusco', 'Cusco / OSM'),
    ('edge_cases', 'Casos borde'),
    ('invalid', 'Inválidos'),
  ];

  @override
  Widget build(BuildContext context) {
    final filtered = _category == 'all'
        ? widget.examples
        : widget.examples.where((e) => e.category == _category).toList();

    return Column(
      children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
          child: Row(
            children: [
              for (final (key, label) in _categories)
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    selected: _category == key,
                    label: Text(label),
                    selectedColor: AppTheme.maroonSoft,
                    checkmarkColor: AppTheme.maroon,
                    onSelected: (_) => setState(() => _category = key),
                  ),
                ),
            ],
          ),
        ),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 20),
            itemCount: filtered.length,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final ex = filtered[index];
              final isSelected = ex.title == widget.activeTitle;
              return _ExampleCard(
                example: ex,
                isSelected: isSelected,
                onSelect: () => widget.onSelectExample(ex),
                onDuplicate:
                    ex.isEditable ? () => widget.onDuplicateToDraft(ex) : null,
              );
            },
          ),
        ),
      ],
    );
  }
}

class _ExampleCard extends StatelessWidget {
  const _ExampleCard({
    required this.example,
    required this.isSelected,
    required this.onSelect,
    this.onDuplicate,
  });

  final BundledExample example;
  final bool isSelected;
  final VoidCallback onSelect;
  final VoidCallback? onDuplicate;

  @override
  Widget build(BuildContext context) {
    final borderColor = isSelected ? AppTheme.gold : AppTheme.border;
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: borderColor, width: isSelected ? 2 : 1),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              spacing: 8,
              runSpacing: 6,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                _TagChip(
                  label: example.validExpected
                      ? (example.isServerSnapshot
                          ? 'Snapshot OSM'
                          : example.format.toUpperCase())
                      : 'Caso inválido',
                  color: example.validExpected
                      ? AppTheme.maroonSoft
                      : AppTheme.errorBg,
                  textColor: example.validExpected
                      ? AppTheme.maroon
                      : AppTheme.errorRed,
                ),
                _TagChip(
                  label:
                      '${example.nodesCount} nodos · ${example.edgesCount} aristas',
                  color: AppTheme.paper,
                  textColor: AppTheme.ink,
                ),
                _TagChip(
                  label: example.directed ? 'Dirigido' : 'No dirigido',
                  color: AppTheme.paper,
                  textColor: AppTheme.mutedInk,
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              example.title,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(example.description),
            const SizedBox(height: 8),
            _InfoLine(label: 'Qué enseña', value: example.learningGoal),
            _InfoLine(label: 'Fuente', value: example.sourceInfo),
            _InfoLine(label: 'Pesos', value: example.weightsMeaning),
            _InfoLine(label: 'Coordenadas', value: example.coordsMeaning),
            if (example.suggestedSource != null &&
                example.suggestedTarget != null)
              _InfoLine(
                label: 'Consulta sugerida',
                value:
                    '${example.suggestedSource} → ${example.suggestedTarget} · ${_expectedSummary(example)}',
              )
            else if (!example.validExpected && example.expectedError != null)
              _InfoLine(
                label: 'Error esperado',
                value: example.expectedError!,
              ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.icon(
                  onPressed: onSelect,
                  icon: Icon(
                    isSelected ? Icons.check_circle : Icons.play_arrow_outlined,
                    size: 18,
                  ),
                  label: Text(
                    isSelected ? 'Activa · Revalidar' : 'Usar y validar',
                  ),
                ),
                if (onDuplicate != null)
                  OutlinedButton.icon(
                    onPressed: onDuplicate,
                    icon: const Icon(Icons.copy_outlined, size: 18),
                    label: const Text('Editar una copia'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _expectedSummary(BundledExample ex) {
    if (!ex.validExpected) return 'Debe rechazarse (HTTP 422)';
    if (ex.expectedCost == null) {
      return ex.expectedPath != null && ex.expectedPath!.isEmpty
          ? 'Inalcanzable (costo null)'
          : 'Por calcular en servidor';
    }
    final pathTxt = ex.expectedPath != null && ex.expectedPath!.isNotEmpty
        ? ' (${ex.expectedPath!.join(' → ')})'
        : '';
    return 'Esperado: ${ex.expectedCost} ${ex.expectedUnit}$pathTxt';
  }
}

class _TagChip extends StatelessWidget {
  const _TagChip({
    required this.label,
    required this.color,
    required this.textColor,
  });

  final String label;
  final Color color;
  final Color textColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11.5,
          fontWeight: FontWeight.w600,
          color: textColor,
          fontFeatures: AppTheme.tabularFigures,
        ),
      ),
    );
  }
}

class _InfoLine extends StatelessWidget {
  const _InfoLine({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 3),
      child: RichText(
        text: TextSpan(
          style: Theme.of(context).textTheme.bodySmall,
          children: [
            TextSpan(
              text: '$label: ',
              style: const TextStyle(
                fontWeight: FontWeight.w700,
                color: AppTheme.ink,
              ),
            ),
            TextSpan(text: value),
          ],
        ),
      ),
    );
  }
}
