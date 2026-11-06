import { useEffect, useMemo, useRef, useState } from 'react'
import type { GeoJSONSource, Map as MapLibreMap, StyleSpecification } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import type { Feature, FeatureCollection, LineString, Point as GeoPoint } from 'geojson'
import type { Point, Preview, RouteResponse } from './api'

type Props = { preview: Preview | null; route: RouteResponse | null; onPick: (point: Point) => void;
  pick: 'source' | 'target'; onPickMode: (value: 'source' | 'target') => void; mapRequested: number;
  sourcePoint: Point | null; targetPoint: Point | null }

function GraphSVG({ preview, route }: Pick<Props, 'preview' | 'route'>) {
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
  const showLabels = preview.nodes <= 45

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
      {edgeList.map(({ u, v, selected }, i) => {
        const [x1, y1] = layout.get(u)!
        const [x2, y2] = layout.get(v)!
        return <line key={`line-${u}-${v}-${i}`} x1={x1} y1={y1} x2={x2} y2={y2}
          stroke={selected ? '#681C32' : '#b4a89d'}
          strokeWidth={selected ? 2.6 : 1.2}
          markerEnd={selected ? 'url(#arrow-selected)' : 'url(#arrow)'} />
      })}

      {/* 2. Etiquetas de peso y costo compactas y legibles */}
      {showLabels && edgeList.map(({ u, v, weight, selected }, i) => {
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
            fill={selected ? '#681C32' : '#ffffff'}
            stroke={selected ? '#dec697' : '#c8b8a8'}
            strokeWidth={selected ? 1.2 : 0.8} />
          <text x={lblX} y={lblY + 3.2} textAnchor="middle" fontSize="9.5" fontWeight="700"
            fill={selected ? '#ffffff' : '#3d322c'} fontFamily="'Source Sans 3', monospace">
            {textStr}
          </text>
        </g>
      })}

      {/* 3. Nodos proporcionados con tipografía centrada */}
      {[...layout].map(([id, [x, y]]) => {
        const isSource = id === String(route?.source)
        const isTarget = id === String(route?.target)
        const isPath = pathNodes.has(id)
        const r = preview.nodes < 50 ? (isSource || isTarget ? 13 : 11.5) : 3.5
        const fillColor = isSource ? '#8A6418' : isTarget ? '#681C32' : isPath ? '#7a3045' : '#315D65'

        return <g key={`node-${id}`}>
          <circle cx={x} cy={y} r={r} fill={fillColor} stroke="#ffffff" strokeWidth={preview.nodes < 50 ? 2 : 1} />
          {preview.nodes < 50 && <text x={x} y={y + 3.5} textAnchor="middle" fontSize={id.length > 2 ? '8.5' : '10'}
            fontWeight="700" fill="#ffffff" fontFamily="'Source Sans 3', Arial, sans-serif">{id}</text>}
          {isSource && preview.nodes < 50 && <text x={x} y={y - 16} textAnchor="middle" fontSize="9" fontWeight="700" fill="#8A6418">Origen</text>}
          {isTarget && preview.nodes < 50 && <text x={x} y={y + 24} textAnchor="middle" fontSize="9" fontWeight="700" fill="#681C32">Destino</text>}
        </g>
      })}
    </svg>
    {preview.nodes > 150 && <p className="fineprint">Se muestran los primeros 150 nodos y todos los nodos de la ruta calculada.</p>}
    {preview.display_limited && <p className="fineprint">Red grande: se limita la vista previa, no el cálculo.</p>}
  </div>
}

type Camera = { network: string; center: [number, number]; zoom: number }

function MapView({ preview, route, onPick, sourcePoint, targetPoint, basemap, showNodes, showNetwork, camera }: Props &
  { basemap: string; showNodes: boolean; showNetwork: boolean; camera: React.RefObject<Camera | null> }) {
  const container = useRef<HTMLDivElement>(null)
  const map = useRef<MapLibreMap | null>(null)
  const onPickRef = useRef(onPick)
  onPickRef.current = onPick
  const networkRef = useRef('')
  const [ready, setReady] = useState(false)
  const [failed, setFailed] = useState(false)
  const [tileError, setTileError] = useState(false)
  const networkId = preview ? `${preview.name}:${preview.nodes}:${preview.edges}` : ''
  useEffect(() => {
    if (!container.current) return
    let disposed = false
    const raster: StyleSpecification = { version: 8,
      sources: { osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap contributors' } },
      layers: [{ id: 'paper', type: 'background', paint: { 'background-color': '#F3EDE3' } },
        { id: 'osm', type: 'raster', source: 'osm', layout: { visibility: 'none' } }] }
    let observer: ResizeObserver | null = null
    async function mount() {
      try {
        const maplibregl = await import('maplibre-gl')
        if (disposed || !container.current) return
        maplibregl.setWorkerUrl(workerUrl)
        const saved = camera.current?.network === networkId ? camera.current : null
        const m = new maplibregl.Map({ container: container.current, style: raster,
          center: saved?.center ?? [-71.9788, -13.5165], zoom: saved?.zoom ?? 13, attributionControl: false })
        map.current = m
        m.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
        m.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right')
        m.on('error', () => { if (!disposed) setTileError(true) })
        m.on('click', e => onPickRef.current({ lat: e.lngLat.lat, lon: e.lngLat.lng }))
        m.on('moveend', () => { camera.current = { network: networkRef.current, center: [m.getCenter().lng, m.getCenter().lat], zoom: m.getZoom() } })
        m.on('load', () => {
          const empty = { type: 'FeatureCollection' as const, features: [] }
          m.addSource('network', { type: 'geojson', data: empty })
          m.addLayer({ id: 'network-line', type: 'line', source: 'network', paint: { 'line-color': '#766F68', 'line-opacity': 0.7, 'line-width': 1 } })
          m.addSource('route', { type: 'geojson', data: empty })
          m.addLayer({ id: 'route-line', type: 'line', source: 'route', paint: { 'line-color': '#681C32', 'line-width': 5 } })
          m.addSource('nodes', { type: 'geojson', data: empty })
          m.addLayer({ id: 'node-dots', type: 'circle', source: 'nodes', paint: { 'circle-color': '#315D65', 'circle-radius': 3.5 } })
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
      if (map.current && networkRef.current) camera.current = { network: networkRef.current,
        center: [map.current.getCenter().lng, map.current.getCenter().lat], zoom: map.current.getZoom() }
      map.current?.remove(); map.current = null
    }
  }, [])

  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    if (!preview) {
      ;(m.getSource('nodes') as GeoJSONSource).setData({ type: 'FeatureCollection', features: [] })
      ;(m.getSource('network') as GeoJSONSource).setData({ type: 'FeatureCollection', features: [] })
      return
    }
    const coords = preview.coords
    const nodes: Feature<GeoPoint>[] = preview.ids.filter(id => coords[String(id)]).map(id => ({ type: 'Feature', properties: { id: String(id) }, geometry: { type: 'Point', coordinates: coords[String(id)] } }))
    const network: Feature<LineString>[] = preview.display_edges.filter(([u, v]) => coords[String(u)] && coords[String(v)]).map(([u, v]) => ({ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: [coords[String(u)], coords[String(v)]] } }))
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
  }, [ready, preview, networkId, camera])

  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    if (!preview) {
      for (const name of ['route', 'endpoints', 'picked'])
        (m.getSource(name) as GeoJSONSource).setData({ type: 'FeatureCollection', features: [] })
      return
    }
    const pathPoints = route?.result.path_geometry?.length ? route.result.path_geometry : route?.path_coords
    const path: FeatureCollection<LineString> = { type: 'FeatureCollection', features: pathPoints && pathPoints.length > 1
      ? [{ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: pathPoints } }] : [] }
    ;(m.getSource('route') as GeoJSONSource).setData(path)
    const endpoints: Feature<GeoPoint>[] = route ? [route.source, route.target].flatMap((id, index) => {
      const point = preview.coords[String(id)]
      return point ? [{ type: 'Feature' as const, properties: { kind: index === 0 ? 'source' : 'target' }, geometry: { type: 'Point' as const, coordinates: point } }] : []
    }) : []
    ;(m.getSource('endpoints') as GeoJSONSource).setData({ type: 'FeatureCollection', features: endpoints })
    const picked: Feature<GeoPoint>[] = [sourcePoint, targetPoint].flatMap((p, index) => p
      ? [{ type: 'Feature' as const, properties: { kind: index === 0 ? 'source' : 'target' },
        geometry: { type: 'Point' as const, coordinates: [p.lon, p.lat] } }] : [])
    ;(m.getSource('picked') as GeoJSONSource).setData({ type: 'FeatureCollection', features: picked })
  }, [ready, route, sourcePoint, targetPoint, preview])

  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    if (basemap === 'plano') setTileError(false)
    m.setLayoutProperty('node-dots', 'visibility', showNodes ? 'visible' : 'none')
    m.setLayoutProperty('network-line', 'visibility', showNetwork ? 'visible' : 'none')
    m.setLayoutProperty('osm', 'visibility', basemap === 'calles' ? 'visible' : 'none')
  }, [ready, showNodes, showNetwork, basemap])

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
    <div className="map-canvas" ref={container} aria-label="Mapa interactivo. Selecciona origen o destino antes de pulsar un punto." />
  </div>
}

export default function GraphView({ preview, route, onPick, pick, onPickMode, mapRequested, sourcePoint, targetPoint }: Props) {
  const [mode, setMode] = useState<'mapa' | 'grafo'>('mapa')
  const [basemap, setBasemap] = useState('plano')
  const [showNodes, setShowNodes] = useState(true)
  const [showNetwork, setShowNetwork] = useState(true)
  const section = useRef<HTMLElement>(null)
  const camera = useRef<Camera | null>(null)
  useEffect(() => { if (preview && !preview.geographic) setMode('grafo') }, [preview])
  useEffect(() => {
    if (!mapRequested) return
    setMode('mapa')
    section.current?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' })
  }, [mapRequested])
  return <section ref={section} className="visual" aria-label="Visualización de red y ruta">
    <div className="visual-tools">
      <div className="segmented" aria-label="Visualización">
        <button type="button" aria-pressed={mode === 'grafo'} className={mode === 'grafo' ? 'active' : ''} onClick={() => setMode('grafo')}>Grafo</button>
        <button type="button" aria-pressed={mode === 'mapa'} className={mode === 'mapa' ? 'active' : ''} onClick={() => setMode('mapa')} disabled={!preview?.geographic}>Mapa</button>
      </div>
      {mode === 'mapa' && <>
        <span className="map-pick" role="status">Pulsa el mapa para elegir {pick === 'source' ? 'origen' : 'destino'}.</span>
        <div className="segmented" aria-label="Punto a elegir en mapa">
          <button type="button" aria-pressed={pick === 'source'} className={pick === 'source' ? 'active' : ''} onClick={() => onPickMode('source')}>Origen</button>
          <button type="button" aria-pressed={pick === 'target'} className={pick === 'target' ? 'active' : ''} onClick={() => onPickMode('target')}>Destino</button>
        </div>
        <div className="map-options" role="group" aria-label="Base y capas del mapa">
          <label>Mapa base <select value={basemap} onChange={e => setBasemap(e.target.value)}><option value="plano">Plano sin teselas</option><option value="calles">Calles OSM</option></select></label>
          <div className="map-layers" role="group" aria-label="Capas visibles">
            <label className="check"><input type="checkbox" checked={showNodes} onChange={e => setShowNodes(e.target.checked)} /> Nodos</label>
            <label className="check"><input type="checkbox" checked={showNetwork} onChange={e => setShowNetwork(e.target.checked)} /> Aristas</label>
          </div>
        </div>
      </>}
    </div>
    {mode === 'mapa' && preview?.geographic ? <MapView preview={preview} route={route} onPick={onPick} pick={pick} onPickMode={onPickMode} mapRequested={mapRequested} sourcePoint={sourcePoint} targetPoint={targetPoint} basemap={basemap} showNodes={showNodes} showNetwork={showNetwork} camera={camera} /> : <GraphSVG preview={preview} route={route} />}
    <p className="legend">{(mode !== 'mapa' || showNodes) && <><span className="legend-node" /> Nodo </>}
      <span className="legend-route" /> Ruta <span className="legend-origin" /> Origen <span className="legend-target" /> Destino</p>
    {mode === 'mapa' && <p className="fineprint">{route?.warning ?? 'Solo la base «Calles OSM» solicita teselas externas.'}</p>}
    {mode === 'mapa' && preview?.display_limited && <p className="fineprint">Se muestra una parte de las aristas para mantener fluido el mapa; la ruta se calcula con la red completa.</p>}
  </section>
}
