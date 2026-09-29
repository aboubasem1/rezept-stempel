import { bytesToBlob } from './buffer'
import { stampedFileName } from './dates'

export type SaveOutcome =
  | { kind: 'filesystem'; name: string }
  | { kind: 'download'; name: string }
  | { kind: 'cancelled' }

function assertNever(value: never): never {
  throw new Error(`Unerwartetes Speichern: ${String(value)}`)
}

export function describeSave(outcome: SaveOutcome): string {
  switch (outcome.kind) {
    case 'filesystem':
      return `Gespeichert neben dem Original: ${outcome.name}`
    case 'download':
      return `Download: ${outcome.name} — Original bleibt unangetastet.`
    case 'cancelled':
      return 'Speichern abgebrochen.'
    default: {
      return assertNever(outcome)
    }
  }
}

export function hasSavePicker(): boolean {
  return typeof window !== 'undefined' && typeof window.showSaveFilePicker === 'function'
}

export async function saveStampedPdf(options: {
  originalName: string
  sourceHandle: FileSystemFileHandle | null
  bytes: Uint8Array
}): Promise<SaveOutcome> {
  const name = stampedFileName(options.originalName)
  if (name.toLowerCase() === options.originalName.toLowerCase()) {
    throw new Error('Die Quelldatei darf nicht überschrieben werden.')
  }

  if (options.sourceHandle && hasSavePicker() && window.showSaveFilePicker) {
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: name,
        startIn: options.sourceHandle,
        types: [
          {
            description: 'PDF-Datei',
            accept: { 'application/pdf': ['.pdf'] },
          },
        ],
      })
      if (handle.name.toLowerCase() === options.originalName.toLowerCase()) {
        throw new Error('Die Originaldatei darf nicht überschrieben werden. Bitte den Timestamp-Namen behalten.')
      }
      const writable = await handle.createWritable()
      await writable.write(bytesToBlob(options.bytes))
      await writable.close()
      return { kind: 'filesystem', name: handle.name }
    } catch (error) {
      if (isAbort(error)) {
        return { kind: 'cancelled' }
      }
      throw error
    }
  }

  downloadBlob(bytesToBlob(options.bytes), name)
  return { kind: 'download', name }
}

function downloadBlob(blob: Blob, name: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.click()
  URL.revokeObjectURL(url)
}

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}
