import { describe, expect, it } from 'vitest'

import { filesFromLaunchParams, isPdfName } from './launch'

describe('isPdfName', () => {
  it('accepts .pdf names regardless of case', () => {
    expect(isPdfName('TEST-REZEPT-0001.pdf')).toBe(true)
    expect(isPdfName('Scan.PDF')).toBe(true)
  })

  it('accepts application/pdf even without an extension', () => {
    expect(isPdfName('rezept', 'application/pdf')).toBe(true)
  })

  it('rejects other files', () => {
    expect(isPdfName('foto.jpg', 'image/jpeg')).toBe(false)
    expect(isPdfName('notiz.txt')).toBe(false)
  })
})

describe('filesFromLaunchParams', () => {
  it('keeps PDF file handles and skips directories and other files', async () => {
    const pdf = {
      kind: 'file' as const,
      name: 'A.pdf',
      getFile: async () => new File([new Uint8Array([1])], 'A.pdf', { type: 'application/pdf' }),
    }
    const other = {
      kind: 'file' as const,
      name: 'notes.txt',
      getFile: async () => new File([new Uint8Array([2])], 'notes.txt', { type: 'text/plain' }),
    }
    const folder = {
      kind: 'directory' as const,
      name: 'scans',
    }
    const opened = await filesFromLaunchParams({
      files: [folder as FileSystemHandle, other as FileSystemFileHandle, pdf as FileSystemFileHandle],
    })
    expect(opened.map((item) => item.file.name)).toEqual(['A.pdf'])
    expect(opened[0].handle).toBe(pdf)
  })

  it('returns an empty list when Windows opens the app without files', async () => {
    await expect(filesFromLaunchParams({})).resolves.toEqual([])
    await expect(filesFromLaunchParams({ files: [] })).resolves.toEqual([])
  })
})
