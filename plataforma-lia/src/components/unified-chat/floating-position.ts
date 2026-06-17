export const BUBBLE_POSITION_STORAGE_KEY = "lia-bubble-position"
export const FLOATING_RESET_EVENT = "lia:reset-floating-position"
export const BUBBLE_RESET_EVENT = "lia:reset-bubble-position"

/**
 * Returns a per-user storage key. Falls back to ":anon" when no userId is
 * known (e.g. before login or in SSR). Used by the bubble's persistence.
 */
export function getUserScopedKey(baseKey: string, userId: string | null | undefined): string {
  const scope = userId && userId.length > 0 ? userId : "anon"
  return `${baseKey}:${scope}`
}

export const FLOATING_WIDTH = 360
export const FLOATING_HEIGHT = 520
export const FLOATING_DRAG_THRESHOLD = 4
export const ARROW_STEP = 8
export const ARROW_STEP_LARGE = 32
export const FLOATING_VIEWPORT_MARGIN = 16

export interface Point {
  x: number
  y: number
}

export interface Viewport {
  width: number
  height: number
}

export function clampFloatingPositionTo(p: Point, viewport: Viewport): Point {
  const x = Math.max(0, Math.min(viewport.width - FLOATING_WIDTH, p.x))
  const y = Math.max(0, Math.min(viewport.height - FLOATING_HEIGHT, p.y))
  return { x, y }
}

export function clampFloatingPosition(p: Point): Point {
  if (typeof window === "undefined") return p
  return clampFloatingPositionTo(p, {
    width: window.innerWidth,
    height: window.innerHeight,
  })
}

export function defaultFloatingPosition(viewport: Viewport): Point {
  return {
    x: viewport.width - FLOATING_WIDTH - FLOATING_VIEWPORT_MARGIN,
    y: viewport.height - FLOATING_HEIGHT - FLOATING_VIEWPORT_MARGIN,
  }
}
