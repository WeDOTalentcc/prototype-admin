/**
 * Tests for useAutoSave (GAP-06-005).
 *
 * Uses fake timers to control debounce timing without real async delays.
 */
import { renderHook, act } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"
import { useAutoSave } from "../useAutoSave"

describe("useAutoSave", () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it("calls onSave after debounce delay", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    renderHook(() => useAutoSave({ data: { x: 1 }, onSave, debounceMs: 1000 }))
    await act(async () => {
      vi.advanceTimersByTime(1000)
    })
    expect(onSave).toHaveBeenCalledTimes(1)
    expect(onSave).toHaveBeenCalledWith({ x: 1 })
  })

  it("debounces — resets timer on data change", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const { rerender } = renderHook(
      ({ data }) => useAutoSave({ data, onSave, debounceMs: 1000 }),
      { initialProps: { data: { x: 1 } } }
    )
    // Advance 500ms — not yet triggered
    await act(async () => {
      vi.advanceTimersByTime(500)
    })
    // Rerender with new data — timer resets
    rerender({ data: { x: 2 } })
    // Advance another 500ms — still only 500ms since last change
    await act(async () => {
      vi.advanceTimersByTime(500)
    })
    expect(onSave).not.toHaveBeenCalled()
    // Advance remaining 500ms — now 1000ms since last change
    await act(async () => {
      vi.advanceTimersByTime(500)
    })
    expect(onSave).toHaveBeenCalledTimes(1)
    expect(onSave).toHaveBeenCalledWith({ x: 2 })
  })

  it("does not save when disabled=true", async () => {
    const onSave = vi.fn()
    renderHook(() =>
      useAutoSave({ data: { x: 1 }, onSave, debounceMs: 500, disabled: true })
    )
    await act(async () => {
      vi.advanceTimersByTime(3000)
    })
    expect(onSave).not.toHaveBeenCalled()
  })

  it("triggerSave fires save immediately without waiting for debounce", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const { result } = renderHook(() =>
      useAutoSave({ data: { x: 1 }, onSave, debounceMs: 5000 })
    )
    // Don't advance timers — call triggerSave instead
    await act(async () => {
      result.current.triggerSave()
    })
    expect(onSave).toHaveBeenCalledTimes(1)
  })

  it("sets lastSavedAt after successful save", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const { result } = renderHook(() =>
      useAutoSave({ data: { x: 1 }, onSave, debounceMs: 100 })
    )
    expect(result.current.lastSavedAt).toBeNull()
    await act(async () => {
      vi.advanceTimersByTime(100)
    })
    expect(result.current.lastSavedAt).toBeInstanceOf(Date)
  })
})
