import { describe, expect, it } from 'vitest'

import {
  clickToBaseline,
  DEFAULT_STAMP_X,
  DEFAULT_STAMP_Y,
  defaultStampPoint,
  RX_ROW_TOPS,
  snapClickToRxRow,
} from './layout'

describe('Kassenrezept snap', () => {
  it('snaps clicks inside the three Verordnungszeilen', () => {
    expect(snapClickToRxRow(RX_ROW_TOPS[0] + 10)).toBe(DEFAULT_STAMP_Y)
    expect(snapClickToRxRow(RX_ROW_TOPS[1] + 8)).toBe(RX_ROW_TOPS[1] + 12)
    expect(snapClickToRxRow(RX_ROW_TOPS[2] + 20)).toBe(RX_ROW_TOPS[2] + 12)
  })

  it('does not snap outside the Rp-Zeilen', () => {
    expect(snapClickToRxRow(80)).toBeNull()
    expect(snapClickToRxRow(500)).toBeNull()
  })

  it('keeps x and uses the first-row default', () => {
    expect(clickToBaseline(210, RX_ROW_TOPS[0] + 5)).toEqual({ x: 210, y: DEFAULT_STAMP_Y })
    expect(defaultStampPoint()).toEqual({ x: DEFAULT_STAMP_X, y: DEFAULT_STAMP_Y })
  })
})
