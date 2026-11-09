import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import EvidencePage from '../src/EvidencePage'

const fixture = {
  schema_version: 1, generated_at_utc: '2026-11-06T12:00:00Z', git: { head: 'abc1234', branch: 'fixture', dirty: true, github_head: null, github_checked_at: null },
  tests: { python: { passed: 1, failed: 0, skipped: 0, seconds: 1, modules: [{ name: 'test_fixture', passed: 1, failed: 0, skipped: 0 }] }, web: { passed: 1, failed: 0, total: 1 } },
  pilot: { generated_at_utc: '2026-11-06T12:00:00Z', protocol: {}, environment: { python: 'fixture', platform: 'fixture' }, rows: [] },
  contributors: [{ name: 'Autor de fixture', count: 1 }], commits: [{ hash: 'abc1234', date: '2026-11-06', author: 'Autor de fixture', subject: 'Cambio de prueba' }],
}
afterEach(() => vi.unstubAllGlobals())
it('muestra carga sin inventar conteos', () => {
  vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
  render(<EvidencePage onMethod={vi.fn()} />)
  expect(screen.getByRole('status')).toHaveTextContent('Cargando')
  expect(screen.queryByText(/Python: .* aprobadas/)).toBeNull()
})
it('mapea los siete productos y enlaza la complejidad', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => fixture }))
  const method = vi.fn()
  render(<EvidencePage onMethod={method} />)
  await screen.findByText('Cambio de prueba')
  expect(screen.getByRole('link', { name: 'Pruebas automatizadas' })).toHaveAttribute('href', '#entrega-pruebas')
  await userEvent.click(screen.getByRole('button', { name: 'Ver análisis de complejidad y modelo' }))
  expect(method).toHaveBeenCalledOnce()
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Filtrar por rama' }), 'Autor de fixture')
  expect(screen.getByText('Cambio de prueba')).toBeInTheDocument()
  expect(screen.getByText(/no un porcentaje de cobertura/)).toBeInTheDocument()
})
it('permite reintentar una carga fallida y no anuncia éxito', async () => {
  const fetch = vi.fn().mockRejectedValueOnce(new Error('sin red')).mockResolvedValueOnce({ ok: true, json: async () => fixture })
  vi.stubGlobal('fetch', fetch)
  render(<EvidencePage onMethod={vi.fn()} />)
  expect(await screen.findByRole('alert')).toHaveTextContent('sin red')
  await userEvent.click(screen.getByRole('button', { name: 'Reintentar lectura' }))
  await screen.findByText('Cambio de prueba')
  expect(fetch).toHaveBeenCalledTimes(2)
})
it('rechaza un JSON que no acredita pruebas ni piloto', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ schema_version: 1 }) }))
  render(<EvidencePage onMethod={vi.fn()} />)
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Formato de evidencia no válido'))
})
