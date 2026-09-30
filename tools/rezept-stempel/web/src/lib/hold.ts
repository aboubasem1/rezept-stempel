export const CUSTOM_HOLD_MS = 1000

export function shouldOpenCustomGrams(heldMs: number): boolean {
  return heldMs >= CUSTOM_HOLD_MS
}
