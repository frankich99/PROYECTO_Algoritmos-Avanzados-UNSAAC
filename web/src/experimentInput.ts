export function experimentInput(profile: 'sparse' | 'dense', sizes: string, seed: string, runs: string) {
  const integer = (raw: string, label: string, min: number, max: number) => {
    if (!/^\d+$/.test(raw.trim()) || !Number.isSafeInteger(Number(raw)) || Number(raw) < min || Number(raw) > max)
      throw new Error(`${label}: introduce un entero entre ${min} y ${max}.`)
    return Number(raw)
  }
  const tokens = sizes.split(',')
  if (tokens.length > 4) throw new Error('Usa como máximo cuatro tamaños.')
  const parsed = tokens.map(token => integer(token, 'Tamaño', 5, 200))
  if (new Set(parsed).size !== parsed.length) throw new Error('Los tamaños no deben repetirse.')
  return { profile, sizes: parsed, seed: integer(seed, 'Semilla', 0, 2147483647), runs: integer(runs, 'Repeticiones', 2, 10) }
}
