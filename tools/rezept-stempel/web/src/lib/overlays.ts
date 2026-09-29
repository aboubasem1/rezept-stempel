import { stampText } from './dates'
import { overlayRect, STAMP_FONTSIZE, type Overlay } from './layout'

export function createOverlay(input: Omit<Overlay, 'id'> & { id?: string }): Overlay {
  return {
    id: input.id ?? crypto.randomUUID(),
    pageIndex: input.pageIndex,
    x: input.x,
    y: input.y,
    grams: input.grams,
    when: input.when,
  }
}

export function updateSelectedGrams(
  overlays: Overlay[],
  selectedId: string | null,
  grams: number,
  when: Date = new Date(),
): Overlay[] {
  if (selectedId === null) {
    return overlays
  }
  return overlays.map((overlay) =>
    overlay.id === selectedId ? { ...overlay, grams, when } : overlay,
  )
}

export function estimateStampWidth(text: string): number {
  return text.length * STAMP_FONTSIZE * 0.52
}

export function hitTestOverlay(
  overlays: Overlay[],
  pageIndex: number,
  x: number,
  y: number,
): Overlay | null {
  for (let index = overlays.length - 1; index >= 0; index -= 1) {
    const overlay = overlays[index]
    if (overlay.pageIndex !== pageIndex) continue
    const box = overlayRect(overlay.x, overlay.y, estimateStampWidth(stampText(overlay.grams, overlay.when)))
    if (x >= box.x0 && x <= box.x1 && y >= box.y0 && y <= box.y1) {
      return overlay
    }
  }
  return null
}
