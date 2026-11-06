export const fmt = (value: number | null | undefined, digits = 2) => value == null
  ? 'No disponible' : value.toLocaleString('es-PE', { maximumFractionDigits: digits })
