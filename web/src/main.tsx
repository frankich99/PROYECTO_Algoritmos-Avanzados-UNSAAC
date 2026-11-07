import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import GraphView from './GraphView'
import { api, apiUrl } from './api'
import type { Benchmark, Catalog, Condition, Experiment, InstanceSpec, Metric, Pilot, Point, Preview, Queue, RouteResponse } from './api'
import { emptyKeys, forgetKeys, forgetWeather, readKeys, readWeather, saveKeys, saveWeather } from './localSettings'
import type { ProviderKeys } from './localSettings'
import WeatherReading from './WeatherReading'
import TrafficReading from './TrafficReading'
import EvidencePage from './EvidencePage'
import ComplexityTable from './ComplexityTable'
import InstanceGenerator from './InstanceGenerator'
import { experimentInput } from './experimentInput'
import { fmt } from './format'
import 'maplibre-gl/dist/maplibre-gl.css'
import './style.css'

const queueNames: Record<Queue, string> = { binary_heap: 'Binario', '4ary_heap': '4-ario', fibonacci_heap: 'Fibonacci' }
const initialGraph = { name: 'Grafo propuesto', directed: true, nodes: [{ id: 'A' }, { id: 'B' }, { id: 'C' }],
  edges: [{ origin: 'A', destination: 'B', weight: 4 }, { origin: 'A', destination: 'C', weight: 10 }, { origin: 'B', destination: 'C', weight: 2 }] }
const menu = ['Rutas', 'Instancias', 'Comparar', 'Experimentos', 'Cobertura Cusco', 'Evidencias', 'Datos y método', 'Acerca de'] as const
const team = [
  { name: 'Noe Franklin Choquenaira Quispe', code: '133962', work: 'Dijkstra, heap binario y modelo didáctico; A*; informe.' },
  { name: 'Aldo Yaranga Achahui', code: '103179', work: 'Pruebas, cuaderno y exportadores; CLI y pruebas de CLI.' },
  { name: 'Yeni Ruth Porroa Sivana', code: '120893', work: 'Heap 4-ario; análisis de estructuras.' },
  { name: 'Romario Quispe Rimachi', code: '164257', work: 'Fibonacci heap y benchmark inicial; actualización de resultados.' },
] as const
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

function MathEquation({ children, title }: { children: React.ReactNode; title?: string }) {
  const [zoom, setZoom] = useState(1.0)
  const zoomIn = () => setZoom(z => Math.min(Math.round((z + 0.15) * 100) / 100, 2.2))
  const zoomOut = () => setZoom(z => Math.max(Math.round((z - 0.15) * 100) / 100, 0.65))
  const resetZoom = () => setZoom(1.0)

  return (
    <div className="math-wrapper">
      <div className="math-toolbar">
        <span className="math-title">{title || 'Fórmula'}</span>
        <div className="math-zoom-controls">
          <button type="button" aria-label="Reducir fórmula" onClick={zoomOut} title="Reducir zoom (−)">−</button>
          <button type="button" className="math-zoom-val" onClick={resetZoom} aria-label="Restablecer fórmula al 100%">{Math.round(zoom * 100)}%</button>
          <button type="button" aria-label="Ampliar fórmula" onClick={zoomIn} title="Aumentar zoom (+)">+</button>
        </div>
      </div>
      <div className="math-scroll-area">
        <div className="math-eq" style={{ fontSize: `${0.88 * zoom}rem` }}>
          {children}
        </div>
      </div>
    </div>
  )
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
  const [trafficMode, setTrafficMode] = useState<'simulated' | 'current'>('current')
  const [simulatedTime, setSimulatedTime] = useState('13:00')
  const [trafficUseTomTom, setTrafficUseTomTom] = useState(false)
  const [gpsLoading, setGpsLoading] = useState(false)
  const [gpsError, setGpsError] = useState('')
  const [gpsFix, setGpsFix] = useState<{ timestamp: number; accuracy: number } | null>(null)
  const [lockSelection, setLockSelection] = useState(false)
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
  const [seed, setSeed] = useState('42')
  const [runs, setRuns] = useState('5')
  const handleSeedChange = (raw: string) => {
    const digits = raw.replace(/[^0-9]/g, '')
    setSeed(digits === '' ? '' : digits.replace(/^0+(?=\d)/, ''))
  }
  const handleRunsChange = (raw: string) => {
    const digits = raw.replace(/[^0-9]/g, '')
    setRuns(digits === '' ? '' : digits.replace(/^0+(?=\d)/, ''))
  }
  const [editorMode, setEditorMode] = useState<'tabla' | 'json' | 'archivo' | 'generar'>('tabla')
  const [nodeDraft, setNodeDraft] = useState<{ id: string; lat: string; lon: string }[]>([{ id: 'A', lat: '', lon: '' }, { id: 'B', lat: '', lon: '' }, { id: 'C', lat: '', lon: '' }])
  const [edgeDraft, setEdgeDraft] = useState<{ origin: string; destination: string; weight: string }[]>([{ origin: 'A', destination: 'B', weight: '4' }, { origin: 'A', destination: 'C', weight: '10' }, { origin: 'B', destination: 'C', weight: '2' }])
  const [jsonDraft, setJsonDraft] = useState(JSON.stringify(initialGraph, null, 2))
  const [textDraft, setTextDraft] = useState('A B 4\nA C 10\nB C 2')
  const [editorError, setEditorError] = useState('')
  const [pasteFeedback, setPasteFeedback] = useState('')

  function handlePasteNodesText(rawText: string) {
    const lines = rawText.split(/\r?\n/).map(l => l.trim()).filter(Boolean)
    const parsed: { id: string; lat: string; lon: string }[] = []
    for (const line of lines) {
      if (line.startsWith('#') || line.startsWith('//') || line.startsWith('---') || line.startsWith('===')) continue
      if (/^(id|lat|nodo|nombre)/i.test(line)) continue
      const tokens = line.split(/[|\t,]+/).map(t => t.trim()).filter(Boolean)
      const cleanTokens = tokens.length > 1 ? tokens : line.split(/\s+/).filter(Boolean)
      if (cleanTokens.length === 0) continue
      const id = cleanTokens[0]
      const lat = cleanTokens[1] && !isNaN(Number(cleanTokens[1])) ? cleanTokens[1] : ''
      const lon = cleanTokens[2] && !isNaN(Number(cleanTokens[2])) ? cleanTokens[2] : ''
      parsed.push({ id, lat, lon })
    }
    if (parsed.length > 0) {
      setNodeDraft(parsed)
      setPasteFeedback(`✓ ${parsed.length} nodos importados correctamente a la tabla.`)
      setEditorError('')
      setTimeout(() => setPasteFeedback(''), 4500)
    }
  }

  function handlePasteEdgesText(rawText: string) {
    const lines = rawText.split(/\r?\n/).map(l => l.trim()).filter(Boolean)
    const parsed: { origin: string; destination: string; weight: string }[] = []
    for (const line of lines) {
      if (line.startsWith('#') || line.startsWith('//') || line.startsWith('---') || line.startsWith('===')) continue
      if (/^(origen|dest|peso|from|to|weight|u|v)/i.test(line)) continue
      const tokens = line.split(/[|\t,]+/).map(t => t.trim()).filter(Boolean)
      const cleanTokens = tokens.length > 1 ? tokens : line.split(/\s+/).filter(Boolean)
      if (cleanTokens.length >= 3) {
        parsed.push({ origin: cleanTokens[0], destination: cleanTokens[1], weight: cleanTokens[2] })
      } else if (cleanTokens.length === 2) {
        parsed.push({ origin: cleanTokens[0], destination: cleanTokens[1], weight: '1' })
      }
    }
    if (parsed.length > 0) {
      setEdgeDraft(parsed)
      setPasteFeedback(`✓ ${parsed.length} aristas dirigidas importadas correctamente a la tabla.`)
      setEditorError('')
      setTimeout(() => setPasteFeedback(''), 4500)
    }
  }
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

  const cuscoLiveDate = useMemo(() => {
    try {
      return new Date(new Date(timeTick).toLocaleString('en-US', { timeZone: 'America/Lima' }))
    } catch {
      return new Date(timeTick - 5 * 3600 * 1000)
    }
  }, [timeTick])

  const cuscoLiveHour = cuscoLiveDate.getHours()
  const cuscoLiveMinute = cuscoLiveDate.getMinutes()
  const cuscoLiveSecond = cuscoLiveDate.getSeconds()
  const cuscoTimeString = `${String(cuscoLiveHour).padStart(2, '0')}:${String(cuscoLiveMinute).padStart(2, '0')}:${String(cuscoLiveSecond).padStart(2, '0')}`
  const cuscoLiveDecimal = cuscoLiveHour + cuscoLiveMinute / 60 + cuscoLiveSecond / 3600

  const getCuscoTrafficFactor = (h: number) => {
    if ((7.25 <= h && h <= 9.0) || (18.0 <= h && h <= 20.25)) {
      return { factor: 2.20, label: 'Hora punta (crítico)' }
    } else if (12.5 <= h && h <= 14.25) {
      return { factor: 1.65, label: 'Tráfico denso (almuerzo)' }
    } else if ((9.0 < h && h < 12.5) || (14.25 < h && h < 18.0)) {
      return { factor: 1.25, label: 'Comercial (moderado)' }
    } else if (21.5 <= h || h < 6.5) {
      return { factor: 1.00, label: 'Flujo libre (nocturno)' }
    } else {
      return { factor: 1.25, label: 'Transición (regular)' }
    }
  }

  const liveTrafficInfo = useMemo(() => getCuscoTrafficFactor(cuscoLiveDecimal), [cuscoLiveDecimal])
  const simulatedTrafficInfo = useMemo(() => {
    const h = validSimulatedTime ? Number(simulatedTime.slice(0, 2)) + Number(simulatedTime.slice(3)) / 60 : 13.0
    return getCuscoTrafficFactor(h)
  }, [validSimulatedTime, simulatedTime])
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
      if (controller.signal.aborted) return
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
    if (lockSelection) return
    routeAbort.current?.abort(); setRouteLoading(false)
    if (pick === 'source') { gpsRequest.current += 1; setGpsLoading(false); setGpsFix(null); setGpsError(''); setSourcePoint(point); setPick('target') }
    else setTargetPoint(point)
    setRoute(null)
  }, [pick, lockSelection])
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
  function setCenterOrigin() {
    setGpsError('')
    setGpsFix(null)
    setSourcePoint({ lat: -13.5165, lon: -71.9788 })
    if (preview?.geographic && preview?.ids?.length) {
      if (preview.ids.includes('A')) setSource('A')
      else setSource(String(preview.ids[0]))
    }
    setRoute(null)
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
        <span className="wordmark-main">UNSAAC <i>/</i> Rutas</span><span className="wordmark-sub">Proyecto de Algoritmos Avanzados · Cusco</span>
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
              <div className="weather-container-card">
                <label className="check weather-heading">
                  <input type="checkbox" checked={weatherEnabled} onChange={e => setWeatherEnabled(e.target.checked)} />
                  <span>Ajustar tiempo por clima meteorológico</span>
                </label>
                {weatherEnabled && <div className="weather-content">
                  <div className="weather-grid">
                    <label><span>Fuente climática</span><select value={weather} onChange={e => setWeather(e.target.value as typeof weather)}>
                      <option value="live">Condiciones actuales (en vivo)</option>
                      <option value="historical">Lectura histórica del informe</option>
                      <option value="snapshot">Snapshot incluido en el proyecto</option>
                      <option value="saved" disabled={!savedReading}>Lectura guardada en este navegador</option>
                    </select></label>
                    {weather === 'live' && <label><span>Proveedor</span><select value={weatherProvider} onChange={e => setWeatherProvider(e.target.value as typeof weatherProvider)}>
                      <option value="openweathermap">OpenWeatherMap (Servidor)</option>
                      <option value="open-meteo">Open-Meteo (Sin clave)</option>
                    </select></label>}
                  </div>

                  {weather === 'live' && <>
                    {weatherProvider === 'openweathermap' && (
                      <details className="weather-key-accordion">
                        <summary>Configurar clave OpenWeatherMap (opcional)</summary>
                        <div className="weather-key-body">
                          <p className="fineprint" style={{ margin: 0 }}>Clave configurada en el servidor por defecto; no se envía al navegador.</p>
                          <ProviderKeyInput provider="openweathermap" configured={catalog?.provider_keys?.openweathermap}
                            value={apiKeys.openweathermap} onChange={value => updateKey('openweathermap', value)} />
                        </div>
                      </details>
                    )}
                    <div className="weather-actions-row">
                      <button type="button" className="btn-weather-refresh" onClick={() => setWeatherRefresh(n => n + 1)} disabled={weatherLoading}>
                        {weatherLoading ? 'Consultando…' : '🔄 Actualizar lectura'}
                      </button>
                      <label className="check weather-auto-check">
                        <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} />
                        <span>Actualizar cada 10 min</span>
                      </label>
                    </div>
                    {weatherLoading && <p role="status" className="fineprint">Consultando las condiciones del origen…</p>}
                    {weatherError && <p className="error" role="alert">{weatherError}</p>}
                    {liveReading && <div className="weather-reading-card">
                      <WeatherReading data={liveReading} />
                      {liveReading.multiplier == null && <p className="warning">Reinicia la API Python para habilitar el cálculo con esta lectura.</p>}
                      {staleLive && <p className="warning">Esta lectura tiene más de 30 minutos o no tiene hora válida. Actualízala antes de calcular.</p>}
                      <button type="button" className="btn-center-origin" onClick={() => saveReading(liveReading)} disabled={liveReading.multiplier == null}>
                        Guardar esta lectura localmente
                      </button>
                    </div>}
                  </>}

                  {weather === 'saved' && <>
                    {savedReading && <div className="weather-reading-card"><WeatherReading data={savedReading} /></div>}
                    {!samePoint && <p className="warning">La lectura guardada pertenece a otro punto. Cambia el origen o actualiza el clima.</p>}
                    <p className="fineprint">Una lectura guardada es un escenario reproducible, no una observación actual.</p>
                    <button type="button" className="btn-center-origin" onClick={() => { forgetWeather(); setSavedReading(null); setWeather('live') }}>
                      Eliminar lectura guardada
                    </button>
                  </>}
                  <p className="fineprint" style={{ margin: '2px 0 0' }}>El factor climático escala proporcionalmente los tiempos de viaje de la red.</p>
                </div>}
              </div>
              <div className="traffic-container-card">
                <label className="check traffic-heading">
                  <input type="checkbox" checked={traffic} onChange={e => setTraffic(e.target.checked)} />
                  <span>Ajustar tiempo por tráfico horario</span>
                </label>
                {traffic && <div className="traffic-content">
                  <div className="traffic-mode-toggle" role="group" aria-label="Modo de tráfico">
                    <button
                      type="button"
                      className={trafficMode === 'simulated' ? 'active' : ''}
                      onClick={() => setTrafficMode('simulated')}
                    >
                      Hora programada
                    </button>
                    <button
                      type="button"
                      className={trafficMode === 'current' ? 'active' : ''}
                      onClick={() => { setTrafficMode('current'); setTimeTick(Date.now()) }}
                    >
                      Hora actual Cusco
                    </button>
                  </div>

                  {trafficMode === 'current' ? (
                    <div className="cusco-live-card">
                      <div className="live-header">
                        <span className="live-badge"><span className="live-dot" /> EN VIVO</span>
                        <span className="live-tz">Hora oficial Cusco · UTC-5</span>
                      </div>
                      <div className="cusco-live-clock">
                        <span className="clock-icon" aria-hidden="true">🕒</span>
                        <span>{cuscoTimeString}</span>
                      </div>
                      <div className="traffic-factor-pill">
                        <span>Nivel horario supuesto: <strong>{liveTrafficInfo.label}</strong>. El factor aplicado aparece al resolver.</span>
                      </div>

                      <div className="traffic-origin-card">
                        <div className="origin-title">
                          <span aria-hidden="true">📍</span> Ubicación de origen para tráfico
                        </div>
                        {preview?.geographic ? (
                          <>
                            <button
                              type="button"
                              className="btn-gps-origin"
                              onClick={useGps}
                              disabled={gpsLoading}
                            >
                              📍 {gpsLoading ? 'Obteniendo GPS…' : 'Usar mi ubicación GPS como origen'}
                            </button>
                            <button
                              type="button"
                              className="btn-center-origin"
                              onClick={setCenterOrigin}
                            >
                              🏛️ Centro Cusco
                            </button>
                            {gpsLoading && <p role="status" className="fineprint">Solicitando ubicación al navegador…</p>}
                            {gpsError && <p className="error" role="alert">{gpsError}</p>}
                            {gpsFix && <p role="status" className={gpsExpired ? 'warning' : 'fineprint'}>GPS: {fmt(sourcePoint?.lat, 5)}, {fmt(sourcePoint?.lon, 5)}; precisión ±{fmt(gpsFix.accuracy, 0)} m.</p>}
                          </>
                        ) : (
                          <p className="fineprint">El GPS y la ubicación requieren una red con coordenadas (ej. Cusco OSM).</p>
                        )}
                      </div>

                      <details className="tomtom-toggle">
                        <summary>Consultar TomTom en tiempo real (opcional)</summary>
                        <div className="tomtom-body">
                          <label className="check">
                            <input
                              type="checkbox"
                              checked={trafficUseTomTom}
                              onChange={e => setTrafficUseTomTom(e.target.checked)}
                              disabled={!preview?.geographic}
                            />
                            Consultar además TomTom en el origen
                          </label>
                          {trafficUseTomTom && preview?.geographic && <ProviderKeyInput provider="tomtom" configured={catalog?.provider_keys?.tomtom}
                            value={apiKeys.tomtom} onChange={value => updateKey('tomtom', value)} />}
                          {trafficUseTomTom && preview?.geographic && !apiKeys.tomtom.trim() && !catalog?.provider_keys?.tomtom && <p className="fineprint">Introduce la clave o desactiva TomTom para calcular con el supuesto horario.</p>}
                          <p className="fineprint">Sin TomTom se usa el supuesto horario a la hora actual. Con TomTom se aplica la relación entre velocidad libre y velocidad puntual como factor uniforme exploratorio.</p>
                        </div>
                      </details>
                    </div>
                  ) : (
                    <div className="cusco-simulated-card">
                      <label>Hora programada en Cusco (HH:MM)<input type="time" required value={simulatedTime} onChange={e => setSimulatedTime(e.target.value)} /></label>
                      <div className="traffic-factor-pill">
                        <span>Nivel horario supuesto: <strong>{simulatedTrafficInfo.label}</strong>. El factor aplicado aparece al resolver.</span>
                      </div>
                      <p className="fineprint">Elige una hora para comparar el supuesto horario del proyecto en Cusco. No son velocidades medidas.</p>
                    </div>
                  )}
                </div>}
              </div>
            </div>}
            <button type="submit" className="primary" disabled={!preview || routeLoading || (metric === 'time' && preview?.metric !== 'weight' && (!canApplyWeather || !canApplyTraffic))}>{routeLoading ? 'Calculando ruta…' : 'Calcular y contrastar'}</button>
            {routeError && <p className="error" role="alert">{routeError}</p>}
          </form></div>
          <div className="main-pane">
            <GraphView
              preview={preview}
              route={route}
              onPick={mapPick}
              pick={pick}
              onPickMode={setPick}
              mapRequested={mapRequested}
              sourcePoint={sourcePoint}
              targetPoint={targetPoint}
              lockSelection={lockSelection}
              onToggleLock={() => setLockSelection(l => !l)}
            />
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
        {editorMode === 'tabla' && <div className="editor-grid">
          <section>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.45rem', flexWrap: 'wrap', gap: '0.4rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.2rem' }}>Nodos</h2>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="btn-action"
                  onClick={async () => {
                    try {
                      const text = await navigator.clipboard.readText()
                      if (text && text.trim()) handlePasteNodesText(text)
                      else {
                        const p = prompt('Pega aquí los nodos (ej. "A | -13.516 | -71.978" o solo IDs por línea):')
                        if (p) handlePasteNodesText(p)
                      }
                    } catch {
                      const p = prompt('Pega aquí los nodos (ej. "A | -13.516 | -71.978" o solo IDs por línea):')
                      if (p) handlePasteNodesText(p)
                    }
                  }}
                  title="Pega texto de nodos directamente desde el portapapeles"
                >
                  📋 Pegar
                </button>
                <button
                  type="button"
                  className="btn-action"
                  onClick={() => {
                    setNodeDraft([])
                    setPasteFeedback('Nodos limpiados. Puedes agregar o pegar nuevos.')
                    setTimeout(() => setPasteFeedback(''), 3000)
                  }}
                  title="Vaciar la lista de nodos"
                >
                  🗑️ Limpiar
                </button>
                <button
                  type="button"
                  className="btn-action"
                  onClick={() => setNodeDraft(old => [...old, { id: '', lat: '', lon: '' }])}
                  title="Agregar un nodo individual"
                >
                  ➕ Agregar
                </button>
              </div>
            </div>
            <p className="fineprint">Coordenadas opcionales. Puedes presionar <strong>Ctrl+V</strong> en cualquier celda para pegar una tabla completa.</p>
            {nodeDraft.map((node, i) => <div className="editor-row" key={i}>
              <label>ID<input aria-label={`Nodo ${i + 1} ID`} value={node.id}
                onPaste={e => {
                  const clip = e.clipboardData.getData('text')
                  if (clip && (clip.includes('\n') || clip.includes('|') || clip.includes('\t'))) {
                    e.preventDefault(); handlePasteNodesText(clip)
                  }
                }}
                onChange={e => setNodeDraft(old => old.map((n, j) => j === i ? { ...n, id: e.target.value } : n))} /></label>
              <label>Latitud<input aria-label={`Nodo ${i + 1} latitud`} value={node.lat}
                onPaste={e => {
                  const clip = e.clipboardData.getData('text')
                  if (clip && (clip.includes('\n') || clip.includes('|') || clip.includes('\t'))) {
                    e.preventDefault(); handlePasteNodesText(clip)
                  }
                }}
                onChange={e => setNodeDraft(old => old.map((n, j) => j === i ? { ...n, lat: e.target.value } : n))} /></label>
              <label>Longitud<input aria-label={`Nodo ${i + 1} longitud`} value={node.lon}
                onPaste={e => {
                  const clip = e.clipboardData.getData('text')
                  if (clip && (clip.includes('\n') || clip.includes('|') || clip.includes('\t'))) {
                    e.preventDefault(); handlePasteNodesText(clip)
                  }
                }}
                onChange={e => setNodeDraft(old => old.map((n, j) => j === i ? { ...n, lon: e.target.value } : n))} /></label>
              <button type="button" aria-label={`Eliminar nodo ${i + 1}`} onClick={() => setNodeDraft(old => old.filter((_, j) => j !== i))}>Quitar</button></div>)}
            <button type="button" onClick={() => setNodeDraft(old => [...old, { id: '', lat: '', lon: '' }])}>Agregar nodo</button>
          </section>

          <section>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.45rem', flexWrap: 'wrap', gap: '0.4rem' }}>
              <h2 style={{ margin: 0, fontSize: '1.2rem' }}>Aristas dirigidas</h2>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="btn-action"
                  onClick={async () => {
                    try {
                      const text = await navigator.clipboard.readText()
                      if (text && text.trim()) handlePasteEdgesText(text)
                      else {
                        const p = prompt('Pega aquí las aristas (ej. "A | B | 4" o "A B 4"):')
                        if (p) handlePasteEdgesText(p)
                      }
                    } catch {
                      const p = prompt('Pega aquí las aristas (ej. "A | B | 4" o "A B 4"):')
                      if (p) handlePasteEdgesText(p)
                    }
                  }}
                  title="Pega texto de aristas directamente desde el portapapeles"
                >
                  📋 Pegar
                </button>
                <button
                  type="button"
                  className="btn-action"
                  onClick={() => {
                    setEdgeDraft([])
                    setPasteFeedback('Aristas limpiadas. Puedes agregar o pegar nuevas.')
                    setTimeout(() => setPasteFeedback(''), 3000)
                  }}
                  title="Vaciar la lista de aristas"
                >
                  🗑️ Limpiar
                </button>
                <button
                  type="button"
                  className="btn-action"
                  onClick={() => setEdgeDraft(old => [...old, { origin: '', destination: '', weight: '' }])}
                  title="Agregar una arista individual"
                >
                  ➕ Agregar
                </button>
              </div>
            </div>
            <p className="fineprint">Para dos sentidos, introduce dos aristas. Puedes presionar <strong>Ctrl+V</strong> en cualquier celda para pegar.</p>
            {edgeDraft.map((edge, i) => <div className="editor-row" key={i}>
              <label>Origen<input aria-label={`Arista ${i + 1} origen`} value={edge.origin}
                onPaste={e => {
                  const clip = e.clipboardData.getData('text')
                  if (clip && (clip.includes('\n') || clip.includes('|') || clip.includes('\t'))) {
                    e.preventDefault(); handlePasteEdgesText(clip)
                  }
                }}
                onChange={e => setEdgeDraft(old => old.map((n, j) => j === i ? { ...n, origin: e.target.value } : n))} /></label>
              <label>Destino<input aria-label={`Arista ${i + 1} destino`} value={edge.destination}
                onPaste={e => {
                  const clip = e.clipboardData.getData('text')
                  if (clip && (clip.includes('\n') || clip.includes('|') || clip.includes('\t'))) {
                    e.preventDefault(); handlePasteEdgesText(clip)
                  }
                }}
                onChange={e => setEdgeDraft(old => old.map((n, j) => j === i ? { ...n, destination: e.target.value } : n))} /></label>
              <label>Peso<input aria-label={`Arista ${i + 1} peso`} value={edge.weight}
                onPaste={e => {
                  const clip = e.clipboardData.getData('text')
                  if (clip && (clip.includes('\n') || clip.includes('|') || clip.includes('\t'))) {
                    e.preventDefault(); handlePasteEdgesText(clip)
                  }
                }}
                onChange={e => setEdgeDraft(old => old.map((n, j) => j === i ? { ...n, weight: e.target.value } : n))} /></label>
              <button type="button" aria-label={`Eliminar arista ${i + 1}`} onClick={() => setEdgeDraft(old => old.filter((_, j) => j !== i))}>Quitar</button></div>)}
            <button type="button" onClick={() => setEdgeDraft(old => [...old, { origin: '', destination: '', weight: '' }])}>Agregar arista</button>
          </section>

          {pasteFeedback && <p className="status" style={{ gridColumn: '1 / -1', margin: '0.4rem 0', fontWeight: 600, color: '#2e7d32', background: '#edf7ed', border: '1px solid #c8e6c9', padding: '0.6rem 0.9rem', borderRadius: '4px' }}>{pasteFeedback}</p>}

          <button type="button" className="primary" onClick={applyTable}>Validar tabla y calcular</button>
        </div>}
        {editorMode === 'json' && <div className="editor-box"><label>Instancia JSON: nodos, aristas y pesos<textarea rows={16} spellCheck={false} value={jsonDraft} onChange={e => setJsonDraft(e.target.value)} /></label>
          <button className="primary" type="button" onClick={applyJson}>Validar JSON y calcular</button></div>}
        {editorMode === 'archivo' && <div className="editor-box"><label>Importar JSON, CSV o TXT<input type="file" accept=".json,.csv,.txt" onChange={importFile} /></label>
          <label>Lista de aristas (origen destino peso, una por línea; CSV con cabecera opcional)<textarea rows={10} value={textDraft} onChange={e => setTextDraft(e.target.value)} /></label>
          <button className="primary" type="button" onClick={() => { setEditorError(''); setInstance({ kind: 'text', text: textDraft }) }}>Validar lista y calcular</button></div>}
         {editorMode === 'generar' && <InstanceGenerator onApply={setInstance} />}
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
      {section === 'Experimentos' && <div className="reading-page"><p className="section-label">Experimentación / 04</p><h1>Mide otra instancia, sin tocar el informe</h1>
        <p>Dos redes por tamaño, semillas guardadas, dos calentamientos y repeticiones acotadas. Los resultados se quedan en esta sesión.</p>
        <form className="experiment-form" onSubmit={async e => {
          e.preventDefault(); setExperiment(null); setExperimentError(''); setExperimentLoading(true)
          try {
            setExperiment(await api<Experiment>('/experiments', experimentInput(profile, sizes, seed, runs)))
          }
          catch (err) { setExperimentError(err instanceof Error ? err.message : 'No se pudo medir.') }
          finally { setExperimentLoading(false) }
        }}>
          <label>Perfil<select value={profile} onChange={e => setProfile(e.target.value as typeof profile)}><option value="sparse">Disperso</option><option value="dense">Denso</option></select></label>
          <label>Tamaños, separados por comas<input value={sizes} onChange={e => setSizes(e.target.value)} /></label>
          <label>Semilla<input type="text" inputMode="numeric" pattern="[0-9]*" placeholder="42" value={seed} onChange={e => handleSeedChange(e.target.value)} /></label>
          <label>Repeticiones por red (2 a 10)<input type="text" inputMode="numeric" pattern="[0-9]*" placeholder="5" value={runs} onChange={e => handleRunsChange(e.target.value)} /></label>
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
      {section === 'Evidencias' && <EvidencePage onMethod={() => setSection('Datos y método')} />}
      {section === 'Datos y método' && <div className="reading-page method-page"><h1>Datos, modelo y complejidad</h1>
        <p>Estructura matemática transparente: de dónde proviene cada dato, cómo se calcula la distancia y el tiempo con relieve cusqueño, y cómo se aplican la meteorología y la congestión.</p>

        <ComplexityTable />
        <details className="method-notes">
          <summary>Notas de implementación de las colas y A*</summary>
          <div className="table-scroll compact-table">
            <table>
              <thead>
                <tr>
                  <th>Estructura / Algoritmo</th>
                  <th>Insertar</th>
                  <th>Extraer-Mín</th>
                  <th>Disminuir-Clave</th>
                  <th>Comportamiento Práctico</th>
                  <th>Uso en Red Vial de Cusco</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Montículo Binario (d=2)</strong></td>
                  <td>O(log n)</td>
                  <td>O(log n)</td>
                  <td>O(log n)</td>
                  <td>Línea base estándar. Memoria contigua compacta; predecible y rápido en grafos generales.</td>
                  <td>Referencia canónica de comparación (CLRS).</td>
                </tr>
                <tr>
                  <td><strong>Montículo 4-ario (d=4)</strong></td>
                  <td>O(log₄ n)</td>
                  <td>O(4 log₄ n)</td>
                  <td>O(log₄ n)</td>
                  <td>Reduce la altura; compara hasta cuatro hijos en cada descenso. No se midieron efectos de caché.</td>
                  <td>Alternativa a contrastar en redes dispersas, no un ganador universal.</td>
                </tr>
                <tr>
                  <td><strong>Montículo Fibonacci</strong></td>
                  <td>O(1)</td>
                  <td>O(log n) amort.</td>
                  <td>O(1) amort.</td>
                  <td>Cotas amortizadas; la implementación y sus constantes afectan las mediciones.</td>
                  <td>Permite estudiar la diferencia entre cota teórica y tiempo observado.</td>
                </tr>
                <tr>
                  <td><strong>Algoritmo A*</strong></td>
                  <td>h(v) admisible</td>
                  <td>Heurística consistente</td>
                  <td>f(v) = g(v) + h(v)</td>
                  <td>Puede reducir expansiones; si h = 0 no obtiene una ventaja heurística.</td>
                  <td>Consulta origen-destino. El beneficio depende de la instancia.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </details>

        <div className="formula-help">
          <span style={{ fontSize: '0.86rem', fontWeight: 600, color: 'var(--wine)' }}>
            Puedes ampliar cada fórmula con sus botones.
          </span>
          <span className="fineprint" style={{ margin: 0 }}>
            Clic en el porcentaje para restablecer al 100% predeterminado.
          </span>
        </div>

        <div className="model-sections">
          <details className="model-detail">
            <summary>Distancia y velocidades supuestas</summary>
            <p><strong>Distancia (metros):</strong> En los snapshots procede de OSM. Las longitudes, pendientes y velocidades de la red de seis nodos son ejemplos didácticos, no un levantamiento de campo.</p>
            <MathEquation title="Distancia Métrica (Σ)">
              <span className="m-var">Distancia</span>(P) = <span className="m-sum">∑</span><sub className="m-sub">e ∈ P</sub> <span className="m-var">longitud</span>(e) &nbsp; [m]
            </MathEquation>
            <p><strong>Velocidades nominales y conversión a m/s:</strong></p>
            <MathEquation title="Tiempo Base y Conversión m/s">
              <span className="m-var">T</span><sub className="m-sub">base</sub>(e) = 
              <span className="m-frac">
                <span className="m-num"><span className="m-var">longitud</span>(e)</span>
                <span className="m-den"><span className="m-var">v</span><sub className="m-sub">m/s</sub>(e)</span>
              </span>
              <span className="m-op">,</span> &nbsp; donde &nbsp;
              <span className="m-var">v</span><sub className="m-sub">m/s</sub> = 
              <span className="m-frac">
                <span className="m-num"><span className="m-var">v</span><sub className="m-sub">km/h</sub></span>
                <span className="m-den">3.6</span>
              </span>
            </MathEquation>
            <ul className="variable-list">
              <li><strong>Calles del ejemplo:</strong> 15 km/h (4,17 m/s).</li>
              <li><strong>Pasajes del ejemplo:</strong> 8 km/h (2,22 m/s).</li>
              <li><strong>Avenidas del ejemplo:</strong> 35 km/h (9,72 m/s).</li>
              <li><strong>Residenciales del ejemplo:</strong> 25 km/h (6,94 m/s). Son velocidades supuestas; OSM usa los atributos y reglas de su importación.</li>
            </ul>
          </details>

          <details className="model-detail">
            <summary>Pendientes de la red didáctica</summary>
            <p>En la red <strong>de seis nodos ilustrativos</strong> se asignan longitudes y pendientes (g) para explicar el cálculo. Los snapshots OSM no tienen pendiente medida por arista:</p>
            <ul className="variable-list">
              <li><strong>Subida de Calle Espaderos:</strong> +1.5%</li>
              <li><strong>Subida de Calle Garcilaso:</strong> +3.0%</li>
              <li><strong>Subida al Arco de Santa Clara:</strong> +2.5%</li>
              <li><strong>Bajadas hacia Qorikancha y Mantas:</strong> -1.0% a -2.5%</li>
            </ul>
            <p>Cuando se selecciona la métrica <strong>«Tiempo»</strong>, se aplica la fórmula del proyecto:</p>
            <MathEquation title="Tiempo con Pendiente y Relieve de Cusco">
              <span className="m-var">Tiempo</span>(u, v) = 
              <span className="m-frac">
                <span className="m-num"><span className="m-var">longitud</span></span>
                <span className="m-den"><span className="m-var">velocidad nominal</span></span>
              </span>
              <span className="m-op">×</span>
              <span className="m-b-sq">[</span>
              1 + 2.5 <span className="m-op">×</span> <span className="m-fn">max</span>
              <span className="m-b-rd">(</span>
              0, 
              <span className="m-frac">
                <span className="m-num"><span className="m-var">pendiente</span> %</span>
                <span className="m-den">100</span>
              </span>
              <span className="m-b-rd">)</span>
              <span className="m-b-sq">]</span>
            </MathEquation>
            <ul className="variable-list">
              <li><strong>Supuesto del modelo:</strong> Solo se penaliza la pendiente positiva. No es una ley física ni una calibración con viajes observados.</li>
              <li><strong>Jerarquía de calzada:</strong> Calles coloniales estrechas a 15 km/h, pasajes peatonales a 8 km/h y avenidas a 35 km/h.</li>
            </ul>
          </details>

          <details className="model-detail">
            <summary>Factor meteorológico y sus límites</summary>
            <p><strong>Temperatura (°C):</strong> Es contexto informativo y no interviene en el factor del proyecto. Los coeficientes meteorológicos son supuestos de sensibilidad, no efectos demostrados sobre la conducción.</p>
            <p><strong>Factores meteorológicos que sí penalizan el tiempo (F_clima):</strong></p>
            <MathEquation title="Factor Climático Combinado (F_clima)">
              F_clima = 1 + 0,20·C(lluvia/10) + 0,15·(1 − C(visibilidad/10000)) + 0,10·C(ráfagas/80) + 0,08·C((humedad − 65)/35)
            </MathEquation>
            <p className="fineprint">C(x) = min(1, max(0, x)). Se usan mm, metros, km/h y porcentaje; el resultado se redondea a cuatro decimales.</p>
            <ul className="variable-list">
              <li><strong>Lluvia:</strong> 0,20 × clamp(lluvia / 10, 0, 1).</li>
              <li><strong>Visibilidad:</strong> 0,15 × (1 − clamp(visibilidad / 10000, 0, 1)).</li>
              <li><strong>Ráfagas:</strong> 0,10 × clamp(ráfagas / 80, 0, 1); el código no tiene umbral de 25 km/h.</li>
              <li><strong>Humedad:</strong> 0,08 × clamp((humedad − 65) / 35, 0, 1). Clamp limita a [0, 1] cada término de la fórmula.</li>
            </ul>
          </details>

          <details className="model-detail">
            <summary>Tráfico supuesto, lectura puntual y tiempo final</summary>
            <p><strong>Factor de congestión (F_tráfico):</strong></p>
            <MathEquation title="Congestión (TomTom y Horario)">
              <span className="m-var">F</span><sub className="m-sub">TomTom</sub> = <span className="m-fn">max</span><span className="m-b-rd">(</span>1.0, 
              <span className="m-frac">
                <span className="m-num"><span className="m-var">v</span><sub className="m-sub">libre</sub></span>
                <span className="m-den"><span className="m-var">v</span><sub className="m-sub">actual</sub></span>
              </span><span className="m-b-rd">)</span>
              &nbsp; | &nbsp;
              <span className="m-var">F</span><sub className="m-sub">horario</sub> = 1 + 1.15 <span className="m-op">×</span> (<span className="m-var">nivel</span> - 1)
            </MathEquation>
            <p><strong>Fórmula final del tiempo de viaje estimado:</strong></p>
            <MathEquation title="Tiempo Estimado Final de la Ruta">
              <span className="m-var">Tiempo estimado</span>(P) = <span className="m-var">Tiempo base</span>(P) <span className="m-op">×</span> <span className="m-b-rd">(</span><span className="m-var">F</span><sub className="m-sub">clima</sub> <span className="m-op">×</span> <span className="m-var">F</span><sub className="m-sub">tráfico</sub><span className="m-b-rd">)</span>
            </MathEquation>
            <p className="fineprint">La ruta óptima se busca con Dijkstra o A* sobre los pesos base; los factores dinámicos escalan el tiempo de forma uniforme y verificable.</p>
          </details>

          <details className="model-detail">
            <summary>Heurística de A*: qué garantiza y qué no</summary>
            <p><strong>Función de evaluación f(v) = g(v) + h(v):</strong></p>
            <MathEquation title="Función de Evaluación A*">
              <span className="m-var">f</span>(v) = <span className="m-var">g</span>(v) + <span className="m-var">h</span>(v)
              &nbsp; , &nbsp;
              <span className="m-var">h</span>(v) = λ <span className="m-op">·</span> <span className="m-var">d</span><sub className="m-sub">euclídea</sub>(v, <span className="m-var">destino</span>)
            </MathEquation>
            <MathEquation title="Calibración de Heurística Admisible λ">
              λ = <span className="m-fn">min</span><sub className="m-sub">e ∈ E</sub>
              <span className="m-frac">
                <span className="m-num"><span className="m-var">peso</span>(e)</span>
                <span className="m-den"><span className="m-var">distancia euclídea</span>(e)</span>
              </span>
              &nbsp; ⟹ &nbsp;
              <span className="m-var">h</span>(v) ≤ <span className="m-var">d</span>*(v, <span className="m-var">destino</span>)
            </MathEquation>
            <ul className="variable-list">
              <li><strong>Garantía matemática (Admisibilidad):</strong> Al fijar λ como la razón mínima entre costo y distancia de cualquier arista, <code>h(v) ≤ d*(v, destino)</code> siempre, asegurando hallar el camino de costo mínimo exacto.</li>
              <li><strong>Límite:</strong> A* prioriza g + h, no prohíbe explorar en sentido opuesto a la meta. Sin coordenadas usa h = 0; no se garantiza un porcentaje de reducción.</li>
            </ul>
          </details>

          <details className="model-detail">
            <summary>Certificado y verificación independiente</summary>
            <p>Dijkstra (con montículo binario, 4-ario y Fibonacci) y A* operan sobre la misma red y generan costos idénticos.</p>
            <MathEquation title="Certificado Dual de Holgura Reducida">
              π(v) - π(u) ≤ <span className="m-var">w</span>(u, v) &nbsp; ∀(u, v) ∈ E
            </MathEquation>
            <ul className="variable-list">
              <li><strong>Certificado:</strong> La desigualdad por arista no basta: se verifican también origen, caminos realizables, costos y nodos inalcanzables.</li>
              <li><strong>Referencia independiente:</strong> Bellman-Ford en pruebas aleatorias, NetworkX en el benchmark y enumeración exhaustiva en grafos pequeños.</li>
            </ul>
            <p className="fineprint">Contratos y especificación: <a href={apiUrl('/docs')} target="_blank" rel="noreferrer">OpenAPI / Docs</a> y atribución de datos a OpenStreetMap.</p>
          </details>
        </div>
      </div>}
      {section === 'Acerca de' && <div className="reading-page about-page"><p className="section-label">Proyecto / 08</p>
        <h1>Un proyecto académico, una ruta verificable</h1>
        <p className="about-lead">Rutas mínimas en Cusco compara tres colas de prioridad en Dijkstra y una extensión A* sobre redes viales reales. La entrega actual incluye la aplicación web y la API; la app móvil en Flutter está planificada para consumir la misma API.</p>

        <section className="section-space">
          <h2>Ficha institucional</h2>
          <dl className="fact-grid about-facts">
            <div><dt>Universidad</dt><dd>Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)</dd></div>
            <div><dt>Facultad</dt><dd>Ingeniería Eléctrica, Electrónica, Informática y Mecánica</dd></div>
            <div><dt>Escuela profesional</dt><dd>Ingeniería Informática y de Sistemas</dd></div>
            <div><dt>Asignatura</dt><dd>Algoritmos Avanzados · Semestre 2026-II</dd></div>
            <div><dt>Docente responsable</dt><dd>Ing. Héctor Eduardo Ugarte Rojas</dd></div>
            <div><dt>Grupo</dt><dd>5 · Cusco, Perú</dd></div>
            <div><dt>Entrega</dt><dd>Web + API v1.5.0</dd></div>
            <div><dt>Estado</dt><dd>Prototipo académico verificable</dd></div>
          </dl>
        </section>

        <section className="section-space">
          <h2>Equipo del Grupo 5</h2>
          <p>La autoría se acredita con los commits registrados; la defensa y la evaluación son individuales.</p>
          <div className="team-list">{team.map(member => <article className="team-member" key={member.code}>
            <div className="team-id"><h3>{member.name}</h3><p>Código {member.code}</p></div>
            <p><span className="team-label">Área de trabajo declarada</span>{member.work}</p>
          </article>)}</div>
          <p className="fineprint">Detalle de autoría y evidencias: <a href="https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC" target="_blank" rel="noreferrer">repositorio del proyecto</a>.</p>
        </section>

        <section className="section-space">
          <h2>Arquitectura de la solución</h2>
          <p>La web no ejecuta los algoritmos: los solicita a la API. Esa separación permite reutilizar el mismo núcleo desde la futura app móvil.</p>
          <ol className="arch-flow">
            <li><span className="arch-number">01</span><div><h3>Cliente web</h3><p>Interfaz de consulta, mapas, resultados y procedencia.</p><small>React · TypeScript · MapLibre</small></div></li>
            <li><span className="arch-number">02</span><div><h3>API REST</h3><p>Valida instancias, resuelve rutas y consulta proveedores.</p><small>FastAPI · Pydantic · Uvicorn</small></div></li>
            <li><span className="arch-number">03</span><div><h3>Núcleo algorítmico</h3><p>Dijkstra con tres colas y A* con heurística euclidiana escalada.</p><small>Python 3.12</small></div></li>
            <li><span className="arch-number">04</span><div><h3>Datos y proveedores</h3><p>Snapshots OSM, benchmark canónico, clima y tráfico puntual.</p><small>OSM · JSON · OpenWeatherMap · TomTom</small></div></li>
            <li className="arch-planned"><span className="arch-number">05</span><div><h3>App móvil</h3><p>Planificada para consumir la misma API REST.</p><small>Flutter · no incluida en esta entrega</small></div></li>
          </ol>
          <p className="fineprint">Las claves de OpenWeatherMap y TomTom se configuran en el servidor. El navegador solo recibe si están disponibles; nunca las claves.</p>
        </section>

        <section className="section-space">
          <h2>Tecnologías y responsabilidades</h2>
          <Table headers={['Capa', 'Tecnología', 'Uso']} rows={[
            ['Interfaz', 'React + TypeScript', 'Componentes, estado y tipos'],
            ['Build', 'Vite', 'Desarrollo y empaquetado'],
            ['Mapa', 'MapLibre GL JS', 'Red vial y ruta'],
            ['API', 'FastAPI + Uvicorn', 'Contrato HTTP, validación y servidor'],
            ['Núcleo', 'Python', 'Algoritmos, datos y pruebas'],
            ['Pruebas', 'pytest + Vitest', 'Resultados fechados en Evidencias'],
            ['Proveedores', 'requests', 'Clima y tráfico'],
          ]} />
          <p className="fineprint">Las dependencias web se fijan con package-lock.json; Python declara requisitos en python/requirements.txt. El registro del piloto conserva el intérprete y la máquina reales.</p>
        </section>

        <section className="section-space">
          <h2>Datos, alcance y límites</h2>
          <div className="about-columns">
            <section><h3>Red vial</h3><p>Centro: 891 nodos y 2139 aristas, radio 1,5 km, snapshot del 28/10/2026. Centro ampliado: 1938 nodos y 4753 aristas, base OSM del 10/08/2026. Ninguna cobertura representa todo Cusco.</p></section>
            <section><h3>Experimento</h3><p>Banco canónico de 1350 muestras: 2 perfiles × 5 escalas × 3 instancias × 3 colas × 15 repeticiones. Los datos originales no se reescriben desde la web.</p></section>
            <section><h3>Clima y tráfico</h3><p>Clima de modelo o estación según proveedor. Tráfico por supuesto horario o por un segmento TomTom cercano al origen. No hay congestión medida por arista ni pendiente en el snapshot OSM.</p></section>
            <section><h3>Alcance</h3><p>Prototipo académico para comparar algoritmos y explicar resultados. No es navegación vial en tiempo real ni sustituye una evaluación individual.</p></section>
          </div>
        </section>

        <section className="section-space">
          <h2>Versiones de la entrega</h2>
          <ol className="version-list">
            <li><div><strong>v1.5.0</strong><span>06/11/2026 · actual</span></div><p>Bordes de nodos de alto contraste sin pérdida en fondos claros, corrección de visualización de grafos, tablas interactivas con pegado directo e instancias de prueba.</p></li>
            <li><div><strong>v1.2.1</strong><span>06/11/2026</span></div><p>Hora actual/simulada, GPS opcional, lectura TomTom puntual, claves gestionadas en el servidor y lecturas estructuradas.</p></li>
            <li><div><strong>v1.2.0</strong><span>05/11/2026</span></div><p>Aplicación web React + TypeScript, API FastAPI, cobertura ampliada y paquete publicable.</p></li>
          </ol>
        </section>

        <section className="section-space">
          <h2>Enlaces de verificación</h2>
          <p><a href="https://github.com/frankich99/PROYECTO_Algoritmos-Avanzados-UNSAAC" target="_blank" rel="noreferrer">Repositorio</a> · <a href={apiUrl('/docs')} target="_blank" rel="noreferrer">Contrato API</a> · <a href="./data/informe_final_unsaac.pdf" download>Informe final (PDF)</a> · <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">Atribución OSM</a></p>
          <div className="result-actions"><button type="button" onClick={() => setSection('Evidencias')}>Ver evidencias</button><button type="button" onClick={() => setSection('Datos y método')}>Ver datos y método</button></div>
          <p className="fineprint">Universidad Nacional de San Antonio Abad del Cusco · Grupo 5 · 2026.</p>
        </section>
      </div>}
    </main><footer className="site-footer"><span>UNSAAC · Grupo 5 · Algoritmos Avanzados</span><span>Datos del proyecto, no navegación vial en tiempo real.</span></footer>
  </>
}

createRoot(document.getElementById('root')!).render(<App />)
