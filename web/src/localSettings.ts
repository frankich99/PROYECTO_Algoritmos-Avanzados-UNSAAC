import type { Condition } from './api'

const keysName = 'cusco-provider-keys-v1'
const readingName = 'cusco-weather-reading-v1'

export type ProviderKeys = { openweathermap: string; tomtom: string }
export const DEFAULT_KEYS: ProviderKeys = {
  openweathermap: 'e0cd9ce83348676c0ef4a46aa041e194',
  tomtom: 'jFzYvp3UJmio3PeiTkKQCBqebIFhKHMO'
}
export const emptyKeys: ProviderKeys = { ...DEFAULT_KEYS }

export function readKeys(): ProviderKeys {
  try {
    const raw = localStorage.getItem(keysName)
    if (!raw) {
      saveKeys(DEFAULT_KEYS)
      return { ...DEFAULT_KEYS }
    }
    const value = JSON.parse(raw) as Partial<ProviderKeys>
    return {
      openweathermap: typeof value.openweathermap === 'string' && value.openweathermap.trim()
        ? value.openweathermap.slice(0, 200)
        : DEFAULT_KEYS.openweathermap,
      tomtom: typeof value.tomtom === 'string' && value.tomtom.trim()
        ? value.tomtom.slice(0, 200)
        : DEFAULT_KEYS.tomtom
    }
  } catch { return { ...DEFAULT_KEYS } }
}

export function saveKeys(keys: ProviderKeys): boolean {
  try { localStorage.setItem(keysName, JSON.stringify(keys)); return true }
  catch { return false }
}

export function forgetKeys() {
  try { localStorage.removeItem(keysName) } catch { /* Almacenamiento bloqueado por el navegador. */ }
}

export function readWeather(): Condition | null {
  try {
    const value = JSON.parse(localStorage.getItem(readingName) ?? 'null') as Condition | null
    const reading = value?.observation
    return reading && typeof value?.multiplier === 'number' && Number.isFinite(value.multiplier) &&
      Number.isFinite(value.requested?.lat) && Number.isFinite(value.requested?.lon) &&
      Number.isFinite(reading.grid_point?.lat) && Number.isFinite(reading.grid_point?.lon) &&
      Number.isFinite(reading.temperature_c) && Number.isFinite(reading.precipitation_mm) &&
      Number.isFinite(reading.visibility_m) && Number.isFinite(reading.wind_gusts_kmh) &&
      Number.isFinite(reading.relative_humidity_pct) &&
      typeof reading.source === 'string' && typeof reading.observed_at === 'string' &&
      typeof reading.timezone === 'string'
      ? value : null
  } catch { return null }
}

export function saveWeather(value: Condition): boolean {
  if (!value.observation || typeof value.multiplier !== 'number') return false
  try { localStorage.setItem(readingName, JSON.stringify(value)); return true }
  catch { return false }
}

export function forgetWeather() {
  try { localStorage.removeItem(readingName) } catch { /* Almacenamiento bloqueado por el navegador. */ }
}
