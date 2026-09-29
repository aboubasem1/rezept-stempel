/** Typical A4 Kassenrezept geometry in PDF points (top-left origin, like the print layout). */

export const PAGE_WIDTH = 595.28
export const PAGE_HEIGHT = 841.89

export const STAMP_FONTSIZE = 11
export const STAMP_PAD_X = 2.4
export const STAMP_PAD_Y = 1.4
export const STAMP_ASCENT = STAMP_FONTSIZE * 0.8
export const STAMP_DESCENT = STAMP_FONTSIZE * 0.22

export const RX_ROW_TOPS = [240.0, 298.2, 356.4] as const
export const RX_ROW_HEIGHT = 46.6
export const DEFAULT_STAMP_X = 198.0
export const DEFAULT_STAMP_Y = RX_ROW_TOPS[0] + 12.0

export type Overlay = {
  id: string
  pageIndex: number
  x: number
  y: number
  grams: number
  when: Date
}

export function snapClickToRxRow(clickY: number): number | null {
  for (const top of RX_ROW_TOPS) {
    if (top - 4 <= clickY && clickY <= top + RX_ROW_HEIGHT + 4) {
      return top + 12
    }
  }
  return null
}

export function clickToBaseline(clickX: number, clickY: number): { x: number; y: number } {
  const snapped = snapClickToRxRow(clickY)
  if (snapped !== null) {
    return { x: clickX, y: snapped }
  }
  return { x: clickX, y: clickY + (STAMP_ASCENT - STAMP_DESCENT) / 2 }
}

export function defaultStampPoint(): { x: number; y: number } {
  return { x: DEFAULT_STAMP_X, y: DEFAULT_STAMP_Y }
}

export function overlayRect(
  x: number,
  y: number,
  textWidth: number,
): { x0: number; y0: number; x1: number; y1: number } {
  return {
    x0: x - STAMP_PAD_X,
    y0: y - STAMP_ASCENT - STAMP_PAD_Y,
    x1: x + textWidth + STAMP_PAD_X,
    y1: y + STAMP_DESCENT + STAMP_PAD_Y,
  }
}
