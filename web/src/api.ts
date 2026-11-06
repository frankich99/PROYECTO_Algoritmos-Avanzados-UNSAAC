export type Kind = 'example' | 'center' | 'urban' | 'custom' | 'text' | 'generated'
export type Metric = 'time' | 'distance'
export type Queue = 'binary_heap' | '4ary_heap' | 'fibonacci_heap'
export type Point = { lat: number; lon: number }
export type InstanceSpec = {
  kind: Kind
  data?: Record<string, unknown>
  text?: string
  generator?: 'random' | 'grid' | 'sparse' | 'dense'
  nodes?: number
  seed?: number
  rows?: number
  cols?: number
}
export type Preview = {
  name: string; nodes: number; edges: number; ids: (string | number)[]
  coords: Record<string, [number, number]>
  geographic: boolean; display_edges: [string | number, string | number][]
  display_limited: boolean; metric: string
}
export type RouteRow = {
  algorithm: 'dijkstra' | 'astar'; queue: Queue; cost: number | null
  path: (string | number)[]; edges: { from: string | number; to: string | number; cost: number; length_m: number | null; time_sec: number | null; street: string | null }[]
  length_m: number | null; time_sec: number | null
  path_geometry: number[][]; expanded: number; relaxations: number; decrease_key: number; elapsed_ms_single_run: number
}
export type RouteResponse = {
  network: string; coverage: Kind; counts: { nodes: number; edges: number }
  source: string | number; target: string | number; metric: Metric; unit: string
  source_snap: { requested: Point; snapped: Point; offset_m_approx: number; node: string | number } | null
  target_snap: { requested: Point; snapped: Point; offset_m_approx: number; node: string | number } | null
  result: RouteRow; comparisons: RouteRow[]; path_coords: [number, number][]
  scenario: { kind: string; factor: number; weather_factor?: number; weather_session_supplied?: boolean; weather_source?: string; weather_observed_at?: string; weather_timezone?: string; weather_cached?: boolean; weather_contributions?: Record<string, number>; weather_reading?: Pick<WeatherReading, 'temperature_c' | 'relative_humidity_pct' | 'precipitation_mm' | 'visibility_m' | 'wind_gusts_kmh' | 'weather_code' | 'surface_pressure_hpa'>; requested_point?: Point; weather_grid_point?: Point; traffic_mode?: 'simulated' | 'current'; traffic_hour?: number; traffic_observed_at?: string; traffic_source?: string; traffic_factor?: number; traffic_level?: string; traffic_description?: string; traffic_point?: Point; traffic_flow?: TrafficFlow; traffic_flow_fetched_at_utc?: string }
  warning: string | null
}
export type BenchmarkRow = { nodes: number; edges: number; median_us: number; q1_us: number; q3_us: number; sample_count?: number }
export type Benchmark = {
  generated_at_utc: string; protocol: Record<string, unknown>; environment: Record<string, unknown>
  profile: string; results: { scales: number[]; data: Record<Queue, BenchmarkRow[]> }
}
export type Pilot = {
  generated_at_utc: string; protocol: Record<string, unknown>
  profiles: Record<'sparse' | 'dense', Benchmark['results']>
}
export type Experiment = {
  kind: string; generated_at_utc: string; profile: string; protocol: Record<string, unknown>
  rows: (BenchmarkRow & { queue: Queue; samples_us: number[]; instance_seeds: number[] })[]
}
export type WeatherReading = {
  temperature_c: number; relative_humidity_pct: number; precipitation_mm: number; visibility_m: number
  wind_gusts_kmh: number; observed_at: string; timezone: string; grid_point: Point; source: string
  weather_code: number; weather_description: string; surface_pressure_hpa: number | null
}
export type TrafficFlow = { current_speed_kmh: number; free_flow_speed_kmh: number; multiplier: number; confidence: number | null; road_closure: boolean | null }
export type Condition = {
  kind: string; requested: Point; fetched_at_utc: string
  observation?: WeatherReading
  multiplier?: number; contributions?: Record<string, number>
  flow?: TrafficFlow
}
export type Catalog = { networks: { kind: Kind; label: string; available: boolean }[]; queues: Queue[]; example: string;
  provider_keys?: { openweathermap: boolean; tomtom: boolean } }

const apiBase = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')

export const apiUrl = (path: string) => `${apiBase}${path}`

// En GitHub Pages no hay API: solo allí se permite el cálculo local de respaldo.
const staticDeployment = !import.meta.env.VITE_API_BASE_URL &&
  typeof location !== 'undefined' && !['127.0.0.1', 'localhost'].includes(location.hostname)

async function staticFallback<T>(path: string, body?: unknown): Promise<T> {
  const { clientFallback } = await import('./clientFallback')
  return clientFallback<T>(path, body)
}

export async function api<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  let response: Response
  try {
    response = await fetch(apiUrl(`/api/v1${path}`), {
      method: body === undefined ? 'GET' : 'POST',
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
  } catch (err) {
    if (signal?.aborted) throw err
    if (staticDeployment) return staticFallback<T>(path, body)
    throw new Error('No se pudo conectar con la API. Comprueba que el servidor está iniciado.')
  }
  if (!response.ok) {
    const contentType = response.headers.get('content-type') ?? ''
    if (staticDeployment && !contentType.includes('application/json')) {
      return staticFallback<T>(path, body)
    }
    const payload: unknown = await response.json().catch(() => null)
    const detail = payload && typeof payload === 'object' && 'detail' in payload ? payload.detail : null
    const message = typeof detail === 'string' ? detail : Array.isArray(detail) ?
      detail.map(item => item && typeof item === 'object' && 'msg' in item ? String(item.msg) : 'Entrada no válida').join('; ') :
      `La API devolvió el estado ${response.status}.`
    throw new Error(message)
  }
  return (await response.json()) as T
}
