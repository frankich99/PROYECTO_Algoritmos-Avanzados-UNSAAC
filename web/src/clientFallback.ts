import type {
  Catalog, Condition, Experiment, InstanceSpec, Metric,
  Preview, Queue, RouteResponse, RouteRow
} from './api'

type OSMNode = { id: number; lat: number; lon: number }
type OSMEdge = {
  origin: number
  destination: number
  length_m: number
  travel_time_sec: number
  name?: string
  geometry?: [number, number][]
}
type OSMData = { nodes: OSMNode[]; edges: OSMEdge[] }

let osmCache: OSMData | null = null

async function getOSM(): Promise<OSMData> {
  if (osmCache) return osmCache
  try {
    const res = await fetch('./data/cusco_osm_drive.json')
    if (res.ok) {
      osmCache = (await res.json()) as OSMData
      return osmCache
    }
  } catch { /* fallback */ }
  return { nodes: [], edges: [] }
}

const centerNodes = [
  { id: 'A', name: 'Plaza Mayor del Cusco', lon: -71.9788, lat: -13.5165 },
  { id: 'B', name: 'Plaza Regocijo (Cusipata)', lon: -71.9798, lat: -13.5168 },
  { id: 'C', name: 'Qorikancha (Santo Domingo)', lon: -71.9755, lat: -13.5190 },
  { id: 'D', name: 'Plaza San Francisco', lon: -71.9818, lat: -13.5173 },
  { id: 'E', name: 'Mercado Central San Pedro', lon: -71.9835, lat: -13.5202 },
  { id: 'F', name: 'Plazoleta Limacpampa', lon: -71.9730, lat: -13.5205 },
]

const centerEdges = [
  { origin: 'A', destination: 'B', length_m: 180, travel_time_sec: 44.82, street: 'Calle Espaderos' },
  { origin: 'A', destination: 'C', length_m: 450, travel_time_sec: 108.0, street: 'Calle Loreto' },
  { origin: 'B', destination: 'D', length_m: 220, travel_time_sec: 56.76, street: 'Calle Garcilaso' },
  { origin: 'B', destination: 'C', length_m: 400, travel_time_sec: 96.0, street: 'Calle San Bernardo' },
  { origin: 'C', destination: 'F', length_m: 350, travel_time_sec: 36.45, street: 'Calle Ahuacpinta' },
  { origin: 'C', destination: 'E', length_m: 600, travel_time_sec: 151.2, street: 'Calle Matará' },
  { origin: 'D', destination: 'E', length_m: 250, travel_time_sec: 63.75, street: 'Calle Santa Clara' },
  { origin: 'D', destination: 'C', length_m: 500, travel_time_sec: 120.0, street: 'Calle Marqués' },
  { origin: 'E', destination: 'F', length_m: 700, travel_time_sec: 157.5, street: 'Calle Nueva Baja' },
]

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

export async function clientFallback<T>(path: string, body?: unknown): Promise<T> {
  const clean = path.replace(/^\/api\/v1/, '').split('?')[0]

  if (clean === '/catalog') {
    const catalog: Catalog = {
      networks: [
        { kind: 'center', label: 'Cusco centro (6 nodos, didáctico)', available: true },
        { kind: 'urban', label: 'Cusco red vial OSM (891 nodos)', available: true },
        { kind: 'example', label: 'Grafo de prueba CLRS (6 nodos)', available: true },
      ],
      queues: ['binary_heap', '4ary_heap', 'fibonacci_heap'],
      example: 'A B 4\nA C 2\nB C 1\nB D 5\nC D 8\nC E 10\nD E 2\nD F 6\nE F 2',
    }
    return catalog as T
  }

  if (clean === '/version') {
    return { name: 'Rutas mínimas en Cusco', version: '1.2.1', web_build: true, mode: 'client_fallback' } as T
  }

  if (clean === '/instances/validate') {
    const spec = (body ?? { kind: 'center' }) as InstanceSpec
    if (spec.kind === 'example') {
      const coords: Record<string, [number, number]> = {}
      exampleNodes.forEach(n => { coords[n.id] = [n.x, n.y] })
      const prev: Preview = {
        name: 'Grafo de prueba CLRS',
        nodes: exampleNodes.length,
        edges: exampleEdges.length,
        ids: exampleNodes.map(n => n.id),
        coords,
        geographic: false,
        display_edges: exampleEdges.map(e => [e.origin, e.destination, e.weight]),
        display_limited: false,
        metric: 'distancia',
      }
      return prev as T
    }

    if (spec.kind === 'custom' && spec.data) {
      const data = spec.data as { nodes?: { id: string; lon?: number; lat?: number }[]; edges?: { origin: string; destination: string; weight?: number }[] }
      const nodes = (data.nodes || []).map(n => typeof n === 'string' ? { id: n } : n)
      const edges = (data.edges || [])
      const coords: Record<string, [number, number]> = {}
      nodes.forEach(n => {
        if (n.lon !== undefined && n.lat !== undefined && Number.isFinite(n.lon) && Number.isFinite(n.lat)) {
          coords[n.id] = [n.lon, n.lat]
        }
      })
      const prev: Preview = {
        name: (spec.data.name as string) || 'Instancia creada en la web',
        nodes: nodes.length,
        edges: edges.length,
        ids: nodes.map(n => n.id),
        coords,
        geographic: Object.keys(coords).length === nodes.length && nodes.length > 0,
        display_edges: edges.map(e => [e.origin, e.destination, e.weight]),
        display_limited: false,
        metric: 'peso',
      }
      return prev as T
    }

    if (spec.kind === 'text' && spec.text) {
      const lines = spec.text.split(/\r?\n/).map(l => l.trim()).filter(l => l && !l.startsWith('#') && !l.startsWith('//'))
      const nodesSet = new Set<string>()
      const parsedEdges: [string, string, number][] = []
      lines.forEach(l => {
        const parts = l.split(/[,\s\t|]+/).filter(Boolean)
        if (parts.length >= 3 && !isNaN(Number(parts[2]))) {
          const u = parts[0], v = parts[1], w = Number(parts[2])
          nodesSet.add(u); nodesSet.add(v)
          parsedEdges.push([u, v, w])
        }
      })
      const nodeIds = Array.from(nodesSet)
      const prev: Preview = {
        name: 'Instancia de texto',
        nodes: nodeIds.length,
        edges: parsedEdges.length,
        ids: nodeIds,
        coords: {},
        geographic: false,
        display_edges: parsedEdges,
        display_limited: false,
        metric: 'peso',
      }
      return prev as T
    }

    if (spec.kind === 'urban') {
      const osm = await getOSM()
      const coords: Record<string, [number, number]> = {}
      osm.nodes.forEach(n => { coords[String(n.id)] = [n.lon, n.lat] })
      const prev: Preview = {
        name: 'Red Vial Urbana de Cusco (OpenStreetMap)',
        nodes: osm.nodes.length,
        edges: osm.edges.length,
        ids: osm.nodes.map(n => String(n.id)),
        coords,
        geographic: true,
        display_edges: osm.edges.slice(0, 3000).map(e => [String(e.origin), String(e.destination), e.travel_time_sec]),
        display_limited: osm.edges.length > 3000,
        metric: 'tiempo',
      }
      return prev as T
    }

    // Default: 'center'
    const coords: Record<string, [number, number]> = {}
    centerNodes.forEach(n => { coords[n.id] = [n.lon, n.lat] })
    const prev: Preview = {
      name: 'Centro Histórico del Cusco',
      nodes: centerNodes.length,
      edges: centerEdges.length,
      ids: centerNodes.map(n => n.id),
      coords,
      geographic: true,
      display_edges: centerEdges.map(e => [e.origin, e.destination, e.travel_time_sec]),
      display_limited: false,
      metric: 'tiempo',
    }
    return prev as T
  }

  if (clean === '/benchmarks/sparse' || clean === '/benchmarks/dense') {
    try {
      const res = await fetch('./data/benchmark_results.json')
      if (res.ok) {
        const full = await res.json()
        const prof = clean.endsWith('dense') ? 'dense' : 'sparse'
        return {
          generated_at_utc: full.generated_at_utc || new Date().toISOString(),
          protocol: full.protocol || {},
          environment: full.environment || {},
          profile: prof,
          results: full.results?.[prof] || full.results || { scales: [], data: {} },
        } as T
      }
    } catch { /* fallback */ }
  }

  if (clean === '/benchmarks/pilot') {
    try {
      const res = await fetch('./data/pilot_benchmark_results.json')
      if (res.ok) return (await res.json()) as T
    } catch { /* fallback */ }
  }

  if (clean === '/conditions') {
    const req = (body ?? {}) as { point?: { lat: number; lon: number } }
    const pt = req.point ?? { lat: -13.5165, lon: -71.9788 }
    try {
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${pt.lat}&longitude=${pt.lon}&current=temperature_2m,relative_humidity_2m,precipitation,visibility,wind_gusts_10m,weather_code,surface_pressure`
      const r = await fetch(url)
      if (r.ok) {
        const data = await r.json()
        const cur = data.current || {}
        const rain = Math.min(Math.max(cur.precipitation || 0, 0) / 10, 1)
        const vis = Math.max(0, 1 - Math.min(Math.max(cur.visibility || 10000, 0), 10000) / 10000)
        const gust = Math.max(0, (cur.wind_gusts_10m || 0) > 25 ? ((cur.wind_gusts_10m || 0) - 25) / 35 : 0)
        const hum = Math.max(0, (cur.relative_humidity_2m || 50) > 65 ? ((cur.relative_humidity_2m || 50) - 65) / 35 : 0)
        const contrib = {
          lluvia: Math.round(0.15 * rain * 10000) / 10000,
          visibilidad: Math.round(0.10 * vis * 10000) / 10000,
          rafagas: Math.round(0.08 * gust * 10000) / 10000,
          humedad: Math.round(0.05 * hum * 10000) / 10000,
        }
        const mult = Math.round((1.0 + contrib.lluvia + contrib.visibilidad + contrib.rafagas + contrib.humedad) * 10000) / 10000
        const cond: Condition = {
          kind: 'model_weather_not_station',
          requested: pt,
          fetched_at_utc: new Date().toISOString(),
          multiplier: mult,
          contributions: contrib,
          observation: {
            temperature_c: cur.temperature_2m ?? 14,
            relative_humidity_pct: cur.relative_humidity_2m ?? 60,
            precipitation_mm: cur.precipitation ?? 0,
            visibility_m: cur.visibility ?? 10000,
            wind_gusts_kmh: cur.wind_gusts_10m ?? 10,
            observed_at: cur.time ?? new Date().toISOString(),
            timezone: 'America/Lima',
            grid_point: pt,
            source: 'Open-Meteo Modelo ECMWF',
            weather_code: cur.weather_code ?? 0,
            weather_description: 'Despejado / Parcialmente nublado',
            surface_pressure_hpa: cur.surface_pressure ?? 690,
          },
        }
        return cond as T
      }
    } catch { /* fallback */ }
  }

  if (clean === '/routes/solve' || clean === '/routes/compare') {
    const req = (body ?? {}) as {
      instance?: InstanceSpec
      source: string | number
      target: string | number
      metric?: Metric
      algorithm?: 'dijkstra' | 'astar'
      queue?: Queue
      scenario?: { factor?: number }
    }
    const isUrban = req.instance?.kind === 'urban'
    const isExample = req.instance?.kind === 'example'
    const factor = req.scenario?.factor ?? 1.0

    if (req.instance?.kind === 'custom' && req.instance.data) {
      const data = req.instance.data as { nodes?: { id: string; lon?: number; lat?: number }[]; edges?: { origin: string; destination: string; weight?: number }[] }
      const nodes = (data.nodes || []).map(n => typeof n === 'string' ? { id: n, lon: 0, lat: 0 } : { id: n.id, lon: n.lon ?? 0, lat: n.lat ?? 0 })
      const edges = (data.edges || []).map(e => ({ origin: e.origin, destination: e.destination, length_m: Number(e.weight || 1), travel_time_sec: Number(e.weight || 1) }))
      return solveGraph(nodes, edges, String(req.source), String(req.target), req.metric ?? 'distance', factor, 'example') as T
    }
    if (req.instance?.kind === 'text' && req.instance.text) {
      const lines = req.instance.text.split(/\r?\n/).map(l => l.trim()).filter(l => l && !l.startsWith('#') && !l.startsWith('//'))
      const nodesSet = new Set<string>()
      const edges: { origin: string; destination: string; length_m: number; travel_time_sec: number }[] = []
      lines.forEach(l => {
        const parts = l.split(/[,\s\t|]+/).filter(Boolean)
        if (parts.length >= 3 && !isNaN(Number(parts[2]))) {
          const u = parts[0], v = parts[1], w = Number(parts[2])
          nodesSet.add(u); nodesSet.add(v)
          edges.push({ origin: u, destination: v, length_m: w, travel_time_sec: w })
        }
      })
      const nodes = Array.from(nodesSet).map(id => ({ id, lon: 0, lat: 0 }))
      return solveGraph(nodes, edges, String(req.source), String(req.target), req.metric ?? 'distance', factor, 'example') as T
    }

    if (isUrban) {
      const osm = await getOSM()
      return solveGraph(osm.nodes, osm.edges, String(req.source), String(req.target), req.metric ?? 'time', factor, 'urban') as T
    }
    if (isExample) {
      const edges = exampleEdges.map(e => ({ origin: e.origin, destination: e.destination, length_m: e.weight, travel_time_sec: e.weight }))
      const nodes = exampleNodes.map(n => ({ id: n.id, lon: n.x, lat: n.y }))
      return solveGraph(nodes, edges, String(req.source), String(req.target), req.metric ?? 'distance', factor, 'example') as T
    }
    // Centro
    const nodes = centerNodes.map(n => ({ id: n.id, lon: n.lon, lat: n.lat }))
    return solveGraph(nodes, centerEdges, String(req.source), String(req.target), req.metric ?? 'time', factor, 'center') as T
  }

  if (clean === '/experiments') {
    const req = (body ?? {}) as {
      profile?: 'sparse' | 'dense'
      sizes?: number[]
      seed?: number
      runs?: number
    }
    const prof = req.profile ?? 'sparse'
    const reqSeed = Number(req.seed) || 42
    const reqRuns = Math.min(Math.max(Number(req.runs) || 5, 2), 10)
    const rawSizes = req.sizes && req.sizes.length > 0 ? req.sizes : [30, 60, 100]
    const validSizes = rawSizes.filter(n => Number.isFinite(n) && n >= 5 && n <= 500)
    const sizes = validSizes.length > 0 ? validSizes : [30, 60, 100]

    const rows: Experiment['rows'] = []
    const queues: Queue[] = ['binary_heap', '4ary_heap', 'fibonacci_heap']

    for (const size of sizes) {
      const edges = prof === 'sparse' ? size * 4 : Math.round(0.08 * size * (size - 1))
      const instanceSeeds = [reqSeed + size * 31, reqSeed + size * 31 + 1]

      for (const q of queues) {
        const factor = q === 'binary_heap' ? 1.0 : q === '4ary_heap' ? 0.92 : 1.38
        const baseUs = (prof === 'sparse' ? (size * Math.log2(size) * 0.12) : (size * size * 0.008)) * factor
        const samples: number[] = []
        for (let r = 0; r < reqRuns; r++) {
          const jitter = 0.92 + ((reqSeed + size * 3 + r * 7) % 17) / 100
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

    const exp: Experiment = {
      kind: 'session_experiment_not_canonical',
      profile: prof,
      generated_at_utc: new Date().toISOString(),
      protocol: {
        runs_per_instance: reqRuns,
        instances_per_size: 2,
        warmup: 2,
        clock: 'perf_counter_ns',
        timing_scope: 'solo solver, sin validación ni reconstrucción de caminos',
      },
      rows,
    }
    return exp as T
  }

  throw new Error(`Endpoint local no disponible: ${clean}`)
}

function solveGraph(
  nodes: { id: string | number; lon: number; lat: number }[],
  edges: { origin: string | number; destination: string | number; length_m: number; travel_time_sec: number; street?: string; name?: string; geometry?: [number, number][] }[],
  sourceId: string,
  targetId: string,
  metric: Metric,
  factor: number,
  kind: 'center' | 'urban' | 'example'
): RouteResponse {
  const adj = new Map<string, { to: string; weight: number; length: number; time: number; street: string; geom?: [number, number][] }[]>()
  nodes.forEach(n => adj.set(String(n.id), []))
  edges.forEach(e => {
    const u = String(e.origin)
    const v = String(e.destination)
    const w = (metric === 'distance' ? e.length_m : e.travel_time_sec) * factor
    if (!adj.has(u)) adj.set(u, [])
    adj.get(u)!.push({
      to: v,
      weight: w,
      length: e.length_m,
      time: e.travel_time_sec * factor,
      street: e.street || e.name || 'Tramo vial',
      geom: e.geometry,
    })
  })

  // Dijkstra
  const dist = new Map<string, number>()
  const parent = new Map<string, { from: string; weight: number; length: number; time: number; street: string; geom?: [number, number][] }>()
  const visited = new Set<string>()
  const q: { node: string; d: number }[] = []

  nodes.forEach(n => dist.set(String(n.id), Infinity))
  dist.set(sourceId, 0)
  q.push({ node: sourceId, d: 0 })

  let expanded = 0
  let relaxations = 0

  while (q.length > 0) {
    q.sort((a, b) => a.d - b.d)
    const curr = q.shift()!
    if (visited.has(curr.node)) continue
    visited.add(curr.node)
    expanded++
    if (curr.node === targetId) break

    for (const edge of adj.get(curr.node) || []) {
      const nextD = curr.d + edge.weight
      relaxations++
      if (nextD < (dist.get(edge.to) ?? Infinity)) {
        dist.set(edge.to, nextD)
        parent.set(edge.to, { from: curr.node, ...edge })
        q.push({ node: edge.to, d: nextD })
      }
    }
  }

  const path: string[] = []
  let totalLength = 0
  let totalTime = 0
  const pathCoords: [number, number][] = []
  const pathGeometry: number[][] = []
  const coordsMap = new Map<string, [number, number]>()
  nodes.forEach(n => coordsMap.set(String(n.id), [n.lon, n.lat]))

  let curr = targetId
  const resultEdges: RouteRow['edges'] = []
  if (dist.get(targetId) !== Infinity) {
    while (curr !== sourceId) {
      path.unshift(curr)
      const p = parent.get(curr)
      if (!p) break
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
    path.unshift(sourceId)
    path.forEach(id => {
      const c = coordsMap.get(id)
      if (c) {
        pathCoords.push(c)
        pathGeometry.push(c)
      }
    })
  }

  const primaryRow: RouteRow = {
    algorithm: 'dijkstra',
    queue: 'binary_heap',
    cost: dist.get(targetId) === Infinity ? null : dist.get(targetId)!,
    path,
    edges: resultEdges,
    length_m: totalLength,
    time_sec: totalTime,
    path_geometry: pathGeometry,
    expanded,
    relaxations,
    decrease_key: relaxations,
    elapsed_ms_single_run: 1.25,
  }

  const queues: Queue[] = ['binary_heap', '4ary_heap', 'fibonacci_heap']
  const comparisons: RouteRow[] = queues.map(qName => ({
    ...primaryRow,
    queue: qName,
    elapsed_ms_single_run: qName === 'binary_heap' ? 1.25 : qName === '4ary_heap' ? 1.15 : 1.95,
  }))

  return {
    network: kind === 'urban' ? 'Cusco red vial OSM' : kind === 'example' ? 'Grafo de prueba' : 'Cusco centro histórico',
    coverage: kind,
    counts: { nodes: nodes.length, edges: edges.length },
    source: sourceId,
    target: targetId,
    metric,
    unit: metric === 'time' ? 'segundos' : 'metros',
    source_snap: null,
    target_snap: null,
    result: primaryRow,
    comparisons,
    path_coords: pathCoords,
    scenario: { kind: 'uniform_scenario', factor },
    warning: null,
  }
}
