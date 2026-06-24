import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useTypewriter } from "../useTypewriter"

describe("useTypewriter", () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it("starts empty and reveals progressively, then completes with full text", () => {
    const { result } = renderHook(() =>
      useTypewriter("hello world", { cps: 300 }),
    )
    expect(result.current.displayed).toBe("")
    expect(result.current.done).toBe(false)

    act(() => {
      vi.advanceTimersByTime(33)
    })
    expect(result.current.displayed.length).toBeGreaterThan(0)
    expect(result.current.displayed.length).toBeLessThan("hello world".length)

    act(() => {
      vi.advanceTimersByTime(5000)
    })
    expect(result.current.displayed).toBe("hello world")
    expect(result.current.done).toBe(true)
  })

  it("returns full text immediately when disabled (e.g. history load)", () => {
    const { result } = renderHook(() =>
      useTypewriter("instant text", { enabled: false }),
    )
    expect(result.current.displayed).toBe("instant text")
    expect(result.current.done).toBe(true)
  })

  it("never overshoots the source text", () => {
    const { result } = renderHook(() => useTypewriter("abc", { cps: 100000 }))
    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(result.current.displayed).toBe("abc")
    expect(result.current.displayed.length).toBe(3)
  })

  it("handles empty text without hanging", () => {
    const { result } = renderHook(() => useTypewriter("", { cps: 200 }))
    expect(result.current.displayed).toBe("")
    expect(result.current.done).toBe(true)
  })
})
