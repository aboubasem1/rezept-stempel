import { PDFDocument, StandardFonts, rgb } from 'pdf-lib'

import { copyBytes } from './buffer'
import { stampText } from './dates'
import { overlayRect, STAMP_FONTSIZE, type Overlay } from './layout'

const STAMP_COLOR = rgb(0.05, 0.14, 0.4)

export async function applyOverlays(
  source: ArrayBuffer | Uint8Array,
  overlays: Overlay[],
): Promise<Uint8Array> {
  const doc = await PDFDocument.load(copyBytes(source), { ignoreEncryption: false })
  const font = await doc.embedFont(StandardFonts.HelveticaBold)

  for (const overlay of overlays) {
    const page = doc.getPages()[overlay.pageIndex]
    if (!page) {
      throw new Error(`Seite ${overlay.pageIndex + 1} fehlt in der PDF.`)
    }
    const { height } = page.getSize()
    const text = stampText(overlay.grams, overlay.when)
    const textWidth = font.widthOfTextAtSize(text, STAMP_FONTSIZE)
    const box = overlayRect(overlay.x, overlay.y, textWidth)
    page.drawRectangle({
      x: box.x0,
      y: height - box.y1,
      width: box.x1 - box.x0,
      height: box.y1 - box.y0,
      color: rgb(1, 1, 1),
    })
    page.drawText(text, {
      x: overlay.x,
      y: height - overlay.y,
      size: STAMP_FONTSIZE,
      font,
      color: STAMP_COLOR,
    })
  }

  return doc.save()
}
