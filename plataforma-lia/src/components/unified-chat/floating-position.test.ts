import { describe, it, expect } from "vitest"
import {
  FLOATING_WIDTH,
  FLOATING_HEIGHT,
  FLOATING_VIEWPORT_MARGIN,
  clampFloatingPositionTo,
  defaultFloatingPosition,
} from "./floating-position"

const VIEWPORT = { width: 1280, height: 800 }

describe("clampFloatingPositionTo", () => {
  it("keeps a position that fits inside the viewport untouched", () => {
    expect(clampFloatingPositionTo({ x: 100, y: 100 }, VIEWPORT)).toEqual({ x: 100, y: 100 })
  })

  it("clamps a position past the right/bottom edges", () => {
    const result = clampFloatingPositionTo({ x: 99999, y: 99999 }, VIEWPORT)
    expect(result).toEqual({
      x: VIEWPORT.width - FLOATING_WIDTH,
      y: VIEWPORT.height - FLOATING_HEIGHT,
    })
  })

  it("clamps a negative position to the top-left corner", () => {
    expect(clampFloatingPositionTo({ x: -50, y: -200 }, VIEWPORT)).toEqual({ x: 0, y: 0 })
  })

  it("re-clamps when the viewport shrinks below the stored position", () => {
    const stored = { x: 1000, y: 600 }
    const small = { width: 800, height: 700 }
    const result = clampFloatingPositionTo(stored, small)
    expect(result.x).toBe(small.width - FLOATING_WIDTH)
    expect(result.y).toBe(small.height - FLOATING_HEIGHT)
  })

  it("anchors at the top-left when the viewport is smaller than the chat", () => {
    const result = clampFloatingPositionTo({ x: 100, y: 100 }, { width: 200, height: 200 })
    expect(result).toEqual({ x: 0, y: 0 })
  })
})

describe("defaultFloatingPosition", () => {
  it("anchors near the bottom-right with the standard margin", () => {
    expect(defaultFloatingPosition(VIEWPORT)).toEqual({
      x: VIEWPORT.width - FLOATING_WIDTH - FLOATING_VIEWPORT_MARGIN,
      y: VIEWPORT.height - FLOATING_HEIGHT - FLOATING_VIEWPORT_MARGIN,
    })
  })
})
