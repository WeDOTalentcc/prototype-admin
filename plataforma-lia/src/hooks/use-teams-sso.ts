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
 * 5. Expose { isTeams, isAuthenticated, isLoading, teamsUserId, error }
 */

import { useState, useEffect, useRef } from "react"

interface TeamsSSOState {
  isTeams: boolean
  isAuthenticated: boolean
  isLoading: boolean
  teamsUserId: string | null
  platformUserId: string | null
  error: string | null
}

const INITIAL_STATE: TeamsSSOState = {
  isTeams: false,
  isAuthenticated: false,
  isLoading: true,
  teamsUserId: null,
  platformUserId: null,
  error: null,
}

export function useTeamsSSO(): TeamsSSOState {
  const [state, setState] = useState<TeamsSSOState>(INITIAL_STATE)
  const initialized = useRef(false)

  useEffect(() => {
    if (initialized.current) return
    initialized.current = true

    const run = async () => {
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

      // Check if we're inside Teams
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
        // Get SSO token from Teams SDK (silent, no popup)
        const ssoToken = await authentication.getAuthToken()

        // Exchange with our backend
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
        const { access_token, user_id, teams_user_id } = data

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
          error: message,
        })
      }
    }

    run()
  }, [])

  return state
}
