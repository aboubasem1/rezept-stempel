import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type DragEvent,
  type MouseEvent,
  type PointerEvent,
} from 'react'

import { stampText } from './lib/dates'
import { DEFAULT_GRAMS, MAX_GRAMS, MIN_GRAMS, parseCustomGrams, stepGrams } from './lib/grams'
import { CUSTOM_HOLD_MS } from './lib/hold'
import { defaultStampPoint, type Overlay } from './lib/layout'
import { createOverlay, hitTestOverlay, stepSelectedOverlayGrams, updateSelectedGrams } from './lib/overlays'
import { filesFromLaunchParams } from './lib/launch'
import { canvasClickToPdf, canvasToPdf, drawStamps, loadPdf, renderPageToCanvas } from './lib/pdf'
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
  const [selectedOverlayId, setSelectedOverlayId] = useState<string | null>(null)
  const [status, setStatus] = useState('PDFs hierher ziehen oder öffnen.')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [customOpen, setCustomOpen] = useState(false)
  const [customDraft, setCustomDraft] = useState('25')
  const [customError, setCustomError] = useState<string | null>(null)
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [standalone, setStandalone] = useState(false)
  const pageCanvasRef = useRef<HTMLCanvasElement | null>(null)
  const stampCanvasRef = useRef<HTMLCanvasElement | null>(null)
  const stageRef = useRef<HTMLElement | null>(null)
  const scaleRef = useRef({ scale: 1, width: 595.28, height: 841.89 })
  const ghostRef = useRef<{ x: number; y: number } | null>(null)
  const gramsRef = useRef(grams)
  const docsRef = useRef(docs)
  const activeIdRef = useRef(activeId)
  const selectedOverlayIdRef = useRef(selectedOverlayId)
  const holdTimerRef = useRef<number | null>(null)
  const customInputRef = useRef<HTMLInputElement | null>(null)
  const customOpenRef = useRef(false)
  const blockContextRef = useRef(false)

  gramsRef.current = grams
  docsRef.current = docs
  activeIdRef.current = activeId
  selectedOverlayIdRef.current = selectedOverlayId
  customOpenRef.current = customOpen

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
    drawStamps(
      ctx,
      scale,
      doc.overlays,
      doc.pageIndex,
      gramsRef.current,
      ghostRef.current,
      selectedOverlayIdRef.current,
    )
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
  }, [active, redrawStamps, grams, selectedOverlayId])

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
    setSelectedOverlayId(null)
    setStatus(
      opened.length === 1
        ? `Geöffnet: ${opened[0].name} — Klick setzt den Stempel.`
        : `${opened.length} PDFs geöffnet. Klick setzt den Stempel.`,
    )
  }, [])

  useEffect(() => {
    const standaloneMedia = window.matchMedia('(display-mode: standalone)')
    const syncStandalone = () => {
      setStandalone(standaloneMedia.matches || window.navigator.standalone === true)
    }
    syncStandalone()
    standaloneMedia.addEventListener('change', syncStandalone)
    const onInstallPrompt = (event: BeforeInstallPromptEvent) => {
      event.preventDefault()
      setInstallPrompt(event)
    }
    window.addEventListener('beforeinstallprompt', onInstallPrompt)
    return () => {
      standaloneMedia.removeEventListener('change', syncStandalone)
      window.removeEventListener('beforeinstallprompt', onInstallPrompt)
    }
  }, [])

  useEffect(() => {
    const queue = window.launchQueue
    if (!queue) return
    queue.setConsumer(async (params) => {
      const collected = await filesFromLaunchParams(params)
      if (collected.length === 0) return
      await addFiles(collected)
    })
  }, [addFiles])

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
    const overlay = createOverlay({
      pageIndex: current.pageIndex,
      x,
      y,
      grams: gramsRef.current,
      when: new Date(),
    })
    patchDoc(current.id, (doc) => ({ ...doc, overlays: [...doc.overlays, overlay] }))
    setSelectedOverlayId(overlay.id)
    setStatus(`Stempel gesetzt: ${stampText(overlay.grams)} — Mausrad ändert nur diesen Stempel.`)
  }

  const onCanvasClick = (event: MouseEvent<HTMLCanvasElement>) => {
    if (event.button !== 0) return
    const canvas = stampCanvasRef.current ?? pageCanvasRef.current
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!canvas || !current) {
      void openPicker()
      return
    }
    const { width, height } = scaleRef.current
    const raw = canvasToPdf(event, canvas, width, height)
    const existing = hitTestOverlay(current.overlays, current.pageIndex, raw.x, raw.y)
    if (existing) {
      setSelectedOverlayId(existing.id)
      setGrams(existing.grams)
      setStatus(`Stempel gewählt: ${stampText(existing.grams, existing.when)}`)
      return
    }
    const point = canvasClickToPdf(event, canvas, width, height)
    placeStamp(point.x, point.y)
  }

  const onCanvasMove = (event: MouseEvent<HTMLCanvasElement>) => {
    const canvas = stampCanvasRef.current
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!canvas || !current) return
    const { width, height } = scaleRef.current
    const raw = canvasToPdf(event, canvas, width, height)
    if (hitTestOverlay(current.overlays, current.pageIndex, raw.x, raw.y)) {
      ghostRef.current = null
    } else {
      ghostRef.current = canvasClickToPdf(event, canvas, width, height)
    }
    redrawStamps(current)
  }

  const selectedOverlay = () => {
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    const selectedId = selectedOverlayIdRef.current
    if (!current || selectedId === null) return null
    return current.overlays.find((overlay) => overlay.id === selectedId) ?? null
  }

  const applyGrams = (next: number) => {
    setGrams(next)
    const selectedId = selectedOverlayIdRef.current
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!current || selectedId === null) return
    if (!current.overlays.some((overlay) => overlay.id === selectedId)) return
    patchDoc(current.id, (doc) => ({
      ...doc,
      overlays: updateSelectedGrams(doc.overlays, selectedId, next),
    }))
  }

  const stepSelectedGrams = (direction: number) => {
    const selected = selectedOverlay()
    if (selected === null) {
      setGrams(stepGrams(gramsRef.current, direction))
      return
    }
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!current) return
    const nextGrams = stepGrams(selected.grams, direction)
    setGrams(nextGrams)
    patchDoc(current.id, (doc) => ({
      ...doc,
      overlays: stepSelectedOverlayGrams(doc.overlays, selected.id, direction),
    }))
  }

  const clearHold = () => {
    if (holdTimerRef.current === null) return
    window.clearTimeout(holdTimerRef.current)
    holdTimerRef.current = null
  }

  const openCustomGrams = () => {
    const selected = selectedOverlay()
    if (selected === null) {
      setStatus('Bitte zuerst einen Stempel wählen.')
      return
    }
    setCustomDraft(String(selected.grams))
    setCustomError(null)
    setCustomOpen(true)
    setStatus('Freie Menge für den ausgewählten Stempel.')
  }

  const closeCustomGrams = () => {
    setCustomOpen(false)
    setCustomError(null)
    blockContextRef.current = false
  }

  const submitCustomGrams = () => {
    if (selectedOverlay() === null) {
      setCustomError('Kein Stempel ausgewählt.')
      return
    }
    const parsed = parseCustomGrams(customDraft)
    if (parsed === null) {
      setCustomError(`Bitte eine Menge zwischen ${MIN_GRAMS} und ${MAX_GRAMS} g eingeben.`)
      return
    }
    applyGrams(parsed)
    closeCustomGrams()
    setStatus(`Freie Menge gesetzt: ${stampText(parsed)}`)
  }

  const onCanvasContextMenu = (event: MouseEvent<HTMLCanvasElement>) => {
    event.preventDefault()
  }

  const onCanvasPointerDown = (event: PointerEvent<HTMLCanvasElement>) => {
    if (event.button !== 2) return
    event.preventDefault()
    const canvas = stampCanvasRef.current
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!canvas || !current) return
    const { width, height } = scaleRef.current
    const raw = canvasToPdf(event, canvas, width, height)
    const existing = hitTestOverlay(current.overlays, current.pageIndex, raw.x, raw.y)
    if (existing) {
      selectedOverlayIdRef.current = existing.id
      gramsRef.current = existing.grams
      setSelectedOverlayId(existing.id)
      setGrams(existing.grams)
    }
    blockContextRef.current = true
    clearHold()
    holdTimerRef.current = window.setTimeout(() => {
      holdTimerRef.current = null
      openCustomGrams()
    }, CUSTOM_HOLD_MS)
  }

  const onCanvasPointerUp = (event: PointerEvent<HTMLCanvasElement>) => {
    if (event.button === 2) {
      clearHold()
      window.setTimeout(() => {
        if (!customOpenRef.current) blockContextRef.current = false
      }, 0)
    }
  }

  const placeDefault = () => {
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!current) {
      void openPicker()
      return
    }
    const point = defaultStampPoint()
    const overlay = createOverlay({
      pageIndex: current.pageIndex,
      x: point.x,
      y: point.y,
      grams: gramsRef.current,
      when: new Date(),
    })
    patchDoc(current.id, (doc) => ({ ...doc, overlays: [...doc.overlays, overlay] }))
    setSelectedOverlayId(overlay.id)
    setStatus(`Stempel auf der ersten Rp-Zeile: ${stampText(overlay.grams)}`)
  }

  const undo = () => {
    const current = docsRef.current.find((doc) => doc.id === activeIdRef.current)
    if (!current || current.overlays.length === 0) {
      setStatus('Kein Stempel zum Entfernen.')
      return
    }
    const removed = current.overlays[current.overlays.length - 1]
    patchDoc(current.id, (doc) => ({ ...doc, overlays: doc.overlays.slice(0, -1) }))
    if (selectedOverlayIdRef.current === removed.id) {
      const previous = current.overlays[current.overlays.length - 2]
      setSelectedOverlayId(previous?.id ?? null)
      if (previous) setGrams(previous.grams)
    }
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
  const stepSelectedGramsRef = useRef(stepSelectedGrams)
  saveRef.current = save
  undoRef.current = undo
  placeDefaultRef.current = placeDefault
  stepSelectedGramsRef.current = stepSelectedGrams

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (customOpenRef.current) return
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
    if (!customOpen) return
    customInputRef.current?.focus()
    customInputRef.current?.select()
  }, [customOpen])

  useEffect(() => {
    const onMenu = (event: Event) => {
      if (blockContextRef.current || customOpenRef.current) {
        event.preventDefault()
      }
    }
    document.addEventListener('contextmenu', onMenu)
    return () => document.removeEventListener('contextmenu', onMenu)
  }, [])

  useEffect(() => {
    const onBlur = () => {
      clearHold()
      if (!customOpenRef.current) blockContextRef.current = false
    }
    window.addEventListener('blur', onBlur)
    return () => {
      onBlur()
      window.removeEventListener('blur', onBlur)
    }
  }, [])

  useEffect(() => {
    const stage = stageRef.current
    if (!stage) return
    const onWheel = (event: WheelEvent) => {
      event.preventDefault()
      stepSelectedGramsRef.current(event.deltaY < 0 ? 1 : -1)
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
          <h1>Rezept-Stempel</h1>
          <p className="privacy">PDFs bleiben im Browser — nichts wird hochgeladen.</p>
        </div>
        <p className="stamp-preview" aria-live="polite">
          {stampText(grams)}
        </p>
      </header>

      <div className="toolbar">
        <button type="button" className="primary" onClick={() => void openPicker()}>
          PDF öffnen
        </button>
        <button type="button" onClick={() => void openSample()}>
          Beispiel
        </button>
        <button type="button" className="primary" onClick={() => void save()} disabled={busy}>
          Speichern
        </button>
        <button type="button" onClick={placeDefault}>
          Erste Rp-Zeile
        </button>
        <button type="button" onClick={undo}>
          Rückgängig
        </button>
        <span className="grams" role="group" aria-label="Menge in Gramm">
          <button type="button" onClick={() => stepSelectedGrams(-1)} aria-label="5 Gramm weniger">
            −5
          </button>
          <span>{grams} g</span>
          <button type="button" onClick={() => stepSelectedGrams(1)} aria-label="5 Gramm mehr">
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
          <h2>Dateien</h2>
          {docs.length === 0 ? (
            <p className="empty-files">Keine Datei.</p>
          ) : (
            <ul>
              {docs.map((doc) => (
                <li key={doc.id}>
                  <button
                    type="button"
                    className={doc.id === activeId ? 'file is-active' : 'file'}
                    onClick={() => {
                      setActiveId(doc.id)
                      setSelectedOverlayId(null)
                    }}
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
            <div className="empty-stage">
              <button type="button" className="dropzone" onClick={() => void openPicker()}>
                <strong>PDFs hierher ziehen</strong>
                <span>oder öffnen. Speichern schreibt eine neue Datei.</span>
              </button>
              <p className="default-app-hint">
                {standalone
                  ? 'Windows: Einstellungen → Apps → Standard-Apps → .pdf → Rezept-Stempel. Danach öffnet ein Doppelklick das Rezept hier statt in Adobe.'
                  : 'Adobe ersetzen: in Edge oder Chrome diese Seite als App installieren, dann unter Windows .pdf auf Rezept-Stempel stellen. Ein normaler Browser-Tab kann das nicht.'}
              </p>
              {installPrompt && !standalone ? (
                <button
                  type="button"
                  className="install-app"
                  onClick={() => {
                    void installPrompt.prompt()
                    setInstallPrompt(null)
                  }}
                >
                  Als App installieren
                </button>
              ) : null}
            </div>
          ) : (
            <div className="page-wrap" onContextMenu={(event) => event.preventDefault()}>
              <canvas ref={pageCanvasRef} className="pdf-page" />
              <canvas
                ref={stampCanvasRef}
                className="pdf-stamps"
                onClick={onCanvasClick}
                onMouseMove={onCanvasMove}
                onContextMenu={onCanvasContextMenu}
                onPointerDown={onCanvasPointerDown}
                onPointerUp={onCanvasPointerUp}
                onPointerCancel={clearHold}
                onMouseLeave={() => {
                  clearHold()
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
      {customOpen ? (
        <div
          className="dialog-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeCustomGrams()
          }}
        >
          <form
            className="dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="custom-grams-title"
            onSubmit={(event) => {
              event.preventDefault()
              submitCustomGrams()
            }}
          >
            <h2 id="custom-grams-title">Freie Menge</h2>
            <p>Nur der ausgewählte Stempel. Beliebige ganze Zahl, nicht auf 5er-Schritte gerundet.</p>
            <label htmlFor="custom-grams-input">
              Gramm ({MIN_GRAMS}–{MAX_GRAMS})
            </label>
            <input
              ref={customInputRef}
              id="custom-grams-input"
              type="text"
              inputMode="decimal"
              value={customDraft}
              onChange={(event) => {
                setCustomDraft(event.target.value)
                setCustomError(null)
              }}
              onKeyDown={(event) => {
                if (event.key === 'Escape') {
                  event.preventDefault()
                  closeCustomGrams()
                }
              }}
            />
            {customError ? (
              <p className="dialog-error" role="alert">
                {customError}
              </p>
            ) : null}
            <div className="dialog-actions">
              <button type="button" onClick={closeCustomGrams}>
                Abbrechen
              </button>
              <button type="submit" className="primary">
                Übernehmen
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  )
}
