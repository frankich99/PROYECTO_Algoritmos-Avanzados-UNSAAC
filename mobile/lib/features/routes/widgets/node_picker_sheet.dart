import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';

Future<Object?> showNodePickerSheet({
  required BuildContext context,
  required String title,
  required List<Object> ids,
  Object? current,
}) {
  return showModalBottomSheet<Object>(
    context: context,
    isScrollControlled: true,
    useSafeArea: true,
    builder: (context) => _NodePickerBody(
      title: title,
      ids: ids,
      current: current,
    ),
  );
}

class _NodePickerBody extends StatefulWidget {
  const _NodePickerBody({
    required this.title,
    required this.ids,
    this.current,
  });

  final String title;
  final List<Object> ids;
  final Object? current;

  @override
  State<_NodePickerBody> createState() => _NodePickerBodyState();
}

class _NodePickerBodyState extends State<_NodePickerBody> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final normalized = _query.trim().toLowerCase();
    final filtered = normalized.isEmpty
        ? widget.ids
        : widget.ids
            .where((id) => id.toString().toLowerCase().contains(normalized))
            .toList();

    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.72,
      minChildSize: 0.45,
      maxChildSize: 0.92,
      builder: (context, scrollController) => Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(widget.title, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 10),
                TextField(
                  autofocus: widget.ids.length > 25,
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.search),
                    hintText: 'Filtrar por identificador de nodo…',
                  ),
                  onChanged: (v) => setState(() => _query = v),
                ),
                const SizedBox(height: 6),
                Text(
                  'Mostrando ${filtered.length} de ${widget.ids.length} vértices',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: ListView.builder(
              controller: scrollController,
              itemCount: filtered.length,
              itemBuilder: (context, index) {
                final id = filtered[index];
                final isSelected =
                    widget.current != null && id.toString() == widget.current.toString();
                return ListTile(
                  title: Text(
                    id.toString(),
                    style: TextStyle(
                      fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                      color: isSelected ? AppTheme.maroon : AppTheme.ink,
                    ),
                  ),
                  trailing: isSelected
                      ? const Icon(Icons.check, color: AppTheme.maroon)
                      : null,
                  onTap: () => Navigator.pop(context, id),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
