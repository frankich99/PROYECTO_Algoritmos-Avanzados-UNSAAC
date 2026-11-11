import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import GraphView from '../src/GraphView'
import InstanceGenerator, { generatorSpec, initialGenerator } from '../src/InstanceGenerator'
import ComplexityTable from '../src/ComplexityTable'
import type { Preview, RouteResponse } from '../src/api'

vi.mock('maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url', () => ({ default: 'worker.js' }))

const preview: Preview = { name: 'Fixture sintético', nodes: 4, edges: 4, ids: ['A', 'B', 'C', 'D'], coords: {},
  geographic: false, display_edges: [['A', 'B', 4], ['B', 'C', 2], ['A', 'C', 10], ['C', 'D', 100]], display_limited: false, metric: 'weight' }
const edge = (from: string, to: string, cost: number) => ({ from, to, cost, length_m: null, time_sec: null, street: null })
const result: RouteResponse['result'] = { algorithm: 'dijkstra', queue: 'binary_heap', cost: 6, path: ['A', 'B', 'C'], edges: [edge('A', 'B', 4), edge('B', 'C', 2)],
  length_m: null, time_sec: null, path_geometry: [], expanded: 3, relaxations: 3, decrease_key: 2, elapsed_ms_single_run: 0 }
const route: RouteResponse = { network: preview.name, coverage: 'custom', counts: { nodes: 4, edges: 4 }, source: 'A', target: 'C', metric: 'time', unit: 'peso',
  source_snap: null, target_snap: null, result, comparisons: [result], path_coords: [], scenario: { kind: 'none', factor: 1 }, warning: null }
const graphProps = { preview, route, onPick: vi.fn(), pick: 'source' as const, onPickMode: vi.fn(), mapRequested: 0, sourcePoint: null, targetPoint: null }

describe('Capas del grafo', () => {
  it('muestra las cinco casillas y cambia pesos, nombres, aristas y nodos', async () => {
    const user = userEvent.setup()
    const { container } = render(<GraphView {...graphProps} />)
    expect(screen.getByRole('group', { name: 'Mostrar en el grafo' })).toBeInTheDocument()
    expect(container.querySelectorAll('svg line')).toHaveLength(4)
    await user.click(screen.getByRole('checkbox', { name: 'Pesos', exact: true }))
    expect(container.querySelectorAll('svg rect')).toHaveLength(0)
    await user.click(screen.getByRole('checkbox', { name: 'Nombres / ID' }))
    expect(container.querySelectorAll('svg text')).toHaveLength(0)
    await user.click(screen.getByRole('checkbox', { name: 'Aristas de la red' }))
    expect(container.querySelectorAll('svg line')).toHaveLength(2)
    await user.click(screen.getByRole('checkbox', { name: 'Nodos', exact: true }))
    expect(container.querySelectorAll('svg circle')).toHaveLength(2)
  })
  it('solo recorrido elimina los nodos ajenos y conserva las preferencias al volver', async () => {
    const user = userEvent.setup()
    const { container } = render(<GraphView {...graphProps} />)
    await user.click(screen.getByRole('checkbox', { name: 'Solo recorrido' }))
    expect(container.querySelectorAll('svg line')).toHaveLength(2)
    expect(container.querySelectorAll('svg circle')).toHaveLength(3)
    await user.click(screen.getByRole('checkbox', { name: 'Solo recorrido' }))
    expect(container.querySelectorAll('svg line')).toHaveLength(4)
  })
  it('sin ruta deshabilita solo recorrido y limpia el modo al invalidar el resultado', async () => {
    const { rerender } = render(<GraphView {...graphProps} />)
    await userEvent.click(screen.getByRole('checkbox', { name: 'Solo recorrido' }))
    rerender(<GraphView {...graphProps} route={null} />)
    await waitFor(() => expect(screen.getByRole('checkbox', { name: 'Solo recorrido' })).not.toBeChecked())
    expect(screen.getByRole('checkbox', { name: 'Solo recorrido' })).toBeDisabled()
  })
  it('explica el estado vacío sin dibujar nodos ficticios', () => {
    const { container } = render(<GraphView {...graphProps} preview={null} route={null} />)
    expect(screen.getByText('Valida una instancia para ver su red.')).toBeInTheDocument()
    expect(container.querySelector('svg')).not.toBeInTheDocument()
  })
  it('trata los IDs adversos como texto, no HTML', () => {
    const id = '<img src=x onerror=alert(1)>'
    const { container } = render(<GraphView {...graphProps} route={null} preview={{ ...preview, ids: [id], nodes: 1, display_edges: [] }} />)
    expect(container.querySelector('img')).toBeNull()
    expect(container.querySelector('svg')?.textContent).toContain(id)
  })
})

describe('Generador editable', () => {
  it('precarga datos reales del formulario y preserva la semilla cero', async () => {
    const apply = vi.fn()
    render(<InstanceGenerator onApply={apply} />)
    expect(screen.getByRole('spinbutton', { name: 'Vértices' })).toHaveValue(30)
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Semilla' }), { target: { value: '0' } })
    await userEvent.click(screen.getByRole('button', { name: 'Generar y abrir Rutas' }))
    expect(apply).toHaveBeenCalledWith({ kind: 'generated', generator: 'random', nodes: 30, seed: 0 })
  })
  it('cambia a cuadrícula sin modificar la red activa hasta aplicar', async () => {
    const apply = vi.fn()
    render(<InstanceGenerator onApply={apply} />)
    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Perfil' }), 'grid')
    expect(screen.getByRole('spinbutton', { name: 'Filas' })).toHaveValue(5)
    expect(screen.queryByRole('spinbutton', { name: 'Vértices' })).toBeNull()
    expect(apply).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Generar y abrir Rutas' }))
    expect(apply).toHaveBeenCalledWith({ kind: 'generated', generator: 'grid', rows: 5, cols: 5, seed: 12 })
  })
  it('muestra error en vez de sustituir silenciosamente un valor vacío', async () => {
    const apply = vi.fn()
    render(<InstanceGenerator onApply={apply} />)
    fireEvent.change(screen.getByRole('spinbutton', { name: 'Vértices' }), { target: { value: '' } })
    await userEvent.click(screen.getByRole('button', { name: 'Generar y abrir Rutas' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Vértices')
    expect(apply).not.toHaveBeenCalled()
  })
  it.each(['', '-1', '1.5', 'NaN', 'Infinity', '9007199254740992'])('rechaza semilla adversa %s', seed => {
    expect(() => generatorSpec({ ...initialGenerator, seed })).toThrow('Semilla')
  })
  it('rechaza una cuadrícula 1 por 1 y acepta el límite de 500 vértices', () => {
    expect(() => generatorSpec({ ...initialGenerator, profile: 'grid', rows: '1', cols: '1' })).toThrow('dos vértices')
    expect(generatorSpec({ ...initialGenerator, nodes: '500' }).nodes).toBe(500)
  })
})

it('presenta cotas de peor caso, amortizadas y memoria sin ganador universal', () => {
  render(<ComplexityTable />)
  expect(screen.getByText('O(E + V log V), amortizado')).toBeInTheDocument()
  expect(screen.getByText(/No se afirma una cota promedio/)).toBeInTheDocument()
})
