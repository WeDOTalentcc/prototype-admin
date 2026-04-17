/**
 * Unit test — useScreeningConfig watchdog path
 *
 * Layer 2 — Hook (jsdom + fake timers)
 *
 * Covers Task #260 acceptance criterion:
 *   When the initial fetch for the screening config stalls past 20 s, the
 *   hook must transition out of the loading state and surface
 *   "Tempo limite de carregamento excedido" through `loadError` so the UI
 *   can render an error/retry banner instead of spinning forever.
 */

import { renderHook, act } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"

import { useScreeningConfig } from "../recruitment/useScreeningConfig"

describe("useScreeningConfig — loading watchdog", () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.useFakeTimers()
    // fetch never resolves — simulates a hung backend.
    fetchMock = vi.fn(() => new Promise(() => {}))
    vi.stubGlobal("fetch", fetchMock)
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it("surfaces 'Tempo limite de carregamento excedido' after 20 s when the initial fetch hangs", async () => {
    const { result } = renderHook(() => useScreeningConfig("job-123"))

    // Initial render queues the fetch effect — let it run.
    await act(async () => {
      await Promise.resolve()
    })

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(result.current.isLoading).toBe(true)
    expect(result.current.loadError).toBeNull()

    // Just before the 20 s deadline — still loading, no error.
    await act(async () => {
      vi.advanceTimersByTime(19_999)
    })
    expect(result.current.isLoading).toBe(true)
    expect(result.current.loadError).toBeNull()

    // Cross the deadline — watchdog fires.
    await act(async () => {
      vi.advanceTimersByTime(1)
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.loadError).toBe(
      "Tempo limite de carregamento excedido",
    )
  })
})
