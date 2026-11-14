import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../../../data/models/analysis_models.dart';

class QueueChartPoint {
  const QueueChartPoint({
    required this.nodes,
    required this.medianUs,
    required this.q1Us,
    required this.q3Us,
  });

  final int nodes;
  final double medianUs;
  final double q1Us;
  final double q3Us;
}

class BenchmarkChart extends StatelessWidget {
  const BenchmarkChart({
    super.key,
    required this.seriesByQueue,
    this.title = 'Mediana (µs) y rango Q1–Q3 por tamaño V',
  });

  final Map<String, List<QueueChartPoint>> seriesByQueue;
  final String title;

  static const Map<String, Color> queueColors = {
    'binary_heap': AppTheme.maroon,
    '4ary_heap': AppTheme.gold,
    'fibonacci_heap': Color(0xFF285F68),
  };

  static const Map<String, String> queueLabels = {
    'binary_heap': 'Binary Heap',
    '4ary_heap': '4-ary Heap',
    'fibonacci_heap': 'Fibonacci Heap',
  };

  factory BenchmarkChart.fromSeries(
    BenchmarkSeries series, {
    String title = 'Mediana (µs) y rango Q1–Q3 por tamaño V',
  }) {
    final mapped = <String, List<QueueChartPoint>>{};
    for (final q in const ['binary_heap', '4ary_heap', 'fibonacci_heap']) {
      final rows = series.data[q] ?? const <BenchmarkRow>[];
      mapped[q] = rows
          .map(
            (r) => QueueChartPoint(
              nodes: r.nodes,
              medianUs: r.medianUs,
              q1Us: r.q1Us,
              q3Us: r.q3Us,
            ),
          )
          .toList();
    }
    return BenchmarkChart(seriesByQueue: mapped, title: title);
  }

  factory BenchmarkChart.fromExperimentRows(
    List<ExperimentRow> rows, {
    String title = 'Mediana de sesión (µs) · no canónica',
  }) {
    final mapped = <String, List<QueueChartPoint>>{
      'binary_heap': [],
      '4ary_heap': [],
      'fibonacci_heap': [],
    };
    for (final r in rows) {
      mapped.putIfAbsent(r.queue, () => []).add(
            QueueChartPoint(
              nodes: r.nodes,
              medianUs: r.medianUs,
              q1Us: r.q1Us,
              q3Us: r.q3Us,
            ),
          );
    }
    for (final list in mapped.values) {
      list.sort((a, b) => a.nodes.compareTo(b.nodes));
    }
    return BenchmarkChart(seriesByQueue: mapped, title: title);
  }

  @override
  Widget build(BuildContext context) {
    final allPoints = seriesByQueue.values.expand((e) => e).toList();
    if (allPoints.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        Wrap(
          spacing: 12,
          runSpacing: 6,
          children: [
            for (final q in const ['binary_heap', '4ary_heap', 'fibonacci_heap'])
              if ((seriesByQueue[q] ?? const []).isNotEmpty)
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 12,
                      height: 12,
                      decoration: BoxDecoration(
                        color: queueColors[q],
                        borderRadius: BorderRadius.circular(3),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      queueLabels[q] ?? q,
                      style: const TextStyle(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
          ],
        ),
        const SizedBox(height: 8),
        Container(
          height: 220,
          width: double.infinity,
          decoration: BoxDecoration(
            color: AppTheme.paper,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: AppTheme.border),
          ),
          padding: const EdgeInsets.all(8),
          child: Semantics(
            label:
                'Gráfico de tiempos medianos en microsegundos por tamaño de grafo. Los valores exactos se listan en la tabla adjunta.',
            child: CustomPaint(
              painter: _BenchmarkPainter(seriesByQueue: seriesByQueue),
            ),
          ),
        ),
      ],
    );
  }
}

class _BenchmarkPainter extends CustomPainter {
  _BenchmarkPainter({required this.seriesByQueue});

  final Map<String, List<QueueChartPoint>> seriesByQueue;

  @override
  void paint(Canvas canvas, Size size) {
    final all = seriesByQueue.values.expand((e) => e).toList();
    if (all.isEmpty) return;

    final scales = all.map((e) => e.nodes).toSet().toList()..sort();
    final minV = scales.first.toDouble();
    final maxV = scales.last.toDouble();
    final maxUs = all
        .map((e) => math.max(e.q3Us, e.medianUs))
        .fold<double>(1.0, math.max);

    const leftPad = 50.0;
    const rightPad = 14.0;
    const topPad = 12.0;
    const bottomPad = 26.0;
    final plotW = math.max(40.0, size.width - leftPad - rightPad);
    final plotH = math.max(40.0, size.height - topPad - bottomPad);

    final gridPaint = Paint()
      ..color = AppTheme.border
      ..strokeWidth = 1.0;

    for (var i = 0; i <= 3; i++) {
      final frac = i / 3;
      final y = topPad + plotH * (1 - frac);
      canvas.drawLine(
        Offset(leftPad, y),
        Offset(leftPad + plotW, y),
        gridPaint,
      );
      final labelVal = maxUs * frac;
      final tp = TextPainter(
        text: TextSpan(
          text: labelVal >= 1000
              ? '${(labelVal / 1000).toStringAsFixed(1)}k'
              : labelVal.toStringAsFixed(0),
          style: const TextStyle(fontSize: 10, color: AppTheme.mutedInk),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      tp.paint(canvas, Offset(leftPad - tp.width - 6, y - tp.height / 2));
    }

    double xForNodes(int v) {
      if (scales.length == 1 || (maxV - minV).abs() < 1e-9) {
        return leftPad + plotW / 2;
      }
      return leftPad + ((v - minV) / (maxV - minV)) * plotW;
    }

    double yForUs(double us) {
      return topPad + plotH * (1 - (us / maxUs).clamp(0.0, 1.0));
    }

    for (final v in scales) {
      final x = xForNodes(v);
      final tp = TextPainter(
        text: TextSpan(
          text: 'V=$v',
          style: const TextStyle(fontSize: 10, color: AppTheme.mutedInk),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      tp.paint(canvas, Offset(x - tp.width / 2, topPad + plotH + 6));
    }

    for (final entry in seriesByQueue.entries) {
      final pts = entry.value;
      if (pts.isEmpty) continue;
      final color = BenchmarkChart.queueColors[entry.key] ?? AppTheme.maroon;
      final linePaint = Paint()
        ..color = color
        ..strokeWidth = 2.4
        ..style = PaintingStyle.stroke;

      final path = Path();
      for (var i = 0; i < pts.length; i++) {
        final pt = pts[i];
        final x = xForNodes(pt.nodes);
        final y = yForUs(pt.medianUs);
        final yQ1 = yForUs(pt.q1Us);
        final yQ3 = yForUs(pt.q3Us);

        // Barra vertical IQR (Q1..Q3)
        canvas.drawLine(
          Offset(x, yQ1),
          Offset(x, yQ3),
          Paint()
            ..color = color.withValues(alpha: 0.4)
            ..strokeWidth = 3.0,
        );

        if (i == 0) {
          path.moveTo(x, y);
        } else {
          path.lineTo(x, y);
        }
      }
      if (pts.length > 1) {
        canvas.drawPath(path, linePaint);
      }
      for (final pt in pts) {
        canvas.drawCircle(
          Offset(xForNodes(pt.nodes), yForUs(pt.medianUs)),
          4.0,
          Paint()..color = color,
        );
      }
    }
  }

  @override
  bool shouldRepaint(covariant _BenchmarkPainter oldDelegate) {
    return oldDelegate.seriesByQueue != seriesByQueue;
  }
}
