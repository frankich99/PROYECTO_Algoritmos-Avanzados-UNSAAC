import { useState } from 'react'
import type { InstanceSpec } from './api'

type Profile = NonNullable<InstanceSpec['generator']>
export type GeneratorDraft = { profile: Profile; seed: string; nodes: string; rows: string; cols: string }
export const initialGenerator: GeneratorDraft = { profile: 'random', seed: '12', nodes: '30', rows: '5', cols: '5' }
const hints: Record<Profile, string> = {
  random: 'Red local aleatoria con pesos sintéticos.', grid: 'Filas × columnas = vértices; cada nodo se conecta con sus vecinos.',
  sparse: 'Pocas aristas por vértice, aproximadamente E = 4V.', dense: 'Más conexiones al crecer V, aproximadamente E = 0,08V(V−1).',
}
export function generatorSpec(draft: GeneratorDraft): InstanceSpec {
  const integer = (raw: string, name: string, min: number, max: number) => {
    const value = Number(raw)
    if (!/^\d+$/.test(raw) || !Number.isSafeInteger(value) || value < min || value > max)
      throw new Error(`${name}: introduce un entero entre ${min} y ${max}.`)
    return value
  }
  const seed = integer(draft.seed, 'Semilla', 0, 2147483647)
  if (draft.profile === 'grid') {
    const rows = integer(draft.rows, 'Filas', 1, 30), cols = integer(draft.cols, 'Columnas', 1, 30)
    if (rows * cols < 2) throw new Error('La cuadrícula necesita al menos dos vértices.')
    return { kind: 'generated', generator: 'grid', seed, rows, cols }
  }
  return { kind: 'generated', generator: draft.profile, seed, nodes: integer(draft.nodes, 'Vértices', 2, 500) }
}

export default function InstanceGenerator({ onApply }: { onApply: (spec: InstanceSpec) => void }) {
  const [draft, setDraft] = useState(initialGenerator)
  const [error, setError] = useState('')
  const update = (field: keyof GeneratorDraft, value: string) => { setDraft(old => ({ ...old, [field]: value })); setError('') }
  return <div className="editor-box">
    <p className="fineprint">Ejemplo precargado y editable. Una semilla reproduce la misma red; los pesos son costos abstractos, no metros ni segundos.</p>
    <label>Perfil<select value={draft.profile} onChange={event => update('profile', event.target.value)}>
      <option value="random">Red local aleatoria</option><option value="grid">Cuadrícula</option><option value="sparse">Disperso</option><option value="dense">Denso</option>
    </select></label><p className="fineprint" role="status">{hints[draft.profile]}</p>
    <label>Semilla<input type="number" min="0" max="2147483647" step="1" value={draft.seed} onChange={event => update('seed', event.target.value)} /></label>
    {draft.profile === 'grid' ? <div className="two-fields"><label>Filas<input type="number" min="1" max="30" step="1" value={draft.rows} onChange={event => update('rows', event.target.value)} /></label>
      <label>Columnas<input type="number" min="1" max="30" step="1" value={draft.cols} onChange={event => update('cols', event.target.value)} /></label></div> :
      <label>Vértices<input type="number" min="2" max="500" step="1" value={draft.nodes} onChange={event => update('nodes', event.target.value)} /></label>}
    <button type="button" className="primary" onClick={() => { try { onApply(generatorSpec(draft)) } catch (reason) { setError(reason instanceof Error ? reason.message : 'Parámetros inválidos.') } }}>Generar y abrir Rutas</button>
    {error && <p className="error" role="alert">{error}</p>}
  </div>
}
