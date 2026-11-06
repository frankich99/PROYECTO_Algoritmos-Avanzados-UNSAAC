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
  scenario: { kind: string; factor: number; weather_source?: string; weather_observed_at?: string; weather_timezone?: string; weather_cached?: boolean; requested_point?: Point; weather_grid_point?: Point; traffic?: string; traffic_hour?: number }
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
export type Condition = {
  kind: string; requested: Point; fetched_at_utc: string
  observation?: { temperature_c: number; relative_humidity_pct: number; precipitation_mm: number; visibility_m: number; wind_gusts_kmh: number; observed_at: string; timezone: string; grid_point: Point; source: string }
  flow?: { current_speed_kmh: number; free_flow_speed_kmh: number; confidence: number | null }
}
export type Catalog = { networks: { kind: Kind; label: string; available: boolean }[]; queues: Queue[]; example: string }

const apiBase = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')

export const apiUrl = (path: string) => `${apiBase}${path}`

export async function api<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(apiUrl(`/api/v1${path}`), {
    method: body === undefined ? 'GET' : 'POST',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  })
  if (!response.ok) {
    let detail = `Error HTTP ${response.status}`
    try {
      const result = await response.json()
      if (typeof result.detail === 'string') detail = result.detail
      else if (Array.isArray(result.detail)) detail = result.detail.map((item: { loc?: (string | number)[]; msg?: string }) =>
        `${item.loc?.join('.') ?? 'Entrada'}: ${item.msg ?? 'valor inválido'}`).join('; ')
    } catch { /* El servidor no devolvió JSON. */ }
    throw new Error(detail)
  }
  return response.json() as Promise<T>
}
