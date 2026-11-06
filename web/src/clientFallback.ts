import { version } from '../package.json'
import type { Benchmark, Catalog, InstanceSpec, Metric, Pilot, Preview, Queue } from './api'

type Network = 'center' | 'urban'
type OSMData = {
  schema_version: number
  name: string
  metadata: { coordinate_kind?: string; coverage_reviewed?: boolean }
  nodes: { id: number; lat: number; lon: number }[]
  edges: { origin: number; destination: number; length_m: number; travel_time_sec: number }[]
}

const snapshots: Partial<Record<Network, Promise<OSMData>>> = {}
const queues: Queue[] = ['binary_heap', '4ary_heap', 'fibonacci_heap']
const requiresApi = 'Esta función requiere FastAPI. GitHub Pages solo sirve archivos; configura RUTAS_API_BASE_URL en el despliegue público.'

async function readData<T>(name: string): Promise<T> {
  const response = await fetch(`./data/${name}`)
  if (!response.ok) throw new Error(`No se pudo cargar ${name} (HTTP ${response.status}).`)
  return response.json() as Promise<T>
}

function snapshot(kind: Network): Promise<OSMData> {
  if (!snapshots[kind]) {
    const file = kind === 'center' ? 'cusco_osm_drive.json' : 'cusco_urbano_drive.json'
    snapshots[kind] = readData<OSMData>(file).catch(error => {
      delete snapshots[kind]
      throw error
    })
  }
  return snapshots[kind]
}

async function previewNetwork(kind: Network, metric: Metric): Promise<Preview> {
  const data = await snapshot(kind)
  if (data.schema_version !== 1 || data.metadata?.coordinate_kind !== 'lon_lat_wgs84' ||
      (kind === 'urban' && data.metadata.coverage_reviewed !== true) ||
      !Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
    throw new Error('El snapshot OSM no tiene el formato o la revisión esperados.')
  }
  const coords: Preview['coords'] = {}
  for (const node of data.nodes) {
    if (!Number.isFinite(node.lat) || !Number.isFinite(node.lon) ||
        Math.abs(node.lat) > 90 || Math.abs(node.lon) > 180 || String(node.id) in coords) {
      throw new Error('El snapshot OSM contiene nodos inválidos.')
    }
    coords[String(node.id)] = [node.lon, node.lat]
  }
  const best = new Map<string, [number, number, number]>()
  const field = metric === 'time' ? 'travel_time_sec' : 'length_m'
  for (const edge of data.edges) {
    const weight = edge[field]
    if (!Number.isFinite(weight) || weight < 0 || !(String(edge.origin) in coords) ||
        !(String(edge.destination) in coords)) throw new Error('El snapshot OSM contiene aristas inválidas.')
    const key = `${edge.origin}:${edge.destination}`
    if (!best.has(key) || weight < best.get(key)![2]) best.set(key, [edge.origin, edge.destination, weight])
  }
  const edges = [...best.values()]
  const stride = Math.max(1, Math.ceil(edges.length / 3000))
  return {
    name: data.name, nodes: data.nodes.length, edges: edges.length,
    ids: data.nodes.map(node => node.id), coords, geographic: true,
    display_edges: edges.filter((_, i) => i % stride === 0).slice(0, 3000),
    display_limited: data.nodes.length > 1200 || edges.length > 3000, metric,
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

export async function clientFallback<T>(path: string, body?: unknown): Promise<T> {
  const clean = path.split('?')[0]
  if (clean === '/version') {
    return { name: 'Rutas mínimas en Cusco', version, web_build: true, mode: 'static_read_only' } as T
  }
  if (clean === '/catalog') {
    const catalog: Catalog = {
      networks: [
        { kind: 'center', label: 'Centro, snapshot OSM (radio 1,5 km)', available: true },
        { kind: 'urban', label: 'Centro ampliado, snapshot OSM (radio 3 km)', available: true },
      ],
      queues, example: 'Seis nodos ilustrativos, no vías medidas',
      provider_keys: { openweathermap: false, tomtom: false },
    }
    return catalog as T
  }
  if (clean === '/instances/validate') {
    const spec = body as InstanceSpec | undefined
    if (spec?.kind !== 'center' && spec?.kind !== 'urban') throw new Error(requiresApi)
    const metric: Metric = path.includes('metric=distance') ? 'distance' : 'time'
    return await previewNetwork(spec.kind, metric) as T
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
  throw new Error(requiresApi)
}
