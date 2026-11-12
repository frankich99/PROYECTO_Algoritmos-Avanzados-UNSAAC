import { expect, it } from 'vitest'
import { experimentInput } from '../src/experimentInput'

it('preserva semilla cero, tamaños y repeticiones explícitas', () => {
  expect(experimentInput('sparse', '5, 30, 60, 200', '0', '5')).toEqual({ profile: 'sparse', sizes: [5, 30, 60, 200], seed: 0, runs: 5 })
})
it.each(['', '30,no', '0,30', '4', '30,30', '30,40,50,60,70', '2.5', 'Infinity', '201', '501'])('rechaza tamaños adversos %s', sizes => {
  expect(() => experimentInput('dense', sizes, '42', '5')).toThrow()
})
it.each(['', '-1', '1', '11', '3.5'])('no sustituye repeticiones inválidas %s', runs => {
  expect(() => experimentInput('sparse', '30', '42', runs)).toThrow('Repeticiones')
})
