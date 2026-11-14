import 'package:flutter/material.dart';

import '../theme/app_theme.dart';

class ResponsiveRowItem {
  const ResponsiveRowItem({
    required this.title,
    this.badge,
    required this.cells,
    this.mobileColumns,
  });

  final String title;
  final String? badge;
  final List<String> cells;
  // Omite en la tarjeta los campos ya expresados por el título o la etiqueta.
  final List<int>? mobileColumns;
}

/// Muestra una tabla completa en pantallas anchas (>= 640 px) y tarjetas
/// estructuradas en teléfonos (< 640 px) para evitar recortes y scroll lateral.
class ResponsiveDataView extends StatelessWidget {
  const ResponsiveDataView({
    super.key,
    required this.headers,
    required this.rows,
    this.breakpoint = 640,
  });

  final List<String> headers;
  final List<ResponsiveRowItem> rows;
  final double breakpoint;

  @override
  Widget build(BuildContext context) {
    if (rows.isEmpty) return const SizedBox.shrink();

    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= breakpoint) {
          return _buildDesktopTable(context);
        }
        return _buildMobileCards(context);
      },
    );
  }

  Widget _buildDesktopTable(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.border),
      ),
      clipBehavior: Clip.antiAlias,
      child: Table(
        columnWidths: {
          for (var i = 0; i < headers.length; i++)
            i: i == 0 ? const FlexColumnWidth(1.3) : const FlexColumnWidth(1.0),
        },
        border: const TableBorder(
          horizontalInside: BorderSide(color: AppTheme.border, width: 0.8),
        ),
        children: [
          TableRow(
            decoration: const BoxDecoration(color: AppTheme.maroonSoft),
            children: [
              for (final h in headers)
                Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 10,
                  ),
                  child: Text(
                    h,
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 12.5,
                      color: AppTheme.maroon,
                    ),
                  ),
                ),
            ],
          ),
          for (var rIdx = 0; rIdx < rows.length; rIdx++)
            TableRow(
              decoration: BoxDecoration(
                color: rIdx.isEven ? AppTheme.surfaceWhite : AppTheme.paper,
              ),
              children: [
                for (var cIdx = 0; cIdx < headers.length; cIdx++)
                  Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 9,
                    ),
                    child: Text(
                      cIdx < rows[rIdx].cells.length
                          ? rows[rIdx].cells[cIdx]
                          : 'Sin dato',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: cIdx == 0
                            ? FontWeight.w600
                            : FontWeight.w400,
                        fontFeatures: AppTheme.tabularFigures,
                      ),
                    ),
                  ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildMobileCards(BuildContext context) {
    return Column(
      children: [
        for (var i = 0; i < rows.length; i++) ...[
          if (i > 0) const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: i.isEven ? AppTheme.paper : AppTheme.surfaceWhite,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppTheme.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 10,
                  runSpacing: 6,
                  children: [
                    Text(
                      rows[i].title,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        color: AppTheme.ink,
                        fontFeatures: AppTheme.tabularFigures,
                      ),
                    ),
                    if (rows[i].badge != null)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: AppTheme.maroonSoft,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          rows[i].badge!,
                          style: const TextStyle(
                            fontSize: 11.5,
                            fontWeight: FontWeight.w700,
                            color: AppTheme.maroon,
                          ),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 14,
                  runSpacing: 6,
                  children: [
                    for (final c
                        in (rows[i].mobileColumns ??
                                List.generate(headers.length, (index) => index))
                            .where(
                              (column) =>
                                  column >= 0 &&
                                  column < headers.length &&
                                  column < rows[i].cells.length,
                            ))
                      SizedBox(
                        width: 130,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              headers[c],
                              style: const TextStyle(
                                fontSize: 11,
                                color: AppTheme.mutedInk,
                              ),
                            ),
                            Text(
                              rows[i].cells[c],
                              style: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                                fontFeatures: AppTheme.tabularFigures,
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}
