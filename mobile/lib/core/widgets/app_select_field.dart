import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class SelectOption<T> {
  const SelectOption({
    required this.value,
    required this.label,
    this.subtitle,
    this.icon,
    this.enabled = true,
  });

  final T value;
  final String label;
  final String? subtitle;
  final IconData? icon;
  final bool enabled;
}

/// Selector Material 3 basado en hoja inferior redondeada (en teléfonos) o
/// diálogo centrado (en tabletas), evitando los popups grises genéricos.
class AppSelectField<T> extends StatelessWidget {
  const AppSelectField({
    super.key,
    required this.label,
    required this.value,
    required this.options,
    required this.onChanged,
    this.helperText,
    this.leadingIcon,
  });

  final String label;
  final T value;
  final List<SelectOption<T>> options;
  final ValueChanged<T> onChanged;
  final String? helperText;
  final IconData? leadingIcon;

  SelectOption<T>? get _selected {
    for (final opt in options) {
      if (opt.value == value) return opt;
    }
    return options.isNotEmpty ? options.first : null;
  }

  Future<void> _openPicker(BuildContext context) async {
    final isWide = MediaQuery.sizeOf(context).width >= 640;
    final picked = isWide
        ? await showDialog<T>(
            context: context,
            builder: (context) => Dialog(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 440, maxHeight: 520),
                child: _PickerList<T>(
                  title: label,
                  current: value,
                  options: options,
                ),
              ),
            ),
          )
        : await showModalBottomSheet<T>(
            context: context,
            isScrollControlled: true,
            useSafeArea: true,
            backgroundColor: AppTheme.surfaceWhite,
            shape: const RoundedRectangleBorder(
              borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
            ),
            builder: (context) => ConstrainedBox(
              constraints: BoxConstraints(
                maxHeight: MediaQuery.sizeOf(context).height * 0.72,
              ),
              child: _PickerList<T>(
                title: label,
                current: value,
                options: options,
              ),
            ),
          );

    if (picked != null && picked != value) {
      onChanged(picked);
    }
  }

  @override
  Widget build(BuildContext context) {
    final active = _selected;
    return Semantics(
      button: true,
      label: '$label: ${active?.label ?? 'Seleccionar'}',
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () => _openPicker(context),
        child: IgnorePointer(
          child: InputDecorator(
            decoration: InputDecoration(
              labelText: label,
              helperText: helperText,
              helperMaxLines: 2,
              prefixIcon:
                  leadingIcon != null ? Icon(leadingIcon, size: 20) : null,
              suffixIcon: const Icon(Icons.expand_more_rounded),
            ),
            child: Text(
              active?.label ?? 'Seleccionar',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                color: AppTheme.ink,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _PickerList<T> extends StatelessWidget {
  const _PickerList({
    required this.title,
    required this.current,
    required this.options,
  });

  final String title;
  final T current;
  final List<SelectOption<T>> options;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 14, 12, 10),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
              IconButton(
                tooltip: 'Cerrar',
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.close),
              ),
            ],
          ),
        ),
        const Divider(height: 1),
        Flexible(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                for (var index = 0; index < options.length; index++) ...[
                  if (index > 0) const SizedBox(height: 6),
                  _OptionTile<T>(
                    option: options[index],
                    isSelected: options[index].value == current,
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _OptionTile<T> extends StatelessWidget {
  const _OptionTile({
    required this.option,
    required this.isSelected,
  });

  final SelectOption<T> option;
  final bool isSelected;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: isSelected ? AppTheme.maroonSoft : AppTheme.paper,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: option.enabled
            ? () => Navigator.pop(context, option.value)
            : null,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isSelected ? AppTheme.maroon : AppTheme.border,
              width: isSelected ? 1.5 : 1,
            ),
          ),
          child: Row(
            children: [
              if (option.icon != null) ...[
                Icon(
                  option.icon,
                  size: 20,
                  color: !option.enabled
                      ? AppTheme.mutedInk.withValues(alpha: 0.5)
                      : isSelected
                          ? AppTheme.maroon
                          : AppTheme.ink,
                ),
                const SizedBox(width: 12),
              ],
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      option.label,
                      style: TextStyle(
                        fontWeight:
                            isSelected ? FontWeight.w700 : FontWeight.w600,
                        color: option.enabled
                            ? (isSelected ? AppTheme.maroon : AppTheme.ink)
                            : AppTheme.mutedInk,
                      ),
                    ),
                    if (option.subtitle != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        option.subtitle!,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ],
                ),
              ),
              if (isSelected)
                const Icon(
                  Icons.check_circle,
                  color: AppTheme.maroon,
                  size: 20,
                ),
            ],
          ),
        ),
      ),
    );
  }
}
