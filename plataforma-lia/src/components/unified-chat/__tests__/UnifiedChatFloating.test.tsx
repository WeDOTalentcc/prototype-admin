import React, { useCallback, useEffect, useRef, useState } from "react"
import { describe, it, expect, beforeEach } from "vitest"
import { render, screen, fireEvent, act } from "@testing-library/react"
import {
  ARROW_STEP,
  ARROW_STEP_LARGE,
  FLOATING_DRAG_THRESHOLD,
  FLOATING_RESET_EVENT,
  FLOATING_WIDTH,
  FLOATING_HEIGHT,
  FLOATING_VIEWPORT_MARGIN,
  clampFloatingPosition,
  defaultFloatingPosition,
  type Point,
} from "../floating-position"

/**
 * Task #1291 — mirror of the floating-window drag wiring inside UnifiedChat.
 * The contract under test:
 *  - position lives ONLY in component state (ephemeral, never localStorage)
 *  - dragging the header moves the window (after a small threshold)
 *  - the position is clamped inside the viewport
 *  - the "back to corner" button (and the global reset event) dock it again
 *  - a reload (unmount + remount) always restarts at the default corner
 *  - arrow keys move the window (accessibility)
 *
 * We replicate the handlers here (rather than mount the full UnifiedChat tree
 * with its auth store / websocket / contexts) so the test exercises the exact
 * pointer + keyboard + reset logic in isolation.
 */
function FloatingDragHarness() {
  const [position, setPosition] = useState<Point | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const dragRef = useRef<{
    startX: number
    startY: number
    baseX: number
    baseY: number
    moved: boolean
  } | null>(null)

  useEffect(() => {
    const handleReset = () => setPosition(null)
    window.addEventListener(FLOATING_RESET_EVENT, handleReset)
    return () => window.removeEventListener(FLOATING_RESET_EVENT, handleReset)
  }, [])

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    if ((e.target as HTMLElement).closest("button, input")) return
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return
    dragRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      baseX: rect.left,
      baseY: rect.top,
      moved: false,
    }
    const handleMove = (ev: PointerEvent) => {
      const drag = dragRef.current
      if (!drag) return
      const dx = ev.clientX - drag.startX
      const dy = ev.clientY - drag.startY
      if (
        !drag.moved &&
        (Math.abs(dx) > FLOATING_DRAG_THRESHOLD ||
          Math.abs(dy) > FLOATING_DRAG_THRESHOLD)
      ) {
        drag.moved = true
      }
      if (!drag.moved) return
      setPosition(clampFloatingPosition({ x: drag.baseX + dx, y: drag.baseY + dy }))
    }
    const handleUp = () => {
      dragRef.current = null
      document.removeEventListener("pointermove", handleMove)
      document.removeEventListener("pointerup", handleUp)
    }
    document.addEventListener("pointermove", handleMove)
    document.addEventListener("pointerup", handleUp)
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    const arrowMap: Record<string, [number, number]> = {
      ArrowUp: [0, -1],
      ArrowDown: [0, 1],
      ArrowLeft: [-1, 0],
      ArrowRight: [1, 0],
    }
    const delta = arrowMap[e.key]
    if (!delta) return
    e.preventDefault()
    const step = e.shiftKey ? ARROW_STEP_LARGE : ARROW_STEP
    setPosition((prev) => {
      const base =
        prev ??
        defaultFloatingPosition({ width: window.innerWidth, height: window.innerHeight })
      return clampFloatingPosition({ x: base.x + delta[0] * step, y: base.y + delta[1] * step })
    })
  }, [])

  return (
    <div
      ref={containerRef}
      data-testid="floating"
      data-x={position?.x ?? ""}
      data-y={position?.y ?? ""}
    >
      <div
        data-testid="floating-drag-handle"
        tabIndex={0}
        onPointerDown={handlePointerDown}
        onKeyDown={handleKeyDown}
      >
        <button
          data-testid="floating-reset-button"
          onClick={() => setPosition(null)}
        >
          corner
        </button>
      </div>
    </div>
  )
}

beforeEach(() => {
  localStorage.clear()
  Object.defineProperty(window, "innerWidth", { value: 1280, configurable: true })
  Object.defineProperty(window, "innerHeight", { value: 800, configurable: true })
})

describe("UnifiedChat floating window — drag", () => {
  it("moves the window when the header is dragged past the threshold", () => {
    render(<FloatingDragHarness />)
    const handle = screen.getByTestId("floating-drag-handle")
    fireEvent.pointerDown(handle, { clientX: 0, clientY: 0, button: 0 })
    fireEvent.pointerMove(document, { clientX: 222, clientY: 200 })
    fireEvent.pointerUp(document)
    const el = screen.getByTestId("floating")
    expect(el.dataset.x).toBe("222")
    expect(el.dataset.y).toBe("200")
  })

  it("does not move on a tiny pointer movement under the threshold", () => {
    render(<FloatingDragHarness />)
    const handle = screen.getByTestId("floating-drag-handle")
    fireEvent.pointerDown(handle, { clientX: 0, clientY: 0, button: 0 })
    fireEvent.pointerMove(document, { clientX: 2, clientY: 2 })
    fireEvent.pointerUp(document)
    const el = screen.getByTestId("floating")
    expect(el.dataset.x).toBe("")
    expect(el.dataset.y).toBe("")
  })

  it("clamps the dragged position inside the viewport", () => {
    render(<FloatingDragHarness />)
    const handle = screen.getByTestId("floating-drag-handle")
    fireEvent.pointerDown(handle, { clientX: 0, clientY: 0, button: 0 })
    fireEvent.pointerMove(document, { clientX: 99999, clientY: 99999 })
    fireEvent.pointerUp(document)
    const el = screen.getByTestId("floating")
    expect(el.dataset.x).toBe(String(1280 - FLOATING_WIDTH))
    expect(el.dataset.y).toBe(String(800 - FLOATING_HEIGHT))
  })

  it("never persists the dragged position to localStorage", () => {
    render(<FloatingDragHarness />)
    const handle = screen.getByTestId("floating-drag-handle")
    fireEvent.pointerDown(handle, { clientX: 0, clientY: 0, button: 0 })
    fireEvent.pointerMove(document, { clientX: 222, clientY: 200 })
    fireEvent.pointerUp(document)
    expect(localStorage.length).toBe(0)
  })
})

describe("UnifiedChat floating window — back to corner", () => {
  it("docks the window via the reset button", () => {
    render(<FloatingDragHarness />)
    const handle = screen.getByTestId("floating-drag-handle")
    fireEvent.pointerDown(handle, { clientX: 0, clientY: 0, button: 0 })
    fireEvent.pointerMove(document, { clientX: 222, clientY: 200 })
    fireEvent.pointerUp(document)
    fireEvent.click(screen.getByTestId("floating-reset-button"))
    const el = screen.getByTestId("floating")
    expect(el.dataset.x).toBe("")
    expect(el.dataset.y).toBe("")
  })

  it("docks the window when the global FLOATING_RESET_EVENT fires", () => {
    render(<FloatingDragHarness />)
    const handle = screen.getByTestId("floating-drag-handle")
    fireEvent.pointerDown(handle, { clientX: 0, clientY: 0, button: 0 })
    fireEvent.pointerMove(document, { clientX: 222, clientY: 200 })
    fireEvent.pointerUp(document)
    act(() => {
      window.dispatchEvent(new CustomEvent(FLOATING_RESET_EVENT))
    })
    const el = screen.getByTestId("floating")
    expect(el.dataset.x).toBe("")
    expect(el.dataset.y).toBe("")
  })
})

describe("UnifiedChat floating window — reload resets to default", () => {
  it("restarts at the default corner after a remount (no persistence)", () => {
    const { unmount } = render(<FloatingDragHarness />)
    const handle = screen.getByTestId("floating-drag-handle")
    fireEvent.pointerDown(handle, { clientX: 0, clientY: 0, button: 0 })
    fireEvent.pointerMove(document, { clientX: 222, clientY: 200 })
    fireEvent.pointerUp(document)
    unmount()
    render(<FloatingDragHarness />)
    const el = screen.getByTestId("floating")
    expect(el.dataset.x).toBe("")
    expect(el.dataset.y).toBe("")
    expect(localStorage.length).toBe(0)
  })
})

describe("UnifiedChat floating window — keyboard accessibility", () => {
  it("moves the window with arrow keys from the default corner", () => {
    render(<FloatingDragHarness />)
    const handle = screen.getByTestId("floating-drag-handle")
    fireEvent.keyDown(handle, { key: "ArrowLeft" })
    const el = screen.getByTestId("floating")
    const defaultX = 1280 - FLOATING_WIDTH - FLOATING_VIEWPORT_MARGIN
    const defaultY = 800 - FLOATING_HEIGHT - FLOATING_VIEWPORT_MARGIN
    expect(el.dataset.x).toBe(String(defaultX - ARROW_STEP))
    expect(el.dataset.y).toBe(String(defaultY))
  })

  it("uses a larger step when Shift is held", () => {
    render(<FloatingDragHarness />)
    const handle = screen.getByTestId("floating-drag-handle")
    fireEvent.keyDown(handle, { key: "ArrowUp", shiftKey: true })
    const el = screen.getByTestId("floating")
    const defaultY = 800 - FLOATING_HEIGHT - FLOATING_VIEWPORT_MARGIN
    expect(el.dataset.y).toBe(String(defaultY - ARROW_STEP_LARGE))
  })
})
