import { describe, expect, it } from 'vitest'

import { stepGrams } from './grams'
import { DEFAULT_STAMP_X, DEFAULT_STAMP_Y, RX_ROW_TOPS } from './layout'
import { createOverlay, hitTestOverlay, stepSelectedOverlayGrams, updateSelectedGrams } from './overlays'

const when = new Date('2026-09-29T12:00:00Z')

function stamp(id: string, grams: number, x = DEFAULT_STAMP_X, y = DEFAULT_STAMP_Y) {
  return createOverlay({ id, pageIndex: 0, x, y, grams, when })
}

describe('per-stamp grams', () => {
  it('keeps stamp A at 25g when B is selected and wheeled to 40g', () => {
    const a = stamp('a', 25, 200, RX_ROW_TOPS[0] + 12)
    const b = stamp('b', 25, 200, RX_ROW_TOPS[1] + 12)
    let overlays = [a, b]
    const selectedId = 'b'
    for (let step = 0; step < 3; step += 1) {
      const selected = overlays.find((overlay) => overlay.id === selectedId)
      expect(selected).toBeDefined()
      overlays = updateSelectedGrams(overlays, selectedId, stepGrams(selected?.grams ?? 0, 1), when)
    }
    expect(overlays.map((item) => ({ id: item.id, grams: item.grams }))).toEqual([
      { id: 'a', grams: 25 },
      { id: 'b', grams: 40 },
    ])
    expect(a.grams).toBe(25)
  })

  it('does not change placed stamps when nothing is selected', () => {
    const a = stamp('a', 25)
    const b = stamp('b', 30)
    const next = updateSelectedGrams([a, b], null, 40, when)
    expect(next[0].grams).toBe(25)
    expect(next[1].grams).toBe(30)
  })

  it('never writes the new grams onto every overlay', () => {
    const overlays = [stamp('a', 25), stamp('b', 25), stamp('c', 25)]
    const next = updateSelectedGrams(overlays, 'c', 100, when)
    expect(next.filter((item) => item.grams === 25).map((item) => item.id)).toEqual(['a', 'b'])
    expect(next.find((item) => item.id === 'c')?.grams).toBe(100)
  })

  it('wheels only the selected stamp from a custom 17g value', () => {
    const a = stamp('a', 25)
    const b = stamp('b', 17)
    const next = stepSelectedOverlayGrams([a, b], 'b', 1, when)
    expect(next.find((item) => item.id === 'a')?.grams).toBe(25)
    expect(next.find((item) => item.id === 'b')?.grams).toBe(20)
  })
})

describe('hit test', () => {
  it('selects the topmost stamp at a point', () => {
    const a = stamp('a', 25, 200, 252)
    const b = stamp('b', 40, 200, 310)
    expect(hitTestOverlay([a, b], 0, 210, 252)?.id).toBe('a')
    expect(hitTestOverlay([a, b], 0, 210, 310)?.id).toBe('b')
    expect(hitTestOverlay([a, b], 0, 40, 80)).toBeNull()
  })
})
