import { describe, expect, it } from 'vitest'

import { filenameTimestamp, overlayDateText, stampedFileName, stampText } from './dates'

const noonUtc = new Date('2026-09-29T12:00:00Z')

describe('dates', () => {
  it('formats overlay date and filename in Europe/Berlin', () => {
    expect(overlayDateText(noonUtc)).toBe('29.09.2026')
    expect(filenameTimestamp(noonUtc)).toBe('2026-09-29_1400')
    expect(stampText(25, noonUtc)).toBe('- 25g 29.09.2026')
  })

  it('never uses the original filename', () => {
    const name = stampedFileName('TEST-REZEPT-0001.pdf', noonUtc)
    expect(name).toBe('TEST-REZEPT-0001_2026-09-29_1400.pdf')
    expect(name.toLowerCase()).not.toBe('TEST-REZEPT-0001.pdf'.toLowerCase())
  })
})
