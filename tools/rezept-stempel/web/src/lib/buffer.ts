export function copyBytes(data: ArrayBuffer | Uint8Array): Uint8Array {
  const view = data instanceof Uint8Array ? data : new Uint8Array(data)
  const copy = new Uint8Array(view.byteLength)
  copy.set(view)
  return copy
}

export function toArrayBuffer(data: ArrayBuffer | Uint8Array): ArrayBuffer {
  if (data instanceof ArrayBuffer) {
    return data.slice(0)
  }
  const out = new ArrayBuffer(data.byteLength)
  new Uint8Array(out).set(data)
  return out
}

export function bytesToBlob(bytes: Uint8Array): Blob {
  return new Blob([toArrayBuffer(bytes)], { type: 'application/pdf' })
}
