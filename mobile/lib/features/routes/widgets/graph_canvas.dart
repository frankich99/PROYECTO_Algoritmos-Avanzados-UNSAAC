import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../../../data/models/instance_models.dart';
import '../../../data/models/route_models.dart';

class GraphCanvas extends StatefulWidget {
  const GraphCanvas({
    super.key,
    required this.preview,
    required this.route,
    required this.showNodes,
    required this.showNames,
    required this.showWeights,
    required this.showNetwork,
    required this.onlyRoute,
    required this.lockSelection,
    required this.pickMode,
    required this.onPickNode,
    required this.onPickModeChanged,
    required this.onToggleLock,
    this.isFullscreen = false,
  });

  final InstancePreview preview;
  final RouteResponse? route;
  final bool showNodes;
  final bool showNames;
  final bool showWeights;
  final bool showNetwork;
  final bool onlyRoute;
  final bool lockSelection;
  final String pickMode;
  final void Function(Object nodeId) onPickNode;
  final void Function(String mode) onPickModeChanged;
  final VoidCallback onToggleLock;
  final bool isFullscreen;

  @override
  State<GraphCanvas> createState() => _GraphCanvasState();
}

class _GraphCanvasState extends State<GraphCanvas> {
  final TransformationController _transformController =
      TransformationController();

  @override
  void didUpdateWidget(covariant GraphCanvas oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.preview.name != widget.preview.name ||
        oldWidget.preview.nodes != widget.preview.nodes) {
      _transformController.value = Matrix4.identity();
    }
  }

  @override
  void dispose() {
    _transformController.dispose();
    super.dispose();
  }

  void _zoomBy(double factor) {
    final next = _transformController.value.clone();
    next.scaleByDouble(factor, factor, 1.0, 1.0);
    _transformController.value = next;
  }

  Map<String, Offset> _computeLayout(Size size) {
    const padX = 48.0;
    const padY = 48.0;
    final usableW = math.max(120.0, size.width - padX * 2);
    final usableH = math.max(120.0, size.height - padY * 2);

    final pathIds = (widget.route?.result.path ?? const [])
        .map((e) => e.toString())
        .toList();
    final visibleIds = <String>{
      ...widget.preview.ids.take(150).map((e) => e.toString()),
      ...pathIds,
    }.toList();

    final coords = widget.preview.coords;
    final hasAllCoords =
        visibleIds.isNotEmpty && visibleIds.every((id) => coords.containsKey(id));

    final layout = <String, Offset>{};
    if (hasAllCoords) {
      final xs = visibleIds.map((id) => coords[id]![0]).toList();
      final ys = visibleIds.map((id) => coords[id]![1]).toList();
      final minX = xs.reduce(math.min);
      final maxX = xs.reduce(math.max);
      final minY = ys.reduce(math.min);
      final maxY = ys.reduce(math.max);
      final spanX = (maxX - minX).abs() < 1e-9 ? 1.0 : (maxX - minX);
      final spanY = (maxY - minY).abs() < 1e-9 ? 1.0 : (maxY - minY);

      for (final id in visibleIds) {
        final raw = coords[id]!;
        final nx = padX + ((raw[0] - minX) / spanX) * usableW;
        final ny = padY + ((maxY - raw[1]) / spanY) * usableH;
        layout[id] = Offset(nx, ny);
      }
      return layout;
    }

    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(usableW, usableH) * 0.43;
    final count = math.max(1, visibleIds.length);
    for (var i = 0; i < visibleIds.length; i++) {
      final angle = -math.pi / 2 + (2 * math.pi * i) / count;
      layout[visibleIds[i]] = Offset(
        center.dx + radius * math.cos(angle),
        center.dy + radius * math.sin(angle),
      );
    }
    return layout;
  }

  void _handleTapUp(TapUpDetails details, Size size) {
    if (widget.lockSelection) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          duration: Duration(seconds: 2),
          content: Text(
            'Vista bloqueada: explora o haz zoom libremente.',
          ),
        ),
      );
      return;
    }
    final scenePoint = _transformController.toScene(details.localPosition);
    final layout = _computeLayout(size);
    String? nearestKey;
    var bestDist = 30.0;
    for (final entry in layout.entries) {
      final dist = (entry.value - scenePoint).distance;
      if (dist < bestDist) {
        bestDist = dist;
        nearestKey = entry.key;
      }
    }
    if (nearestKey == null) return;
    for (final id in widget.preview.ids) {
      if (id.toString() == nearestKey) {
        widget.onPickNode(id);
        break;
      }
    }
  }

  void _openFullscreen() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        fullscreenDialog: true,
        builder: (context) => _FullscreenGraphScaffold(parentWidget: widget),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final routeOnly =
        widget.onlyRoute && (widget.route?.result.path.isNotEmpty ?? false);
    final height = widget.isFullscreen
        ? MediaQuery.sizeOf(context).height * 0.76
        : (MediaQuery.sizeOf(context).width >= 840 ? 420.0 : 330.0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          height: height,
          width: double.infinity,
          decoration: BoxDecoration(
            color: AppTheme.paper,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppTheme.border),
          ),
          clipBehavior: Clip.antiAlias,
          child: Stack(
            children: [
              LayoutBuilder(
                builder: (context, constraints) {
                  final canvasSize = Size(
                    constraints.maxWidth,
                    constraints.maxHeight,
                  );
                  final layout = _computeLayout(canvasSize);
                  return GestureDetector(
                    onTapUp: (details) => _handleTapUp(details, canvasSize),
                    child: InteractiveViewer(
                      transformationController: _transformController,
                      minScale: 0.65,
                      maxScale: 6.0,
                      boundaryMargin: const EdgeInsets.all(80),
                      child: CustomPaint(
                        size: canvasSize,
                        painter: _GraphPainter(
                          preview: widget.preview,
                          route: widget.route,
                          layout: layout,
                          showNodes: widget.showNodes,
                          showNames: widget.showNames,
                          showWeights: widget.showWeights,
                          showNetwork: widget.showNetwork,
                          onlyRoute: routeOnly,
                        ),
                      ),
                    ),
                  );
                },
              ),
              Positioned(
                top: 10,
                left: 10,
                child: Material(
                  elevation: 2,
                  color: AppTheme.surfaceWhite.withValues(alpha: 0.94),
                  borderRadius: BorderRadius.circular(10),
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: AppTheme.border),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _PillItem(
                          label: 'Origen',
                          active: !widget.lockSelection &&
                              widget.pickMode == 'source',
                          color: AppTheme.gold,
                          onTap: () {
                            if (widget.lockSelection) widget.onToggleLock();
                            widget.onPickModeChanged('source');
                          },
                        ),
                        const SizedBox(width: 4),
                        _PillItem(
                          label: 'Destino',
                          active: !widget.lockSelection &&
                              widget.pickMode == 'target',
                          color: AppTheme.maroon,
                          onTap: () {
                            if (widget.lockSelection) widget.onToggleLock();
                            widget.onPickModeChanged('target');
                          },
                        ),
                        const SizedBox(width: 4),
                        _PillItem(
                          icon: widget.lockSelection
                              ? Icons.lock
                              : Icons.lock_open,
                          active: widget.lockSelection,
                          color: AppTheme.ink,
                          onTap: widget.onToggleLock,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              Positioned(
                top: 10,
                right: 10,
                child: Material(
                  elevation: 2,
                  color: AppTheme.surfaceWhite.withValues(alpha: 0.94),
                  borderRadius: BorderRadius.circular(10),
                  child: Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: AppTheme.border),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _ToolBtn(
                          icon: Icons.add,
                          tooltip: 'Acercar',
                          onTap: () => _zoomBy(1.25),
                        ),
                        const Divider(height: 1, thickness: 0.8),
                        _ToolBtn(
                          icon: Icons.remove,
                          tooltip: 'Alejar',
                          onTap: () => _zoomBy(0.8),
                        ),
                        const Divider(height: 1, thickness: 0.8),
                        _ToolBtn(
                          icon: Icons.center_focus_strong,
                          tooltip: 'Restablecer zoom',
                          onTap: () {
                            _transformController.value = Matrix4.identity();
                          },
                        ),
                        const Divider(height: 1, thickness: 0.8),
                        _ToolBtn(
                          icon: widget.lockSelection
                              ? Icons.lock
                              : Icons.lock_open,
                          tooltip: widget.lockSelection
                              ? 'Desbloquear selección'
                              : 'Bloquear selección',
                          highlighted: widget.lockSelection,
                          onTap: widget.onToggleLock,
                        ),
                        if (!widget.isFullscreen) ...[
                          const Divider(height: 1, thickness: 0.8),
                          _ToolBtn(
                            icon: Icons.open_in_full,
                            tooltip: 'Ampliar grafo',
                            onTap: _openFullscreen,
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
        if (widget.preview.nodes > 150 && !routeOnly)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              'Se muestran hasta 150 nodos de fondo y todos los nodos de la ruta calculada.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        if (widget.preview.displayLimited)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              'Red grande: se simplifica la vista previa, no el cálculo en el servidor.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
      ],
    );
  }
}

class _PillItem extends StatelessWidget {
  const _PillItem({
    this.label,
    this.icon,
    required this.active,
    required this.color,
    required this.onTap,
  });

  final String? label;
  final IconData? icon;
  final bool active;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(7),
      child: Container(
        constraints: const BoxConstraints(minHeight: 34, minWidth: 34),
        padding:
            EdgeInsets.symmetric(horizontal: label != null ? 9 : 6, vertical: 6),
        decoration: BoxDecoration(
          color: active ? color : Colors.transparent,
          borderRadius: BorderRadius.circular(7),
        ),
        alignment: Alignment.center,
        child: icon != null
            ? Icon(icon, size: 16, color: active ? Colors.white : AppTheme.ink)
            : Text(
                label ?? '',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: active ? Colors.white : AppTheme.ink,
                ),
              ),
      ),
    );
  }
}

class _ToolBtn extends StatelessWidget {
  const _ToolBtn({
    required this.icon,
    required this.tooltip,
    required this.onTap,
    this.highlighted = false,
  });

  final IconData icon;
  final String tooltip;
  final VoidCallback onTap;
  final bool highlighted;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: onTap,
        child: Container(
          width: 40,
          height: 38,
          color: highlighted ? AppTheme.maroonSoft : Colors.transparent,
          alignment: Alignment.center,
          child: Icon(
            icon,
            size: 19,
            color: highlighted ? AppTheme.maroon : AppTheme.ink,
          ),
        ),
      ),
    );
  }
}

class _FullscreenGraphScaffold extends StatefulWidget {
  const _FullscreenGraphScaffold({required this.parentWidget});

  final GraphCanvas parentWidget;

  @override
  State<_FullscreenGraphScaffold> createState() =>
      _FullscreenGraphScaffoldState();
}

class _FullscreenGraphScaffoldState extends State<_FullscreenGraphScaffold> {
  late bool _locked = widget.parentWidget.lockSelection;
  late String _pickMode = widget.parentWidget.pickMode;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.parentWidget.preview.name)),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: GraphCanvas(
            preview: widget.parentWidget.preview,
            route: widget.parentWidget.route,
            showNodes: widget.parentWidget.showNodes,
            showNames: widget.parentWidget.showNames,
            showWeights: widget.parentWidget.showWeights,
            showNetwork: widget.parentWidget.showNetwork,
            onlyRoute: widget.parentWidget.onlyRoute,
            lockSelection: _locked,
            pickMode: _pickMode,
            onPickNode: widget.parentWidget.onPickNode,
            onPickModeChanged: (m) {
              setState(() => _pickMode = m);
              widget.parentWidget.onPickModeChanged(m);
            },
            onToggleLock: () {
              setState(() => _locked = !_locked);
              widget.parentWidget.onToggleLock();
            },
            isFullscreen: true,
          ),
        ),
      ),
    );
  }
}

class _GraphPainter extends CustomPainter {
  _GraphPainter({
    required this.preview,
    required this.route,
    required this.layout,
    required this.showNodes,
    required this.showNames,
    required this.showWeights,
    required this.showNetwork,
    required this.onlyRoute,
  });

  final InstancePreview preview;
  final RouteResponse? route;
  final Map<String, Offset> layout;
  final bool showNodes;
  final bool showNames;
  final bool showWeights;
  final bool showNetwork;
  final bool onlyRoute;

  @override
  void paint(Canvas canvas, Size size) {
    final routeEdges = route?.result.edges ?? const <RouteEdgeDetail>[];
    final pathPairSet = <String>{
      for (final e in routeEdges) '${e.from}|${e.to}',
    };
    final pathNodesSet = <String>{
      for (final n in (route?.result.path ?? const [])) n.toString(),
    };

    final bgEdgePaint = Paint()
      ..color = const Color(0xFF8B7355).withValues(alpha: 0.55)
      ..strokeWidth = 1.4
      ..style = PaintingStyle.stroke;

    final routeEdgePaint = Paint()
      ..color = AppTheme.maroon
      ..strokeWidth = 3.6
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;

    if (showNetwork && !onlyRoute) {
      for (final edge in preview.displayEdges) {
        final u = edge.from.toString();
        final v = edge.to.toString();
        if (pathPairSet.contains('$u|$v')) continue;
        final p1 = layout[u];
        final p2 = layout[v];
        if (p1 == null || p2 == null) continue;
        canvas.drawLine(p1, p2, bgEdgePaint);
        if (showWeights && preview.nodes <= 45) {
          _drawWeightBadge(
            canvas,
            p1,
            p2,
            _fmtWeight(edge.weight),
            selected: false,
          );
        }
      }
    }

    for (var i = 0; i < routeEdges.length; i++) {
      final edge = routeEdges[i];
      final p1 = layout[edge.from.toString()];
      final p2 = layout[edge.to.toString()];
      if (p1 == null || p2 == null) continue;
      canvas.drawLine(p1, p2, routeEdgePaint);
      _drawArrowHead(canvas, p1, p2, AppTheme.maroon);
      if (showWeights && (routeEdges.length <= 40 || i % 3 == 0)) {
        _drawWeightBadge(
          canvas,
          p1,
          p2,
          _fmtWeight(edge.cost),
          selected: true,
        );
      }
    }

    final sourceStr = route?.source.toString();
    final targetStr = route?.target.toString();
    final radius = preview.nodes < 50 ? 11.5 : 4.0;

    var labelCount = 0;
    for (final entry in layout.entries) {
      final id = entry.key;
      final pos = entry.value;
      final isSource = id == sourceStr;
      final isTarget = id == targetStr;
      final isPath = pathNodesSet.contains(id);

      if (onlyRoute && !isPath) continue;
      if (!showNodes && !isSource && !isTarget) continue;

      final fillColor = isSource
          ? AppTheme.gold
          : isTarget
              ? AppTheme.maroon
              : isPath
                  ? const Color(0xFF7A3045)
                  : const Color(0xFF315D65);
      final strokeColor = isSource
          ? const Color(0xFF4E370A)
          : isTarget
              ? AppTheme.maroonDark
              : const Color(0xFF163136);

      final nodeRadius =
          (isSource || isTarget) && preview.nodes < 50 ? 13.5 : radius;

      canvas.drawCircle(pos, nodeRadius, Paint()..color = fillColor);
      canvas.drawCircle(
        pos,
        nodeRadius,
        Paint()
          ..color = strokeColor
          ..style = PaintingStyle.stroke
          ..strokeWidth = preview.nodes < 50 ? 2.0 : 1.0,
      );

      final shouldLabel = showNodes &&
          showNames &&
          (preview.nodes <= 45 ||
              isSource ||
              isTarget ||
              (isPath && labelCount < 25) ||
              (!onlyRoute && labelCount < 20));
      if (shouldLabel) {
        labelCount += 1;
        final inside = preview.nodes < 50 && id.length <= 2;
        _drawNodeLabel(
          canvas,
          pos,
          nodeRadius,
          id,
          inside: inside,
          isEndpoint: isSource || isTarget,
        );
      }
    }
  }

  void _drawArrowHead(Canvas canvas, Offset p1, Offset p2, Color color) {
    final vec = p2 - p1;
    final len = vec.distance;
    if (len < 16) return;
    final dir = vec / len;
    final tip = p2 - dir * (preview.nodes < 50 ? 14 : 6);
    const size = 7.0;
    final left = Offset(
      tip.dx - dir.dx * size + dir.dy * (size * 0.55),
      tip.dy - dir.dy * size - dir.dx * (size * 0.55),
    );
    final right = Offset(
      tip.dx - dir.dx * size - dir.dy * (size * 0.55),
      tip.dy - dir.dy * size + dir.dx * (size * 0.55),
    );
    final path = Path()
      ..moveTo(tip.dx, tip.dy)
      ..lineTo(left.dx, left.dy)
      ..lineTo(right.dx, right.dy)
      ..close();
    canvas.drawPath(path, Paint()..color = color);
  }

  void _drawWeightBadge(
    Canvas canvas,
    Offset p1,
    Offset p2,
    String text, {
    required bool selected,
  }) {
    final vec = p2 - p1;
    final len = vec.distance;
    if (len < 24) return;
    final mid = Offset((p1.dx + p2.dx) / 2, (p1.dy + p2.dy) / 2);
    final normal = Offset(-vec.dy / len, vec.dx / len);
    final center = mid + normal * 10;

    final tp = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(
          fontSize: 9.5,
          fontWeight: FontWeight.w700,
          color: selected ? Colors.white : AppTheme.ink,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();

    final rect = Rect.fromCenter(
      center: center,
      width: tp.width + 8,
      height: tp.height + 4,
    );
    final rrect = RRect.fromRectAndRadius(rect, const Radius.circular(4));
    canvas.drawRRect(
      rrect,
      Paint()..color = selected ? AppTheme.maroon : const Color(0xFFF5F0E6),
    );
    canvas.drawRRect(
      rrect,
      Paint()
        ..color = selected ? const Color(0xFFDEC697) : const Color(0xFF9C8E81)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 0.9,
    );
    tp.paint(canvas, Offset(rect.left + 4, rect.top + 2));
  }

  void _drawNodeLabel(
    Canvas canvas,
    Offset pos,
    double radius,
    String label, {
    required bool inside,
    required bool isEndpoint,
  }) {
    final tp = TextPainter(
      text: TextSpan(
        text: label,
        style: TextStyle(
          fontSize: inside ? 10.5 : 9.5,
          fontWeight: FontWeight.w700,
          color: inside ? Colors.white : AppTheme.ink,
          backgroundColor:
              inside ? null : AppTheme.paper.withValues(alpha: 0.85),
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();

    if (inside) {
      tp.paint(canvas, Offset(pos.dx - tp.width / 2, pos.dy - tp.height / 2));
    } else {
      final dy =
          isEndpoint ? pos.dy - radius - tp.height - 3 : pos.dy + radius + 3;
      tp.paint(canvas, Offset(pos.dx - tp.width / 2, dy));
    }
  }

  String _fmtWeight(double v) =>
      v == v.roundToDouble() ? v.toInt().toString() : v.toStringAsFixed(1);

  @override
  bool shouldRepaint(covariant _GraphPainter oldDelegate) {
    return oldDelegate.preview != preview ||
        oldDelegate.route != route ||
        oldDelegate.showNodes != showNodes ||
        oldDelegate.showNames != showNames ||
        oldDelegate.showWeights != showWeights ||
        oldDelegate.showNetwork != showNetwork ||
        oldDelegate.onlyRoute != onlyRoute;
  }
}
