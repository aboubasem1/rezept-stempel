import { getDocument, GlobalWorkerOptions } from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

import { copyBytes } from './buffer'
import { stampText } from './dates'
import {
  clickToBaseline,
  defaultStampPoint,
  overlayRect,
  STAMP_FONTSIZE,
  type Overlay,
} from './layout'

GlobalWorkerOptions.workerSrc = workerUrl

const PDFJS_ASSETS = `${import.meta.env.BASE_URL}pdfjs/`

export async function loadPdf(data: ArrayBuffer) {
  return getDocument({
    data: copyBytes(data),
    cMapUrl: `${PDFJS_ASSETS}cmaps/`,
    cMapPacked: true,
    standardFontDataUrl: `${PDFJS_ASSETS}standard_fonts/`,
    wasmUrl: `${PDFJS_ASSETS}wasm/`,
    iccUrl: `${PDFJS_ASSETS}iccs/`,
  }).promise
}

export async function renderPageToCanvas(
  data: ArrayBuffer,
  pageIndex: number,
  canvas: HTMLCanvasElement,
  cssWidth: number,
): Promise<{ scale: number; width: number; height: number }> {
  const pdf = await loadPdf(data)
  const page = await pdf.getPage(pageIndex + 1)
  const base = page.getViewport({ scale: 1 })
  const scale = cssWidth / base.width
  const viewport = page.getViewport({ scale })
  canvas.width = Math.floor(viewport.width)
  canvas.height = Math.floor(viewport.height)
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('Canvas nicht verfügbar.')
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0)
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  await page.render({ canvasContext: ctx, viewport, canvas }).promise
  return { scale, width: base.width, height: base.height }
}

export function drawStamps(
  ctx: CanvasRenderingContext2D,
  scale: number,
  overlays: Overlay[],
  pageIndex: number,
  grams: number,
  ghost: { x: number; y: number } | null,
): void {
  ctx.save()
  for (const overlay of overlays) {
    if (overlay.pageIndex !== pageIndex) continue
    paintStamp(ctx, scale, overlay.x, overlay.y, stampText(overlay.grams, overlay.when), '#0d245c')
  }
  if (ghost) {
    paintStamp(ctx, scale, ghost.x, ghost.y, stampText(grams), '#6b7280')
  } else if (!overlays.some((item) => item.pageIndex === pageIndex)) {
    const point = defaultStampPoint()
    paintStamp(ctx, scale, point.x, point.y, stampText(grams), '#9aa3af')
  }
  ctx.restore()
}

function paintStamp(
  ctx: CanvasRenderingContext2D,
  scale: number,
  x: number,
  y: number,
  text: string,
  fill: string,
): void {
  const fontPx = Math.max(9, Math.round(STAMP_FONTSIZE * scale))
  ctx.font = `bold ${fontPx}px Helvetica, Arial, sans-serif`
  const width = ctx.measureText(text).width / scale
  const box = overlayRect(x, y, width)
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(box.x0 * scale, box.y0 * scale, (box.x1 - box.x0) * scale, (box.y1 - box.y0) * scale)
  ctx.fillStyle = fill
  ctx.textBaseline = 'alphabetic'
  ctx.fillText(text, x * scale, y * scale)
}

export function canvasClickToPdf(
  event: { clientX: number; clientY: number },
  canvas: HTMLCanvasElement,
  pdfWidth: number,
  pdfHeight: number,
): { x: number; y: number } {
  const rect = canvas.getBoundingClientRect()
  const x = ((event.clientX - rect.left) / rect.width) * pdfWidth
  const y = ((event.clientY - rect.top) / rect.height) * pdfHeight
  return clickToBaseline(x, y)
}
