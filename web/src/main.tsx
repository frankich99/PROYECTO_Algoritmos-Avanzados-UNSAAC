import { useCallback, useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import GraphView from './GraphView'
import { api, apiUrl } from './api'
import type { Benchmark, Catalog, Condition, Experiment, InstanceSpec, Metric, Pilot, Point, Preview, Queue, RouteResponse } from './api'
import { emptyKeys, forgetKeys, forgetWeather, readKeys, readWeather, saveKeys, saveWeather } from './localSettings'
import type { ProviderKeys } from './localSettings'
import WeatherReading from './WeatherReading'
import TrafficReading from './TrafficReading'
import { fmt } from './format'
import 'maplibre-gl/dist/maplibre-gl.css'
import './style.css'

const queueNames: Record<Queue, string> = { binary_heap: 'Binario', '4ary_heap': '4-ario', fibonacci_heap: 'Fibonacci' }
const initialGraph = { name: 'Grafo propuesto', directed: true, nodes: [{ id: 'A' }, { id: 'B' }, { id: 'C' }],
  edges: [{ origin: 'A', destination: 'B', weight: 4 }, { origin: 'A', destination: 'C', weight: 10 }, { origin: 'B', destination: 'C', weight: 2 }] }
const menu = ['Rutas', 'Instancias', 'Comparar', 'Experimentos', 'Cobertura Cusco', 'Datos y método'] as const
type Section = typeof menu[number]
type Saved = { name: string; metric: string; network: string; nodes: number; edges: number; route: RouteResponse }

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

function ProviderKeyInput({ provider, configured, value, onChange }: {
  provider: keyof ProviderKeys; configured?: boolean; value: string; onChange: (value: string) => void
}) {
  const label = provider === 'tomtom' ? 'TomTom' : 'OpenWeatherMap'
  return <div className="provider-key">
    <p className="fineprint">{configured === undefined ? 'Comprobando las claves configuradas en el servidor…' :
      configured ? `Clave ${label} configurada en el servidor; no se muestra ni se envía al navegador.` :
        `Sin clave ${label} en el servidor. Puedes introducir una para esta consulta.`}</p>
    <label>{configured ? `Usar otra clave ${label} (opcional)` : `Clave ${label}`}
      <input type="password" maxLength={200} value={value} onChange={e => onChange(e.target.value)} autoComplete="off" />
    </label>
    {value && <button type="button" className="text-button" onClick={() => onChange('')}>Quitar clave del navegador y usar {configured ? 'la del servidor' : 'ninguna'}</button>}
  </div>
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
  const [weatherEnabled, setWeatherEnabled] = useState(false)
  const [weather, setWeather] = useState<'historical' | 'snapshot' | 'live' | 'saved'>('live')
  const [weatherProvider, setWeatherProvider] = useState<'open-meteo' | 'openweathermap'>('openweathermap')
  const [conditionProvider, setConditionProvider] = useState<'open-meteo' | 'openweathermap' | 'tomtom'>('openweathermap')
  const [rememberKeys, setRememberKeys] = useState(() => {
    try { return localStorage.getItem('cusco-provider-keys-v1') !== null } catch { return false }
  })
  const [apiKeys, setApiKeys] = useState<ProviderKeys>(() => readKeys())
  const [storageError, setStorageError] = useState('')
  const [liveReading, setLiveReading] = useState<Condition | null>(null)
  const [savedReading, setSavedReading] = useState<Condition | null>(() => readWeather())
  const [weatherLoading, setWeatherLoading] = useState(false)
  const [weatherError, setWeatherError] = useState('')
  const [weatherRefresh, setWeatherRefresh] = useState(0)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [timeTick, setTimeTick] = useState(Date.now())
  const [traffic, setTraffic] = useState(false)
  const [trafficMode, setTrafficMode] = useState<'simulated' | 'current'>('simulated')
  const [simulatedTime, setSimulatedTime] = useState('13:00')
  const [trafficUseTomTom, setTrafficUseTomTom] = useState(false)
  const [gpsLoading, setGpsLoading] = useState(false)
  const [gpsError, setGpsError] = useState('')
  const [gpsFix, setGpsFix] = useState<{ timestamp: number; accuracy: number } | null>(null)
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
  const gpsRequest = useRef(0)
  const sourceCoords = preview?.geographic ? preview.coords[source] : undefined
  const conditionPoint = sourcePoint ?? (sourceCoords ? { lat: sourceCoords[1], lon: sourceCoords[0] } : { lat: -13.5165, lon: -71.9788 })
  const activeReading = weather === 'saved' ? savedReading : liveReading
  const observedAt = liveReading?.observation?.observed_at
  const zone = liveReading?.observation?.timezone === 'America/Lima' ? '-05:00' : 'Z'
  const observedTime = observedAt ? Date.parse(observedAt + (/[Z+-]\d\d:?\d\d$/.test(observedAt) || observedAt.endsWith('Z') ? '' : zone)) : NaN
  const staleLive = weather === 'live' && (!Number.isFinite(observedTime) || Math.abs(timeTick - observedTime) > 30 * 60 * 1000)
  const samePoint = !!activeReading && Math.abs(activeReading.requested.lat - conditionPoint.lat) < 0.00001 &&
    Math.abs(activeReading.requested.lon - conditionPoint.lon) < 0.00001
  const canApplyWeather = !weatherEnabled || weather === 'historical' || weather === 'snapshot' ||
    (!!activeReading?.observation && typeof activeReading.multiplier === 'number' && samePoint &&
      (weather !== 'live' || !staleLive) && !weatherLoading && !weatherError)
  const gpsExpired = !!gpsFix && timeTick - gpsFix.timestamp > 5 * 60 * 1000
  const validSimulatedTime = /^([01]\d|2[0-3]):[0-5]\d$/.test(simulatedTime)
  const simulatedHour = validSimulatedTime ? Number(simulatedTime.slice(0, 2)) + Number(simulatedTime.slice(3)) / 60 : null
  const canApplyTraffic = !traffic || (trafficMode === 'simulated' ? validSimulatedTime :
    !gpsLoading && !gpsExpired && (!trafficUseTomTom || !preview?.geographic || !!apiKeys.tomtom.trim() || !!catalog?.provider_keys?.tomtom))
  useEffect(() => () => { routeAbort.current?.abort(); conditionAbort.current?.abort(); gpsRequest.current += 1 }, [])
  useEffect(() => {
    if (!rememberKeys) return
    setStorageError(saveKeys(apiKeys) ? '' : 'El navegador no permitió guardar las claves. Permanecen solo en esta sesión.')
  }, [rememberKeys, apiKeys])
  useEffect(() => {
    if (!weatherEnabled || weather !== 'live' || metric !== 'time' || !preview || preview.metric === 'weight') {
      setWeatherLoading(false)
      return
    }
    const controller = new AbortController()
    setWeatherLoading(true); setWeatherError(''); setLiveReading(null)
    api<Condition>('/conditions', { point: conditionPoint, provider: weatherProvider,
      key: weatherProvider === 'openweathermap' ? apiKeys.openweathermap.trim() || null : null }, controller.signal)
      .then(value => { if (!controller.signal.aborted) { setLiveReading(value); setTimeTick(Date.now()) } })
      .catch(error => { if (!controller.signal.aborted) setWeatherError(error instanceof Error ? error.message : 'No se obtuvo el clima actual.') })
      .finally(() => { if (!controller.signal.aborted) setWeatherLoading(false) })
    return () => controller.abort()
  }, [weatherEnabled, weather, metric, weatherProvider, apiKeys.openweathermap, conditionPoint.lat, conditionPoint.lon, preview, weatherRefresh])
  useEffect(() => {
    if (!autoRefresh || !weatherEnabled || weather !== 'live') return
    const timer = window.setInterval(() => setWeatherRefresh(n => n + 1), 10 * 60 * 1000)
    return () => window.clearInterval(timer)
  }, [autoRefresh, weatherEnabled, weather])
  useEffect(() => {
    if ((!weatherEnabled || weather !== 'live') && (!traffic || trafficMode !== 'current')) return
    const timer = window.setInterval(() => setTimeTick(Date.now()), 60 * 1000)
    return () => window.clearInterval(timer)
  }, [weatherEnabled, weather, traffic, trafficMode])
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
  useEffect(() => { routeAbort.current?.abort(); setRouteLoading(false); setRoute(null) }, [algorithm, queue, weatherEnabled, weather, weatherProvider, liveReading, savedReading, traffic, trafficMode, simulatedTime, trafficUseTomTom, apiKeys.tomtom])
  useEffect(() => { conditionAbort.current?.abort(); setConditionLoading(false); setCondition(null); setConditionError('') }, [sourcePoint, source, preview, conditionProvider, apiKeys])
  useEffect(() => { routeAbort.current?.abort(); setRouteLoading(false); setRoute(null); setRouteError('') }, [source, target, sourcePoint, targetPoint])

  const setInstance = (value: InstanceSpec) => { gpsRequest.current += 1; setGpsLoading(false); setGpsFix(null); setGpsError(''); setSourcePoint(null); setTargetPoint(null); setSpec(value); setSection('Rutas') }
  const mapPick = useCallback((point: Point) => {
    routeAbort.current?.abort(); setRouteLoading(false)
    if (pick === 'source') { gpsRequest.current += 1; setGpsLoading(false); setGpsFix(null); setGpsError(''); setSourcePoint(point); setPick('target') }
    else setTargetPoint(point)
    setRoute(null)
  }, [pick])
  function useGps() {
    if (!navigator.geolocation) { setGpsError('Este navegador no ofrece ubicación. Selecciona un nodo o escribe coordenadas.'); return }
    const request = ++gpsRequest.current
    if (gpsFix) setSourcePoint(null)
    setGpsLoading(true); setGpsError(''); setGpsFix(null); setRoute(null)
    navigator.geolocation.getCurrentPosition(position => {
      if (request !== gpsRequest.current) return
      const { latitude, longitude, accuracy } = position.coords
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude) || !Number.isFinite(accuracy)) {
        setGpsError('El dispositivo entregó coordenadas inválidas.'); setGpsLoading(false); return
      }
      if (accuracy > 250) {
        setGpsError(`La precisión del dispositivo es ±${Math.round(accuracy)} m; no es suficiente para elegir un nodo. Inténtalo de nuevo o selecciona un nodo.`)
        setGpsLoading(false); return
      }
      setSourcePoint({ lat: latitude, lon: longitude }); setGpsFix({ timestamp: position.timestamp, accuracy })
      setTimeTick(Date.now()); setGpsLoading(false); setRoute(null)
    }, error => {
      if (request !== gpsRequest.current) return
      setGpsLoading(false)
      setGpsError(error.code === 1 ? 'Permiso de ubicación denegado. Puedes elegir un nodo manualmente.' :
        error.code === 3 ? 'La ubicación tardó demasiado. Vuelve a intentarlo o elige un nodo.' :
          'No se pudo conocer tu ubicación. Puedes elegir un nodo manualmente.')
    }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 })
  }
  async function runRoute(event: React.FormEvent) {
    event.preventDefault(); routeAbort.current?.abort()
    if (!canApplyWeather && metric === 'time' && preview?.metric !== 'weight') {
      setRouteError('Actualiza la lectura meteorológica del origen antes de calcular.'); return
    }
    if (!canApplyTraffic && metric === 'time' && preview?.metric !== 'weight') {
      setRouteError('Revisa la hora, el GPS o la clave TomTom antes de calcular.'); return
    }
    const controller = new AbortController(); routeAbort.current = controller
    setRoute(null); setRouteError(''); setRouteLoading(true)
    try {
      const response = await api<RouteResponse>('/routes/solve', { instance: spec, metric, source: sourcePoint ? null : source,
        target: targetPoint ? null : target, source_point: sourcePoint, target_point: targetPoint,
        algorithm, queue, compare: true,
         scenario: { weather: metric === 'time' && preview?.metric !== 'weight' && weatherEnabled ? weather : 'none',
           weather_provider: weatherProvider,
           weather_observation: weatherEnabled && (weather === 'live' || weather === 'saved') ? activeReading?.observation : null,
           weather_request_point: weatherEnabled && (weather === 'live' || weather === 'saved') ? activeReading?.requested : null,
             traffic_hour: metric === 'time' && preview?.metric !== 'weight' && traffic && trafficMode === 'simulated' ? simulatedHour : null,
             traffic_mode: metric === 'time' && preview?.metric !== 'weight' && traffic ? trafficMode : null,
             traffic_live: metric === 'time' && preview?.geographic && traffic && trafficMode === 'current' && trafficUseTomTom,
             traffic_live_key: metric === 'time' && preview?.geographic && traffic && trafficMode === 'current' && trafficUseTomTom ? apiKeys.tomtom.trim() : null } }, controller.signal)
      if (!controller.signal.aborted) setRoute(response)
    } catch (e) { if (!controller.signal.aborted) setRouteError(e instanceof Error ? e.message : 'No se pudo calcular la ruta.') }
    finally { if (!controller.signal.aborted) setRouteLoading(false) }
  }
  async function fetchConditions() {
    conditionAbort.current?.abort(); const controller = new AbortController(); conditionAbort.current = controller
    setCondition(null); setConditionError(''); setConditionLoading(true)
    try {
      const response = await api<Condition>('/conditions', { point: conditionPoint, provider: conditionProvider,
        key: conditionProvider === 'open-meteo' ? null : apiKeys[conditionProvider].trim() || null }, controller.signal)
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
  const updateKey = (provider: keyof ProviderKeys, value: string) => setApiKeys(old => ({ ...old, [provider]: value }))
  const toggleRemember = (value: boolean) => {
    if (!value) { forgetKeys(); setStorageError('') }
    setRememberKeys(value)
  }
  const saveReading = (value: Condition) => {
    if (!saveWeather(value)) { setStorageError('No se pudo guardar la lectura en este navegador.'); return false }
    setSavedReading(value); setStorageError('Lectura guardada en este navegador, sin credenciales.'); return true
  }

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
            <div className="form-section"><h2>02 / Puntos</h2><p className="fineprint">Elige nodos de la lista. Para las redes OSM también puedes marcar puntos en el mapa o escribir coordenadas.</p>
              <label>Origen (nodo) <select value={sourcePoint ? '' : source} onChange={e => { gpsRequest.current += 1; setGpsLoading(false); setGpsFix(null); setGpsError(''); setSource(e.target.value); setSourcePoint(null); setRoute(null) }}>
                {sourcePoint && <option value="">Coordenadas seleccionadas</option>}
                {preview?.ids.map(id => <option value={String(id)} key={String(id)}>{String(id)}</option>)}
              </select></label>
              <label>Destino (nodo) <select value={targetPoint ? '' : target} onChange={e => { setTarget(e.target.value); setTargetPoint(null); setRoute(null) }}>
                {targetPoint && <option value="">Coordenadas seleccionadas</option>}
                {preview?.ids.map(id => <option value={String(id)} key={String(id)}>{String(id)}</option>)}
              </select></label>
              {preview?.geographic && <><div className="pick-row"><button type="button" className={pick === 'source' ? 'choice selected' : 'choice'} onClick={() => { setPick('source'); setMapRequested(n => n + 1) }}>Elegir origen en mapa</button>
                <button type="button" className={pick === 'target' ? 'choice selected' : 'choice'} onClick={() => { setPick('target'); setMapRequested(n => n + 1) }}>Elegir destino en mapa</button></div>
                <div className="coord-grid">{(['source', 'target'] as const).map(type => {
                  const value = type === 'source' ? sourcePoint : targetPoint
                  const setter = type === 'source' ? setSourcePoint : setTargetPoint
                  return <fieldset key={type}><legend>{type === 'source' ? 'Origen' : 'Destino'} por coordenadas</legend>
                    <div className="coord-fields"><label>Latitud<input type="number" step="any" min="-90" max="90" value={value?.lat ?? ''}
                      onChange={e => { if (type === 'source') { gpsRequest.current += 1; setGpsLoading(false); setGpsFix(null); setGpsError('') } setter({ lat: Number(e.target.value), lon: value?.lon ?? -71.9788 }); setRoute(null) }} /></label>
                      <label>Longitud<input type="number" step="any" min="-180" max="180" value={value?.lon ?? ''}
                        onChange={e => { if (type === 'source') { gpsRequest.current += 1; setGpsLoading(false); setGpsFix(null); setGpsError('') } setter({ lat: value?.lat ?? -13.5165, lon: Number(e.target.value) }); setRoute(null) }} /></label></div>
                    {value && <button type="button" className="text-button" onClick={() => { if (type === 'source') { gpsRequest.current += 1; setGpsLoading(false); setGpsFix(null); setGpsError('') } setter(null); setRoute(null) }}>Usar ID en su lugar</button>}
                  </fieldset>
                })}</div>
              </>}
            </div>
            <div className="form-section"><h2>03 / Algoritmo</h2><div className="two-fields">
              <label>Algoritmo<select value={algorithm} onChange={e => setAlgorithm(e.target.value as 'dijkstra' | 'astar')}><option value="dijkstra">Dijkstra</option><option value="astar">A* consistente</option></select></label>
              <label>Cola<select value={queue} onChange={e => setQueue(e.target.value as Queue)}>{(Object.keys(queueNames) as Queue[]).map(q => <option key={q} value={q}>{queueNames[q]}</option>)}</select></label></div>
              <p className="fineprint">Se ejecutan también los tres Dijkstra y A* con la cola elegida para contrastar costos.</p></div>
            {metric === 'time' && preview?.metric !== 'weight' && <div className="form-section scenario"><h2>04 / Condiciones</h2>
              <label className="check"><input type="checkbox" checked={weatherEnabled} onChange={e => setWeatherEnabled(e.target.checked)} /> Aplicar datos meteorológicos al tiempo estimado</label>
              {weatherEnabled && <div className="details-body"><label>Fuente climática<select value={weather} onChange={e => setWeather(e.target.value as typeof weather)}>
                <option value="live">Consultar condiciones actuales</option><option value="historical">Lectura histórica del informe</option>
                <option value="snapshot">Snapshot incluido en el proyecto</option><option value="saved" disabled={!savedReading}>Lectura guardada en este navegador</option></select></label>
                {weather === 'live' && <><label>Proveedor<select value={weatherProvider} onChange={e => setWeatherProvider(e.target.value as typeof weatherProvider)}>
                  <option value="openweathermap">OpenWeatherMap, clave del servidor</option><option value="open-meteo">Open-Meteo, sin clave</option></select></label>
                  {weatherProvider === 'openweathermap' && <ProviderKeyInput provider="openweathermap" configured={catalog?.provider_keys?.openweathermap}
                    value={apiKeys.openweathermap} onChange={value => updateKey('openweathermap', value)} />}
                  <div className="inline-actions"><button type="button" onClick={() => setWeatherRefresh(n => n + 1)} disabled={weatherLoading}>Actualizar lectura</button>
                    <label className="check"><input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} /> Actualizar cada 10 min</label></div>
                  {weatherLoading && <p role="status">Consultando las condiciones del origen…</p>}
                  {weatherError && <p className="error" role="alert">{weatherError}</p>}
                  {liveReading && <><WeatherReading data={liveReading} />{liveReading.multiplier == null && <p className="warning">Reinicia la API Python para habilitar el cálculo con esta lectura.</p>}
                    {staleLive && <p className="warning">Esta lectura tiene más de 30 minutos o no tiene hora válida. Actualízala antes de calcular.</p>}
                    <button type="button" onClick={() => saveReading(liveReading)} disabled={liveReading.multiplier == null}>Guardar esta lectura localmente</button></>}
                </>}
                {weather === 'saved' && <>{savedReading && <WeatherReading data={savedReading} />}{!samePoint && <p className="warning">La lectura guardada pertenece a otro punto. Cambia el origen o actualiza el clima.</p>}
                  <p className="fineprint">Una lectura guardada es un escenario reproducible, no una observación actual.</p>
                  <button type="button" onClick={() => { forgetWeather(); setSavedReading(null); setWeather('live') }}>Eliminar lectura guardada</button></>}
                <p className="fineprint">Estas condiciones ajustan todos los tiempos por igual: no cambian el camino ni son mediciones en cada calle.</p>
              </div>}
              <label className="check"><input type="checkbox" checked={traffic} onChange={e => setTraffic(e.target.checked)} /> Ajustar tiempo por tráfico</label>
              {traffic && <fieldset className="traffic-options"><legend>Elige cómo obtener el factor de tráfico</legend>
                <label className="check"><input type="radio" name="traffic-mode" checked={trafficMode === 'simulated'} onChange={() => setTrafficMode('simulated')} /> Hora simulada</label>
                {trafficMode === 'simulated' && <div className="option-body"><label>Hora en Cusco (HH:MM)<input type="time" required value={simulatedTime} onChange={e => setSimulatedTime(e.target.value)} /></label>
                  <p className="fineprint">Elige una hora para comparar el supuesto horario del proyecto. No son velocidades medidas.</p></div>}
                <label className="check"><input type="radio" name="traffic-mode" checked={trafficMode === 'current'} onChange={() => { setTrafficMode('current'); setTimeTick(Date.now()) }} /> Hora actual de Cusco · GPS opcional</label>
                {trafficMode === 'current' && <div className="option-body">
                  <p className="fineprint">La hora exacta de Cusco la calcula el servidor al resolver. El GPS solo coloca el origen; no mide congestión ni se solicita sin pulsar el botón.</p>
                  {preview?.geographic ? <><button type="button" onClick={useGps} disabled={gpsLoading}>{gpsLoading ? 'Obteniendo ubicación…' : 'Usar mi ubicación como origen'}</button>
                    {gpsLoading && <p role="status">Solicitando ubicación al navegador…</p>}
                    {gpsError && <p className="error" role="alert">{gpsError}</p>}
                    {gpsFix && <p role="status" className={gpsExpired ? 'warning' : 'fineprint'}>GPS: {fmt(sourcePoint?.lat, 5)}, {fmt(sourcePoint?.lon, 5)}; precisión declarada ±{fmt(gpsFix.accuracy, 0)} m. {gpsExpired ? 'La ubicación tiene más de cinco minutos; solicítala de nuevo o selecciona un nodo.' : 'Origen enviado para ajuste al nodo vial próximo.'}</p>}
                  </> : <p className="fineprint">El GPS requiere seleccionar una de las redes OSM de Cusco.</p>}
                   <label className="check"><input type="checkbox" checked={trafficUseTomTom} onChange={e => setTrafficUseTomTom(e.target.checked)} disabled={!preview?.geographic} /> Consultar además TomTom en el origen</label>
                   {trafficUseTomTom && preview?.geographic && <ProviderKeyInput provider="tomtom" configured={catalog?.provider_keys?.tomtom}
                     value={apiKeys.tomtom} onChange={value => updateKey('tomtom', value)} />}
                   {trafficUseTomTom && preview?.geographic && !apiKeys.tomtom.trim() && !catalog?.provider_keys?.tomtom && <p className="fineprint">Introduce la clave o desactiva TomTom para calcular con el supuesto horario.</p>}
                  <p className="fineprint">Sin TomTom se usa el supuesto horario a la hora actual. Con TomTom se aplica la relación entre velocidad libre y velocidad puntual como factor uniforme exploratorio, nunca como medición de toda la ruta.</p>
                </div>}
              </fieldset>}
            </div>}
            <button type="submit" className="primary" disabled={!preview || routeLoading || (metric === 'time' && preview?.metric !== 'weight' && (!canApplyWeather || !canApplyTraffic))}>{routeLoading ? 'Calculando ruta…' : 'Calcular y contrastar'}</button>
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
                {route.scenario.kind === 'uniform_scenario' && <div className="scenario-result"><h3>Cómo se ajustó el tiempo</h3>
                  <dl className="reading-grid"><div><dt>Tiempo base de la ruta</dt><dd>{fmt(route.result.cost != null ? route.result.cost / route.scenario.factor : null, 2)} s</dd></div>
                    <div><dt>Factor aplicado</dt><dd>{fmt(route.scenario.factor, 4)}×</dd></div>
                    <div><dt>Tiempo ajustado</dt><dd>{fmt(route.result.time_sec, 2)} s</dd></div>
                    <div><dt>Diferencia estimada</dt><dd>+{fmt(route.result.cost != null ? route.result.cost - route.result.cost / route.scenario.factor : null, 2)} s</dd></div></dl>
                  <p className="fineprint">Tiempo ajustado = tiempo base × factor total. Se escala toda la red por igual: el camino y las operaciones de las colas no cambian.</p>
                  {route.scenario.weather_source && <section className="scenario-source"><h4>Clima: {route.scenario.weather_source}</h4>
                    <p>Factor {fmt(route.scenario.weather_factor, 4)}×. Lectura {route.scenario.weather_observed_at} ({route.scenario.weather_timezone}). {route.scenario.weather_session_supplied ? 'Lectura aportada por el navegador, no verificada por el servidor.' : route.scenario.weather_cached ? 'Lectura local histórica del proyecto.' : 'Consulta realizada por el servidor.'}</p>
                    {route.scenario.weather_reading && <p>Lluvia {fmt(route.scenario.weather_reading.precipitation_mm)} mm; humedad {fmt(route.scenario.weather_reading.relative_humidity_pct, 0)} %; visibilidad {fmt(route.scenario.weather_reading.visibility_m, 0)} m; ráfagas {fmt(route.scenario.weather_reading.wind_gusts_kmh, 1)} km/h. Temperatura {fmt(route.scenario.weather_reading.temperature_c, 1)} °C (informativa).</p>}
                    {route.scenario.weather_contributions && <p>Aportes: {Object.entries(route.scenario.weather_contributions).map(([name, value]) => `${name} +${fmt(value * 100, 2)} %`).join(' · ')}.</p>}
                    {route.scenario.requested_point && <p className="fineprint">Origen consultado: {fmt(route.scenario.requested_point.lat, 5)}, {fmt(route.scenario.requested_point.lon, 5)}. Grilla del proveedor: {fmt(route.scenario.weather_grid_point?.lat, 5)}, {fmt(route.scenario.weather_grid_point?.lon, 5)}.</p>}
                  </section>}
                  {route.scenario.traffic_source && <section className="scenario-source"><h4>Tráfico: {route.scenario.traffic_source}</h4>
                    <p>Factor {fmt(route.scenario.traffic_factor, 4)}×. {route.scenario.traffic_mode === 'current' ? `Hora del servidor: ${route.scenario.traffic_observed_at} (Cusco).` : `Hora simulada: ${String(Math.floor(route.scenario.traffic_hour ?? 0)).padStart(2, '0')}:${String(Math.round(((route.scenario.traffic_hour ?? 0) % 1) * 60)).padStart(2, '0')} (Cusco).`} {route.scenario.traffic_flow ? 'Dato de un solo segmento cercano al origen.' : `Nivel horario supuesto: ${route.scenario.traffic_level}.`}</p>
                    {route.scenario.traffic_flow && route.scenario.traffic_point && <TrafficReading flow={route.scenario.traffic_flow} requested={route.scenario.traffic_point} fetchedAt={route.scenario.traffic_flow_fetched_at_utc ?? ''} />}
                    <p className="fineprint">{route.scenario.traffic_description && !route.scenario.traffic_flow ? `Descripción del supuesto: ${route.scenario.traffic_description} ` : ''}No hay velocidades medidas para cada arista del recorrido.</p>
                  </section>}
                  <p className="fineprint">Es una sensibilidad hipotética, no un tiempo real de navegación.</p></div>}
                <div className="result-actions"><button type="button" onClick={() => { setSaved(old => [...old, { name: `${route.network}: ${route.source} a ${route.target}`, metric: route.unit, network: route.network, nodes: route.counts.nodes, edges: route.counts.edges, route }]); setSection('Comparar') }}>Agregar al comparador de consultas</button>
                  <button type="button" onClick={() => download('ruta-cusco.json', JSON.stringify(route, null, 2))}>Descargar resultado JSON</button></div>
                <details><summary>Tramos y costos de la ruta</summary><Table headers={['Desde', 'Hasta', 'Calle registrada', `Costo (${route.unit})`, 'Distancia (m)', 'Tiempo estimado (s)']} rows={route.result.edges.map(e => [String(e.from), String(e.to), e.street ?? 'Sin nombre', fmt(e.cost, 3), fmt(e.length_m, 2), fmt(e.time_sec, 2)])} /></details>
              </>}
              <h3>Tres colas, una misma pregunta</h3>
              <Table headers={['Algoritmo', 'Cola', `Costo (${route.unit})`, 'Expandidos', 'Relajaciones', 'Decrease-key', 'Tiempo aislado (ms)']}
                rows={route.comparisons.map(r => [r.algorithm === 'astar' ? 'A*' : 'Dijkstra', queueNames[r.queue], fmt(r.cost, 3), r.expanded, r.relaxations, r.decrease_key, fmt(r.elapsed_ms_single_run, 3)])} />
            <p className="fineprint">Expandidos = nodos extraídos; relajaciones = aristas examinadas; decrease-key = prioridades reducidas. Un tiempo aislado no prueba qué cola es más rápida.</p>
            </section>}
          </div>
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
        <section className="source-panel"><div><p className="section-label">Lecturas opcionales</p><h2>Consultar un punto, no toda la red</h2>
          <p>Origen seleccionado: {fmt(conditionPoint.lat, 5)}, {fmt(conditionPoint.lon, 5)}{sourceCoords || sourcePoint ? '.' : ' (centro de Cusco por defecto).'}</p>
          <p className="fineprint">Open-Meteo ofrece datos de modelo, no una estación en esa coordenada. TomTom devuelve un segmento cercano. Estas consultas no cambian automáticamente la ruta.</p></div>
          <div className="source-controls"><label>Proveedor<select value={conditionProvider} onChange={e => { setConditionProvider(e.target.value as typeof conditionProvider); setCondition(null) }}>
            <option value="openweathermap">OpenWeatherMap, clave del servidor</option><option value="open-meteo">Open-Meteo, sin clave</option><option value="tomtom">TomTom, tráfico puntual</option></select></label>
            {conditionProvider !== 'open-meteo' && <ProviderKeyInput provider={conditionProvider} configured={catalog?.provider_keys?.[conditionProvider]}
              value={apiKeys[conditionProvider]} onChange={value => updateKey(conditionProvider, value)} />}
            <button type="button" onClick={fetchConditions} disabled={conditionLoading} className="secondary">{conditionLoading ? 'Consultando…' : 'Consultar este punto'}</button>
            {conditionLoading && <p role="status">Consultando al proveedor…</p>}
            {conditionError && <p className="error" role="alert">{conditionError}</p>}
            {!condition && !conditionLoading && !conditionError && <p className="fineprint">Aún no hay lectura. Elige el proveedor y consulta el origen seleccionado.</p>}
            {condition?.observation && <><WeatherReading data={condition} /><button type="button" disabled={condition.multiplier == null || metric !== 'time' || preview?.metric === 'weight'} onClick={() => {
              if (saveReading(condition)) { setWeather('saved'); setWeatherEnabled(true); setSection('Rutas') }
            }}>Guardar y aplicar en Rutas</button></>}
            {condition?.flow && <TrafficReading flow={condition.flow} requested={condition.requested} fetchedAt={condition.fetched_at_utc} />}
            <label className="check"><input type="checkbox" checked={rememberKeys} onChange={e => toggleRemember(e.target.checked)} /> Recordar claves en este navegador</label>
            <button type="button" className="text-button" onClick={() => { forgetKeys(); setApiKeys({ ...emptyKeys }); setRememberKeys(false); setStorageError('Claves opcionales olvidadas en este navegador. Las del servidor permanecen configuradas.') }}>Olvidar claves del navegador</button>
            {storageError && <p role="status">{storageError}</p>}
            <p className="fineprint">Las claves del servidor no se envían aquí. Las claves alternativas solo se guardan en este navegador si marcas «Recordar»; localStorage no es una bóveda segura. «Olvidar» no elimina las claves del servidor.</p>
          </div></section>
        <p className="warning">Un punto fuera del snapshot o lejos de un nodo no se conectará artificialmente. Ampliar la cobertura exige adquirir, comprobar y versionar otra red. No cambia el banco histórico.</p>
        <p className="fineprint"><code>python/scripts/build_urban_snapshot.py</code> prepara un pendiente y exige una segunda revisión para publicarlo; las coberturas sin archivo revisado permanecen inactivas.</p>
      </div>}
      {section === 'Datos y método' && <div className="reading-page method-page"><p className="section-label">Cómo se calcula / 06</p><h1>De los datos al resultado</h1>
        <p>Estas son las reglas que aplica esta versión. Son estimaciones para comparar algoritmos, no indicaciones de tránsito en vivo.</p>
        <section><h2>1. Distancia y tiempo base</h2>
          <p className="formula">Distancia(P) = Σ longitud(e) &nbsp; | &nbsp; Tiempo base(P) = Σ tiempo_nominal(e)</p>
          <p>Cada arista OSM conserva su longitud en metros y su tiempo en segundos. Si falta el tiempo, se estima como <strong>longitud / (velocidad en km/h ÷ 3,6)</strong>; la velocidad procede del límite OSM o del valor supuesto para el tipo de vía. No se incorporó pendiente medida al snapshot. Para aristas propias con longitud y sin tiempo, el modelo usa <strong>(longitud ÷ velocidad) × (1 + 2,5 × max(0, pendiente/100))</strong>. Los grafos de pesos genéricos solo tienen «peso».</p>
          <p className="fineprint">La ruta óptima depende de la métrica elegida: la más corta en metros no tiene por qué ser la más rápida en segundos.</p>
        </section>
        <section><h2>2. Clima: factor hipotético</h2>
          <p className="formula">F<sub>clima</sub> = redondear(1 + 0,20·min(max(lluvia,0)/10, 1) + 0,15·max(0, 1 − min(max(visibilidad,0),10 000)/10 000) + 0,10·min(max(ráfagas,0)/80, 1) + 0,08·min(1, max(0, (humedad − 65)/35)), 4)</p>
          <p>Lluvia en mm, visibilidad en m, ráfagas en km/h y humedad en %. Open-Meteo usa datos de modelo; OpenWeatherMap usa la clave del servidor o una alternativa introducida. Una consulta puntual no mide todas las calles. <strong>Temperatura y descripción del cielo se muestran, pero no entran en la fórmula.</strong></p>
        </section>
        <section><h2>3. Tráfico: horario o segmento puntual</h2>
          <p className="formula">F<sub>horario</sub> = redondear(1 + 1,15·(nivel − 1), 4) &nbsp; | &nbsp; F<sub>TomTom</sub> = max(1, redondear(velocidad libre / velocidad actual, 4))</p>
          <p>El nivel horario es <strong>supuesto</strong>: fluido 1, moderado 1,25, alto 1,65 u hora punta 2,20. «Hora simulada» usa la que eliges; «hora actual» toma la hora de Cusco del servidor. El GPS solo obtiene el origen con permiso. Si activas TomTom, su velocidad corresponde a <strong>un segmento cercano al origen</strong>, no a cada calle de la ruta.</p>
        </section>
        <section><h2>4. Ruta, factores y colas</h2>
          <p className="formula">Tiempo estimado(P) = Tiempo base(P) × redondear(F<sub>clima</sub> × F<sub>tráfico</sub>, 4)</p>
          <p>Los factores se aplican uniformemente <strong>después</strong> de buscar la ruta. Dijkstra usa pesos no negativos y compara tres colas: montículo binario indexado, montículo 4-ario indexado y montículo Fibonacci. Cambia la gestión de prioridades, <strong>no los pesos ni el costo óptimo</strong>.</p>
          <p>A* prioriza <strong>f(v) = g(v) + h(v)</strong>, con <strong>h(v) = λ·distancia euclidiana(v, destino)</strong> y <strong>λ = min<sub>aristas útiles</sub>(peso / distancia euclidiana de la arista)</strong>. Si faltan coordenadas, usa h = 0. Así preserva el costo correcto; puede expandir menos nodos, pero <strong>no se garantiza que sea más rápido</strong> en todas las redes.</p>
        </section>
        <p className="fineprint">Para verificar datos y algoritmos: <a href={apiUrl('/docs')} target="_blank" rel="noreferrer">contrato API</a>, <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">atribución OSM</a> y el benchmark reproducible en «Comparar».</p>
      </div>}
    </main><footer className="site-footer"><span>UNSAAC · Grupo 5 · Algoritmos Avanzados</span><span>Datos del proyecto, no navegación vial en tiempo real.</span></footer>
  </>
}

createRoot(document.getElementById('root')!).render(<App />)
