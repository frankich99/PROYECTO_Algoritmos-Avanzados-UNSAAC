import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import '../../../core/theme/app_theme.dart';
import '../../../data/models/instance_models.dart';
import '../../../data/models/route_models.dart';

class CuscoMapView extends StatefulWidget {
  const CuscoMapView({
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
    required this.sourcePoint,
    required this.targetPoint,
    required this.onPickPoint,
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
  final PointCoord? sourcePoint;
  final PointCoord? targetPoint;
  final void Function(PointCoord point) onPickPoint;
  final void Function(String mode) onPickModeChanged;
  final VoidCallback onToggleLock;
  final bool isFullscreen;

  @override
  State<CuscoMapView> createState() => _CuscoMapViewState();
}

class _CuscoMapViewState extends State<CuscoMapView> {
  final MapController _mapController = MapController();
  String _basemap = 'plano';
  bool _tileError = false;
  double _currentZoom = 14.2;
  LatLng _currentCenter = _cuscoCenter;

  static const LatLng _cuscoCenter = LatLng(-13.5165, -71.9788);

  List<LatLng> _networkPoints() {
    final pts = <LatLng>[];
    for (final entry in widget.preview.coords.entries) {
      if (entry.value.length >= 2) {
        pts.add(LatLng(entry.value[1], entry.value[0]));
      }
    }
    return pts;
  }

  List<LatLng> _routeLatLngs() {
    final route = widget.route;
    if (route == null) return const [];
    final raw = route.result.pathGeometry.isNotEmpty
        ? route.result.pathGeometry
        : route.pathCoords;
    return raw
        .where((pair) => pair.length >= 2)
        .map((pair) => LatLng(pair[1], pair[0]))
        .toList();
  }

  void _zoomBy(double delta) {
    final nextZoom = (_currentZoom + delta).clamp(10.0, 18.5);
    _currentZoom = nextZoom;
    _mapController.move(_currentCenter, nextZoom);
  }

  void _fitPoints(List<LatLng> points) {
    if (points.isEmpty) return;
    if (points.length == 1) {
      _mapController.move(points.first, 15.5);
      return;
    }
    final bounds = LatLngBounds.fromPoints(points);
    _mapController.fitCamera(
      CameraFit.bounds(
        bounds: bounds,
        padding: const EdgeInsets.all(42),
        maxZoom: 16.5,
      ),
    );
  }

  void _openFullscreen() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        fullscreenDialog: true,
        builder: (context) => _FullscreenMapScaffold(parentWidget: widget),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final routeOnly =
        widget.onlyRoute && (widget.route?.result.path.isNotEmpty ?? false);
    final routePoints = _routeLatLngs();
    final networkPolylines = <Polyline>[];

    if (widget.showNetwork && !routeOnly) {
      final coords = widget.preview.coords;
      for (final edge in widget.preview.displayEdges) {
        final p1 = coords[edge.from.toString()];
        final p2 = coords[edge.to.toString()];
        if (p1 == null || p2 == null) continue;
        networkPolylines.add(
          Polyline(
            points: [LatLng(p1[1], p1[0]), LatLng(p2[1], p2[0])],
            color: const Color(0xFF8B7355).withValues(alpha: 0.7),
            strokeWidth: 1.6,
          ),
        );
      }
    }

    final nodeCircles = <CircleMarker>[];
    if (widget.showNodes) {
      final pathSet = <String>{
        for (final n in (widget.route?.result.path ?? const [])) n.toString(),
      };
      var count = 0;
      for (final id in widget.preview.ids) {
        final key = id.toString();
        if (routeOnly && !pathSet.contains(key)) continue;
        if (!routeOnly && !pathSet.contains(key) && count >= 450) continue;
        final c = widget.preview.coords[key];
        if (c == null) continue;
        count += 1;
        nodeCircles.add(
          CircleMarker(
            point: LatLng(c[1], c[0]),
            radius: pathSet.contains(key) ? 4.5 : 3.0,
            color: pathSet.contains(key)
                ? AppTheme.maroon
                : const Color(0xFF1E3F44),
            borderColor: const Color(0xFFDEC697),
            borderStrokeWidth: 1,
          ),
        );
      }
    }

    final markers = <Marker>[];
    void addEndpointMarker(LatLng pos, Color color, String label) {
      markers.add(
        Marker(
          point: pos,
          width: 32,
          height: 32,
          child: Container(
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 2.2),
              boxShadow: const [
                BoxShadow(
                  color: Colors.black26,
                  blurRadius: 4,
                  offset: Offset(0, 1),
                ),
              ],
            ),
            alignment: Alignment.center,
            child: Text(
              label,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 11.5,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ),
      );
    }

    if (widget.route != null) {
      final srcC = widget.preview.coords[widget.route!.source.toString()];
      final tgtC = widget.preview.coords[widget.route!.target.toString()];
      if (srcC != null) addEndpointMarker(LatLng(srcC[1], srcC[0]), AppTheme.gold, 'O');
      if (tgtC != null) addEndpointMarker(LatLng(tgtC[1], tgtC[0]), AppTheme.maroon, 'D');
    }
    if (widget.sourcePoint != null) {
      addEndpointMarker(
        LatLng(widget.sourcePoint!.lat, widget.sourcePoint!.lon),
        AppTheme.gold,
        'O',
      );
    }
    if (widget.targetPoint != null) {
      addEndpointMarker(
        LatLng(widget.targetPoint!.lat, widget.targetPoint!.lon),
        AppTheme.maroon,
        'D',
      );
    }

    // Etiquetas de nombres/pesos sobre la ruta si están activadas
    if (widget.showNames && widget.showNodes && widget.route != null) {
      final path = widget.route!.result.path;
      final step = math.max(1, (path.length / 8).ceil());
      for (var i = 0; i < path.length; i++) {
        if (i != 0 && i != path.length - 1 && i % step != 0) continue;
        final c = widget.preview.coords[path[i].toString()];
        if (c == null) continue;
        markers.add(
          Marker(
            point: LatLng(c[1], c[0]),
            width: 86,
            height: 24,
            alignment: Alignment.topCenter,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.92),
                borderRadius: BorderRadius.circular(5),
                border: Border.all(color: AppTheme.border),
              ),
              child: Text(
                path[i].toString(),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.ink,
                ),
              ),
            ),
          ),
        );
      }
    }

    if (widget.showWeights && widget.route != null) {
      final edges = widget.route!.result.edges;
      final step = math.max(1, (edges.length / 8).ceil());
      for (var i = 0; i < edges.length; i++) {
        if (i != edges.length - 1 && i % step != 0) continue;
        final p1 = widget.preview.coords[edges[i].from.toString()];
        final p2 = widget.preview.coords[edges[i].to.toString()];
        if (p1 == null || p2 == null) continue;
        markers.add(
          Marker(
            point: LatLng((p1[1] + p2[1]) / 2, (p1[0] + p2[0]) / 2),
            width: 54,
            height: 22,
            child: Container(
              alignment: Alignment.center,
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
              decoration: BoxDecoration(
                color: AppTheme.maroon,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                edges[i].cost.toStringAsFixed(1),
                style: const TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                  fontFeatures: AppTheme.tabularFigures,
                ),
              ),
            ),
          ),
        );
      }
    }

    final mapHeight = widget.isFullscreen
        ? double.infinity
        : (MediaQuery.sizeOf(context).width >= 840 ? 440.0 : 350.0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 6,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            ChoiceChip(
              label: const Text('Plano sin conexión'),
              selected: _basemap == 'plano',
              selectedColor: AppTheme.maroonSoft,
              onSelected: (_) => setState(() {
                _basemap = 'plano';
                _tileError = false;
              }),
            ),
            ChoiceChip(
              label: const Text('Calles OSM'),
              selected: _basemap == 'calles',
              selectedColor: AppTheme.maroonSoft,
              onSelected: (_) => setState(() => _basemap = 'calles'),
            ),
          ],
        ),
        const SizedBox(height: 8),
        if (_tileError && _basemap == 'calles')
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Text(
              'No se pudieron descargar algunas teselas OSM. Puedes seguir usando «Plano sin conexión».',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        if (widget.route?.geometryQuality == 'node_chords_only')
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Text(
              'Nota: el snapshot no guarda curvas de todas las calles; el trazo une intersecciones.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
        SizedBox(
          height: widget.isFullscreen ? MediaQuery.sizeOf(context).height * 0.72 : mapHeight,
          width: double.infinity,
          child: Container(
            decoration: BoxDecoration(
              color: AppTheme.paper,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppTheme.border),
            ),
            clipBehavior: Clip.antiAlias,
            child: Stack(
              children: [
                FlutterMap(
                  mapController: _mapController,
                  options: MapOptions(
                    initialCenter: _cuscoCenter,
                    initialZoom: _currentZoom,
                    minZoom: 10,
                    maxZoom: 18.5,
                    backgroundColor: AppTheme.paper,
                    onPositionChanged: (pos, _) {
                      _currentCenter = pos.center;
                      _currentZoom = pos.zoom;
                    },
                    onTap: (_, latLng) {
                      if (widget.lockSelection) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            duration: Duration(seconds: 2),
                            content: Text(
                              'Selección bloqueada: puedes mover y hacer zoom sin cambiar origen/destino.',
                            ),
                          ),
                        );
                        return;
                      }
                      widget.onPickPoint(
                        PointCoord(lat: latLng.latitude, lon: latLng.longitude),
                      );
                    },
                  ),
                  children: [
                    if (_basemap == 'calles')
                      TileLayer(
                        urlTemplate:
                            'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                        userAgentPackageName: 'com.unsaac.rutas_cusco_mobile',
                        errorTileCallback: (_, _, _) {
                          if (!_tileError && mounted) {
                            setState(() => _tileError = true);
                          }
                        },
                      ),
                    if (networkPolylines.isNotEmpty)
                      PolylineLayer(polylines: networkPolylines),
                    if (routePoints.length > 1)
                      PolylineLayer(
                        polylines: [
                          Polyline(
                            points: routePoints,
                            color: AppTheme.maroon,
                            strokeWidth: 5.2,
                          ),
                        ],
                      ),
                    if (nodeCircles.isNotEmpty)
                      CircleLayer(circles: nodeCircles),
                    if (markers.isNotEmpty) MarkerLayer(markers: markers),
                  ],
                ),
                // Selector flotante Origen / Destino / Bloqueado arriba a la izquierda
                Positioned(
                  top: 10,
                  left: 10,
                  child: _MapModePill(
                    lockSelection: widget.lockSelection,
                    pickMode: widget.pickMode,
                    onSelectSource: () {
                      if (widget.lockSelection) widget.onToggleLock();
                      widget.onPickModeChanged('source');
                    },
                    onSelectTarget: () {
                      if (widget.lockSelection) widget.onToggleLock();
                      widget.onPickModeChanged('target');
                    },
                    onToggleLock: widget.onToggleLock,
                  ),
                ),
                // Controles flotantes de zoom, bloqueo y ajuste arriba a la derecha
                Positioned(
                  top: 10,
                  right: 10,
                  child: _MapToolColumn(
                    lockSelection: widget.lockSelection,
                    hasRoute: routePoints.isNotEmpty,
                    isFullscreen: widget.isFullscreen,
                    onZoomIn: () => _zoomBy(0.9),
                    onZoomOut: () => _zoomBy(-0.9),
                    onToggleLock: widget.onToggleLock,
                    onFitNetwork: () => _fitPoints(_networkPoints()),
                    onFitRoute: routePoints.isEmpty
                        ? null
                        : () => _fitPoints(routePoints),
                    onExpand: widget.isFullscreen ? null : _openFullscreen,
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

class _MapModePill extends StatelessWidget {
  const _MapModePill({
    required this.lockSelection,
    required this.pickMode,
    required this.onSelectSource,
    required this.onSelectTarget,
    required this.onToggleLock,
  });

  final bool lockSelection;
  final String pickMode;
  final VoidCallback onSelectSource;
  final VoidCallback onSelectTarget;
  final VoidCallback onToggleLock;

  @override
  Widget build(BuildContext context) {
    return Material(
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
            _MiniPillButton(
              label: 'Origen',
              active: !lockSelection && pickMode == 'source',
              activeColor: AppTheme.gold,
              onTap: onSelectSource,
            ),
            const SizedBox(width: 4),
            _MiniPillButton(
              label: 'Destino',
              active: !lockSelection && pickMode == 'target',
              activeColor: AppTheme.maroon,
              onTap: onSelectTarget,
            ),
            const SizedBox(width: 4),
            _MiniPillButton(
              icon: lockSelection ? Icons.lock : Icons.lock_open,
              active: lockSelection,
              activeColor: AppTheme.ink,
              tooltip: lockSelection ? 'Desbloquear toque' : 'Bloquear toque',
              onTap: onToggleLock,
            ),
          ],
        ),
      ),
    );
  }
}

class _MiniPillButton extends StatelessWidget {
  const _MiniPillButton({
    this.label,
    this.icon,
    required this.active,
    required this.activeColor,
    required this.onTap,
    this.tooltip,
  });

  final String? label;
  final IconData? icon;
  final bool active;
  final Color activeColor;
  final VoidCallback onTap;
  final String? tooltip;

  @override
  Widget build(BuildContext context) {
    final child = InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(7),
      child: Container(
        constraints: const BoxConstraints(minHeight: 34, minWidth: 34),
        padding: EdgeInsets.symmetric(horizontal: label != null ? 9 : 6, vertical: 6),
        decoration: BoxDecoration(
          color: active ? activeColor : Colors.transparent,
          borderRadius: BorderRadius.circular(7),
        ),
        alignment: Alignment.center,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null)
              Icon(
                icon,
                size: 16,
                color: active ? Colors.white : AppTheme.ink,
              ),
            if (label != null)
              Text(
                label!,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: active ? Colors.white : AppTheme.ink,
                ),
              ),
          ],
        ),
      ),
    );
    return tooltip != null ? Tooltip(message: tooltip!, child: child) : child;
  }
}

class _MapToolColumn extends StatelessWidget {
  const _MapToolColumn({
    required this.lockSelection,
    required this.hasRoute,
    required this.isFullscreen,
    required this.onZoomIn,
    required this.onZoomOut,
    required this.onToggleLock,
    required this.onFitNetwork,
    required this.onFitRoute,
    this.onExpand,
  });

  final bool lockSelection;
  final bool hasRoute;
  final bool isFullscreen;
  final VoidCallback onZoomIn;
  final VoidCallback onZoomOut;
  final VoidCallback onToggleLock;
  final VoidCallback onFitNetwork;
  final VoidCallback? onFitRoute;
  final VoidCallback? onExpand;

  @override
  Widget build(BuildContext context) {
    return Material(
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
            _MapIconButton(
              icon: Icons.add,
              tooltip: 'Acercar',
              onTap: onZoomIn,
            ),
            const Divider(height: 1, thickness: 0.8),
            _MapIconButton(
              icon: Icons.remove,
              tooltip: 'Alejar',
              onTap: onZoomOut,
            ),
            const Divider(height: 1, thickness: 0.8),
            _MapIconButton(
              icon: lockSelection ? Icons.lock : Icons.lock_open,
              tooltip: lockSelection ? 'Desbloquear mapa' : 'Bloquear mapa',
              highlighted: lockSelection,
              onTap: onToggleLock,
            ),
            const Divider(height: 1, thickness: 0.8),
            _MapIconButton(
              icon: Icons.fit_screen_outlined,
              tooltip: 'Ver toda la red',
              onTap: onFitNetwork,
            ),
            if (hasRoute) ...[
              const Divider(height: 1, thickness: 0.8),
              _MapIconButton(
                icon: Icons.route,
                tooltip: 'Centrar ruta',
                onTap: onFitRoute,
              ),
            ],
            if (!isFullscreen && onExpand != null) ...[
              const Divider(height: 1, thickness: 0.8),
              _MapIconButton(
                icon: Icons.open_in_full,
                tooltip: 'Ampliar mapa',
                onTap: onExpand,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _MapIconButton extends StatelessWidget {
  const _MapIconButton({
    required this.icon,
    required this.tooltip,
    this.onTap,
    this.highlighted = false,
  });

  final IconData icon;
  final String tooltip;
  final VoidCallback? onTap;
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
            color: onTap == null
                ? AppTheme.mutedInk.withValues(alpha: 0.4)
                : highlighted
                    ? AppTheme.maroon
                    : AppTheme.ink,
          ),
        ),
      ),
    );
  }
}

class _FullscreenMapScaffold extends StatefulWidget {
  const _FullscreenMapScaffold({required this.parentWidget});

  final CuscoMapView parentWidget;

  @override
  State<_FullscreenMapScaffold> createState() =>
      _FullscreenMapScaffoldState();
}

class _FullscreenMapScaffoldState extends State<_FullscreenMapScaffold> {
  late bool _locked = widget.parentWidget.lockSelection;
  late String _pickMode = widget.parentWidget.pickMode;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.parentWidget.preview.name),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: CuscoMapView(
            preview: widget.parentWidget.preview,
            route: widget.parentWidget.route,
            showNodes: widget.parentWidget.showNodes,
            showNames: widget.parentWidget.showNames,
            showWeights: widget.parentWidget.showWeights,
            showNetwork: widget.parentWidget.showNetwork,
            onlyRoute: widget.parentWidget.onlyRoute,
            lockSelection: _locked,
            pickMode: _pickMode,
            sourcePoint: widget.parentWidget.sourcePoint,
            targetPoint: widget.parentWidget.targetPoint,
            onPickPoint: widget.parentWidget.onPickPoint,
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
