import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, act } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

vi.mock("@/contexts/lia-float-context", () => ({
  useLiaChatContext: () => ({ chatIsConnected: false }),
}))

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: (selector: (s: any) => any) => selector({ user: { id: "u-123" } }),
}))

import { UnifiedChatBubble } from "../UnifiedChatBubble"
import {
  BUBBLE_POSITION_STORAGE_KEY,
  BUBBLE_RESET_EVENT,
  getUserScopedKey,
} from "../floating-position"

const SCOPED_KEY = getUserScopedKey(BUBBLE_POSITION_STORAGE_KEY, "u-123")

beforeEach(() => {
  localStorage.clear()
  // Polyfill setPointerCapture / releasePointerCapture for jsdom
  if (!("setPointerCapture" in HTMLElement.prototype)) {
    HTMLElement.prototype.setPointerCapture = vi.fn() as any
    HTMLElement.prototype.releasePointerCapture = vi.fn() as any
  }
})

function pointerEvent(type: string, init: PointerEventInit) {
  // jsdom lacks PointerEvent — simulate via MouseEvent which carries the same fields we use.
  return new MouseEvent(type, { bubbles: true, cancelable: true, ...init }) as unknown as PointerEvent
}

describe("UnifiedChatBubble — click vs drag", () => {
  it("opens the chat when the user simply clicks the bubble (no movement)", () => {
    const onOpen = vi.fn()
    render(<UnifiedChatBubble onOpen={onOpen} />)
    const btn = screen.getByTestId("lia-bubble")
    fireEvent.pointerDown(btn, { clientX: 100, clientY: 100, pointerId: 1 })
    fireEvent.pointerUp(btn, { clientX: 100, clientY: 100, pointerId: 1 })
    expect(onOpen).toHaveBeenCalledTimes(1)
  })

  it("does NOT open the chat when the pointer moved past the drag threshold", () => {
    const onOpen = vi.fn()
    render(<UnifiedChatBubble onOpen={onOpen} />)
    const btn = screen.getByTestId("lia-bubble")
    btn.getBoundingClientRect = () =>
      ({ left: 50, top: 50, right: 106, bottom: 106, width: 56, height: 56, x: 50, y: 50, toJSON: () => ({}) } as DOMRect)
    fireEvent.pointerDown(btn, { clientX: 100, clientY: 100, pointerId: 1 })
    fireEvent.pointerMove(btn, { clientX: 200, clientY: 200, pointerId: 1 })
    fireEvent.pointerUp(btn, { clientX: 200, clientY: 200, pointerId: 1 })
    expect(onOpen).not.toHaveBeenCalled()
    // After a real drag, position is persisted under the user-scoped key
    expect(localStorage.getItem(SCOPED_KEY)).not.toBeNull()
  })
})

describe("UnifiedChatBubble — keyboard movement", () => {
  it("moves the bubble with arrow keys (8px steps, 32px with Shift)", () => {
    Object.defineProperty(window, "innerWidth", { value: 1280, configurable: true })
    Object.defineProperty(window, "innerHeight", { value: 800, configurable: true })

    const onOpen = vi.fn()
    render(<UnifiedChatBubble onOpen={onOpen} />)
    const btn = screen.getByTestId("lia-bubble")

    fireEvent.keyDown(btn, { key: "ArrowLeft" })
    const after1 = JSON.parse(localStorage.getItem(SCOPED_KEY) ?? "null")
    expect(after1).toBeTruthy()
    const x1 = after1.x

    fireEvent.keyDown(btn, { key: "ArrowLeft", shiftKey: true })
    const after2 = JSON.parse(localStorage.getItem(SCOPED_KEY) ?? "null")
    expect(after2.x).toBe(x1 - 32)
  })
})

describe("UnifiedChatBubble — reset position", () => {
  it("right-clicking the bubble clears the persisted position and dispatches the reset event", () => {
    localStorage.setItem(SCOPED_KEY, JSON.stringify({ x: 100, y: 100 }))
    const onOpen = vi.fn()
    const resetSpy = vi.fn()
    window.addEventListener(BUBBLE_RESET_EVENT, resetSpy)
    render(<UnifiedChatBubble onOpen={onOpen} />)
    const btn = screen.getByTestId("lia-bubble")
    fireEvent.contextMenu(btn)
    expect(localStorage.getItem(SCOPED_KEY)).toBeNull()
    expect(resetSpy).toHaveBeenCalled()
    window.removeEventListener(BUBBLE_RESET_EVENT, resetSpy)
  })

  it("listens to the global reset event and clears its position", () => {
    localStorage.setItem(SCOPED_KEY, JSON.stringify({ x: 100, y: 100 }))
    render(<UnifiedChatBubble onOpen={vi.fn()} />)
    act(() => {
      window.dispatchEvent(new CustomEvent(BUBBLE_RESET_EVENT))
    })
    expect(localStorage.getItem(SCOPED_KEY)).toBeNull()
  })
})

describe("UnifiedChatBubble — per-user persistence", () => {
  it("reads the per-user-scoped storage key on mount", () => {
    const stored = { x: 200, y: 300 }
    localStorage.setItem(SCOPED_KEY, JSON.stringify(stored))
    Object.defineProperty(window, "innerWidth", { value: 1280, configurable: true })
    Object.defineProperty(window, "innerHeight", { value: 800, configurable: true })
    render(<UnifiedChatBubble onOpen={vi.fn()} />)
    const btn = screen.getByTestId("lia-bubble") as HTMLElement
    expect(btn.style.left).toBe("200px")
    expect(btn.style.top).toBe("300px")
  })

  it("falls back to the legacy unscoped key when no per-user value exists", () => {
    localStorage.setItem(BUBBLE_POSITION_STORAGE_KEY, JSON.stringify({ x: 42, y: 42 }))
    Object.defineProperty(window, "innerWidth", { value: 1280, configurable: true })
    Object.defineProperty(window, "innerHeight", { value: 800, configurable: true })
    render(<UnifiedChatBubble onOpen={vi.fn()} />)
    const btn = screen.getByTestId("lia-bubble") as HTMLElement
    expect(btn.style.left).toBe("42px")
    expect(btn.style.top).toBe("42px")
  })

  it("reset is durable: legacy key is wiped on reset so reload stays at default", () => {
    // User had data in the legacy unscoped key
    localStorage.setItem(BUBBLE_POSITION_STORAGE_KEY, JSON.stringify({ x: 42, y: 42 }))
    const { unmount } = render(<UnifiedChatBubble onOpen={vi.fn()} />)
    // Reset (right-click)
    fireEvent.contextMenu(screen.getByTestId("lia-bubble"))
    expect(localStorage.getItem(SCOPED_KEY)).toBeNull()
    expect(localStorage.getItem(BUBBLE_POSITION_STORAGE_KEY)).toBeNull()
    unmount()
    // Simulate a reload — bubble should mount at the default position (no inline left/top)
    render(<UnifiedChatBubble onOpen={vi.fn()} />)
    const btn = screen.getByTestId("lia-bubble") as HTMLElement
    expect(btn.style.left).toBe("")
    expect(btn.style.top).toBe("")
  })
})
