import { useEffect, useRef } from "react"

/**
 * Calls `onTimeout` if `isLoading` remains true for longer than `ms` milliseconds.
 * The timer is reset whenever `isLoading` changes back to false.
 *
 * @param isLoading - Whether the loading state is currently active.
 * @param onTimeout - Callback invoked when the watchdog fires.
 * @param ms        - Maximum tolerated loading duration in milliseconds (default 20 000).
 */
export function useLoadingWatchdog(
  isLoading: boolean,
  onTimeout: () => void,
  ms: number = 20_000
): void {
  const onTimeoutRef = useRef(onTimeout)
  onTimeoutRef.current = onTimeout

  useEffect(() => {
    if (!isLoading) return

    const id = setTimeout(() => {
      onTimeoutRef.current()
    }, ms)

    return () => clearTimeout(id)
  }, [isLoading, ms])
}
