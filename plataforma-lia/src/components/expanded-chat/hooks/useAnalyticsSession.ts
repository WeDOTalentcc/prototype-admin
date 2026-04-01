"use client"

import { useRef, useEffect } from "react"

interface UseAnalyticsSessionParams {
  analytics: {
    startSession: () => string | null
    trackStageChange: (stage: string) => void
    completeSession: () => void
    trackSuggestion: (type: string, accepted: boolean) => void
  }
  isOpen: boolean
  mode: string
}

export function useAnalyticsSession({ analytics, isOpen, mode }: UseAnalyticsSessionParams) {
  // Use refs to avoid infinite loops from function dependencies
  const { startSession, trackStageChange, completeSession } = analytics
  const startSessionRef = useRef(startSession)
  const trackStageChangeRef = useRef(trackStageChange)
  const completeSessionRef = useRef(completeSession)
  const analyticsInitializedRef = useRef(false)

  // Keep refs updated
  startSessionRef.current = startSession
  trackStageChangeRef.current = trackStageChange
  completeSessionRef.current = completeSession

  useEffect(() => {
    // Only initialize once per modal open to prevent loops
    if (isOpen && mode === 'job-creation' && !analyticsInitializedRef.current) {
      analyticsInitializedRef.current = true
      const sessionId = startSessionRef.current()
      if (sessionId) {
        trackStageChangeRef.current('input-evaluation')
      }
    }

    // Reset flag when modal closes
    if (!isOpen) {
      analyticsInitializedRef.current = false
    }

    return () => {
      if (mode === 'job-creation' && analyticsInitializedRef.current) {
        completeSessionRef.current()
      }
    }
  }, [isOpen, mode])
}
