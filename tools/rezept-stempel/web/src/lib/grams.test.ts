import { describe, expect, it } from 'vitest'

import { clampGrams, DEFAULT_GRAMS, MAX_GRAMS, MIN_GRAMS, STEP_GRAMS, stepGrams } from './grams'

describe('grams', () => {
  it('starts at 25 and stays on the 5 g ladder', () => {
    expect(DEFAULT_GRAMS).toBe(25)
    expect(clampGrams(27)).toBe(25)
    expect(clampGrams(28)).toBe(30)
    expect(clampGrams(0)).toBe(MIN_GRAMS)
    expect(clampGrams(999)).toBe(MAX_GRAMS)
  })

  it('steps by 5 and clamps at 5 and 100', () => {
    expect(stepGrams(25, 1)).toBe(30)
    expect(stepGrams(25, -1)).toBe(20)
    expect(stepGrams(MIN_GRAMS, -1)).toBe(MIN_GRAMS)
    expect(stepGrams(MAX_GRAMS, 1)).toBe(MAX_GRAMS)
    expect(STEP_GRAMS).toBe(5)
  })
})
