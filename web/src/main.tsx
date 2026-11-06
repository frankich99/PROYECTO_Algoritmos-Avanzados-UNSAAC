import { useCallback, useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import GraphView from './GraphView'
import { api, apiUrl } from './api'
import type { Benchmark, Catalog, Condition, Experiment, InstanceSpec, Metric, Pilot, Point, Preview, Queue, RouteResponse } from './api'
import 'maplibre-gl/dist/maplibre-gl.css'
import './style.css'

const queueNames: Record<Queue, string> = { binary_heap: 'Binario', '4ary_heap': '4-ario', fibonacci_heap: 'Fibonacci' }
const initialGraph = { name: 'Grafo propuesto', directed: true, nodes: [{ id: 'A' }, { id: 'B' }, { id: 'C' }],
  edges: [{ origin: 'A', destination: 'B', weight: 4 }, { origin: 'A', destination: 'C', weight: 10 }, { origin: 'B', destination: 'C', weight: 2 }] }
const menu = ['Rutas', 'Instancias', 'Comparar', 'Experimentos', 'Cobertura Cusco', 'Datos y método'] as const
type Section = typeof menu[number]
type Saved = { name: string; metric: string; network: string; nodes: number; edges: number; route: RouteResponse }

const fmt = (value: number | null | undefined, digits = 2) => value == null ? 'No disponible' : value.toLocaleString('es-PE', { maximumFractionDigits: digits })
function download(name: string, data: string, type = 'application/json') {
  const url = URL.createObjectURL(new Blob([data], { type }))
  const a = document.createElement('a')
  a.href = url; a.download = name; a.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
function Table({ headers, rows }: { headers: string[]; rows: (string | number)[][] }) {
  return <div className="table-scroll"><table><thead><tr>{headers.map(h => <th key={h} scope="col">{h}</th>)}</tr></thead>
    <tbody>{rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>)}</tbody></table></div>
}

function App() {
  const [section, setSection] = useState<Section>('Rutas')
  const [mobileMenu, setMobileMenu] = useState(false)
  const [catalog, setCatalog] = useState<Catalog | null>(null)
  const [spec, setSpec] = useState<InstanceSpec>({ kind: 'center' })
  const [metric, setMetric] = useState<Metric>('time')
  const [preview, setPreview] = useState<Preview | null>(null)
  const [previewError, setPreviewError] = useState('')
  const [previewLoading, setPreviewLoading] = useState(false)
  const [source, setSource] = useState('')
  const [target, setTarget] = useState('')
  const [sourcePoint, setSourcePoint] = useState<Point | null>(null)
  const [targetPoint, setTargetPoint] = useState<Point | null>(null)
  const [pick, setPick] = useState<'source' | 'target'>('source')
  const [algorithm, setAlgorithm] = useState<'dijkstra' | 'astar'>('dijkstra')
  const [queue, setQueue] = useState<Queue>('binary_heap')
  const [weather, setWeather] = useState<'none' | 'historical' | 'snapshot' | 'live'>('none')
  const [provider, setProvider] = useState<'open-meteo' | 'openweathermap' | 'tomtom'>('open-meteo')
  const [apiKey, setApiKey] = useState('')
  const [traffic, setTraffic] = useState(false)
  const [hour, setHour] = useState(13)
  const [route, setRoute] = useState<RouteResponse | null>(null)
  const [routeLoading, setRouteLoading] = useState(false)
  const [routeError, setRouteError] = useState('')
  const [condition, setCondition] = useState<Condition | null>(null)
  const [conditionLoading, setConditionLoading] = useState(false)
  const [conditionError, setConditionError] = useState('')
  const [saved, setSaved] = useState<Saved[]>([])
  const [profile, setProfile] = useState<'sparse' | 'dense'>('sparse')
  const [benchmark, setBenchmark] = useState<Benchmark | null>(null)
  const [pilot, setPilot] = useState<Pilot | null>(null)
  const [benchmarkError, setBenchmarkError] = useState('')
  const [benchmarkLoading, setBenchmarkLoading] = useState(false)
  const [experiment, setExperiment] = useState<Experiment | null>(null)
  const [experimentError, setExperimentError] = useState('')
  const [experimentLoading, setExperimentLoading] = useState(false)
  const [sizes, setSizes] = useState('30, 60, 100')
  const [seed, setSeed] = useState(42)
  const [runs, setRuns] = useState(5)
  const [editorMode, setEditorMode] = useState<'tabla' | 'json' | 'archivo' | 'generar'>('tabla')
  const [nodeDraft, setNodeDraft] = useState<{ id: string; lat: string; lon: string }[]>([{ id: 'A', lat: '', lon: '' }, { id: 'B', lat: '', lon: '' }, { id: 'C', lat: '', lon: '' }])
  const [edgeDraft, setEdgeDraft] = useState<{ origin: string; destination: string; weight: string }[]>([{ origin: 'A', destination: 'B', weight: '4' }, { origin: 'A', destination: 'C', weight: '10' }, { origin: 'B', destination: 'C', weight: '2' }])
  const [jsonDraft, setJsonDraft] = useState(JSON.stringify(initialGraph, null, 2))
  const [textDraft, setTextDraft] = useState('A B 4\nA C 10\nB C 2')
  const [editorError, setEditorError] = useState('')
  const [mapRequested, setMapRequested] = useState(0)
  const routeAbort = useRef<AbortController | null>(null)
  const conditionAbort = useRef<AbortController | null>(null)
  useEffect(() => () => { routeAbort.current?.abort(); conditionAbort.current?.abort() }, [])
  useEffect(() => { api<Catalog>('/catalog').then(setCatalog).catch(() => { /* La selección local sigue disponible. */ }) }, [])
  useEffect(() => {
    const controller = new AbortController()
    routeAbort.current?.abort(); setRouteLoading(false)
    setPreviewLoading(true); setPreviewError(''); setPreview(null); setRoute(null); setRouteError('')
    api<Preview>(`/instances/validate?metric=${metric}`, spec, controller.signal).then(data => {
      setPreview(data)
      setSource(old => data.ids.some(id => String(id) === old) ? old : String(data.ids[0] ?? ''))
      setTarget(old => data.ids.some(id => String(id) === old) ? old : String(data.ids[data.ids.length - 1] ?? ''))
    }).catch(e => { if (!controller.signal.aborted) setPreviewError(String(e.message)) })
      .finally(() => { if (!controller.signal.aborted) setPreviewLoading(false) })
    return () => controller.abort()
  }, [spec, metric])
  useEffect(() => {
    if (section !== 'Comparar') return
    const controller = new AbortController()
    setBenchmarkLoading(true); setBenchmarkError('')
    api<Benchmark>(`/benchmarks/${profile}`, undefined, controller.signal).then(setBenchmark)
      .catch(e => { if (!controller.signal.aborted) setBenchmarkError(e.message) })
      .finally(() => { if (!controller.signal.aborted) setBenchmarkLoading(false) })
    return () => controller.abort()
  }, [section, profile])
  useEffect(() => {
    if (section !== 'Comparar') return
    const controller = new AbortController()
    api<Pilot>('/benchmarks/pilot/summary', undefined, controller.signal).then(setPilot).catch(() => { /* El piloto es opcional. */ })
    return () => controller.abort()
  }, [section])
  useEffect(() => { routeAbort.current?.abort(); setRouteLoading(false); setRoute(null) }, [algorithm, queue, weather, provider, apiKey, traffic, hour])
  useEffect(() => { conditionAbort.current?.abort(); setConditionLoading(false); setCondition(null); setConditionError('') }, [sourcePoint, source, preview, provider, apiKey])
  useEffect(() => { routeAbort.current?.abort(); setRouteLoading(false); setRoute(null); setRouteError('') }, [source, target, sourcePoint, targetPoint])

  const setInstance = (value: InstanceSpec) => { setSourcePoint(null); setTargetPoint(null); setSpec(value); setSection('Rutas') }
  const mapPick = useCallback((point: Point) => {
    routeAbort.current?.abort(); setRouteLoading(false)
    if (pick === 'source') { setSourcePoint(point); setPick('target') }
    else setTargetPoint(point)
    setRoute(null)
  }, [pick])
  async function runRoute(event: React.FormEvent) {
    event.preventDefault(); routeAbort.current?.abort()
    const controller = new AbortController(); routeAbort.current = controller
    setRoute(null); setRouteError(''); setRouteLoading(true)
    try {
      const response = await api<RouteResponse>('/routes/solve', { instance: spec, metric, source: sourcePoint ? null : source,
        target: targetPoint ? null : target, source_point: sourcePoint, target_point: targetPoint,
        algorithm, queue, compare: true,
        scenario: { weather: metric === 'time' ? weather : 'none', weather_provider: provider === 'tomtom' ? 'open-meteo' : provider,
          weather_key: apiKey || null, traffic_hour: metric === 'time' && traffic ? hour : null } }, controller.signal)
      if (!controller.signal.aborted) setRoute(response)
    } catch (e) { if (!controller.signal.aborted) setRouteError(e instanceof Error ? e.message : 'No se pudo calcular la ruta.') }
    finally { if (!controller.signal.aborted) setRouteLoading(false) }
  }
  async function fetchConditions() {
    conditionAbort.current?.abort(); const controller = new AbortController(); conditionAbort.current = controller
    setCondition(null); setConditionError(''); setConditionLoading(true)
    try {
      const response = await api<Condition>('/conditions', { point: conditionPoint, provider, key: apiKey || null }, controller.signal)
      if (!controller.signal.aborted) setCondition(response)
    } catch (e) { if (!controller.signal.aborted) setConditionError(e instanceof Error ? e.message : 'No se pudo consultar el proveedor.') }
    finally { if (!controller.signal.aborted) setConditionLoading(false) }
  }
  function applyTable() {
    try {
      const nodes = nodeDraft.map(row => {
        if (!row.id.trim()) throw new Error('Cada nodo necesita un ID.')
        if (row.lat === '' && row.lon === '') return { id: row.id.trim() }
        if (!row.lat || !row.lon || !Number.isFinite(Number(row.lat)) || !Number.isFinite(Number(row.lon))) throw new Error('Complete ambas coordenadas numéricas de cada nodo.')
        return { id: row.id.trim(), lon: Number(row.lon), lat: Number(row.lat) }
      })
      const edges = edgeDraft.map(row => ({ origin: row.origin.trim(), destination: row.destination.trim(), weight: Number(row.weight) }))
      if (edgeDraft.some(row => !row.weight.trim() || !row.origin.trim() || !row.destination.trim())) throw new Error('Complete origen, destino y peso de cada arista.')
      setEditorError(''); setInstance({ kind: 'custom', data: { name: 'Instancia creada en la web', directed: true, nodes, edges } })
    } catch (e) { setEditorError(e instanceof Error ? e.message : 'Tabla inválida.') }
  }
  function applyJson() {
    try { const parsed = JSON.parse(jsonDraft) as Record<string, unknown>; setEditorError(''); setInstance({ kind: 'custom', data: parsed }) }
    catch { setEditorError('JSON mal formado. Revise comas y comillas.') }
  }
  async function importFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]; if (!file) return
    if (file.size > 2_000_000) { setEditorError('El archivo supera 2 MB.'); event.target.value = ''; return }
    try {
      const content = await file.text()
      if (file.name.toLowerCase().endsWith('.json')) { setJsonDraft(content); setEditorMode('json') }
      else { setTextDraft(content); setEditorMode('archivo') }
      setEditorError(''); setSection('Instancias')
    } catch { setEditorError('No se pudo leer el archivo como texto.') }
    event.target.value = ''
  }
  const sourceCoords = preview?.geographic ? preview.coords[source] : undefined
  const conditionPoint = sourcePoint ?? (sourceCoords ? { lat: sourceCoords[1], lon: sourceCoords[0] } : { lat: -13.5165, lon: -71.9788 })

  return <>
    <a className="skip-link" href="#contenido">Saltar al contenido</a>
    <header className="site-header"><div className="header-inner">
      <button className="wordmark" onClick={() => { setSection('Rutas'); setMobileMenu(false) }} aria-label="Ir a Rutas">
        <span className="wordmark-main">UNSAAC <i>/</i> Rutas</span><span className="wordmark-sub">Laboratorio de algoritmos · Cusco</span>
      </button>
      <button className="menu-toggle" aria-expanded={mobileMenu} aria-controls="principal" onClick={() => setMobileMenu(!mobileMenu)}>{mobileMenu ? 'Cerrar' : 'Menú'}</button>
      <nav id="principal" className={mobileMenu ? 'nav-links open' : 'nav-links'} aria-label="Navegación principal">
        {menu.map(item => <button key={item} className={item === section ? 'current' : ''} aria-current={item === section ? 'page' : undefined}
          onClick={() => { setSection(item); setMobileMenu(false); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>{item}</button>)}
      </nav>
    </div></header>
    <main id="contenido" className="shell">
      {section === 'Rutas' && <>
        <div className="page-lead"><div><p className="section-label">Consulta vial / 01</p><h1>Encuentra y comprueba una ruta</h1>
          <p>Una instancia, los mismos pesos y cuatro ejecuciones verificables.</p></div><div className="lead-aside">Red actual: <strong>{preview?.name ?? 'Validando instancia'}</strong><br />{preview ? `${preview.nodes} nodos · ${preview.edges} aristas` : 'Sin datos disponibles'}</div></div>
        <div className="workspace">
          <div className="controls-pane"><form onSubmit={runRoute}>
            <div className="form-section"><h2>01 / Instancia</h2><label>Red de trabajo
              <select value={spec.kind} onChange={e => setInstance({ kind: e.target.value as InstanceSpec['kind'] })}>
                <option value="center">Centro histórico, OSM guardado</option><option value="example">Seis nodos, ilustrativa</option>
                {catalog?.networks.some(n => n.kind === 'urban' && n.available) && <option value="urban">Centro ampliado (radio 3 km)</option>}
                {spec.kind === 'custom' && <option value="custom">Mi grafo JSON</option>}
                {spec.kind === 'text' && <option value="text">Mi lista de aristas</option>}
                {spec.kind === 'generated' && <option value="generated">Grafo generado</option>}
              </select></label>
              <button type="button" className="text-button" onClick={() => setSection('Instancias')}>Crear o importar una instancia</button>
              <label>Optimizar <select value={metric} onChange={e => setMetric(e.target.value as Metric)}><option value="time">Tiempo nominal (s)</option><option value="distance">Distancia (m)</option></select></label>
              {previewLoading && <p role="status">Validando red…</p>}{previewError && <p className="error" role="alert">{previewError}</p>}
            </div>
            <div className="form-section"><h2>02 / Puntos</h2><p className="fineprint">Puedes usar IDs o introducir coordenadas para ajustarlas al nodo vial próximo.</p>
              <label>Origen (ID) <input value={source} onChange={e => { setSource(e.target.value); setSourcePoint(null); setRoute(null) }} list="nodos" disabled={!!sourcePoint} /></label>
              <label>Destino (ID) <input value={target} onChange={e => { setTarget(e.target.value); setTargetPoint(null); setRoute(null) }} list="nodos" disabled={!!targetPoint} /></label>
              <datalist id="nodos">{preview?.ids.map(id => <option value={String(id)} key={String(id)} />)}</datalist>
              {preview?.geographic && <><div className="pick-row"><button type="button" className={pick === 'source' ? 'choice selected' : 'choice'} onClick={() => { setPick('source'); setMapRequested(n => n + 1) }}>Elegir origen en mapa</button>
                <button type="button" className={pick === 'target' ? 'choice selected' : 'choice'} onClick={() => { setPick('target'); setMapRequested(n => n + 1) }}>Elegir destino en mapa</button></div>
                <div className="coord-grid">{(['source', 'target'] as const).map(type => {
                  const value = type === 'source' ? sourcePoint : targetPoint
                  const setter = type === 'source' ? setSourcePoint : setTargetPoint
                  return <fieldset key={type}><legend>{type === 'source' ? 'Origen' : 'Destino'} por coordenadas</legend>
                    <div className="coord-fields"><label>Latitud<input type="number" step="any" min="-90" max="90" value={value?.lat ?? ''}
                      onChange={e => { setter({ lat: Number(e.target.value), lon: value?.lon ?? -71.9788 }); setRoute(null) }} /></label>
                      <label>Longitud<input type="number" step="any" min="-180" max="180" value={value?.lon ?? ''}
                        onChange={e => { setter({ lat: value?.lat ?? -13.5165, lon: Number(e.target.value) }); setRoute(null) }} /></label></div>
                    {value && <button type="button" className="text-button" onClick={() => { setter(null); setRoute(null) }}>Usar ID en su lugar</button>}
                  </fieldset>
                })}</div>
              </>}
            </div>
            <div className="form-section"><h2>03 / Algoritmo</h2><div className="two-fields">
              <label>Algoritmo<select value={algorithm} onChange={e => setAlgorithm(e.target.value as 'dijkstra' | 'astar')}><option value="dijkstra">Dijkstra</option><option value="astar">A* consistente</option></select></label>
              <label>Cola<select value={queue} onChange={e => setQueue(e.target.value as Queue)}>{(Object.keys(queueNames) as Queue[]).map(q => <option key={q} value={q}>{queueNames[q]}</option>)}</select></label></div>
              <p className="fineprint">Se ejecutan también los tres Dijkstra y A* con la cola elegida para contrastar costos.</p></div>
            {metric === 'time' && <details className="form-section scenario"><summary>Condiciones y escenarios optativos</summary><div className="details-body">
              <label>Fuente climática<select value={weather} onChange={e => setWeather(e.target.value as typeof weather)}><option value="none">Sin clima: peso nominal</option><option value="historical">Lectura histórica del informe</option><option value="snapshot">Snapshot local posterior</option><option value="live">Consulta actual al calcular</option></select></label>
              {weather === 'live' && <label>Proveedor<select value={provider === 'tomtom' ? 'open-meteo' : provider} onChange={e => setProvider(e.target.value as typeof provider)}><option value="open-meteo">Open-Meteo</option><option value="openweathermap">OpenWeatherMap</option></select></label>}
              {weather === 'live' && provider === 'openweathermap' && <label>Clave para esta consulta<input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} autoComplete="off" /></label>}
              <label className="check"><input type="checkbox" checked={traffic} onChange={e => setTraffic(e.target.checked)} /> Aplicar tráfico horario supuesto</label>
              {traffic && <label>Hora simulada en Cusco <input type="number" min="0" max="23" value={hour} onChange={e => setHour(Number(e.target.value))} /></label>}
              <p className="fineprint">El factor es uniforme. Cambia el costo estimado, no el camino; no hay aforo por arista.</p>
            </div></details>}
            <button type="submit" className="primary" disabled={!preview || routeLoading}>{routeLoading ? 'Calculando ruta…' : 'Calcular y contrastar'}</button>
            {routeError && <p className="error" role="alert">{routeError}</p>}
          </form></div>
          <div className="main-pane">
            <GraphView preview={preview} route={route} onPick={mapPick} pick={pick} onPickMode={setPick} mapRequested={mapRequested} sourcePoint={sourcePoint} targetPoint={targetPoint} />
            {routeLoading && <p role="status" className="status">Ejecutando los algoritmos sobre la misma instancia…</p>}
            {!route && !routeLoading && !routeError && <p className="status">Selecciona los puntos y calcula la ruta. La red del centro procede de un snapshot OSM, no de tráfico actual.</p>}
            {route && <section className="result-block" aria-live="polite"><h2>Resultado de la consulta</h2>
              {route.result.cost === null ? <p className="warning">No existe camino dirigido entre los nodos elegidos. Prueba otro destino o revisa el sentido de las aristas.</p> : <>
                <div className="headline-result"><div><span>Costo óptimo</span><strong>{fmt(route.result.cost)} <small>{route.unit}</small></strong></div>
                  <div><span>Distancia de esta ruta</span><strong>{fmt(route.result.length_m)} {route.result.length_m != null && <small>m</small>}</strong></div>
                  <div><span>Tiempo de esta ruta</span><strong>{fmt(route.result.time_sec)} {route.result.time_sec != null && <small>s</small>}</strong></div></div>
                <p className="route-sequence"><strong>Secuencia:</strong> {route.result.path.join(' → ')}. {route.result.path.length} nodos, {route.result.edges.length} aristas; {route.result.expanded} expandidos.</p>
                {route.source_snap && <p className="fineprint">Origen solicitado: {fmt(route.source_snap.requested.lat, 5)}, {fmt(route.source_snap.requested.lon, 5)}. Ajustado al nodo {route.source_snap.node}, a unos {fmt(route.source_snap.offset_m_approx, 1)} m.</p>}
                {route.target_snap && <p className="fineprint">Destino solicitado: {fmt(route.target_snap.requested.lat, 5)}, {fmt(route.target_snap.requested.lon, 5)}. Ajustado al nodo {route.target_snap.node}, a unos {fmt(route.target_snap.offset_m_approx, 1)} m.</p>}
                {route.warning && <p className="warning">{route.warning}</p>}
                {route.scenario.kind === 'uniform_scenario' && <p className="warning">Escenario uniforme {route.scenario.factor}×, no tiempo observado. {route.scenario.weather_source ? `${route.scenario.weather_source}; lectura ${route.scenario.weather_observed_at} (${route.scenario.weather_timezone})${route.scenario.weather_cached ? ' (guardada)' : ''}.` : ''} {route.scenario.requested_point ? `Consulta en ${fmt(route.scenario.requested_point.lat, 5)}, ${fmt(route.scenario.requested_point.lon, 5)}.` : ''} {route.scenario.weather_grid_point ? `Punto de grilla: ${fmt(route.scenario.weather_grid_point.lat, 5)}, ${fmt(route.scenario.weather_grid_point.lon, 5)}.` : ''} {route.scenario.traffic ? `Hora simulada: ${route.scenario.traffic_hour}:00 (Cusco).` : ''} La ruta no cambia por un factor uniforme.</p>}
                <div className="result-actions"><button type="button" onClick={() => { setSaved(old => [...old, { name: `${route.network}: ${route.source} a ${route.target}`, metric: route.unit, network: route.network, nodes: route.counts.nodes, edges: route.counts.edges, route }]); setSection('Comparar') }}>Agregar al comparador de consultas</button>
                  <button type="button" onClick={() => download('ruta-cusco.json', JSON.stringify(route, null, 2))}>Descargar resultado JSON</button></div>
                <details><summary>Tramos y costos de la ruta</summary><Table headers={['Desde', 'Hasta', 'Calle registrada', `Costo (${route.unit})`, 'Distancia (m)', 'Tiempo estimado (s)']} rows={route.result.edges.map(e => [String(e.from), String(e.to), e.street ?? 'Sin nombre', fmt(e.cost, 3), fmt(e.length_m, 2), fmt(e.time_sec, 2)])} /></details>
              </>}
              <h3>Tres colas, una misma pregunta</h3>
              <Table headers={['Algoritmo', 'Cola', `Costo (${route.unit})`, 'Expandidos', 'Relajaciones', 'Decrease-key', 'Tiempo aislado (ms)']}
                rows={route.comparisons.map(r => [r.algorithm === 'astar' ? 'A*' : 'Dijkstra', queueNames[r.queue], fmt(r.cost, 3), r.expanded, r.relaxations, r.decrease_key, fmt(r.elapsed_ms_single_run, 3)])} />
              <p className="fineprint">Una ejecución sirve para inspección, no para declarar la cola más rápida. A* cambia la estrategia de búsqueda y se informa por separado.</p>
            </section>}
          </div>
          <aside className="context-pane"><h2>Condiciones en el punto</h2><p className="fineprint">Punto consultado: {fmt(conditionPoint.lat, 5)}, {fmt(conditionPoint.lon, 5)}{sourceCoords || sourcePoint ? ' (origen seleccionado)' : ' (centro de Cusco)'}.</p>
            <label>Fuente<select value={provider} onChange={e => { setProvider(e.target.value as typeof provider); setCondition(null) }}><option value="open-meteo">Open-Meteo</option><option value="openweathermap">OpenWeatherMap</option><option value="tomtom">TomTom, segmento puntual</option></select></label>
            {provider !== 'open-meteo' && <label>Clave del proveedor<input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} autoComplete="off" /></label>}
            <button type="button" onClick={fetchConditions} disabled={conditionLoading} className="secondary">{conditionLoading ? 'Consultando…' : 'Consultar ahora'}</button>
            {conditionError && <p className="error" role="alert">{conditionError}</p>}
            {!condition && !conditionLoading && !conditionError && <p className="fineprint">No hay lectura actual para este punto. Pulsa «Consultar ahora» para solicitarla.</p>}
            {condition && <div className="observation" role="status"><strong>{condition.observation?.source ?? 'TomTom, segmento consultado'}</strong>
              <p>Solicitado: {fmt(condition.requested.lat, 5)}, {fmt(condition.requested.lon, 5)}</p>
              {condition.observation ? <><p><b>{fmt(condition.observation.temperature_c, 1)} °C</b> · {fmt(condition.observation.relative_humidity_pct, 0)} % humedad</p>
                <p>Lluvia {fmt(condition.observation.precipitation_mm)} mm · Visibilidad {fmt(condition.observation.visibility_m, 0)} m · Ráfagas {fmt(condition.observation.wind_gusts_kmh, 1)} km/h</p>
                <p>Grilla del proveedor: {fmt(condition.observation.grid_point.lat, 5)}, {fmt(condition.observation.grid_point.lon, 5)}.</p>
                <p>Observado: {condition.observation.observed_at} ({condition.observation.timezone})</p></> : <p>Velocidad en el segmento: {fmt(condition.flow?.current_speed_kmh)} km/h; flujo libre: {fmt(condition.flow?.free_flow_speed_kmh)} km/h. No se aplica al resto de la red.</p>}
              <p>Consultado: {condition.fetched_at_utc}</p></div>}
            <p className="fineprint">Open-Meteo entrega datos de modelo, no de una estación exactamente en ese punto. La consulta TomTom es puntual y no altera el cálculo vial.</p>
          </aside>
        </div>
      </>}
      {section === 'Instancias' && <div className="reading-page"><p className="section-label">Preparar datos / 02</p><h1>Construye una instancia verificable</h1>
        <p>El docente puede dictar una red nueva. Todos los métodos usarán las mismas aristas y pesos.</p>
        <div className="segmented tabs">{(['tabla', 'json', 'archivo', 'generar'] as const).map(tab => <button type="button" aria-pressed={editorMode === tab} className={editorMode === tab ? 'active' : ''} onClick={() => { setEditorMode(tab); setEditorError('') }} key={tab}>{({ tabla: 'Nodos y aristas', json: 'JSON', archivo: 'CSV / TXT', generar: 'Generar' })[tab]}</button>)}</div>
        {editorMode === 'tabla' && <div className="editor-grid"><section><h2>Nodos</h2><p className="fineprint">Coordenadas opcionales. Si no se proporcionan, se dibuja un grafo abstracto.</p>
          {nodeDraft.map((node, i) => <div className="editor-row" key={i}><label>ID<input aria-label={`Nodo ${i + 1} ID`} value={node.id} onChange={e => setNodeDraft(old => old.map((n, j) => j === i ? { ...n, id: e.target.value } : n))} /></label>
            <label>Latitud<input aria-label={`Nodo ${i + 1} latitud`} value={node.lat} onChange={e => setNodeDraft(old => old.map((n, j) => j === i ? { ...n, lat: e.target.value } : n))} /></label>
            <label>Longitud<input aria-label={`Nodo ${i + 1} longitud`} value={node.lon} onChange={e => setNodeDraft(old => old.map((n, j) => j === i ? { ...n, lon: e.target.value } : n))} /></label>
            <button type="button" aria-label={`Eliminar nodo ${i + 1}`} onClick={() => setNodeDraft(old => old.filter((_, j) => j !== i))}>Quitar</button></div>)}
          <button type="button" onClick={() => setNodeDraft(old => [...old, { id: '', lat: '', lon: '' }])}>Agregar nodo</button></section>
          <section><h2>Aristas dirigidas</h2><p className="fineprint">Para dos sentidos, introduce dos aristas. El peso debe ser finito y no negativo.</p>
            {edgeDraft.map((edge, i) => <div className="editor-row" key={i}><label>Origen<input aria-label={`Arista ${i + 1} origen`} value={edge.origin} onChange={e => setEdgeDraft(old => old.map((n, j) => j === i ? { ...n, origin: e.target.value } : n))} /></label>
              <label>Destino<input aria-label={`Arista ${i + 1} destino`} value={edge.destination} onChange={e => setEdgeDraft(old => old.map((n, j) => j === i ? { ...n, destination: e.target.value } : n))} /></label>
              <label>Peso<input aria-label={`Arista ${i + 1} peso`} value={edge.weight} onChange={e => setEdgeDraft(old => old.map((n, j) => j === i ? { ...n, weight: e.target.value } : n))} /></label>
              <button type="button" aria-label={`Eliminar arista ${i + 1}`} onClick={() => setEdgeDraft(old => old.filter((_, j) => j !== i))}>Quitar</button></div>)}
            <button type="button" onClick={() => setEdgeDraft(old => [...old, { origin: '', destination: '', weight: '' }])}>Agregar arista</button></section>
          <button type="button" className="primary" onClick={applyTable}>Validar tabla y calcular</button></div>}
        {editorMode === 'json' && <div className="editor-box"><label>Instancia JSON: nodos, aristas y pesos<textarea rows={16} spellCheck={false} value={jsonDraft} onChange={e => setJsonDraft(e.target.value)} /></label>
          <button className="primary" type="button" onClick={applyJson}>Validar JSON y calcular</button></div>}
        {editorMode === 'archivo' && <div className="editor-box"><label>Importar JSON, CSV o TXT<input type="file" accept=".json,.csv,.txt" onChange={importFile} /></label>
          <label>Lista de aristas (origen destino peso, una por línea; CSV con cabecera opcional)<textarea rows={10} value={textDraft} onChange={e => setTextDraft(e.target.value)} /></label>
          <button className="primary" type="button" onClick={() => { setEditorError(''); setInstance({ kind: 'text', text: textDraft }) }}>Validar lista y calcular</button></div>}
        {editorMode === 'generar' && <div className="editor-box"><label>Perfil<select value={spec.kind === 'generated' ? spec.generator : 'random'} onChange={e => setSpec({ kind: 'generated', generator: e.target.value as 'random' | 'grid' | 'sparse' | 'dense', nodes: 30, seed })}><option value="random">Red local aleatoria</option><option value="grid">Cuadrícula</option><option value="sparse">Disperso</option><option value="dense">Denso</option></select></label>
          <label>Semilla<input type="number" value={seed} onChange={e => setSeed(Number(e.target.value))} /></label>
          <label>Vértices (no aplica a cuadrícula)<input type="number" min="2" max="500" value={spec.nodes ?? 30} onChange={e => setSpec({ ...spec, kind: 'generated', nodes: Number(e.target.value) })} /></label>
          <div className="two-fields"><label>Filas<input type="number" min="1" max="30" value={spec.rows ?? 5} onChange={e => setSpec({ ...spec, kind: 'generated', rows: Number(e.target.value) })} /></label>
            <label>Columnas<input type="number" min="1" max="30" value={spec.cols ?? 5} onChange={e => setSpec({ ...spec, kind: 'generated', cols: Number(e.target.value) })} /></label></div>
          <button className="primary" type="button" onClick={() => setInstance({ kind: 'generated', generator: spec.generator ?? 'random', nodes: spec.nodes ?? 30, rows: spec.rows ?? 5, cols: spec.cols ?? 5, seed })}>Generar y calcular</button></div>}
        {editorError && <p className="error" role="alert">{editorError}</p>}
        <p className="fineprint">Para un grafo con pesos genéricos, «tiempo» y «distancia» son etiquetas de consulta, no unidades físicas verificadas. En el resultado solo se muestra el costo abstracto; no se inventa una longitud vial.</p>
      </div>}
      {section === 'Comparar' && <div className="reading-page"><p className="section-label">Evidencia / 03</p><h1>Comparar sin mezclar experimentos</h1>
        <section className="section-space"><h2>Consultas guardadas en esta sesión</h2><p>Para comparar rutas de redes diferentes, primero calcula cada consulta en «Rutas» y agrégala aquí. Sus tiempos aislados no forman un benchmark.</p>
          {saved.length === 0 ? <p className="empty-state">Todavía no hay consultas guardadas. Calcula una ruta y pulsa «Agregar al comparador de consultas».</p> : <><Table headers={['Consulta', 'Unidad', 'Nodos', 'Aristas', 'Costo', 'Expandidos']} rows={saved.map(s => [s.name, s.metric, s.nodes, s.edges, fmt(s.route.result.cost, 3), s.route.result.expanded])} />
            <button type="button" onClick={() => setSaved([])}>Vaciar consultas guardadas</button><p className="fineprint">No compares costos entre unidades o redes distintas como si fueran el mismo problema.</p></>}</section>
        <section className="section-space"><h2>Banco canónico: tres colas de Dijkstra</h2>
          <label>Topología<select value={profile} onChange={e => setProfile(e.target.value as typeof profile)}><option value="sparse">Disperso</option><option value="dense">Denso</option></select></label>
          {benchmarkLoading && <p role="status">Cargando mediciones guardadas…</p>}{benchmarkError && <p className="error" role="alert">{benchmarkError}</p>}
          {benchmark && !benchmarkLoading && <><p className="fineprint">Generado {benchmark.generated_at_utc}. Fuente: benchmark_results.json (28/10/2026). Mediana e IQR en microsegundos; los intervalos no prueban significación.</p>
            <div className="bench-chart" role="img" aria-label="Barras de medianas por cola y escala">
              {benchmark.results.scales.map((size, i) => {
                const rows = (Object.keys(queueNames) as Queue[]).map(q => ({ q, v: benchmark.results.data[q][i].median_us }))
                const max = Math.max(...rows.map(r => r.v))
                return <div className="bench-group" key={size}><strong>{size} vértices</strong><div>{rows.map(r => <div className="bar-line" key={r.q}><span>{queueNames[r.q]}</span><div className={`bar bar-${r.q}`} style={{ width: `${Math.max(2, r.v / max * 100)}%` }} /><b>{fmt(r.v, 1)} µs</b></div>)}</div></div>
              })}</div>
            <Table headers={['Vértices', 'Aristas', 'Cola', 'Mediana (µs)', 'Q1 (µs)', 'Q3 (µs)', 'Muestras']}
              rows={benchmark.results.scales.flatMap((_, i) => (Object.keys(queueNames) as Queue[]).map(q => { const r = benchmark.results.data[q][i]; return [r.nodes, r.edges, queueNames[q], fmt(r.median_us, 1), fmt(r.q1_us, 1), fmt(r.q3_us, 1), r.sample_count ?? ''] }))} />
            <button type="button" onClick={() => download(`benchmark-${profile}.json`, JSON.stringify(benchmark, null, 2))}>Descargar perfil JSON</button>
          </>}
        </section>
        {pilot && <section className="section-space"><h2>Piloto posterior, independiente</h2>
          <p className="fineprint">{pilot.generated_at_utc}. Fuente: pilot_benchmark_results.json; 18 muestras, no se agregan al banco de 1350 ni permiten decidir un ganador. Se usa el perfil {profile === 'sparse' ? 'disperso' : 'denso'} seleccionado arriba.</p>
          <Table headers={['Vértices', 'Aristas', 'Cola', 'Mediana (µs)', 'Muestras']}
            rows={pilot.profiles[profile].scales.flatMap((_, i) => (Object.keys(queueNames) as Queue[]).map(q => {
              const r = pilot.profiles[profile].data[q][i]
              return [r.nodes, r.edges, queueNames[q], fmt(r.median_us, 1), r.sample_count ?? '']
            }))} />
        </section>}
      </div>}
      {section === 'Experimentos' && <div className="reading-page"><p className="section-label">Laboratorio / 04</p><h1>Mide otra instancia, sin tocar el informe</h1>
        <p>Dos redes por tamaño, semillas guardadas, dos calentamientos y repeticiones acotadas. Los resultados se quedan en esta sesión.</p>
        <form className="experiment-form" onSubmit={async e => {
          e.preventDefault(); setExperiment(null); setExperimentError(''); setExperimentLoading(true)
          try { const parsed = sizes.split(',').map(n => Number(n.trim())); setExperiment(await api<Experiment>('/experiments', { profile, sizes: parsed, seed, runs })) }
          catch (err) { setExperimentError(err instanceof Error ? err.message : 'No se pudo medir.') }
          finally { setExperimentLoading(false) }
        }}>
          <label>Perfil<select value={profile} onChange={e => setProfile(e.target.value as typeof profile)}><option value="sparse">Disperso</option><option value="dense">Denso</option></select></label>
          <label>Tamaños, separados por comas<input value={sizes} onChange={e => setSizes(e.target.value)} /></label>
          <label>Semilla<input type="number" value={seed} onChange={e => setSeed(Number(e.target.value))} /></label>
          <label>Repeticiones por red<input type="number" min="2" max="10" value={runs} onChange={e => setRuns(Number(e.target.value))} /></label>
          <button className="primary" type="submit" disabled={experimentLoading}>{experimentLoading ? 'Midiendo…' : 'Ejecutar experimento'}</button>
        </form>
        {experimentError && <p className="error" role="alert">{experimentError}</p>}
        {!experiment && !experimentLoading && !experimentError && <p className="empty-state">Aún no hay mediciones nuevas. Ejecuta el experimento para obtener una tabla.</p>}
        {experiment && <section className="section-space"><h2>Mediciones de esta sesión</h2><p className="fineprint">Perfil medido: {experiment.profile}. {experiment.generated_at_utc}. Separadas del banco canónico. La mediana observada no prueba una ventaja universal.</p>
          <Table headers={['Vértices', 'Aristas', 'Cola', 'Mediana (µs)', 'Q1 (µs)', 'Q3 (µs)', 'Semillas']} rows={experiment.rows.map(r => [r.nodes, r.edges, queueNames[r.queue], fmt(r.median_us, 1), fmt(r.q1_us, 1), fmt(r.q3_us, 1), r.instance_seeds.join(', ')])} />
          <button type="button" onClick={() => download('experimento-sesion.json', JSON.stringify(experiment, null, 2))}>Descargar muestras y protocolo</button></section>}
      </div>}
      {section === 'Cobertura Cusco' && <div className="reading-page"><p className="section-label">Alcance geográfico / 05</p><h1>Dos coberturas locales, ninguna es todo Cusco</h1>
        <p>La red central se extrajo alrededor de (-13.5165, -71.9788) con un radio de 1500 m el 28/10/2026. La cobertura ampliada es una consulta radial de 3000 m recortada por distancia de red, con base OSM del 10/08/2026; incluye 1938 nodos y 4753 aristas. Ninguna de las dos representa todas las vías de la ciudad.</p>
        <div className="coverage-list">{catalog?.networks.map(n => <section key={n.kind}><h2>{n.label}</h2><p>{n.available ? 'Snapshot local revisado y disponible para rutas.' : 'Sin snapshot validado. No se muestran rutas de esta cobertura.'}</p>
          {n.available && <button type="button" onClick={() => setInstance({ kind: n.kind })}>Consultar esta red</button>}</section>) ?? <p role="status">Consultando coberturas…</p>}</div>
        <p className="warning">Un punto fuera del snapshot o lejos de un nodo no se conectará artificialmente. Ampliar la cobertura exige adquirir, comprobar y versionar otra red. No cambia el banco histórico.</p>
        <p className="fineprint"><code>python/scripts/build_urban_snapshot.py</code> prepara un pendiente y exige una segunda revisión para publicarlo; las coberturas sin archivo revisado permanecen inactivas.</p>
      </div>}
      {section === 'Datos y método' && <div className="reading-page"><p className="section-label">Procedencia / 06</p><h1>Qué mide este sistema y qué no</h1>
        <div className="method-grid"><section><h2>Problema</h2><p>Grafo dirigido con pesos finitos no negativos. Entradas: nodos, aristas, métrica, origen y destino. Salida: camino de costo mínimo o inalcanzabilidad. Las tres colas cambian la estructura, no la función objetivo.</p></section>
          <section><h2>Verificación</h2><p>Dijkstra con binario, 4-ario y Fibonacci deben coincidir en costo. A* usa una heurística consistente escalada con los pesos y se informa aparte. La suite Python incluye casos básicos, límite, adversos y oráculos independientes.</p></section>
          <section><h2>Tres fuentes distintas</h2><p>Seis nodos: ejemplo esquemático. Benchmark: grafos sintéticos y 1350 mediciones históricas del 28/10. OSM: snapshot central de 891 nodos y 2139 aristas, más un snapshot ampliado radial de 3 km con 1938 nodos y 4753 aristas; sin pendiente ni tráfico medido por tramo.</p></section>
          <section><h2>Clima y tráfico</h2><p>Los proveedores pueden devolver observaciones y un punto de grilla diferente al solicitado. El horario es una simulación. Los multiplicadores globales modifican el costo, no la elección de la ruta.</p></section></div>
        <h2>Recursos del proyecto</h2><p><a href={apiUrl('/openapi.json')}>Contrato OpenAPI</a> · <a href={apiUrl('/docs')} target="_blank" rel="noreferrer">Documentación de API</a> · <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">Atribución OpenStreetMap</a></p>
        <p className="fineprint">La aplicación no sustituye bitácoras de aprendizaje, entregas ni defensas individuales.</p>
      </div>}
    </main><footer className="site-footer"><span>UNSAAC · Grupo 5 · Algoritmos Avanzados</span><span>Datos del proyecto, no navegación vial en tiempo real.</span></footer>
  </>
}

createRoot(document.getElementById('root')!).render(<App />)
