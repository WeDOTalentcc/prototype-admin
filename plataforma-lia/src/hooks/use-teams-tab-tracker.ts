"use client"

/**
 * useTeamsTabTracker
 *
 * Tracks recruiter behavior inside the Teams Tab iframe and fires proactive
 * messages when complex actions are detected.
 *
 * Usage:
 *   const { trackEvent } = useTeamsTabTracker({ teamsUserId, platformUserId })
 *
 *   <Button onClick={() => { trackEvent("click_create_job"); /* normal action * / }}>
 *     Nova vaga
 *   </Button>
 *
 * The hook also fires a "prolonged_stay" event automatically after PROLONGED_STAY_MS
 * of inactivity on the same page (default: 3 minutes).
 */

import { useCallback, useEffect, useRef } from "react"

const PROLONGED_STAY_MS = 3 * 60 * 1000 // 3 minutes

interface TrackerOptions {
  teamsUserId?: string | null
  platformUserId?: string | null
  /** Pass entity id when tracking actions on a specific resource */
  entityId?: string | null
  entityType?: string | null
}

interface UseTeamsTabTrackerReturn {
  trackEvent: (eventType: string, overrides?: Partial<TrackerOptions>) => void
}

export function useTeamsTabTracker(options: TrackerOptions = {}): UseTeamsTabTrackerReturn {
  const { teamsUserId, platformUserId, entityId, entityType } = options
  const prolongedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const firedProlongedRef = useRef(false)

  const sendEvent = useCallback(
    async (
      eventType: string,
      overrides: Partial<TrackerOptions> = {},
    ) => {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null

      const payload = {
        event_type: eventType,
        entity_type: overrides.entityType ?? entityType ?? null,
        entity_id: overrides.entityId ?? entityId ?? null,
        teams_user_id: overrides.teamsUserId ?? teamsUserId ?? null,
        platform_user_id: overrides.platformUserId ?? platformUserId ?? null,
        context: {
          url: typeof window !== "undefined" ? window.location.pathname : null,
          timestamp: new Date().toISOString(),
        },
      }

      try {
        await fetch("/api/backend-proxy/teams/tab/events", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(payload),
        })
      } catch {
        // Fire-and-forget — never block the UI on this
      }
    },
    [teamsUserId, platformUserId, entityId, entityType],
  )

  const trackEvent = useCallback(
    (eventType: string, overrides: Partial<TrackerOptions> = {}) => {
      sendEvent(eventType, overrides)
    },
    [sendEvent],
  )

  // Auto-fire prolonged_stay after 3 minutes on the page
  useEffect(() => {
    if (firedProlongedRef.current) return

    prolongedTimerRef.current = setTimeout(() => {
      if (!firedProlongedRef.current) {
        firedProlongedRef.current = true
        sendEvent("prolonged_stay")
      }
    }, PROLONGED_STAY_MS)

    return () => {
      if (prolongedTimerRef.current) clearTimeout(prolongedTimerRef.current)
    }
  }, [sendEvent])

  return { trackEvent }
}
