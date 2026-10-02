export function isPdfName(name: string, type = ''): boolean {
  return name.toLowerCase().endsWith('.pdf') || type === 'application/pdf'
}

export async function filesFromLaunchParams(params: {
  files?: ReadonlyArray<FileSystemHandle>
}): Promise<Array<{ file: File; handle: FileSystemFileHandle | null }>> {
  const collected: Array<{ file: File; handle: FileSystemFileHandle | null }> = []
  for (const handle of params.files ?? []) {
    switch (handle.kind) {
      case 'directory':
        break
      case 'file': {
        const fileHandle = handle as FileSystemFileHandle
        const file = await fileHandle.getFile()
        if (!isPdfName(fileHandle.name, file.type) && !isPdfName(file.name, file.type)) {
          break
        }
        collected.push({ file, handle: fileHandle })
        break
      }
      default: {
        const _exhaustive: never = handle.kind
        void _exhaustive
      }
    }
  }
  return collected
}
