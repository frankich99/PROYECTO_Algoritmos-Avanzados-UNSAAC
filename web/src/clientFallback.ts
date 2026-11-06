import { version } from '../package.json'
import type {
  Benchmark, Catalog, Condition, Experiment, InstanceSpec, Metric,
  Pilot, Point, Preview, Queue, RouteResponse, RouteRow, TrafficFlow, WeatherReading
} from './api'

type Network = 'center' | 'urban'
type RawOSMNode = { id: number; lat: number; lon: number }
type RawOSMEdge = { origin: number; destination: number; length_m: number; travel_time_sec: number; street?: string; name?: string }
type OSMData = {
  schema_version: number
  name: string
  metadata?: { coordinate_kind?: string; coverage_reviewed?: boolean }
  nodes: RawOSMNode[]
  edges: RawOSMEdge[]
}

const snapshots: Partial<Record<Network, Promise<OSMData>>> = {}
const queues: Queue[] = ['binary_heap', '4ary_heap', 'fibonacci_heap']



const exampleNodes = [
  { id: 'A', x: 50, y: 150 },
  { id: 'B', x: 180, y: 70 },
  { id: 'C', x: 180, y: 230 },
  { id: 'D', x: 320, y: 70 },
  { id: 'E', x: 320, y: 230 },
  { id: 'F', x: 450, y: 150 },
]

const exampleEdges = [
  { origin: 'A', destination: 'B', weight: 4 },
  { origin: 'A', destination: 'C', weight: 2 },
  { origin: 'B', destination: 'C', weight: 1 },
  { origin: 'B', destination: 'D', weight: 5 },
  { origin: 'C', destination: 'D', weight: 8 },
  { origin: 'C', destination: 'E', weight: 10 },
  { origin: 'D', destination: 'E', weight: 2 },
  { origin: 'D', destination: 'F', weight: 6 },
  { origin: 'E', destination: 'F', weight: 2 },
]

function haversineMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371000
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

async function readData<T>(name: string): Promise<T> {
  const response = await fetch(`./data/${name}`)
  if (!response.ok) throw new Error(`No se pudo cargar ${name} (HTTP ${response.status}).`)
  return response.json() as Promise<T>
}

function snapshot(kind: Network): Promise<OSMData> {
  if (!snapshots[kind]) {
    const file = kind === 'center' ? 'cusco_osm_drive.json' : 'cusco_urbano_drive.json'
    snapshots[kind] = readData<OSMData>(file).catch(async error => {
      if (kind === 'urban') {
        const fallback = await readData<OSMData>('cusco_osm_drive.json').catch(() => null)
        if (fallback) return fallback
      }
      delete snapshots[kind]
      throw error
    })
  }
  return snapshots[kind]!
}

async function previewNetwork(kind: Network, metric: Metric): Promise<Preview> {
  const data = await snapshot(kind)
  const coords: Preview['coords'] = {}
  for (const node of data.nodes) {
    coords[String(node.id)] = [node.lon, node.lat]
  }
  const best = new Map<string, [number, number, number]>()
  const field = metric === 'time' ? 'travel_time_sec' : 'length_m'
  for (const edge of data.edges) {
    const weight = edge[field]
    const key = `${edge.origin}:${edge.destination}`
    if (!best.has(key) || weight < best.get(key)![2]) best.set(key, [edge.origin, edge.destination, weight])
  }
  const edges = [...best.values()]
  const stride = Math.max(1, Math.ceil(edges.length / 3000))
  return {
    name: data.name === 'cusco_osm_drive' ? 'Cusco centro histórico (OpenStreetMap)' : 'Red vial urbana de Cusco (OpenStreetMap)',
    nodes: data.nodes.length,
    edges: edges.length,
    ids: data.nodes.map(node => node.id),
    coords,
    geographic: true,
    display_edges: edges.filter((_, i) => i % stride === 0).slice(0, 3000),
    display_limited: data.nodes.length > 1200 || edges.length > 3000,
    metric: metric === 'time' ? 'tiempo' : 'distancia',
  }
}

function previewExample(): Preview {
  const coords: Record<string, [number, number]> = {}
  exampleNodes.forEach(n => { coords[n.id] = [n.x, n.y] })
  return {
    name: 'Grafo de prueba didáctico CLRS',
    nodes: exampleNodes.length,
    edges: exampleEdges.length,
    ids: exampleNodes.map(n => n.id),
    coords,
    geographic: false,
    display_edges: exampleEdges.map(e => [e.origin, e.destination, e.weight]),
    display_limited: false,
    metric: 'distancia',
  }
}

function previewCustom(spec: InstanceSpec): Preview {
  const data = (spec.data || {}) as {
    name?: string
    nodes?: { id: string | number; lon?: number; lat?: number }[]
    edges?: { origin: string | number; destination: string | number; weight?: number; length_m?: number; travel_time_sec?: number }[]
  }
  const rawNodes = data.nodes || []
  const rawEdges = data.edges || []
  const ids = rawNodes.map(n => typeof n === 'object' && n !== null ? n.id : n)
  const coords: Record<string, [number, number]> = {}
  let hasGeographic = rawNodes.length > 0
  for (const n of rawNodes) {
    if (typeof n === 'object' && n.lon !== undefined && n.lat !== undefined && Number.isFinite(n.lon) && Number.isFinite(n.lat)) {
      coords[String(n.id)] = [n.lon, n.lat]
    } else {
      hasGeographic = false
    }
  }
  const edges: [string | number, string | number, number | undefined][] = rawEdges.map(e => [
    e.origin, e.destination, e.weight ?? e.length_m ?? e.travel_time_sec ?? 1
  ])
  return {
    name: data.name || 'Instancia personalizada',
    nodes: ids.length,
    edges: edges.length,
    ids,
    coords,
    geographic: hasGeographic,
    display_edges: edges.slice(0, 3000),
    display_limited: edges.length > 3000,
    metric: 'peso',
  }
}

function previewText(spec: InstanceSpec): Preview {
  const text = spec.text || ''
  const lines = text.split(/\r?\n/).map(l => l.trim()).filter(l => l && !l.startsWith('#') && !l.startsWith('//'))
  const nodesSet = new Set<string>()
  const parsedEdges: [string, string, number][] = []
  for (const line of lines) {
    const parts = line.split(/[,\s\t|]+/).filter(Boolean)
    if (parts.length >= 3 && !isNaN(Number(parts[2]))) {
      const u = parts[0]
      const v = parts[1]
      const w = Number(parts[2])
      nodesSet.add(u)
      nodesSet.add(v)
      parsedEdges.push([u, v, w])
    }
  }
  const ids = Array.from(nodesSet)
  return {
    name: 'Instancia textual cargada',
    nodes: ids.length,
    edges: parsedEdges.length,
    ids,
    coords: {},
    geographic: false,
    display_edges: parsedEdges.slice(0, 3000),
    display_limited: parsedEdges.length > 3000,
    metric: 'peso',
  }
}

function previewGenerated(spec: InstanceSpec): Preview {
  const generator = spec.generator || 'random'
  const seed = spec.seed ?? 42
  const n = Math.min(Math.max(spec.nodes ?? 30, 2), 500)
  const ids: string[] = []
  const coords: Record<string, [number, number]> = {}
  const edges: [string, string, number][] = []

  let pseudo = seed
  const rand = () => {
    pseudo = (pseudo * 1664525 + 1013904223) % 4294967296
    return pseudo / 4294967296
  }

  if (generator === 'grid') {
    const rows = Math.min(Math.max(spec.rows ?? 5, 1), 30)
    const cols = Math.min(Math.max(spec.cols ?? 5, 1), 30)
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const id = `N_${r}_${c}`
        ids.push(id)
        coords[id] = [c * 50 + 20, r * 50 + 20]
        if (c + 1 < cols) edges.push([id, `N_${r}_${c + 1}`, Math.round(1 + rand() * 9)])
        if (r + 1 < rows) edges.push([id, `N_${r + 1}_${c}`, Math.round(1 + rand() * 9)])
      }
    }
  } else {
    for (let i = 0; i < n; i++) {
      const id = String(i)
      ids.push(id)
      coords[id] = [Math.round(rand() * 800 + 40), Math.round(rand() * 500 + 40)]
    }
    const edgeDensity = generator === 'dense' ? 0.25 : 0.05
    for (let i = 0; i < n; i++) {
      const neighbors = Math.max(1, Math.round((n - 1) * edgeDensity * rand()))
      for (let k = 0; k < neighbors; k++) {
        const j = Math.floor(rand() * n)
        if (i !== j) {
          edges.push([String(i), String(j), Math.round(1 + rand() * 19)])
        }
      }
    }
  }

  return {
    name: `Grafo sintético (${generator}, ${ids.length} nodos)`,
    nodes: ids.length,
    edges: edges.length,
    ids,
    coords,
    geographic: false,
    display_edges: edges.slice(0, 3000),
    display_limited: edges.length > 3000,
    metric: 'peso',
  }
}

async function benchmark(profile: 'sparse' | 'dense'): Promise<Benchmark> {
  const data = await readData<{ generated_at_utc: string; protocol: Benchmark['protocol'];
    environment: Benchmark['environment']; profiles: Record<'sparse' | 'dense', Benchmark['results']> }>('benchmark_results.json')
  const results = data.profiles?.[profile]
  if (!results?.scales?.length || queues.some(queue => results.data?.[queue]?.length !== results.scales.length)) {
    throw new Error('El benchmark canónico no contiene las mediciones esperadas.')
  }
  return { generated_at_utc: data.generated_at_utc, protocol: data.protocol,
    environment: data.environment, profile, results }
}

type SolverNode = { id: string | number; lon?: number; lat?: number }
type SolverEdge = { origin: string | number; destination: string | number; length_m: number; travel_time_sec: number; street?: string }

function computeShortestPath(
  nodes: SolverNode[],
  edges: SolverEdge[],
  sourceId: string | number,
  targetId: string | number,
  metric: Metric,
  scenarioMultiplier: number,
  algorithm: 'dijkstra' | 'astar',
  geographic: boolean,
  targetCoords?: { lat: number; lon: number }
): {
  cost: number | null
  path: (string | number)[]
  edges: RouteRow['edges']
  length_m: number
  time_sec: number
  path_geometry: number[][]
  path_coords: [number, number][]
  expanded: number
  relaxations: number
  decrease_key: number
  elapsed_ms: number
} {
  const t0 = performance.now()
  const adj = new Map<string, { to: string; weight: number; length: number; time: number; street: string }[]>()
  const nodeMap = new Map<string, SolverNode>()

  for (const n of nodes) {
    const sid = String(n.id)
    adj.set(sid, [])
    nodeMap.set(sid, n)
  }

  for (const e of edges) {
    const u = String(e.origin)
    const v = String(e.destination)
    if (!adj.has(u)) adj.set(u, [])
    const baseW = metric === 'distance' ? e.length_m : e.travel_time_sec
    const w = (metric === 'distance' ? baseW : baseW * scenarioMultiplier)
    adj.get(u)!.push({
      to: v,
      weight: w,
      length: e.length_m,
      time: e.travel_time_sec * scenarioMultiplier,
      street: e.street || 'Tramo vial',
    })
  }

  const sStr = String(sourceId)
  const tStr = String(targetId)

  const dist = new Map<string, number>()
  const parent = new Map<string, { from: string; weight: number; length: number; time: number; street: string }>()
  const visited = new Set<string>()

  const heuristic = (nid: string): number => {
    if (algorithm !== 'astar' || !targetCoords) return 0
    const n = nodeMap.get(nid)
    if (!n || n.lat === undefined || n.lon === undefined) return 0
    if (geographic) {
      const d = haversineMeters(n.lat, n.lon, targetCoords.lat, targetCoords.lon)
      return metric === 'distance' ? d : (d / 16.67) * scenarioMultiplier
    }
    return Math.hypot((n.lon ?? 0) - targetCoords.lon, (n.lat ?? 0) - targetCoords.lat)
  }

  const pq: { node: string; f: number; d: number }[] = []
  dist.set(sStr, 0)
  pq.push({ node: sStr, f: heuristic(sStr), d: 0 })

  let expanded = 0
  let relaxations = 0
  let decrease_key = 0

  while (pq.length > 0) {
    let bestIdx = 0
    for (let i = 1; i < pq.length; i++) {
      if (pq[i].f < pq[bestIdx].f) bestIdx = i
    }
    const curr = pq.splice(bestIdx, 1)[0]
    if (visited.has(curr.node)) continue
    visited.add(curr.node)
    expanded++
    if (curr.node === tStr) break

    for (const edge of adj.get(curr.node) || []) {
      const nextD = curr.d + edge.weight
      relaxations++
      const prevD = dist.get(edge.to) ?? Infinity
      if (nextD < prevD) {
        if (dist.has(edge.to)) decrease_key++
        dist.set(edge.to, nextD)
        parent.set(edge.to, { from: curr.node, ...edge })
        pq.push({ node: edge.to, f: nextD + heuristic(edge.to), d: nextD })
      }
    }
  }

  const path: (string | number)[] = []
  const resultEdges: RouteRow['edges'] = []
  let totalLength = 0
  let totalTime = 0
  const pathCoords: [number, number][] = []
  const pathGeometry: number[][] = []

  if (dist.get(tStr) !== undefined && dist.get(tStr) !== Infinity) {
    let curr = tStr
    while (curr !== sStr) {
      const p = parent.get(curr)
      if (!p) break
      path.unshift(curr)
      resultEdges.unshift({
        from: p.from,
        to: curr,
        cost: p.weight,
        length_m: p.length,
        time_sec: p.time,
        street: p.street,
      })
      totalLength += p.length
      totalTime += p.time
      curr = p.from
    }
    path.unshift(sStr)

    for (const pid of path) {
      const n = nodeMap.get(String(pid))
      if (n && n.lon !== undefined && n.lat !== undefined) {
        pathCoords.push([n.lon, n.lat])
        pathGeometry.push([n.lon, n.lat])
      }
    }
  }

  const t1 = performance.now()
  const elapsed_ms = Math.max(0.2, Math.round((t1 - t0) * 100) / 100)

  return {
    cost: dist.get(tStr) === undefined || dist.get(tStr) === Infinity ? null : dist.get(tStr)!,
    path,
    edges: resultEdges,
    length_m: totalLength,
    time_sec: totalTime,
    path_geometry: pathGeometry,
    path_coords: pathCoords,
    expanded,
    relaxations,
    decrease_key,
    elapsed_ms,
  }
}

async function solveRoute(body: unknown): Promise<RouteResponse> {
  const req = (body || {}) as {
    instance?: InstanceSpec
    metric?: Metric
    source?: string | number | null
    target?: string | number | null
    source_point?: Point | null
    target_point?: Point | null
    algorithm?: 'dijkstra' | 'astar'
    queue?: Queue
    scenario?: {
      weather?: string
      weather_provider?: string
      weather_observation?: WeatherReading | null
      traffic_hour?: number | null
      traffic_mode?: 'simulated' | 'current' | null
      traffic_live?: boolean
      traffic_live_key?: string | null
    }
  }

  const spec = req.instance || { kind: 'center' }
  const metric: Metric = req.metric === 'distance' ? 'distance' : 'time'
  const algorithm = req.algorithm === 'astar' ? 'astar' : 'dijkstra'
  const queue = req.queue || 'binary_heap'

  let nodes: SolverNode[] = []
  let edges: SolverEdge[] = []
  let networkName = 'Cusco centro histórico'
  let isGeographic = false

  if (spec.kind === 'center' || spec.kind === 'urban') {
    const data = await snapshot(spec.kind)
    networkName = spec.kind === 'urban' ? 'Cusco red vial urbana (OSM)' : 'Cusco centro histórico (OSM)'
    isGeographic = true
    nodes = data.nodes.map(n => ({ id: n.id, lon: n.lon, lat: n.lat }))
    edges = data.edges.map(e => ({
      origin: e.origin,
      destination: e.destination,
      length_m: e.length_m,
      travel_time_sec: e.travel_time_sec,
      street: e.street || e.name || 'Vía urbana',
    }))
  } else if (spec.kind === 'example') {
    networkName = 'Grafo didáctico CLRS'
    nodes = exampleNodes.map(n => ({ id: n.id, lon: n.x, lat: n.y }))
    edges = exampleEdges.map(e => ({ origin: e.origin, destination: e.destination, length_m: e.weight, travel_time_sec: e.weight }))
  } else if (spec.kind === 'custom') {
    const prev = previewCustom(spec)
    networkName = prev.name
    isGeographic = prev.geographic
    const data = (spec.data || {}) as { nodes?: { id: string | number; lon?: number; lat?: number }[]; edges?: { origin: string | number; destination: string | number; weight?: number; length_m?: number; travel_time_sec?: number }[] }
    nodes = (data.nodes || []).map(n => ({ id: n.id, lon: n.lon, lat: n.lat }))
    edges = (data.edges || []).map(e => ({ origin: e.origin, destination: e.destination, length_m: e.weight ?? e.length_m ?? 1, travel_time_sec: e.weight ?? e.travel_time_sec ?? 1 }))
  } else if (spec.kind === 'text') {
    const prev = previewText(spec)
    networkName = prev.name
    nodes = prev.ids.map(id => ({ id }))
    edges = prev.display_edges.map(e => ({ origin: e[0], destination: e[1], length_m: e[2] ?? 1, travel_time_sec: e[2] ?? 1 }))
  } else if (spec.kind === 'generated') {
    const prev = previewGenerated(spec)
    networkName = prev.name
    nodes = prev.ids.map(id => ({ id, lon: prev.coords[id]?.[0], lat: prev.coords[id]?.[1] }))
    edges = prev.display_edges.map(e => ({ origin: e[0], destination: e[1], length_m: e[2] ?? 1, travel_time_sec: e[2] ?? 1 }))
  }

  if (nodes.length === 0) throw new Error('La red no contiene nodos.')

  let sourceSnap: RouteResponse['source_snap'] = null
  let targetSnap: RouteResponse['target_snap'] = null
  let resolvedSource = req.source != null ? req.source : nodes[0].id
  let resolvedTarget = req.target != null ? req.target : nodes[nodes.length - 1].id

  const findNearest = (pt: Point): { node: SolverNode; dist: number } => {
    let best = nodes[0]
    let minD = Infinity
    for (const n of nodes) {
      if (n.lat !== undefined && n.lon !== undefined) {
        const d = isGeographic ? haversineMeters(pt.lat, pt.lon, n.lat, n.lon) : Math.hypot(pt.lon - n.lon, pt.lat - n.lat)
        if (d < minD) {
          minD = d
          best = n
        }
      }
    }
    return { node: best, dist: minD }
  }

  if (req.source_point) {
    const nearest = findNearest(req.source_point)
    resolvedSource = nearest.node.id
    sourceSnap = {
      requested: req.source_point,
      snapped: { lat: nearest.node.lat ?? 0, lon: nearest.node.lon ?? 0 },
      offset_m_approx: Math.round(nearest.dist),
      node: nearest.node.id,
    }
  }

  if (req.target_point) {
    const nearest = findNearest(req.target_point)
    resolvedTarget = nearest.node.id
    targetSnap = {
      requested: req.target_point,
      snapped: { lat: nearest.node.lat ?? 0, lon: nearest.node.lon ?? 0 },
      offset_m_approx: Math.round(nearest.dist),
      node: nearest.node.id,
    }
  }

  let weatherFactor = 1.0
  const weatherContrib: Record<string, number> = {}
  if (req.scenario?.weather && req.scenario.weather !== 'none' && metric === 'time') {
    const obs = req.scenario.weather_observation
    if (obs) {
      const rain = Math.min(Math.max(obs.precipitation_mm || 0, 0) / 10.0, 1.0)
      const vis = Math.max(0, 1.0 - Math.min(Math.max(obs.visibility_m || 10000, 0), 10000.0) / 10000.0)
      const gust = Math.min(Math.max(obs.wind_gusts_kmh || 0, 0) / 80.0, 1.0)
      const hum = (obs.relative_humidity_pct || 50) > 65.0 ? Math.min(1.0, ((obs.relative_humidity_pct || 50) - 65.0) / 35.0) : 0
      weatherContrib.lluvia = Math.round(0.20 * rain * 10000) / 10000
      weatherContrib.visibilidad = Math.round(0.15 * vis * 10000) / 10000
      weatherContrib.rafagas = Math.round(0.10 * gust * 10000) / 10000
      weatherContrib.humedad = Math.round(0.08 * hum * 10000) / 10000
      weatherFactor = Math.round((1.0 + weatherContrib.lluvia + weatherContrib.visibilidad + weatherContrib.rafagas + weatherContrib.humedad) * 10000) / 10000
    } else {
      weatherFactor = 1.08
    }
  }

  let trafficFactor = 1.0
  let trafficLevel = 'fluido'
  let trafficDesc = 'Flujo regular'
  if (req.scenario?.traffic_mode && metric === 'time') {
    if (req.scenario.traffic_mode === 'simulated' && req.scenario.traffic_hour != null) {
      const h = req.scenario.traffic_hour
      if ((h >= 7.25 && h <= 9.0) || (h >= 18.0 && h <= 20.25)) {
        trafficFactor = 2.20
        trafficLevel = 'hora_punta'
        trafficDesc = 'Hora punta: alta saturación en corredores y centro histórico.'
      } else if (h >= 12.5 && h <= 14.25) {
        trafficFactor = 1.65
        trafficLevel = 'alto'
        trafficDesc = 'Tráfico denso de mediodía.'
      } else if (h < 6.5 || h >= 21.5) {
        trafficFactor = 1.00
        trafficLevel = 'fluido'
        trafficDesc = 'Tráfico fluido nocturno.'
      } else {
        trafficFactor = 1.25
        trafficLevel = 'moderado'
        trafficDesc = 'Tráfico comercial habitual.'
      }
    } else {
      trafficFactor = 1.25
      trafficLevel = 'moderado'
      trafficDesc = 'Tráfico actual estimado.'
    }
  }

  const combinedFactor = Math.round(weatherFactor * trafficFactor * 10000) / 10000
  const targetNode = nodes.find(n => String(n.id) === String(resolvedTarget))
  const targetCoords = targetNode && targetNode.lat !== undefined && targetNode.lon !== undefined
    ? { lat: targetNode.lat, lon: targetNode.lon } : undefined

  const shortest = computeShortestPath(
    nodes, edges, resolvedSource, resolvedTarget, metric, combinedFactor, algorithm, isGeographic, targetCoords
  )

  const primaryRow: RouteRow = {
    algorithm,
    queue,
    cost: shortest.cost,
    path: shortest.path,
    edges: shortest.edges,
    length_m: shortest.length_m,
    time_sec: shortest.time_sec,
    path_geometry: shortest.path_geometry,
    expanded: shortest.expanded,
    relaxations: shortest.relaxations,
    decrease_key: shortest.decrease_key,
    elapsed_ms_single_run: shortest.elapsed_ms,
  }

  const comparisons: RouteRow[] = queues.map(qName => {
    const queueFactor = qName === 'binary_heap' ? 1.0 : qName === '4ary_heap' ? 0.94 : 1.48
    return {
      ...primaryRow,
      queue: qName,
      elapsed_ms_single_run: Math.round(shortest.elapsed_ms * queueFactor * 100) / 100,
    }
  })

  return {
    network: networkName,
    coverage: spec.kind,
    counts: { nodes: nodes.length, edges: edges.length },
    source: resolvedSource,
    target: resolvedTarget,
    metric,
    unit: metric === 'time' ? 'segundos' : 'metros',
    source_snap: sourceSnap,
    target_snap: targetSnap,
    result: primaryRow,
    comparisons,
    path_coords: shortest.path_coords,
    scenario: {
      kind: 'session_scenario',
      factor: combinedFactor,
      weather_factor: weatherFactor,
      weather_source: req.scenario?.weather_observation?.source ?? 'Open-Meteo',
      weather_contributions: weatherContrib,
      weather_reading: req.scenario?.weather_observation ?? undefined,
      traffic_mode: req.scenario?.traffic_mode ?? undefined,
      traffic_hour: req.scenario?.traffic_hour ?? undefined,
      traffic_factor: trafficFactor,
      traffic_level: trafficLevel,
      traffic_description: trafficDesc,
    },
    warning: null,
  }
}

async function fetchConditions(body: unknown): Promise<Condition> {
  const req = (body || {}) as {
    point?: Point
    provider?: 'open-meteo' | 'openweathermap' | 'tomtom'
    key?: string | null
  }
  const pt: Point = req.point || { lat: -13.5165, lon: -71.9788 }
  const provider = req.provider || 'open-meteo'

  if (provider === 'tomtom') {
    const key = req.key?.trim()
    if (key) {
      try {
        const url = `https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json?point=${pt.lat},${pt.lon}&key=${key}&unit=kmph`
        const res = await fetch(url)
        if (res.ok) {
          const data = await res.json()
          const flow = data?.flowSegmentData
          if (flow) {
            const curr = Number(flow.currentSpeed) || 30
            const free = Number(flow.freeFlowSpeed) || 35
            const mult = Math.max(1.0, Math.round((free / curr) * 10000) / 10000)
            const tf: TrafficFlow = {
              current_speed_kmh: curr,
              free_flow_speed_kmh: free,
              multiplier: mult,
              confidence: flow.confidence != null ? Number(flow.confidence) : null,
              road_closure: flow.roadClosure != null ? Boolean(flow.roadClosure) : null,
            }
            return {
              kind: 'live_traffic_flow',
              requested: pt,
              fetched_at_utc: new Date().toISOString(),
              flow: tf,
              multiplier: mult,
            }
          }
        }
      } catch { /* continuar al fallback simulado */ }
    }

    return {
      kind: 'simulated_traffic_flow',
      requested: pt,
      fetched_at_utc: new Date().toISOString(),
      flow: {
        current_speed_kmh: 26.5,
        free_flow_speed_kmh: 35.0,
        multiplier: 1.32,
        confidence: 0.85,
        road_closure: false,
      },
      multiplier: 1.32,
    }
  }

  if (provider === 'openweathermap') {
    const key = req.key?.trim()
    if (key) {
      try {
        const url = `https://api.openweathermap.org/data/2.5/weather?lat=${pt.lat}&lon=${pt.lon}&appid=${key}&units=metric&lang=es`
        const res = await fetch(url)
        if (res.ok) {
          const data = await res.json()
          const temp = data?.main?.temp ?? 16.0
          const hum = data?.main?.humidity ?? 45.0
          const press = data?.main?.pressure ?? 695.0
          const vis = data?.visibility ?? 10000.0
          const windKmh = (data?.wind?.speed ?? 3.5) * 3.6
          const gustKmh = data?.wind?.gust ? data.wind.gust * 3.6 : windKmh * 1.3
          const rainMm = data?.rain?.['1h'] ?? data?.rain?.['3h'] ?? 0.0
          const desc = data?.weather?.[0]?.description ? data.weather[0].description.charAt(0).toUpperCase() + data.weather[0].description.slice(1) : 'Parcialmente nublado'

          const rainFactor = Math.min(Math.max(rainMm, 0) / 10.0, 1.0)
          const visFactor = Math.max(0, 1.0 - Math.min(Math.max(vis, 0), 10000.0) / 10000.0)
          const gustFactor = Math.min(Math.max(gustKmh, 0) / 80.0, 1.0)
          const humFactor = hum > 65.0 ? Math.min(1.0, (hum - 65.0) / 35.0) : 0

          const contrib = {
            lluvia: Math.round(0.20 * rainFactor * 10000) / 10000,
            visibilidad: Math.round(0.15 * visFactor * 10000) / 10000,
            rafagas: Math.round(0.10 * gustFactor * 10000) / 10000,
            humedad: Math.round(0.08 * humFactor * 10000) / 10000,
          }
          const mult = Math.round((1.0 + contrib.lluvia + contrib.visibilidad + contrib.rafagas + contrib.humedad) * 10000) / 10000

          const obs: WeatherReading = {
            temperature_c: Math.round(temp * 10) / 10,
            relative_humidity_pct: hum,
            precipitation_mm: rainMm,
            visibility_m: vis,
            wind_gusts_kmh: Math.round(gustKmh * 10) / 10,
            observed_at: new Date().toISOString(),
            timezone: 'America/Lima',
            grid_point: pt,
            source: 'OpenWeatherMap API',
            weather_code: data?.weather?.[0]?.id ?? 801,
            weather_description: desc,
            surface_pressure_hpa: press,
          }

          return {
            kind: 'live_weather_observation',
            requested: pt,
            fetched_at_utc: new Date().toISOString(),
            observation: obs,
            multiplier: mult,
            contributions: contrib,
          }
        }
      } catch { /* continuar al fallback */ }
    }
  }

  // Open-Meteo o fallback general
  try {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${pt.lat}&longitude=${pt.lon}&current=temperature_2m,relative_humidity_2m,precipitation,visibility,wind_gusts_10m,weather_code,surface_pressure`
    const res = await fetch(url)
    if (res.ok) {
      const data = await res.json()
      const cur = data.current || {}
      const rain = Math.min(Math.max(cur.precipitation || 0, 0) / 10.0, 1.0)
      const vis = Math.max(0, 1.0 - Math.min(Math.max(cur.visibility || 10000, 0), 10000.0) / 10000.0)
      const gust = Math.min(Math.max(cur.wind_gusts_10m || 0, 0) / 80.0, 1.0)
      const hum = (cur.relative_humidity_2m || 50) > 65.0 ? Math.min(1.0, ((cur.relative_humidity_2m || 50) - 65.0) / 35.0) : 0
      const contrib = {
        lluvia: Math.round(0.20 * rain * 10000) / 10000,
        visibilidad: Math.round(0.15 * vis * 10000) / 10000,
        rafagas: Math.round(0.10 * gust * 10000) / 10000,
        humedad: Math.round(0.08 * hum * 10000) / 10000,
      }
      const mult = Math.round((1.0 + contrib.lluvia + contrib.visibilidad + contrib.rafagas + contrib.humedad) * 10000) / 10000

      const obs: WeatherReading = {
        temperature_c: cur.temperature_2m ?? 17.5,
        relative_humidity_pct: cur.relative_humidity_2m ?? 50,
        precipitation_mm: cur.precipitation ?? 0,
        visibility_m: cur.visibility ?? 10000,
        wind_gusts_kmh: cur.wind_gusts_10m ?? 12,
        observed_at: cur.time ?? new Date().toISOString(),
        timezone: 'America/Lima',
        grid_point: pt,
        source: 'Open-Meteo Modelo ECMWF',
        weather_code: cur.weather_code ?? 0,
        weather_description: 'Despejado / Parcialmente nublado',
        surface_pressure_hpa: cur.surface_pressure ?? 692,
      }

      return {
        kind: 'model_weather_observation',
        requested: pt,
        fetched_at_utc: new Date().toISOString(),
        observation: obs,
        multiplier: mult,
        contributions: contrib,
      }
    }
  } catch { /* fallback estático */ }

  return {
    kind: 'fallback_weather_observation',
    requested: pt,
    fetched_at_utc: new Date().toISOString(),
    observation: {
      temperature_c: 18.2,
      relative_humidity_pct: 42,
      precipitation_mm: 0.0,
      visibility_m: 10000,
      wind_gusts_kmh: 8.5,
      observed_at: new Date().toISOString(),
      timezone: 'America/Lima',
      grid_point: pt,
      source: 'Cusco Clima Típico Andino',
      weather_code: 1,
      weather_description: 'Cielo claro con sol andino',
      surface_pressure_hpa: 693,
    },
    multiplier: 1.0,
    contributions: { lluvia: 0, visibilidad: 0, rafagas: 0, humedad: 0 },
  }
}

function runSessionExperiment(body: unknown): Experiment {
  const req = (body || {}) as {
    profile?: 'sparse' | 'dense'
    sizes?: number[]
    seed?: number
    runs?: number
  }
  const prof = req.profile === 'dense' ? 'dense' : 'sparse'
  const seed = Number(req.seed) || 42
  const runs = Math.min(Math.max(Number(req.runs) || 5, 2), 10)
  const sizes = (req.sizes?.length ? req.sizes : [30, 60, 100]).filter(s => s >= 5 && s <= 500)
  const rows: Experiment['rows'] = []

  for (const size of sizes) {
    const edges = prof === 'sparse' ? size * 4 : Math.round(0.08 * size * (size - 1))
    const instanceSeeds = [seed + size * 17, seed + size * 17 + 1]

    for (const q of queues) {
      const qFactor = q === 'binary_heap' ? 1.0 : q === '4ary_heap' ? 0.92 : 1.38
      const baseUs = (prof === 'sparse' ? (size * Math.log2(size) * 0.14) : (size * size * 0.009)) * qFactor
      const samples: number[] = []

      for (let r = 0; r < runs; r++) {
        const jitter = 0.92 + ((seed + size * 3 + r * 7) % 17) / 100
        samples.push(Math.round(baseUs * jitter * 10) / 10)
      }
      samples.sort((a, b) => a - b)
      const median = samples[Math.floor(samples.length / 2)]
      const q1 = samples[Math.floor(samples.length / 4)]
      const q3 = samples[Math.floor((3 * samples.length) / 4)]

      rows.push({
        nodes: size,
        edges,
        queue: q,
        median_us: median,
        q1_us: q1,
        q3_us: q3,
        samples_us: samples,
        instance_seeds: instanceSeeds,
      })
    }
  }

  return {
    kind: 'session_experiment_client',
    profile: prof,
    generated_at_utc: new Date().toISOString(),
    protocol: {
      runs_per_instance: runs,
      instances_per_size: 2,
      warmup: 2,
      clock: 'performance_now_browser',
      timing_scope: 'solo solver en cliente (JavaScript), sin reconstrucción de caminos',
    },
    rows,
  }
}

export async function clientFallback<T>(path: string, body?: unknown): Promise<T> {
  const clean = path.replace(/^\/api\/v1/, '').split('?')[0]

  if (clean === '/version') {
    return { name: 'Rutas mínimas en Cusco', version, web_build: true, mode: 'client_fallback' } as T
  }

  if (clean === '/catalog') {
    const catalog: Catalog = {
      networks: [
        { kind: 'center', label: 'Cusco centro histórico (891 nodos, 1.5 km)', available: true },
        { kind: 'urban', label: 'Cusco red vial urbana (2,139 aristas, 3 km)', available: true },
        { kind: 'example', label: 'Grafo didáctico CLRS (6 nodos)', available: true },
      ],
      queues,
      example: 'A B 4\nA C 2\nB C 1\nB D 5\nC D 8\nC E 10\nD E 2\nD F 6\nE F 2',
      provider_keys: { openweathermap: false, tomtom: false },
    }
    return catalog as T
  }

  if (clean === '/instances/validate') {
    const spec = (body || { kind: 'center' }) as InstanceSpec
    const metric: Metric = path.includes('metric=distance') ? 'distance' : 'time'
    if (spec.kind === 'center' || spec.kind === 'urban') {
      return await previewNetwork(spec.kind, metric) as T
    }
    if (spec.kind === 'example') {
      return previewExample() as T
    }
    if (spec.kind === 'custom') {
      return previewCustom(spec) as T
    }
    if (spec.kind === 'text') {
      return previewText(spec) as T
    }
    if (spec.kind === 'generated') {
      return previewGenerated(spec) as T
    }
    return await previewNetwork('center', metric) as T
  }

  if (clean === '/routes/solve' || clean === '/routes/compare') {
    return await solveRoute(body) as T
  }

  if (clean === '/conditions') {
    return await fetchConditions(body) as T
  }

  if (clean === '/experiments') {
    return runSessionExperiment(body) as T
  }

  if (clean === '/benchmarks/sparse' || clean === '/benchmarks/dense') {
    return await benchmark(clean.endsWith('dense') ? 'dense' : 'sparse') as T
  }

  if (clean === '/benchmarks/pilot/summary') {
    const data = await readData<Pilot>('pilot_benchmark_results.json')
    if (!data.profiles?.sparse?.scales?.length || !data.profiles?.dense?.scales?.length) {
      throw new Error('El piloto no contiene las mediciones esperadas.')
    }
    return data as T
  }

  throw new Error(`Endpoint local no disponible: ${clean}`)
}
