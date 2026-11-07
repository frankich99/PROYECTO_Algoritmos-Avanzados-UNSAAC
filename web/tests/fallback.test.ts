import { afterEach, beforeEach, expect, it, vi } from 'vitest'

beforeEach(() => vi.resetModules())
afterEach(() => vi.unstubAllGlobals())
it.each(['/routes/solve', '/experiments', '/conditions'])('no fabrica resultados para %s', async path => {
  const { clientFallback } = await import('../src/clientFallback')
  await expect(clientFallback(path, {})).rejects.toThrow('requiere FastAPI')
})
it('no sustituye una cobertura urbana fallida por el centro', async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: false, status: 404 })
  vi.stubGlobal('fetch', fetch)
  const { clientFallback } = await import('../src/clientFallback')
  await expect(clientFallback('/instances/validate', { kind: 'urban' })).rejects.toThrow('cusco_urbano_drive')
  expect(fetch).toHaveBeenCalledTimes(1)
})
it.each([-1, NaN, Infinity])('rechaza peso adverso %s de un snapshot', async weight => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ schema_version: 1, metadata: { coordinate_kind: 'lon_lat_wgs84' },
    nodes: [{ id: 1, lon: -71, lat: -13 }], edges: [{ origin: 1, destination: 1, travel_time_sec: weight }] }) }))
  const { clientFallback } = await import('../src/clientFallback')
  await expect(clientFallback('/instances/validate', { kind: 'center' })).rejects.toThrow('aristas inválidas')
})
it('carga un snapshot válido y no usa unidades inventadas', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ schema_version: 1, name: 'fixture', metadata: { coordinate_kind: 'lon_lat_wgs84' },
    nodes: [{ id: 1, lon: -71, lat: -13 }], edges: [{ origin: 1, destination: 1, travel_time_sec: 2, length_m: 3 }] }) }))
  const { clientFallback } = await import('../src/clientFallback')
  expect(await clientFallback('/instances/validate?metric=distance', { kind: 'center' })).toMatchObject({ nodes: 1, edges: 1, metric: 'distance', display_edges: [[1, 1, 3]] })
})
