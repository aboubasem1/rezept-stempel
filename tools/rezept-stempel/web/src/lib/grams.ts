export const MIN_GRAMS = 5
export const MAX_GRAMS = 100
export const STEP_GRAMS = 5
export const DEFAULT_GRAMS = 25

export function clampGrams(value: number): number {
  const snapped = Math.round(value / STEP_GRAMS) * STEP_GRAMS
  return Math.max(MIN_GRAMS, Math.min(MAX_GRAMS, snapped))
}

/** Clamp to min/max without snapping onto the 5 g ladder. */
export function clampCustomGrams(value: number): number {
  if (!Number.isFinite(value)) {
    return MIN_GRAMS
  }
  return Math.max(MIN_GRAMS, Math.min(MAX_GRAMS, Math.round(value)))
}

export function parseCustomGrams(raw: string): number | null {
  const normalized = raw.trim().replace(',', '.')
  if (normalized === '') {
    return null
  }
  const value = Number(normalized)
  if (!Number.isFinite(value)) {
    return null
  }
  return clampCustomGrams(value)
}

export function stepGrams(current: number, direction: number): number {
  if (direction === 0) {
    return clampGrams(current)
  }
  const step = direction > 0 ? STEP_GRAMS : -STEP_GRAMS
  return clampGrams(clampGrams(current) + step)
}
