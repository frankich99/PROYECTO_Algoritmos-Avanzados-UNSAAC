import type { Condition } from './api'
import { fmt } from './format'

export default function WeatherReading({ data }: { data: Condition }) {
  if (!data.observation) return null
  const reading = data.observation
  return <div className="observation"><h3>{reading.source}</h3>
    <dl className="reading-grid"><div><dt>Temperatura</dt><dd>{fmt(reading.temperature_c, 1)} °C</dd></div>
      <div><dt>Lluvia</dt><dd>{fmt(reading.precipitation_mm)} mm</dd></div>
      <div><dt>Humedad</dt><dd>{fmt(reading.relative_humidity_pct, 0)} %</dd></div>
      <div><dt>Visibilidad</dt><dd>{fmt(reading.visibility_m, 0)} m</dd></div>
      <div><dt>Ráfagas</dt><dd>{fmt(reading.wind_gusts_kmh, 1)} km/h</dd></div>
      <div><dt>Condición</dt><dd>{reading.weather_description || 'Sin descripción'}</dd></div></dl>
    <p className="fineprint">Hora reportada: {reading.observed_at} ({reading.timezone}). Solicitado: {fmt(data.requested.lat, 5)}, {fmt(data.requested.lon, 5)}; punto del proveedor: {fmt(reading.grid_point.lat, 5)}, {fmt(reading.grid_point.lon, 5)}. Consulta: {data.fetched_at_utc}.</p>
    {data.multiplier != null && <p><strong>Factor exploratorio: {fmt(data.multiplier, 4)}×.</strong> Aportes: {Object.entries(data.contributions ?? {}).map(([key, value]) => `${key} +${fmt(value * 100, 2)} %`).join(' · ')}.</p>}
    <p className="fineprint">La temperatura y la descripción son informativas: no se usan en el factor.</p>
  </div>
}
