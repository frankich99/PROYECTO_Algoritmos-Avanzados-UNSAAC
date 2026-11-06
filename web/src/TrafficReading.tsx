import type { Condition, TrafficFlow } from './api'
import { fmt } from './format'

export default function TrafficReading({ flow, requested, fetchedAt }: { flow: TrafficFlow; requested: Condition['requested']; fetchedAt: string }) {
  return <div className="observation"><h3>TomTom: segmento cercano al punto</h3>
    <dl className="reading-grid"><div><dt>Velocidad actual</dt><dd>{fmt(flow.current_speed_kmh, 1)} km/h</dd></div>
      <div><dt>Flujo libre</dt><dd>{fmt(flow.free_flow_speed_kmh, 1)} km/h</dd></div>
      <div><dt>Relación estimada</dt><dd>{fmt(flow.multiplier, 4)}×</dd></div>
      <div><dt>Confianza informada</dt><dd>{flow.confidence == null ? 'No informada' : fmt(flow.confidence, 2)}</dd></div>
      <div><dt>Cierre del segmento</dt><dd>{flow.road_closure == null ? 'No informado' : flow.road_closure ? 'Sí' : 'No'}</dd></div></dl>
    <p className="fineprint">Consulta: {fetchedAt}. Punto solicitado: {fmt(requested.lat, 5)}, {fmt(requested.lon, 5)}. No representa otras calles.</p>
  </div>
}
