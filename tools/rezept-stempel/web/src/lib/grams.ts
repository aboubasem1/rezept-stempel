export const MIN_GRAMS = 5
export const MAX_GRAMS = 100
export const STEP_GRAMS = 5
export const DEFAULT_GRAMS = 25

export function clampGrams(value: number): number {
  const snapped = Math.round(value / STEP_GRAMS) * STEP_GRAMS
  return Math.max(MIN_GRAMS, Math.min(MAX_GRAMS, snapped))
}

export function stepGrams(current: number, direction: number): number {
  if (direction === 0) {
    return clampGrams(current)
  }
  const step = direction > 0 ? STEP_GRAMS : -STEP_GRAMS
  return clampGrams(clampGrams(current) + step)
}
