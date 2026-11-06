import type { Condition } from './api'
import { fmt } from './format'

export default function WeatherReading({ data }: { data: Condition }) {
  if (!data.observation) return null
  const reading = data.observation
  return <div className="observation"><strong>{reading.source}</strong>
    <p><b>{fmt(reading.temperature_c, 1)} °C</b> · {fmt(reading.relative_humidity_pct, 0)} % humedad</p>
    <p>Lluvia {fmt(reading.precipitation_mm)} mm · Visibilidad {fmt(reading.visibility_m, 0)} m · Ráfagas {fmt(reading.wind_gusts_kmh, 1)} km/h</p>
    <p>Lectura: {reading.observed_at} ({reading.timezone}); consultada: {data.fetched_at_utc}.</p>
    <p>Solicitado: {fmt(data.requested.lat, 5)}, {fmt(data.requested.lon, 5)}; grilla: {fmt(reading.grid_point.lat, 5)}, {fmt(reading.grid_point.lon, 5)}.</p>
    {data.multiplier != null && <p>Factor hipotético: {fmt(data.multiplier, 4)}×. Aportes: {Object.entries(data.contributions ?? {}).map(([key, value]) => `${key} +${fmt(value * 100, 2)} %`).join(' · ')}.</p>}
    <p className="fineprint">La temperatura se informa, pero no interviene en la fórmula de costos.</p>
  </div>
}
