import { PDFDocument, StandardFonts } from 'pdf-lib'
import { describe, expect, it } from 'vitest'

import { DEFAULT_STAMP_X, DEFAULT_STAMP_Y } from './layout'
import { applyOverlays } from './stamp'

describe('stamp overlay', () => {
  it('embeds the gram/date text without shrinking the page', async () => {
    const src = await PDFDocument.create()
    const page = src.addPage([595.28, 841.89])
    const font = await src.embedFont(StandardFonts.Helvetica)
    page.drawText('TEST-REZEPT-0001', { x: 30, y: 800, size: 12, font })
    const bytes = await src.save()
    const stamped = await applyOverlays(bytes, [
      {
        id: 'a',
        pageIndex: 0,
        x: DEFAULT_STAMP_X,
        y: DEFAULT_STAMP_Y,
        grams: 25,
        when: new Date('2026-09-29T12:00:00Z'),
      },
    ])
    expect(stamped.byteLength).toBeGreaterThan(80)
    const out = await PDFDocument.load(stamped)
    expect(out.getPageCount()).toBe(1)
    expect(out.getPage(0).getSize().height).toBeCloseTo(841.89, 1)
  })
})
