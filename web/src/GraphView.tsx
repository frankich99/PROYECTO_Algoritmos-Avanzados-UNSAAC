import { useEffect, useMemo, useRef, useState } from 'react'
import type { GeoJSONSource, Map as MapLibreMap, Marker, StyleSpecification } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import type { Feature, FeatureCollection, LineString, Point as GeoPoint } from 'geojson'
import type { Point, Preview, RouteResponse } from './api'

type Props = { preview: Preview | null; route: RouteResponse | null; onPick: (point: Point) => void;
  pick: 'source' | 'target'; onPickMode: (value: 'source' | 'target') => void; mapRequested: number;
  sourcePoint: Point | null; targetPoint: Point | null;
  lockSelection?: boolean; onToggleLock?: () => void }

type Layers = { showNodes: boolean; showNames: boolean; showWeights: boolean; showNetwork: boolean; onlyRoute: boolean }

function GraphSVG({ preview, route, showNodes, showNames, showWeights, showNetwork, onlyRoute }: Pick<Props, 'preview' | 'route'> & Layers) {
  const layout = useMemo(() => {
    if (!preview) return null
    const ids = [...new Set([...preview.ids.slice(0, 150).map(String), ...(route?.result.path ?? []).map(String)])]
    const positions = new Map<string, [number, number]>()
    const allCoords = ids.length > 0 && ids.every(id => Array.isArray(preview.coords[String(id)]))
    if (allCoords) {
      const xs = ids.map(id => preview.coords[String(id)][0])
      const ys = ids.map(id => preview.coords[String(id)][1])
      const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys)
      ids.forEach(id => {
        const [x, y] = preview.coords[String(id)]
        positions.set(String(id), [50 + (x - minX) / (maxX - minX || 1) * 600,
          45 + (maxY - y) / (maxY - minY || 1) * 320])
      })
    } else {
      ids.forEach((id, index) => {
        const angle = index * 2 * Math.PI / ids.length - Math.PI / 2
        positions.set(String(id), [350 + Math.cos(angle) * 240, 205 + Math.sin(angle) * 150])
      })
    }
    return positions
  }, [preview, route])

  if (!preview || !layout) return <div className="empty-map">Valida una instancia para ver su red.</div>

  const pathNodes = new Set((route?.result.path ?? []).map(String))
  const sampleNodes = new Set(preview.ids.slice(0, 20).map(String))
  const path = route?.result.path ?? []
  const nodeStep = Math.max(1, Math.ceil(path.length / 100))
  const namedPathNodes = new Set(path.filter((_, index) => index % nodeStep === 0 || index === path.length - 1).map(String))
  const routeEdges = route?.result.edges ?? []
  const weightStep = Math.max(1, Math.ceil(routeEdges.length / 100))
  const weightedPathEdges = new Set(routeEdges.filter((_, index) => index % weightStep === 0 || index === routeEdges.length - 1).map(edge => `${edge.from}|${edge.to}`))
  const selectedEdges = new Set((route?.result.edges ?? []).map(edge => `${edge.from}|${edge.to}`))

  // Mapeo de pesos para visualizarlos sobre cada arista
  const weightMap = new Map<string, number | string>()
  preview.display_edges.forEach(e => {
    const u = String(e[0]), v = String(e[1])
    if (e.length >= 3 && e[2] !== undefined && e[2] !== null) {
      weightMap.set(`${u}|${v}`, e[2])
    }
  })
  if (route?.result?.edges) {
    route.result.edges.forEach(e => {
      const u = String(e.from), v = String(e.to)
      if (e.cost !== undefined && e.cost !== null) {
        weightMap.set(`${u}|${v}`, Number.isInteger(e.cost) ? e.cost : Number(e.cost.toFixed(2)))
      }
    })
  }

  // Lista desduplicada de aristas dirigidas
  const edgeMap = new Map<string, { u: string; v: string; weight?: number | string; selected: boolean }>()
  preview.display_edges.forEach(e => {
    const u = String(e[0]), v = String(e[1])
    if (layout.has(u) && layout.has(v)) {
      const isSel = selectedEdges.has(`${u}|${v}`)
      edgeMap.set(`${u}|${v}`, { u, v, weight: weightMap.get(`${u}|${v}`), selected: isSel })
    }
  })
  if (route?.result?.edges) {
    route.result.edges.forEach(e => {
      const u = String(e.from), v = String(e.to)
      if (layout.has(u) && layout.has(v)) {
        edgeMap.set(`${u}|${v}`, { u, v, weight: weightMap.get(`${u}|${v}`) ?? e.cost, selected: true })
      }
    })
  }
  const edgeList = Array.from(edgeMap.values())
  const showBackgroundWeights = showWeights && showNetwork && !onlyRoute
  const visibleEdges = edgeList.filter(edge => edge.selected || (showNetwork && !onlyRoute))

  return <div className="graph-container" role="img" aria-label={`Grafo con ${preview.nodes} nodos y ${preview.edges} aristas. Ruta: ${route?.result.path.join(', ') || 'sin calcular'}`}>
    <svg viewBox="0 0 700 410" preserveAspectRatio="xMidYMid meet" style={{ width: '100%', height: 'auto' }}>
      <defs>
        {/* Flecha estándar: delgada y estilizada */}
        <marker id="arrow" viewBox="0 0 10 10" refX="20" refY="5" markerUnits="userSpaceOnUse" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
          <path d="M 1 2.2 L 8.5 5 L 1 7.8 L 2.8 5 z" fill="#9c8f83" />
        </marker>
        {/* Flecha de ruta óptima: afilada, delgada y elegante */}
        <marker id="arrow-selected" viewBox="0 0 10 10" refX="21" refY="5" markerUnits="userSpaceOnUse" markerWidth="10.5" markerHeight="10.5" orient="auto-start-reverse">
          <path d="M 1 2 L 9 5 L 1 8 L 3 5 z" fill="#681C32" />
        </marker>
      </defs>

      {/* 1. Líneas de aristas con grosor refinado */}
      {visibleEdges.map(({ u, v, selected }, i) => {
        const [x1, y1] = layout.get(u)!
        const [x2, y2] = layout.get(v)!
        return <line key={`line-${u}-${v}-${i}`} x1={x1} y1={y1} x2={x2} y2={y2}
          stroke={selected ? '#681C32' : '#b4a89d'}
          strokeWidth={selected ? 2.6 : 1.2}
          markerEnd={selected ? 'url(#arrow-selected)' : 'url(#arrow)'} />
      })}

      {/* 2. Etiquetas de peso y costo compactas y legibles */}
      {visibleEdges.filter((edge, index) => showWeights && (edge.selected ? weightedPathEdges.has(`${edge.u}|${edge.v}`) :
        showBackgroundWeights && (preview.nodes <= 45 || index < 20))).map(({ u, v, weight, selected }, i) => {
        if (weight === undefined || weight === null) return null
        const [x1, y1] = layout.get(u)!
        const [x2, y2] = layout.get(v)!
        const dx = x2 - x1, dy = y2 - y1
        const len = Math.hypot(dx, dy) || 1
        const midX = (x1 + x2) / 2
        const midY = (y1 + y2) / 2
        const nx = -dy / len, ny = dx / len
        const lblX = midX + nx * 10
        const lblY = midY + ny * 10
        const textStr = String(weight)
        const badgeW = Math.max(18, textStr.length * 6.5 + 8)

        return <g key={`lbl-${u}-${v}-${i}`}>
          <rect x={lblX - badgeW / 2} y={lblY - 7.5} width={badgeW} height={15} rx={3}
            fill={selected ? '#681C32' : '#f5f0e6'}
            stroke={selected ? '#dec697' : '#9c8e81'}
            strokeWidth={selected ? 1.2 : 0.9} />
          <text x={lblX} y={lblY + 3.2} textAnchor="middle" fontSize="9.5" fontWeight="700"
            fill={selected ? '#ffffff' : '#2b211d'} fontFamily="'Source Sans 3', monospace">
            {textStr}
          </text>
        </g>
      })}

      {/* 3. Nodos proporcionados con borde de alto contraste (sin blanco que se pierda en fondo claro) */}
      {[...layout].filter(([id]) => (!onlyRoute || pathNodes.has(id)) && (showNodes || id === String(route?.source) || id === String(route?.target))).map(([id, [x, y]]) => {
        const isSource = id === String(route?.source)
        const isTarget = id === String(route?.target)
        const isPath = pathNodes.has(id)
        const r = preview.nodes < 50 ? (isSource || isTarget ? 13 : 11.5) : 3.5
        const fillColor = isSource ? '#8A6418' : isTarget ? '#681C32' : isPath ? '#7a3045' : '#315D65'
        const strokeColor = isSource ? '#4e370a' : isTarget ? '#3d0d1b' : isPath ? '#481523' : '#163136'

        const isUpper = y < 205
        const nameY = isSource ? y + r + 13 : isTarget ? y - r - 6 : (isUpper ? y - r - 6 : y + r + 13)
        const nameColor = isSource ? '#543b08' : isTarget ? '#4a0e1e' : '#1f1b1c'

        const labels = (preview as Preview & { labels?: Record<string, string> }).labels
        const name = labels?.[id]
        return <g key={`node-${id}`}>
          {showNodes && showNames && name && <title>{`${id}: ${name}`}</title>}
          <circle cx={x} cy={y} r={r} fill={fillColor} stroke={strokeColor} strokeWidth={preview.nodes < 50 ? 2 : 1} />
          {showNodes && showNames && (preview.nodes <= 45 || namedPathNodes.has(id) || (sampleNodes.has(id) && !onlyRoute)) && (
            id.length <= 2 && preview.nodes < 50 ? (
              <text x={x} y={y + 3.5} textAnchor="middle" fontSize="10"
                fontWeight="700" fill="#fffbf2" fontFamily="'Source Sans 3', Arial, sans-serif">{id}</text>
            ) : (
              <text x={x} y={nameY} textAnchor="middle" fontSize={id.length > 12 ? '9' : '10'}
                fontWeight="700" fill={nameColor} stroke="#faf7f1" strokeWidth="3.5" strokeLinejoin="round"
                paintOrder="stroke fill" fontFamily="'Source Sans 3', Arial, sans-serif">
                 {name && preview.nodes > 45 ? `${id}: ${name.slice(0, 18)}` : id}
              </text>
            )
          )}
          {showNodes && showNames && name && preview.nodes <= 45 && <text x={x} y={y + r + 23} textAnchor="middle" fontSize="9"
            fontWeight="700" fill="#341e25" stroke="#faf7f1" strokeWidth="3" paintOrder="stroke fill">
            {name.length > 22 ? `${name.slice(0, 21)}…` : name}
          </text>}
          {isSource && showNames && preview.nodes < 50 && (
            <text x={x} y={y - 16} textAnchor="middle" fontSize="9" fontWeight="700" fill="#6e4e10"
              stroke="#faf7f1" strokeWidth="2.5" strokeLinejoin="round" paintOrder="stroke fill">Origen</text>
          )}
          {isTarget && showNames && preview.nodes < 50 && (
            <text x={x} y={y + 24} textAnchor="middle" fontSize="9" fontWeight="700" fill="#541224"
              stroke="#faf7f1" strokeWidth="2.5" strokeLinejoin="round" paintOrder="stroke fill">Destino</text>
          )}
        </g>
      })}
    </svg>
    {preview.nodes > 150 && !onlyRoute && <p className="fineprint">Se muestran los primeros 150 nodos y todos los nodos de la ruta calculada.</p>}
    {preview.nodes > 45 && !onlyRoute && (showNames || showWeights) && <p className="fineprint">En redes grandes se rotulan hasta 20 nodos y 20 aristas de fondo; el recorrido se dibuja completo.</p>}
    {routeEdges.length > 100 && (showNames || showWeights) && <p className="fineprint">Para evitar solapamientos, se rotulan hasta 100 pasos del recorrido; la ruta se dibuja completa.</p>}
    {preview.display_limited && <p className="fineprint">Red grande: se limita la vista previa, no el cálculo.</p>}
  </div>
}

type Camera = { network: string; center: [number, number]; zoom: number }

function MapView({ preview, route, onPick, sourcePoint, targetPoint, basemap, showNodes, showNames, showWeights, showNetwork, onlyRoute, camera, lockSelection }: Props &
  Layers & { basemap: string; camera: React.RefObject<Camera | null>; lockSelection: boolean }) {
  const container = useRef<HTMLDivElement>(null)
  const map = useRef<MapLibreMap | null>(null)
  const markers = useRef<Marker[]>([])
  const markerType = useRef<typeof import('maplibre-gl').Marker | null>(null)
  const onPickRef = useRef(onPick)
  onPickRef.current = onPick
  const lockRef = useRef(lockSelection)
  lockRef.current = lockSelection
  const [toast, setToast] = useState('')
  const toastTimer = useRef<number | null>(null)
  const networkRef = useRef('')
  const [ready, setReady] = useState(false)
  const [failed, setFailed] = useState(false)
  const [tileError, setTileError] = useState(false)
  const networkId = preview ? `${preview.name}-${preview.nodes}-${preview.edges}` : ''

  useEffect(() => {
    let disposed = false
    let observer: ResizeObserver | null = null
    async function mount() {
      if (!container.current) return
      try {
        const maplibregl = await import('maplibre-gl')
        if (disposed || !container.current) return
        markerType.current = maplibregl.Marker
        maplibregl.setWorkerUrl(workerUrl)
        const saved = camera.current?.network === networkId ? camera.current : null
        const empty: FeatureCollection = { type: 'FeatureCollection', features: [] }
        const raster: StyleSpecification = {
          version: 8,
          sources: { osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap contributors' } },
          layers: [{ id: 'osm', type: 'raster', source: 'osm', minzoom: 0, maxzoom: 19, layout: { visibility: basemap === 'calles' ? 'visible' : 'none' } }]
        }
        const m = new maplibregl.Map({ container: container.current, style: raster,
          center: saved ? saved.center : [-71.9788, -13.5165], zoom: saved ? saved.zoom : 13, minZoom: 9, maxZoom: 18 })
        map.current = m
        m.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right')
        m.on('error', () => { if (!disposed) setTileError(true) })
        m.on('click', event => {
          if (lockRef.current) {
            if (toastTimer.current) window.clearTimeout(toastTimer.current)
            setToast('🔒 Selección bloqueada: zoom y exploración libres sin modificar origen ni destino.')
            toastTimer.current = window.setTimeout(() => setToast(''), 2500)
            return
          }
          onPickRef.current({ lat: event.lngLat.lat, lon: event.lngLat.lng })
        })
        m.on('load', () => {
          if (disposed) return
          m.addSource('network', { type: 'geojson', data: empty })
          m.addLayer({ id: 'network', type: 'line', source: 'network', layout: { 'line-cap': 'round', 'line-join': 'round' },
            paint: { 'line-color': '#8B7355', 'line-width': 1.6, 'line-opacity': 0.75 } })
          m.addSource('route', { type: 'geojson', data: empty })
          m.addLayer({ id: 'route', type: 'line', source: 'route', layout: { 'line-cap': 'round', 'line-join': 'round' },
            paint: { 'line-color': '#681C32', 'line-width': 5.5, 'line-opacity': 0.95 } })
          m.addSource('nodes', { type: 'geojson', data: empty })
          m.addLayer({ id: 'nodes', type: 'circle', source: 'nodes', paint: {
            'circle-color': '#1E3F44', 'circle-radius': 3.5, 'circle-stroke-color': '#dec697', 'circle-stroke-width': 1 } })
          m.addSource('endpoints', { type: 'geojson', data: empty })
          m.addLayer({ id: 'endpoints', type: 'circle', source: 'endpoints', paint: {
            'circle-color': ['match', ['get', 'kind'], 'source', '#8A6418', '#681C32'],
            'circle-radius': 9, 'circle-stroke-color': '#fff', 'circle-stroke-width': 2 } })
          m.addSource('picked', { type: 'geojson', data: empty })
          m.addLayer({ id: 'picked', type: 'circle', source: 'picked', paint: {
            'circle-color': ['match', ['get', 'kind'], 'source', '#8A6418', '#681C32'],
            'circle-radius': 7, 'circle-stroke-color': '#fff', 'circle-stroke-width': 2 } })
          if (!disposed) setReady(true)
        })
        observer = new ResizeObserver(() => m.resize())
        observer.observe(container.current)
      } catch { if (!disposed) setFailed(true) }
    }
    void mount()
    return () => {
      disposed = true
      observer?.disconnect()
      markers.current.forEach(marker => marker.remove()); markers.current = []
      markerType.current = null
      if (map.current && networkRef.current) camera.current = { network: networkRef.current,
        center: [map.current.getCenter().lng, map.current.getCenter().lat], zoom: map.current.getZoom() }
      map.current?.remove(); map.current = null
    }
  }, [])

  useEffect(() => {
    const m = map.current
    if (!ready || !m || !m.getLayer('osm')) return
    m.setLayoutProperty('osm', 'visibility', basemap === 'calles' ? 'visible' : 'none')
    if (basemap === 'plano') setTileError(false)
  }, [basemap, ready])

  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    if (!preview) {
      ;(m.getSource('nodes') as GeoJSONSource).setData({ type: 'FeatureCollection', features: [] })
      ;(m.getSource('network') as GeoJSONSource).setData({ type: 'FeatureCollection', features: [] })
      return
    }
    const coords = preview.coords
    const pathIds = new Set((route?.result.path ?? []).map(String))
    const nodes: Feature<GeoPoint>[] = preview.ids.filter(id => coords[String(id)] && (!onlyRoute || pathIds.has(String(id)))).map(id => ({ type: 'Feature', properties: { id: String(id) }, geometry: { type: 'Point', coordinates: coords[String(id)] } }))
    const network: Feature<LineString>[] = onlyRoute ? [] : preview.display_edges.filter(([u, v]) => coords[String(u)] && coords[String(v)]).map(([u, v]) => ({ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: [coords[String(u)], coords[String(v)]] } }))
    ;(m.getSource('nodes') as GeoJSONSource).setData({ type: 'FeatureCollection', features: nodes })
    ;(m.getSource('network') as GeoJSONSource).setData({ type: 'FeatureCollection', features: network })
    if (networkRef.current !== networkId) {
      networkRef.current = networkId
      if (camera.current?.network !== networkId && nodes.length) {
        const points = nodes.map(n => n.geometry.coordinates)
        m.fitBounds([[Math.min(...points.map(p => p[0])), Math.min(...points.map(p => p[1]))],
          [Math.max(...points.map(p => p[0])), Math.max(...points.map(p => p[1]))]],
        { padding: 38, maxZoom: 16, duration: 0 })
      }
    }
  }, [ready, preview, networkId, camera, onlyRoute])

  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    if (m.getLayer('nodes')) m.setLayoutProperty('nodes', 'visibility', showNodes ? 'visible' : 'none')
    if (m.getLayer('network')) m.setLayoutProperty('network', 'visibility', showNetwork && !onlyRoute ? 'visible' : 'none')
  }, [ready, showNodes, showNetwork, onlyRoute])

  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    if (!preview) {
      for (const name of ['route', 'endpoints', 'picked'])
        (m.getSource(name) as GeoJSONSource).setData({ type: 'FeatureCollection', features: [] })
      return
    }
    const pathPoints = route?.result.path_geometry?.length ? route.result.path_geometry : route?.path_coords
    const path: FeatureCollection<LineString> = { type: 'FeatureCollection', features: pathPoints && pathPoints.length > 1 ?
      [{ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: pathPoints } }] : [] }
    const endpointFeatures: Feature<GeoPoint>[] = []
    if (route) {
      const srcCoord = preview.coords[String(route.source)]
      const tgtCoord = preview.coords[String(route.target)]
      if (srcCoord) endpointFeatures.push({ type: 'Feature', properties: { kind: 'source' }, geometry: { type: 'Point', coordinates: srcCoord } })
      if (tgtCoord) endpointFeatures.push({ type: 'Feature', properties: { kind: 'target' }, geometry: { type: 'Point', coordinates: tgtCoord } })
    }
    const pickedFeatures: Feature<GeoPoint>[] = []
    if (sourcePoint) pickedFeatures.push({ type: 'Feature', properties: { kind: 'source' }, geometry: { type: 'Point', coordinates: [sourcePoint.lon, sourcePoint.lat] } })
    if (targetPoint) pickedFeatures.push({ type: 'Feature', properties: { kind: 'target' }, geometry: { type: 'Point', coordinates: [targetPoint.lon, targetPoint.lat] } })

    ;(m.getSource('route') as GeoJSONSource).setData(path)
    ;(m.getSource('endpoints') as GeoJSONSource).setData({ type: 'FeatureCollection', features: endpointFeatures })
    ;(m.getSource('picked') as GeoJSONSource).setData({ type: 'FeatureCollection', features: pickedFeatures })
  }, [ready, preview, route, sourcePoint, targetPoint])

  useEffect(() => {
    markers.current.forEach(marker => marker.remove()); markers.current = []
    const m = map.current
    const MapMarker = markerType.current
    if (!ready || !m || !preview || !MapMarker || (!showNames && !showWeights)) return
    const coords = preview.coords
    const path = route?.result.path ?? []
    const step = Math.max(1, Math.ceil(path.length / 100))
    const routeLabelIds = path.filter((_, index) => index % step === 0 || index === path.length - 1).map(String)
    const labelIds = onlyRoute ? routeLabelIds : preview.nodes <= 45 ? preview.ids.map(String) :
      [...new Set([...preview.ids.slice(0, 20).map(String), ...routeLabelIds])]
    const add = (point: [number, number], text: string, className: string) => {
      const el = document.createElement('div')
      el.className = className
      el.textContent = text
      markers.current.push(new MapMarker({ element: el, anchor: 'bottom', offset: [0, -7] }).setLngLat(point).addTo(m))
    }
    const labels = (preview as Preview & { labels?: Record<string, string> }).labels
    if (showNames && showNodes) labelIds.forEach(id => { if (coords[id]) add(coords[id], labels?.[id] ? `${id}: ${labels[id]}` : id, 'map-data-label map-node-label') })
    if (showWeights && route) {
      const step = Math.max(1, Math.ceil(route.result.edges.length / 100))
      route.result.edges.forEach((edge, index) => {
        if (index % step !== 0 && index !== route.result.edges.length - 1) return
        const p1 = coords[String(edge.from)], p2 = coords[String(edge.to)]
        if (!p1 || !p2) return
        add([(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2], `${edge.cost != null ? Number(edge.cost.toFixed(1)) : ''}`, 'map-data-label map-weight-label')
      })
    }
    if (showWeights && showNetwork && !onlyRoute) {
      const pathEdges = new Set((route?.result.edges ?? []).map(edge => `${edge.from}|${edge.to}`))
      preview.display_edges.slice(0, preview.nodes <= 45 ? 80 : 20).forEach(([u, v, weight]) => {
        if (pathEdges.has(`${u}|${v}`)) return
        const p1 = coords[String(u)], p2 = coords[String(v)]
        if (!p1 || !p2) return
        add([(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2], String(weight), 'map-data-label map-weight-muted')
      })
    }
    return () => { markers.current.forEach(marker => marker.remove()); markers.current = [] }
  }, [ready, preview, route, showNames, showWeights, showNetwork, showNodes, onlyRoute])

  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    const canvas = m.getCanvas()
    if (canvas) canvas.style.cursor = lockSelection ? 'grab' : 'crosshair'
  }, [ready, lockSelection])

  const fit = (which: 'network' | 'route') => {
    const m = map.current
    const points = which === 'route' ? (route?.result.path_geometry?.length ? route.result.path_geometry : route?.path_coords) :
      preview?.ids.map(id => preview.coords[String(id)]).filter((p): p is [number, number] => !!p)
    if (!m || !points?.length) return
    const minLon = Math.min(...points.map(p => p[0])), maxLon = Math.max(...points.map(p => p[0]))
    const minLat = Math.min(...points.map(p => p[1])), maxLat = Math.max(...points.map(p => p[1]))
    m.fitBounds([[minLon, minLat], [maxLon, maxLat]], { padding: 44, maxZoom: 16, duration: 0 })
  }
  return <div className="map-wrap">
    {failed && <p className="map-note" role="status">No se pudo cargar el mapa. Usa «Grafo» para ver la red sin WebGL ni teselas.</p>}
    {tileError && basemap === 'calles' && <p className="map-note" role="status">No se cargaron algunas teselas. Puedes seguir usando el plano sin conexión.</p>}
    <div className="map-actions"><button type="button" onClick={() => fit('network')} disabled={!ready}>Ver toda la red</button>
      <button type="button" onClick={() => fit('route')} disabled={!ready || !route?.result.path.length}>Centrar ruta</button></div>
    {toast && <div className="map-lock-toast" role="status">{toast}</div>}
    <div className="map-canvas" ref={container} aria-label="Mapa interactivo. Selecciona origen o destino antes de pulsar un punto." />
  </div>
}

export default function GraphView({ preview, route, onPick, pick, onPickMode, mapRequested, sourcePoint, targetPoint, lockSelection: extLock, onToggleLock: extToggle }: Props) {
  const [internalLock, setInternalLock] = useState(false)
  const isLocked = extLock !== undefined ? extLock : internalLock
  const toggleLock = extToggle ?? (() => setInternalLock(l => !l))

  const [mode, setMode] = useState<'mapa' | 'grafo'>('mapa')
  const [basemap, setBasemap] = useState('plano')
  const [showNodes, setShowNodes] = useState(true)
  const [showNames, setShowNames] = useState(true)
  const [showNetwork, setShowNetwork] = useState(true)
  const [showWeights, setShowWeights] = useState(true)
  const [onlyRoute, setOnlyRoute] = useState(false)
  const routeOnly = onlyRoute && !!route?.result.path.length
  const section = useRef<HTMLElement>(null)
  const camera = useRef<Camera | null>(null)

  useEffect(() => { if (preview && !preview.geographic) setMode('grafo') }, [preview])
  useEffect(() => { if (!route) setOnlyRoute(false) }, [route])
  useEffect(() => {
    if (!mapRequested) return
    setMode('mapa')
    section.current?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' })
  }, [mapRequested])

  return <section ref={section} className="visual" aria-label="Visualización de red y ruta">
    <div className="visual-toolbar">
      <div className="visual-tools">
        <div className="segmented" aria-label="Visualización">
          <button type="button" aria-pressed={mode === 'grafo'} className={mode === 'grafo' ? 'active' : ''} onClick={() => setMode('grafo')}>Grafo</button>
          <button type="button" aria-pressed={mode === 'mapa'} className={mode === 'mapa' ? 'active' : ''} onClick={() => setMode('mapa')} disabled={!preview?.geographic}>Mapa</button>
        </div>

        {mode === 'mapa' && <button
          type="button"
          className={`lock-toolbar-btn ${isLocked ? 'is-locked' : 'is-unlocked'}`}
          onClick={toggleLock}
          title={isLocked ? "Selección bloqueada: haz clic para desbloquear y permitir elegir nuevos puntos en el mapa" : "Bloquear selección para hacer zoom y explorar libremente sin modificar origen ni destino"}
          aria-pressed={isLocked}
        >
          {isLocked ? 'Puntos bloqueados' : 'Bloquear puntos'}
        </button>}

        {mode === 'mapa' && (
          isLocked ? (
            <span className="map-pick locked-indicator" role="status">
              Selección fija: zoom y navegación libres
            </span>
          ) : (
            <>
              <span className="map-pick" role="status">Elegir en mapa:</span>
              <div className="segmented" aria-label="Punto a elegir en mapa">
                <button type="button" aria-pressed={pick === 'source'} className={pick === 'source' ? 'active' : ''} onClick={() => onPickMode('source')}>Origen</button>
                <button type="button" aria-pressed={pick === 'target'} className={pick === 'target' ? 'active' : ''} onClick={() => onPickMode('target')}>Destino</button>
              </div>
            </>
          )
        )}
      </div>

      <fieldset className="graph-layers">
        <legend>Mostrar en {mode === 'mapa' ? 'el mapa' : 'el grafo'}</legend>
        <div className="graph-layer-content">
          {mode === 'mapa' && (
            <label className="graph-basemap">
              Mapa base{' '}
              <select value={basemap} onChange={e => setBasemap(e.target.value)} disabled={routeOnly}>
                <option value="plano">Plano sin teselas</option>
                <option value="calles">Calles OSM</option>
              </select>
            </label>
          )}
          <div className="graph-layer-list">
            <label className="check">
              <input type="checkbox" checked={showNodes} onChange={e => setShowNodes(e.target.checked)} /> Nodos
            </label>
            <label className="check">
              <input type="checkbox" checked={showNetwork} onChange={e => setShowNetwork(e.target.checked)} disabled={routeOnly} /> Aristas de la red
            </label>
            <label className="check">
              <input type="checkbox" checked={showNames} onChange={e => setShowNames(e.target.checked)} disabled={!showNodes} /> Nombres / ID
            </label>
            <label className="check"><input type="checkbox" checked={showWeights} onChange={e => setShowWeights(e.target.checked)} /> Pesos</label>
            <label className="check"><input type="checkbox" checked={routeOnly} onChange={e => setOnlyRoute(e.target.checked)} disabled={!route?.result.path.length} /> Solo recorrido</label>
          </div>
        </div>
        {routeOnly && <p className="fineprint">Se ocultan las aristas y los nodos ajenos a la ruta; el origen y el destino permanecen visibles.</p>}
      </fieldset>
    </div>
    {mode === 'mapa' && preview?.geographic ? (
      <MapView
        preview={preview}
        route={route}
        onPick={onPick}
        pick={pick}
        onPickMode={onPickMode}
        mapRequested={mapRequested}
        sourcePoint={sourcePoint}
        targetPoint={targetPoint}
        basemap={basemap}
        showNodes={showNodes}
        showNames={showNames}
        showWeights={showWeights}
        showNetwork={showNetwork}
        onlyRoute={routeOnly}
        camera={camera}
        lockSelection={isLocked}
      />
    ) : (
      <GraphSVG
        preview={preview}
        route={route}
        showNodes={showNodes}
        showNames={showNames}
        showWeights={showWeights}
        showNetwork={showNetwork}
        onlyRoute={routeOnly}
      />
    )}
    <p className="legend">
      {showNodes && <><span className="legend-node" /> Nodo </>}
      {route?.result.path.length ? (
        <><span className="legend-route" /> Ruta <span className="legend-origin" /> Origen <span className="legend-target" /> Destino</>
      ) : (
        'Calcula una ruta para resaltar el recorrido.'
      )}
    </p>
    {mode === 'mapa' && preview && preview.nodes > 45 && !routeOnly && (showNames || showWeights) && (
      <p className="fineprint">En redes grandes se rotulan hasta 20 nodos y 20 aristas de fondo; el recorrido se dibuja completo.</p>
    )}
    {mode === 'mapa' && route && route.result.edges.length > 100 && (showNames || showWeights) && (
      <p className="fineprint">Para evitar solapamientos, se rotulan hasta 100 pasos del recorrido; la ruta se dibuja completa.</p>
    )}
    {mode === 'mapa' && <p className="fineprint">{route?.warning ?? 'Solo la base «Calles OSM» solicita teselas externas.'}</p>}
    {mode === 'mapa' && preview?.display_limited && (
      <p className="fineprint">Se muestra una parte de las aristas para mantener fluido el mapa; la ruta se calcula con la red completa.</p>
    )}
  </section>
}
