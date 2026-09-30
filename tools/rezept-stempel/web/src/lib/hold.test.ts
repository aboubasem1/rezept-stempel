import { describe, expect, it } from 'vitest'

import { clampCustomGrams, parseCustomGrams } from './grams'
import { shouldOpenCustomGrams } from './hold'
import { DEFAULT_STAMP_X, DEFAULT_STAMP_Y } from './layout'
import { createOverlay, updateSelectedGrams } from './overlays'

const when = new Date('2026-09-29T12:00:00Z')

describe('right-click hold threshold', () => {
  it('does not open for a short right-click', () => {
    expect(shouldOpenCustomGrams(0)).toBe(false)
    expect(shouldOpenCustomGrams(999)).toBe(false)
  })

  it('opens only after a hold of at least 1 second', () => {
    expect(shouldOpenCustomGrams(1000)).toBe(true)
    expect(shouldOpenCustomGrams(1500)).toBe(true)
  })
})

describe('custom grams on selected stamp', () => {
  it('sets 17g on B and leaves A at 25g without snapping to 5', () => {
    const a = createOverlay({
      id: 'a',
      pageIndex: 0,
      x: DEFAULT_STAMP_X,
      y: DEFAULT_STAMP_Y,
      grams: 25,
      when,
    })
    const b = createOverlay({
      id: 'b',
      pageIndex: 0,
      x: DEFAULT_STAMP_X,
      y: DEFAULT_STAMP_Y + 58,
      grams: 25,
      when,
    })
    const custom = parseCustomGrams('17')
    expect(custom).toBe(17)
    expect(clampCustomGrams(17)).toBe(17)
    const next = updateSelectedGrams([a, b], 'b', custom ?? 0, when)
    expect(next.find((item) => item.id === 'a')?.grams).toBe(25)
    expect(next.find((item) => item.id === 'b')?.grams).toBe(17)
  })
})
