"use client"

import { useState, useEffect, useCallback } from "react"

/**
 * useOnboardingFlow — detects first login and manages onboarding state.
 *
 * Checks auth store for activation_state and first_login flag.
 * Redirects to /onboarding if needed.
 *
 * Usage in layout:
 *   const { needsOnboarding, sessionId } = useOnboardingFlow()
 *   if (needsOnboarding) router.push("/onboarding")
 */

interface OnboardingFlowState {
  needsOnboarding: boolean
  sessionId: string | null
  activationState: string | null
  loading: boolean
}

const ONBOARDING_CHECKED_KEY = "lia-onboarding-checked"

export function useOnboardingFlow() {
  const [state, setState] = useState<OnboardingFlowState>({
    needsOnboarding: false,
    sessionId: null,
    activationState: null,
    loading: true,
  })

  useEffect(() => {
    async function checkOnboarding() {
      // Skip if already checked this session
      if (typeof window !== "undefined" && sessionStorage.getItem(ONBOARDING_CHECKED_KEY)) {
        setState((prev) => ({ ...prev, loading: false }))
        return
      }

      try {
        const resp = await fetch("/api/backend-proxy/onboarding/status", {
          credentials: "include",
        })

        if (!resp.ok) {
          setState((prev) => ({ ...prev, loading: false }))
          return
        }

        const data = await resp.json()
        const needsOnboarding =
          data.activation_state === "onboarding" &&
          !data.onboarding_completed &&
          data.session?.phase !== "complete"

        setState({
          needsOnboarding,
          sessionId: data.session?.id ?? null,
          activationState: data.activation_state,
          loading: false,
        })

        // Mark as checked so we don't re-check on every navigation
        if (!needsOnboarding && typeof window !== "undefined") {
          sessionStorage.setItem(ONBOARDING_CHECKED_KEY, "true")
        }
      } catch {
        setState((prev) => ({ ...prev, loading: false }))
      }
    }

    checkOnboarding()
  }, [])

  const markComplete = useCallback(async () => {
    try {
      await fetch("/api/backend-proxy/onboarding/progress", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phase: "complete" }),
        credentials: "include",
      })
      setState((prev) => ({ ...prev, needsOnboarding: false, activationState: "active" }))
      if (typeof window !== "undefined") {
        sessionStorage.setItem(ONBOARDING_CHECKED_KEY, "true")
      }
    } catch { /* ignore */ }
  }, [])

  return {
    ...state,
    markComplete,
  }
}
