import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type DragEvent,
  type MouseEvent,
} from 'react'

import { overlayDateText, stampText } from './lib/dates'
import { DEFAULT_GRAMS, MAX_GRAMS, MIN_GRAMS, STEP_GRAMS, stepGrams } from './lib/grams'
import { defaultStampPoint, type Overlay } from './lib/layout'
import { canvasClickToPdf, drawStamps, loadPdf, renderPageToCanvas } from './lib/pdf'
import { describeSave, saveStampedPdf } from './lib/save'
import { applyOverlays } from './lib/stamp'
import './App.css'

type OpenDoc = {
  id: string
  name: string
  bytes: ArrayBuffer
  handle: FileSystemFileHandle | null
  overlays: Overlay[]
  pageIndex: number
  pageCount: number
}

export default function App() {
  const [docs, setDocs] = useState<OpenDoc[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [grams, setGrams] = useState(DEFAULT_GRAMS)
  const [status, setStatus] = useState('Bereit. PDFs hierher ziehen oder über „PDF öffnen“ wählen.')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [dragging, setDragging] = useState(false)
  const pageCanvasRef = useRef<HTMLCanvasElement | null>(null)
  const stampCanvasRef = useRef<HTMLCanvasElement | null>(null)
  const stageRef = useRef<HTMLElement | null>(null)
  const scaleRef = useRef({ scale: 1, width: 595.28, height: 841.89 })
  const ghostRef = useRef<{ x: number; y: number } | null>(null)
  const gramsRef = useRef(grams)
  const docsRef = useRef(docs)
  const activeIdRef = useRef(activeId)

  gramsRef.current = grams
  docsRef.current = docs
  activeIdRef.current = activeId

  const active = docs.find((doc) => doc.id === activeId) ?? null

  const redrawStamps = useCallback((doc: OpenDoc | null) => {
    const canvas = stampCanvasRef.current
    const page = pageCanvasRef.current
    if (!canvas || !page) return
    canvas.width = page.width
    canvas.height = page.height
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    if (!doc) return
    const { scale } = scaleRef.current
    drawStamps(ctx, scale, doc.overlays, doc.pageIndex, gramsRef.current, ghostRef.current)
  }, [])

  useEffect(() => {
    const page = pageCanvasRef.current
    const doc = docsRef.current.find((item) => item.id === activeId) ?? null
    if (!doc || !page) {
      redrawStamps(null)
      return
    }
    let cancelled = false
    const cssWidth = Math.min(720, page.parentElement?.clientWidth || 720)
    const bytes = doc.bytes
    const pageIndex = doc.pageIndex
    setBusy(true)
    void renderPageToCanvas(bytes, pageIndex, page, cssWidth)
      .then((info) => {
        if (cancelled) return
        scaleRef.current = info
        const overlay = stampCanvasRef.current
        if (overlay) {
          overlay.width = page.width
          overlay.height = page.height
          overlay.style.width = `${page.clientWidth}px`
          overlay.style.height = `${page.clientHeight}px`
        }
        page.style.width = '100%'
        page.style.height = 'auto'
        const latest = docsRef.current.find((item) => item.id === activeId) ?? doc
        redrawStamps(latest)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'PDF konnte nicht gerendert werden.')
      })
      .finally(() => {
        if (!cancelled) setBusy(false)
      })
    return () => {
      cancelled = true
    }
  }, [activeId, active?.pageIndex, redrawStamps])

  useEffect(() => {
    redrawStamps(active)
  }, [active, redrawStamps, grams])

  const addFiles = useCallback(async (files: Array<{ file: File; handle: FileSystemFileHandle | null }>) => {
    const pdfs = files.filter((item) => item.file.name.toLowerCase().endsWith('.pdf'))
    if (pdfs.length === 0) {
      setError('Bitte eine oder mehrere PDF-Dateien ablegen.')
      return
    }
    setError(null)
    const opened: OpenDoc[] = []
    for (const item of pdfs) {
      try {
        const bytes = await item.file.arrayBuffer()
        const pdf = await loadPdf(bytes)
        opened.push({
          id: `${item.file.name}-${item.file.size}-${item.file.lastModified}-${crypto.randomUUID()}`,
          name: item.file.name,
          bytes,
          handle: item.handle,
          overlays: [],
          pageIndex: 0,
          pageCount: pdf.numPages,
        })
      } catch (err) {
        setError(
          err instanceof Error
            ? `„${item.file.name}“ konnte nicht geöffnet werden: ${err.message}`
            : `„${item.file.name}“ konnte nicht geöffnet werden.`,
        )
      }
    }
    if (opened.length === 0) return
    setDocs((current) => [...current, ...opened])
    setActiveId(opened[0].id)
    setStatus(
      opened.length === 1
        ? `Geöffnet: ${opened[0].name} — Klick setzt den Stempel.`
        : `${opened.length} PDFs geöffnet. Klick setzt den Stempel.`,
    )
  }, [])

  const onDrop = async (event: DragEvent<HTMLElement>) => {
    event.preventDefault()
    setDragging(false)
    const items = [...event.dataTransfer.items]
    const collected: Array<{ file: File; handle: FileSystemFileHandle | null }> = []
    for (const item of items) {
      if (item.kind !== 'file') continue
      const handle = item.getAsFileSystemHandle ? await item.getAsFileSystemHandle() : null
      if (handle && handle.kind === 'directory') continue
      const fileHandle = handle && handle.kind === 'file' ? (handle as FileSystemFileHandle) : null
      const file = fileHandle ? await fileHandle.getFile() : item.getAsFile()
      if (file) collected.push({ file, handle: fileHandle })
    }
    if (collected.length === 0 && event.dataTransfer.files.length > 0) {
      for (const file of event.dataTransfer.files) {
        collected.push({ file, handle: null })
      }
    }
    await addFiles(collected)
  }

  const openPicker = async () => {
    if (window.showOpenFilePicker) {
      try {
        const handles = await window.showOpenFilePicker({
          multiple: true,
          types: [{ description: 'PDF-Dateien', accept: { 'application/pdf': ['.pdf'] } }],
        })
        const collected = await Promise.all(
          handles.map(async (handle) => ({ file: await handle.getFile(), handle })),
        )
        await addFiles(collected)
        return
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === 'AbortError') return
      }
    }
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'application/pdf'
    input.multiple = true
    input.onchange = () => {
      const list = input.files
      if (!list) return
      void addFiles([...list].map((file) => ({ file, handle: null })))
    }
    input.click()
  }

  const openSample = async () => {
    try {
      const response = await fetch('/samples/TEST-REZEPT-0001.pdf')
      if (!response.ok) throw new Error('Musterdatei fehlt.')
      const blob = await response.blob()
      const file = new File([blob], 'TEST-REZEPT-0001.pdf', { type: 'application/pdf' })
      await addFiles([{ file, handle: null }])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Musterdatei konnte nicht geladen werden.')
    }
  }

  const patchDoc = (id: string, patch: Partial<OpenDoc> | ((doc: OpenDoc) => OpenDoc)) => {
    setDocs((current) =>
      current.map((doc) => {
        if (doc.id !== id) return doc
        return typeof patch === 'function' ? patch(doc) : { ...doc, ...patch }
      }),
    )
  }

  const placeStamp = (x: number, y: number) => {
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!current) {
      void openPicker()
      return
    }
    const overlay: Overlay = {
      pageIndex: current.pageIndex,
      x,
      y,
      grams: gramsRef.current,
      when: new Date(),
    }
    patchDoc(current.id, { overlays: [...current.overlays, overlay] })
    setStatus(`Stempel gesetzt: ${stampText(gramsRef.current)} — Mausrad ändert die Menge.`)
  }

  const onCanvasClick = (event: MouseEvent<HTMLCanvasElement>) => {
    const canvas = stampCanvasRef.current ?? pageCanvasRef.current
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!canvas || !current) {
      void openPicker()
      return
    }
    const { width, height } = scaleRef.current
    const point = canvasClickToPdf(event, canvas, width, height)
    placeStamp(point.x, point.y)
  }

  const onCanvasMove = (event: MouseEvent<HTMLCanvasElement>) => {
    const canvas = stampCanvasRef.current
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!canvas || !current) return
    const { width, height } = scaleRef.current
    ghostRef.current = canvasClickToPdf(event, canvas, width, height)
    redrawStamps(current)
  }

  const applyGrams = (next: number) => {
    setGrams(next)
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!current || current.overlays.length === 0) return
    const overlays = [...current.overlays]
    const last = overlays[overlays.length - 1]
    overlays[overlays.length - 1] = { ...last, grams: next, when: new Date() }
    patchDoc(current.id, { overlays })
  }

  const placeDefault = () => {
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!current) {
      void openPicker()
      return
    }
    const point = defaultStampPoint()
    const overlay: Overlay = {
      pageIndex: current.pageIndex,
      x: point.x,
      y: point.y,
      grams: gramsRef.current,
      when: new Date(),
    }
    const overlays = [...current.overlays]
    if (overlays.length > 0 && overlays[overlays.length - 1].pageIndex === current.pageIndex) {
      overlays[overlays.length - 1] = overlay
    } else {
      overlays.push(overlay)
    }
    patchDoc(current.id, { overlays })
    setStatus(`Stempel auf der ersten Rp-Zeile: ${stampText(gramsRef.current)}`)
  }

  const undo = () => {
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!current || current.overlays.length === 0) {
      setStatus('Kein Stempel zum Entfernen.')
      return
    }
    patchDoc(current.id, { overlays: current.overlays.slice(0, -1) })
    setStatus('Letzten Stempel entfernt.')
  }

  const save = async () => {
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!current) {
      setError('Bitte zuerst ein Rezept-PDF öffnen.')
      return
    }
    if (current.overlays.length === 0) {
      setError('Setzen Sie zuerst mit einem Klick mindestens einen Stempel.')
      return
    }
    setError(null)
    setBusy(true)
    try {
      const bytes = await applyOverlays(current.bytes, current.overlays)
      const outcome = await saveStampedPdf({
        originalName: current.name,
        sourceHandle: current.handle,
        bytes,
      })
      setStatus(describeSave(outcome))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Speichern fehlgeschlagen.')
    } finally {
      setBusy(false)
    }
  }

  const saveRef = useRef(save)
  const undoRef = useRef(undo)
  const placeDefaultRef = useRef(placeDefault)
  const applyGramsRef = useRef(applyGrams)
  saveRef.current = save
  undoRef.current = undo
  placeDefaultRef.current = placeDefault
  applyGramsRef.current = applyGrams

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target
      const onField =
        target instanceof HTMLElement && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')
      if (event.ctrlKey && event.key.toLowerCase() === 's') {
        event.preventDefault()
        void saveRef.current()
      }
      if (event.ctrlKey && event.key.toLowerCase() === 'z') {
        event.preventDefault()
        undoRef.current()
      }
      if (event.key === 'Enter' && !onField) {
        if (target instanceof HTMLElement && target.tagName === 'BUTTON') return
        placeDefaultRef.current()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  useEffect(() => {
    const stage = stageRef.current
    if (!stage) return
    const onWheel = (event: WheelEvent) => {
      event.preventDefault()
      applyGramsRef.current(stepGrams(gramsRef.current, event.deltaY < 0 ? 1 : -1))
    }
    stage.addEventListener('wheel', onWheel, { passive: false })
    return () => stage.removeEventListener('wheel', onWheel)
  }, [])

  return (
    <div
      className={`app${dragging ? ' is-drop' : ''}`}
      onDragOver={(event) => {
        event.preventDefault()
        setDragging(true)
      }}
      onDragLeave={(event) => {
        if (event.currentTarget.contains(event.relatedTarget as Node)) return
        setDragging(false)
      }}
      onDrop={(event) => void onDrop(event)}
    >
      <header className="top">
        <div>
          <p className="kicker">Apotheke · lokal im Browser</p>
          <h1>Rezept-Stempel</h1>
          <p className="lead">
            PDFs hierher ziehen. Ein Klick setzt <strong>{stampText(grams)}</strong>. Mausrad ändert die
            Menge ({MIN_GRAMS}–{MAX_GRAMS} g, {STEP_GRAMS}er-Schritte). Speichern schreibt eine neue Datei
            — das Original bleibt.
          </p>
        </div>
        <p className="stamp-preview" aria-live="polite">
          Stempel: {stampText(grams)}
        </p>
      </header>

      <div className="toolbar">
        <button type="button" className="primary" onClick={() => void openPicker()}>
          PDF öffnen
        </button>
        <button type="button" onClick={() => void openSample()}>
          Beispiel öffnen
        </button>
        <button type="button" className="primary" onClick={() => void save()} disabled={busy}>
          Speichern
        </button>
        <button type="button" onClick={placeDefault}>
          Erste Rp-Zeile
        </button>
        <button type="button" onClick={undo}>
          Letzten Stempel entfernen
        </button>
        <span className="grams" role="group" aria-label="Menge in Gramm">
          <button type="button" onClick={() => applyGrams(stepGrams(grams, -1))} aria-label="5 Gramm weniger">
            −5
          </button>
          <span>{grams} g</span>
          <button type="button" onClick={() => applyGrams(stepGrams(grams, 1))} aria-label="5 Gramm mehr">
            +5
          </button>
        </span>
        <span className="grow" />
        <span className="page">{active ? `Seite ${active.pageIndex + 1} / ${active.pageCount}` : 'Seite —'}</span>
        <button
          type="button"
          disabled={!active || active.pageIndex <= 0}
          onClick={() => active && patchDoc(active.id, { pageIndex: active.pageIndex - 1 })}
        >
          ←
        </button>
        <button
          type="button"
          disabled={!active || active.pageIndex >= active.pageCount - 1}
          onClick={() => active && patchDoc(active.id, { pageIndex: active.pageIndex + 1 })}
        >
          →
        </button>
      </div>

      <div className="workspace">
        <aside className="files">
          <h2>Offene Dateien</h2>
          <p className="hint">Mehrere PDFs ablegen möglich</p>
          {docs.length === 0 ? (
            <p className="empty-files">Noch keine Datei.</p>
          ) : (
            <ul>
              {docs.map((doc) => (
                <li key={doc.id}>
                  <button
                    type="button"
                    className={doc.id === activeId ? 'file is-active' : 'file'}
                    onClick={() => setActiveId(doc.id)}
                  >
                    {doc.name}
                    {doc.overlays.length > 0 ? ` · ${doc.overlays.length}` : ''}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <section className="stage" ref={stageRef}>
          {!active ? (
            <button type="button" className="dropzone" onClick={() => void openPicker()}>
              <strong>PDFs hierher ziehen</strong>
              <span>
                oder klicken, um Dateien zu wählen. Nur TEST-Muster und Ihre lokalen Rezepte — nichts wird
                hochgeladen.
              </span>
            </button>
          ) : (
            <div className="page-wrap">
              <canvas ref={pageCanvasRef} className="pdf-page" />
              <canvas
                ref={stampCanvasRef}
                className="pdf-stamps"
                onClick={onCanvasClick}
                onMouseMove={onCanvasMove}
                onMouseLeave={() => {
                  ghostRef.current = null
                  redrawStamps(active)
                }}
              />
            </div>
          )}
        </section>
      </div>

      {error ? (
        <p className="banner error" role="alert">
          {error}
        </p>
      ) : null}
      {busy ? <p className="banner muted">Bitte warten …</p> : null}
      <footer className="status">{status}</footer>
      <p className="fine">
        Datum {overlayDateText()} · Europe/Berlin · Originaldatei wird nie überschrieben
      </p>
    </div>
  )
}
