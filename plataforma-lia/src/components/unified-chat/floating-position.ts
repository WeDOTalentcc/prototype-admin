export const FLOATING_POSITION_STORAGE_KEY = "lia-chat-floating-position"
export const FLOATING_RESET_EVENT = "lia:reset-floating-position"
export const BUBBLE_RESET_EVENT = "lia:reset-bubble-position"

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

export function readPersistedFloatingPosition(
  storage: Pick<Storage, "getItem"> | null | undefined,
  viewport: Viewport,
): Point | null {
  if (!storage) return null
  try {
    const raw = storage.getItem(FLOATING_POSITION_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<Point>
    if (typeof parsed?.x !== "number" || typeof parsed?.y !== "number") return null
    return clampFloatingPositionTo({ x: parsed.x, y: parsed.y }, viewport)
  } catch {
    return null
  }
}
