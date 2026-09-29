const BERLIN = 'Europe/Berlin'

function berlinParts(when: Date): Record<string, string> {
  const fmt = new Intl.DateTimeFormat('en-GB', {
    timeZone: BERLIN,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  })
  const parts: Record<string, string> = {}
  for (const part of fmt.formatToParts(when)) {
    if (part.type !== 'literal') {
      parts[part.type] = part.value
    }
  }
  return parts
}

export function overlayDateText(when: Date = new Date()): string {
  const p = berlinParts(when)
  return `${p.day}.${p.month}.${p.year}`
}

export function filenameTimestamp(when: Date = new Date()): string {
  const p = berlinParts(when)
  return `${p.year}-${p.month}-${p.day}_${p.hour}${p.minute}`
}

export function stampText(grams: number, when: Date = new Date()): string {
  return `- ${grams}g ${overlayDateText(when)}`
}

export function stampedFileName(originalName: string, when: Date = new Date()): string {
  const stem = originalName.replace(/\.pdf$/i, '')
  const candidate = `${stem}_${filenameTimestamp(when)}.pdf`
  if (candidate.toLowerCase() === originalName.toLowerCase()) {
    return `${stem}_${filenameTimestamp(when)}-2.pdf`
  }
  return candidate
}
