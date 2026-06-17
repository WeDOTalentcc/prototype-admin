"use client"

import { useRef, useCallback, useEffect, useState } from "react"

const HOVER_OPEN_DELAY = 200
const HOVER_CLOSE_DELAY = 300

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false)
  useEffect(() => {
    const mql = window.matchMedia("(prefers-reduced-motion: reduce)")
    setReduced(mql.matches)
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches)
    mql.addEventListener("change", handler)
    return () => mql.removeEventListener("change", handler)
  }, [])
  return reduced
}

export interface UseHoverDebounceOptions {
  onExpand: () => void
  onCollapse: () => void
  isEnabled: boolean
  openDelay?: number
  closeDelay?: number
}

export function useHoverDebounce({
  onExpand,
  onCollapse,
  isEnabled,
  openDelay = HOVER_OPEN_DELAY,
  closeDelay = HOVER_CLOSE_DELAY,
}: UseHoverDebounceOptions) {
  const openTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reducedMotion = usePrefersReducedMotion()

  const clearTimers = useCallback(() => {
    if (openTimerRef.current) {
      clearTimeout(openTimerRef.current)
      openTimerRef.current = null
    }
    if (closeTimerRef.current) {
      clearTimeout(closeTimerRef.current)
      closeTimerRef.current = null
    }
  }, [])

  useEffect(() => {
    clearTimers()
  }, [isEnabled, clearTimers])

  const handleMouseEnter = useCallback(() => {
    if (!isEnabled) return

    if (closeTimerRef.current) {
      clearTimeout(closeTimerRef.current)
      closeTimerRef.current = null
    }

    if (openTimerRef.current) {
      clearTimeout(openTimerRef.current)
      openTimerRef.current = null
    }

    const delay = reducedMotion ? 0 : openDelay
    openTimerRef.current = setTimeout(() => {
      onExpand()
      openTimerRef.current = null
    }, delay)
  }, [isEnabled, onExpand, openDelay, reducedMotion])

  const handleMouseLeave = useCallback(() => {
    if (openTimerRef.current) {
      clearTimeout(openTimerRef.current)
      openTimerRef.current = null
    }

    if (!isEnabled) return

    if (closeTimerRef.current) {
      clearTimeout(closeTimerRef.current)
      closeTimerRef.current = null
    }

    const delay = reducedMotion ? 0 : closeDelay
    closeTimerRef.current = setTimeout(() => {
      onCollapse()
      closeTimerRef.current = null
    }, delay)
  }, [isEnabled, onCollapse, closeDelay, reducedMotion])

  useEffect(() => {
    return () => clearTimers()
  }, [clearTimers])

  return { handleMouseEnter, handleMouseLeave, reducedMotion }
}

export { usePrefersReducedMotion, HOVER_OPEN_DELAY, HOVER_CLOSE_DELAY }
