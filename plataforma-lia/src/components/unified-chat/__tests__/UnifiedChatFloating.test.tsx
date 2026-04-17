import React, { useEffect, useState } from "react"
import { describe, it, expect, beforeEach, vi } from "vitest"
import { render, screen, fireEvent, act } from "@testing-library/react"
import {
  FLOATING_POSITION_STORAGE_KEY,
  FLOATING_RESET_EVENT,
  BUBBLE_RESET_EVENT,
  getUserScopedKey,
  readPersistedFloatingPosition,
  type Point,
} from "../floating-position"

const USER_ID = "u-floating-1"
const SCOPED_KEY = getUserScopedKey(FLOATING_POSITION_STORAGE_KEY, USER_ID)

/**
 * Mirror of the persistence + reset wiring inside UnifiedChat (floating mode).
 * Lets us exercise the user-scoped storage flow and the reset event without
 * rendering UnifiedChat's full tree (auth store, contexts, ws, etc).
 */
function FloatingPositionHarness({ userId = USER_ID }: { userId?: string }) {
  const [position, setPosition] = useState<Point | null>(() => {
    const viewport = { width: window.innerWidth, height: window.innerHeight }
    const scoped = readPersistedFloatingPosition(localStorage, viewport, getUserScopedKey(FLOATING_POSITION_STORAGE_KEY, userId))
    if (scoped) return scoped
    return readPersistedFloatingPosition(localStorage, viewport, FLOATING_POSITION_STORAGE_KEY)
  })

  useEffect(() => {
    const key = getUserScopedKey(FLOATING_POSITION_STORAGE_KEY, userId)
    if (position) {
      localStorage.setItem(key, JSON.stringify(position))
    } else {
      localStorage.removeItem(key)
    }
    localStorage.removeItem(FLOATING_POSITION_STORAGE_KEY)
  }, [position, userId])

  useEffect(() => {
    const handleReset = () => setPosition(null)
    window.addEventListener(FLOATING_RESET_EVENT, handleReset)
    return () => window.removeEventListener(FLOATING_RESET_EVENT, handleReset)
  }, [])

  return (
    <div data-testid="floating" data-x={position?.x ?? ""} data-y={position?.y ?? ""}>
      <button data-testid="move" onClick={() => setPosition({ x: 222, y: 200 })}>move</button>
      <button
        data-testid="reset"
        onClick={() => {
          setPosition(null)
          window.dispatchEvent(new CustomEvent(BUBBLE_RESET_EVENT))
        }}
      >
        reset
      </button>
    </div>
  )
}

beforeEach(() => {
  localStorage.clear()
  Object.defineProperty(window, "innerWidth", { value: 1280, configurable: true })
  Object.defineProperty(window, "innerHeight", { value: 800, configurable: true })
})

describe("UnifiedChat floating position — persistence flow", () => {
  it("persists a moved position to the user-scoped key and clears the legacy key", () => {
    localStorage.setItem(FLOATING_POSITION_STORAGE_KEY, JSON.stringify({ x: 10, y: 10 }))
    render(<FloatingPositionHarness />)
    fireEvent.click(screen.getByTestId("move"))
    expect(JSON.parse(localStorage.getItem(SCOPED_KEY) ?? "null")).toEqual({ x: 222, y: 200 })
    expect(localStorage.getItem(FLOATING_POSITION_STORAGE_KEY)).toBeNull()
  })

  it("restores the saved position after a reload", () => {
    const { unmount } = render(<FloatingPositionHarness />)
    fireEvent.click(screen.getByTestId("move"))
    unmount()
    render(<FloatingPositionHarness />)
    const el = screen.getByTestId("floating")
    expect(el.dataset.x).toBe("222")
    expect(el.dataset.y).toBe("200")
  })

  it("loads the legacy unscoped value on first mount, then migrates it to the scoped key", () => {
    localStorage.setItem(FLOATING_POSITION_STORAGE_KEY, JSON.stringify({ x: 77, y: 88 }))
    render(<FloatingPositionHarness />)
    const el = screen.getByTestId("floating")
    expect(el.dataset.x).toBe("77")
    expect(el.dataset.y).toBe("88")
    // The persistence effect runs on mount and should have migrated the value
    expect(JSON.parse(localStorage.getItem(SCOPED_KEY) ?? "null")).toEqual({ x: 77, y: 88 })
    expect(localStorage.getItem(FLOATING_POSITION_STORAGE_KEY)).toBeNull()
  })
})

describe("UnifiedChat floating position — reset durability", () => {
  it("reset clears both the scoped and the legacy key, so a reload stays at default", () => {
    // Pre-existing legacy data
    localStorage.setItem(FLOATING_POSITION_STORAGE_KEY, JSON.stringify({ x: 100, y: 100 }))
    const { unmount } = render(<FloatingPositionHarness />)
    fireEvent.click(screen.getByTestId("reset"))
    expect(localStorage.getItem(SCOPED_KEY)).toBeNull()
    expect(localStorage.getItem(FLOATING_POSITION_STORAGE_KEY)).toBeNull()
    unmount()
    // Reload — should mount at default (null position)
    render(<FloatingPositionHarness />)
    const el = screen.getByTestId("floating")
    expect(el.dataset.x).toBe("")
    expect(el.dataset.y).toBe("")
  })

  it("reacts to the global FLOATING_RESET_EVENT", () => {
    render(<FloatingPositionHarness />)
    fireEvent.click(screen.getByTestId("move"))
    act(() => {
      window.dispatchEvent(new CustomEvent(FLOATING_RESET_EVENT))
    })
    const el = screen.getByTestId("floating")
    expect(el.dataset.x).toBe("")
    expect(el.dataset.y).toBe("")
    expect(localStorage.getItem(SCOPED_KEY)).toBeNull()
  })
})
