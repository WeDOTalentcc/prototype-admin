"use client"

/**
 * useTeamsSSO
 *
 * Handles Silent SSO for Teams Tab pages.
 *
 * Flow:
 * 1. Detect if the page is running inside a Teams iframe using @microsoft/teams-js
 * 2. Call authentication.getAuthToken() to get the SSO JWT silently
 * 3. Exchange it with our backend (/api/backend-proxy/teams/tab/auth) for a platform token
 * 4. Store the platform token in localStorage (same key used by the normal auth flow)
 * 5. Expose { isTeams, isAuthenticated, isLoading, teamsUserId, platformUserId,
 *    companyId, error, refresh }
 *
 * W2.3 fixes (auditoria 2026-04-26):
 *   - P1-9: companyId is now extracted from the auth response and exposed via state
 *   - P1-10: token refresh — periodic re-handshake every REFRESH_INTERVAL_MS
 *            (default 25min, just under the typical 30min token lifetime) plus
 *            a `refresh()` callback consumers can invoke on 401.
 */

import { useState, useEffect, useRef, useCallback } from "react"

interface TeamsSSOState {
  isTeams: boolean
  isAuthenticated: boolean
  isLoading: boolean
  teamsUserId: string | null
  platformUserId: string | null
  companyId: string | null
  error: string | null
}

interface TeamsSSOResult extends TeamsSSOState {
  /** Manually trigger a re-handshake. Use on 401 from API calls. */
  refresh: () => Promise<void>
}

const INITIAL_STATE: TeamsSSOState = {
  isTeams: false,
  isAuthenticated: false,
  isLoading: true,
  teamsUserId: null,
  platformUserId: null,
  companyId: null,
  error: null,
}

// Re-handshake every 25min. Teams SSO tokens typically live ~30min — this
// gives a 5min safety window. Exported as constant to allow tests to override.
export const REFRESH_INTERVAL_MS = 25 * 60 * 1000

export function useTeamsSSO(): TeamsSSOResult {
  const [state, setState] = useState<TeamsSSOState>(INITIAL_STATE)
  const initialized = useRef(false)
  const refreshTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const handshake = useCallback(async () => {
    // Dynamically import teams-js to avoid SSR issues
    let app: typeof import("@microsoft/teams-js").app
    let authentication: typeof import("@microsoft/teams-js").authentication
    try {
      const teamsJs = await import("@microsoft/teams-js")
      app = teamsJs.app
      authentication = teamsJs.authentication
    } catch {
      setState((s) => ({ ...s, isLoading: false }))
      return
    }

    try {
      await app.initialize()
    } catch {
      // Not inside Teams — fall through to normal auth
      setState((s) => ({ ...s, isLoading: false }))
      return
    }

    const isTeams = app.isInitialized()
    if (!isTeams) {
      setState((s) => ({ ...s, isLoading: false }))
      return
    }

    setState((s) => ({ ...s, isTeams: true }))

    try {
      const ssoToken = await authentication.getAuthToken()

      const res = await fetch("/api/backend-proxy/teams/tab/auth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sso_token: ssoToken }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "Auth failed" }))
        throw new Error(err.detail || err.error || `HTTP ${res.status}`)
      }

      const data = await res.json()
      const { access_token, user_id, teams_user_id, company_id } = data

      // Store platform token so existing API hooks work without changes
      if (typeof window !== "undefined" && access_token) {
        localStorage.setItem("access_token", access_token)
      }

      setState({
        isTeams: true,
        isAuthenticated: true,
        isLoading: false,
        teamsUserId: teams_user_id ?? null,
        platformUserId: user_id ?? null,
        companyId: company_id ?? null,
        error: null,
      })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "SSO failed"
      setState({
        isTeams: true,
        isAuthenticated: false,
        isLoading: false,
        teamsUserId: null,
        platformUserId: null,
        companyId: null,
        error: message,
      })
    }
  }, [])

  // Public refresh callback — consumers call on 401 to force re-handshake.
  const refresh = useCallback(async () => {
    await handshake()
  }, [handshake])

  useEffect(() => {
    if (initialized.current) return
    initialized.current = true

    handshake()

    // P1-10 fix: schedule periodic re-handshake to keep token fresh.
    refreshTimerRef.current = setInterval(() => {
      // Fire-and-forget; errors update state via handshake's catch.
      void handshake()
    }, REFRESH_INTERVAL_MS)

    return () => {
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current)
        refreshTimerRef.current = null
      }
    }
  }, [handshake])

  return { ...state, refresh }
}
