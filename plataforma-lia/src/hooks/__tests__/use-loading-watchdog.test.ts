/**
 * Unit tests — useLoadingWatchdog
 *
 * Layer 2 — Unit (jsdom + fake timers)
 * Covers:
 *   1. Callback fires after the configured timeout while isLoading stays true.
 *   2. Timer is cancelled when isLoading flips to false — callback never called.
 *   3. Callback is NOT called early (before the deadline elapses).
 */

import { renderHook, act } from "@testing-library/react"
import { useLoadingWatchdog } from "../shared/use-loading-watchdog"

describe("useLoadingWatchdog", () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("fires the callback after the specified timeout when isLoading stays true", () => {
    const onTimeout = vi.fn()

    renderHook(() => useLoadingWatchdog(true, onTimeout, 5_000))

    expect(onTimeout).not.toHaveBeenCalled()

    act(() => {
      vi.advanceTimersByTime(5_000)
    })

    expect(onTimeout).toHaveBeenCalledTimes(1)
  })

  it("does NOT call the callback before the deadline elapses", () => {
    const onTimeout = vi.fn()

    renderHook(() => useLoadingWatchdog(true, onTimeout, 5_000))

    act(() => {
      vi.advanceTimersByTime(4_999)
    })

    expect(onTimeout).not.toHaveBeenCalled()
  })

  it("cancels the timer and never calls the callback when isLoading flips to false", () => {
    const onTimeout = vi.fn()

    const { rerender } = renderHook(
      ({ loading }: { loading: boolean }) =>
        useLoadingWatchdog(loading, onTimeout, 5_000),
      { initialProps: { loading: true } }
    )

    act(() => {
      vi.advanceTimersByTime(3_000)
    })

    expect(onTimeout).not.toHaveBeenCalled()

    rerender({ loading: false })

    act(() => {
      vi.advanceTimersByTime(5_000)
    })

    expect(onTimeout).not.toHaveBeenCalled()
  })

  it("does not start the timer when isLoading begins as false", () => {
    const onTimeout = vi.fn()

    renderHook(() => useLoadingWatchdog(false, onTimeout, 5_000))

    act(() => {
      vi.advanceTimersByTime(10_000)
    })

    expect(onTimeout).not.toHaveBeenCalled()
  })

  it("uses the default 20 000 ms timeout when no ms argument is provided", () => {
    const onTimeout = vi.fn()

    renderHook(() => useLoadingWatchdog(true, onTimeout))

    act(() => {
      vi.advanceTimersByTime(19_999)
    })
    expect(onTimeout).not.toHaveBeenCalled()

    act(() => {
      vi.advanceTimersByTime(1)
    })
    expect(onTimeout).toHaveBeenCalledTimes(1)
  })
})
