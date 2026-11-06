import { useEffect, useMemo, useRef, useState } from 'react'
import type { Map as MapLibreMap, StyleSpecification } from 'maplibre-gl'
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
        positions.set(String(id), [38 + (x - minX) / (maxX - minX || 1) * 624,
          30 + (maxY - y) / (maxY - minY || 1) * 350])
      })
    } else {
      ids.forEach((id, index) => {
        const angle = index * 2 * Math.PI / ids.length - Math.PI / 2
        positions.set(String(id), [350 + Math.cos(angle) * 250, 205 + Math.sin(angle) * 160])
      })
    }
    return positions
  }, [preview, route])
  if (!preview || !layout) return <div className="empty-map">Valida una instancia para ver su red.</div>
  const selected = new Set((route?.result.edges ?? []).map(edge => `${edge.from}|${edge.to}`))
  const edges = [...preview.display_edges, ...(route?.result.edges.map(e => [e.from, e.to] as [string | number, string | number]) ?? [])]
    .filter(([u, v]) => layout.has(String(u)) && layout.has(String(v)))
  return <div className="graph-container" role="img" aria-label={`Grafo con ${preview.nodes} nodos y ${preview.edges} aristas. Ruta: ${route?.result.path.join(', ') || 'sin calcular'}`}>
    <svg viewBox="0 0 700 410" preserveAspectRatio="xMidYMid meet">
      {edges.map(([u, v], i) => <line key={`${u}-${v}-${i}`} x1={layout.get(String(u))![0]} y1={layout.get(String(u))![1]}
        x2={layout.get(String(v))![0]} y2={layout.get(String(v))![1]}
        stroke={selected.has(`${u}|${v}`) ? '#681C32' : '#A89D92'} strokeWidth={selected.has(`${u}|${v}`) ? 3.5 : 1.2} />)}
      {[...layout].map(([id, [x, y]]) => <g key={id}>
        <circle cx={x} cy={y} r={preview.nodes < 50 ? 8 : 3} fill={id === String(route?.source) ? '#8A6418' : id === String(route?.target) ? '#681C32' : '#315D65'} />
        {preview.nodes < 50 && <text x={x + 10} y={y + 4} fontSize="12" fill="#1F1B1C">{id}</text>}
      </g>)}
    </svg>
    {preview.nodes > 150 && <p className="fineprint">Se muestran los primeros 150 nodos y todos los nodos de la ruta calculada.</p>}
    {preview.display_limited && <p className="fineprint">Red grande: se limita la vista previa, no el cálculo.</p>}
  </div>
}

function MapView({ preview, route, onPick, sourcePoint, targetPoint, basemap, showNodes, showNetwork }: Props & { basemap: string; showNodes: boolean; showNetwork: boolean }) {
  const container = useRef<HTMLDivElement>(null)
  const map = useRef<MapLibreMap | null>(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    if (!container.current || !preview) return
    let disposed = false
    const networkPreview = preview
    const coords = networkPreview.coords
    const center: [number, number] = networkPreview.ids.length ? coords[String(networkPreview.ids[0])] : [-71.9788, -13.5165]
    const raster: StyleSpecification = basemap === 'calles'
      ? { version: 8, sources: { osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap contributors' } }, layers: [{ id: 'osm', type: 'raster', source: 'osm' }] }
      : { version: 8, sources: {}, layers: [{ id: 'paper', type: 'background', paint: { 'background-color': '#F3EDE3' } }] }
    async function mount() {
    try {
      const maplibregl = await import('maplibre-gl')
      if (disposed || !container.current) return
      maplibregl.setWorkerUrl(workerUrl)
      const m = new maplibregl.Map({ container: container.current, style: raster, center: center ?? [-71.9788, -13.5165], zoom: 13, attributionControl: false })
      map.current = m
      m.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
      m.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right')
      m.on('error', () => { if (!disposed) setFailed(true) })
      m.on('click', e => onPick({ lat: e.lngLat.lat, lon: e.lngLat.lng }))
      m.on('load', () => {
        const nodes: Feature<GeoPoint>[] = networkPreview.ids.filter(id => coords[String(id)]).map(id => ({ type: 'Feature', properties: { id: String(id) }, geometry: { type: 'Point', coordinates: coords[String(id)] } }))
        const network: Feature<LineString>[] = networkPreview.display_edges.filter(([u, v]) => coords[String(u)] && coords[String(v)]).map(([u, v]) => ({ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: [coords[String(u)], coords[String(v)]] } }))
        const pathPoints = route?.result.path_geometry?.length ? route.result.path_geometry : route?.path_coords
        const path: FeatureCollection<LineString> = { type: 'FeatureCollection', features: pathPoints && pathPoints.length > 1 ? [{ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: pathPoints } }] : [] }
        m.addSource('network', { type: 'geojson', data: { type: 'FeatureCollection', features: network } })
        m.addLayer({ id: 'network-line', type: 'line', source: 'network', paint: { 'line-color': '#766F68', 'line-opacity': 0.7, 'line-width': 1 }, layout: { visibility: showNetwork ? 'visible' : 'none' } })
        m.addSource('route', { type: 'geojson', data: path })
        m.addLayer({ id: 'route-line', type: 'line', source: 'route', paint: { 'line-color': '#681C32', 'line-width': 5 } })
        m.addSource('nodes', { type: 'geojson', data: { type: 'FeatureCollection', features: nodes } })
        m.addLayer({ id: 'node-dots', type: 'circle', source: 'nodes', paint: { 'circle-color': '#315D65', 'circle-radius': 3.5 }, layout: { visibility: showNodes ? 'visible' : 'none' } })
        const endpoints: Feature<GeoPoint>[] = route ? [route.source, route.target].flatMap((id, index) => {
          const point = coords[String(id)]
          return point ? [{ type: 'Feature' as const, properties: { kind: index === 0 ? 'source' : 'target' }, geometry: { type: 'Point' as const, coordinates: point } }] : []
        }) : []
        m.addSource('endpoints', { type: 'geojson', data: { type: 'FeatureCollection', features: endpoints } })
        m.addLayer({ id: 'endpoints', type: 'circle', source: 'endpoints', paint: {
          'circle-color': ['match', ['get', 'kind'], 'source', '#8A6418', '#681C32'],
          'circle-radius': 9, 'circle-stroke-color': '#fff', 'circle-stroke-width': 2,
        } })
        const picked: Feature<GeoPoint>[] = [sourcePoint, targetPoint].flatMap((p, index) => p
          ? [{ type: 'Feature' as const, properties: { kind: index === 0 ? 'source' : 'target' },
            geometry: { type: 'Point' as const, coordinates: [p.lon, p.lat] } }] : [])
        m.addSource('picked', { type: 'geojson', data: { type: 'FeatureCollection', features: picked } })
        m.addLayer({ id: 'picked', type: 'circle', source: 'picked', paint: {
          'circle-color': ['match', ['get', 'kind'], 'source', '#8A6418', '#681C32'],
          'circle-radius': 7, 'circle-stroke-color': '#fff', 'circle-stroke-width': 2,
        } })
        if (pathPoints?.length) {
          const bounds = new maplibregl.LngLatBounds()
          pathPoints.forEach(([lon, lat]) => bounds.extend([lon, lat]))
          m.fitBounds(bounds, { padding: 55, maxZoom: 16 })
        }
      })
    } catch { if (!disposed) setFailed(true) }
    }
    void mount()
    return () => { disposed = true; map.current?.remove(); map.current = null }
  }, [preview, route, basemap, onPick, showNodes, showNetwork, sourcePoint, targetPoint])
  return <div className="map-wrap">
    {failed && <p className="map-note" role="status">No se pudo cargar el mapa. Usa «Grafo» para ver la red sin WebGL ni teselas.</p>}
    <div className="map-canvas" ref={container} aria-label="Mapa interactivo. Selecciona origen o destino antes de pulsar un punto." />
  </div>
}

export default function GraphView({ preview, route, onPick, pick, onPickMode, mapRequested, sourcePoint, targetPoint }: Props) {
  const [mode, setMode] = useState<'mapa' | 'grafo'>('grafo')
  const [basemap, setBasemap] = useState('plano')
  const [showNodes, setShowNodes] = useState(true)
  const [showNetwork, setShowNetwork] = useState(true)
  const section = useRef<HTMLElement>(null)
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
        <label>Base <select value={basemap} onChange={e => setBasemap(e.target.value)}><option value="plano">Plano sin teselas</option><option value="calles">Calles OSM</option></select></label>
        <label className="check"><input type="checkbox" checked={showNodes} onChange={e => setShowNodes(e.target.checked)} /> Nodos</label>
        <label className="check"><input type="checkbox" checked={showNetwork} onChange={e => setShowNetwork(e.target.checked)} /> Aristas</label>
      </>}
    </div>
    {mode === 'mapa' && preview?.geographic ? <MapView preview={preview} route={route} onPick={onPick} pick={pick} onPickMode={onPickMode} mapRequested={mapRequested} sourcePoint={sourcePoint} targetPoint={targetPoint} basemap={basemap} showNodes={showNodes} showNetwork={showNetwork} /> : <GraphSVG preview={preview} route={route} />}
    <p className="legend"><span className="legend-node" /> Nodo <span className="legend-route" /> Ruta <span className="legend-origin" /> Origen <span className="legend-target" /> Destino</p>
    {mode === 'mapa' && <p className="fineprint">{route?.warning ?? 'Solo la base «Calles OSM» solicita teselas externas.'}</p>}
  </section>
}
