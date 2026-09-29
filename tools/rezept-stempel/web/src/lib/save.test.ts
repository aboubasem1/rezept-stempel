import { describe, expect, it } from 'vitest'

import { describeSave, type SaveOutcome } from './save'

describe('save copy', () => {
  it('explains filesystem, download, and cancel', () => {
    const cases: SaveOutcome[] = [
      { kind: 'filesystem', name: 'TEST-REZEPT-0001_2026-09-29_1400.pdf' },
      { kind: 'download', name: 'TEST-REZEPT-0001_2026-09-29_1400.pdf' },
      { kind: 'cancelled' },
    ]
    expect(describeSave(cases[0])).toContain('neben dem Original')
    expect(describeSave(cases[1])).toContain('Download')
    expect(describeSave(cases[2])).toContain('abgebrochen')
  })
})
