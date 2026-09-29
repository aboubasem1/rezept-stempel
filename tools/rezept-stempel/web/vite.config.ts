import { cpSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import type { Plugin } from 'vite'
import { defineConfig } from 'vitest/config'

const root = dirname(fileURLToPath(import.meta.url))

function copyPdfjsAssets(): Plugin {
  const copy = () => {
    const srcRoot = join(root, 'node_modules/pdfjs-dist')
    const destRoot = join(root, 'public/pdfjs')
    mkdirSync(destRoot, { recursive: true })
    for (const dir of ['standard_fonts', 'cmaps', 'wasm', 'iccs'] as const) {
      cpSync(join(srcRoot, dir), join(destRoot, dir), { recursive: true })
    }
  }
  return {
    name: 'copy-pdfjs-assets',
    buildStart: copy,
  }
}

export default defineConfig({
  plugins: [react(), copyPdfjsAssets()],
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
})
