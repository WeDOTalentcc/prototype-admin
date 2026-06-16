"use client"

import { useCallback, useEffect, useState } from "react"

/**
 * useOnboardingFlow — gates onboarding using REAL setup progress.
 *
 * Source of truth: GET /api/backend-proxy/settings/progress (overall: 0..100).
 * - needsOnboarding when overall < COMPLETE_THRESHOLD (80%).
 * - >= 80% dismisses the banner (parity with SetupProgressBanner).
 *
 * The previous implementation derived gating from `activation_state` returned by
 * `/onboarding/status`, which did not reflect what the recruiter had actually
 * filled in Configurações. Acceptance criteria for Task #712 require that the
 * proactive onboarding be driven by setup_progress so that when the user
 * advances via chat OR via UI the gate flips automatically.
 */

const ONBOARDING_CHECKED_KEY = "lia-onboarding-checked"
const COMPLETE_THRESHOLD = 80

interface OnboardingFlowState {
  needsOnboarding: boolean
  sessionId: string | null
  setupProgress: number | null
  loading: boolean
}

interface ProgressPayload {
  overall?: number
  sections?: Record<string, number>
  setup_progress?: number
}

export function useOnboardingFlow() {
  const [state, setState] = useState<OnboardingFlowState>({
    needsOnboarding: false,
    sessionId: null,
    setupProgress: null,
    loading: true,
  })

  const evaluate = useCallback(async () => {
    try {
      const [progressRes, sessionRes] = await Promise.all([
        fetch("/api/backend-proxy/settings/progress/", { credentials: "include" }),
        fetch("/api/backend-proxy/onboarding/status", { credentials: "include" }).catch(
          () => null,
        ),
      ])

      let overall: number | null = null
      if (progressRes.ok) {
        const data: ProgressPayload = await progressRes.json()
        const raw =
          typeof data.overall === "number"
            ? data.overall
            : typeof data.setup_progress === "number"
              ? data.setup_progress
              : null
        if (typeof raw === "number" && Number.isFinite(raw)) {
          overall = Math.max(0, Math.min(100, raw))
        }
      }

      let sessionId: string | null = null
      if (sessionRes && sessionRes.ok) {
        try {
          const sd = await sessionRes.json()
          sessionId = sd?.session?.id ?? null
        } catch {
          sessionId = null
        }
      }

      const needsOnboarding = overall === null ? false : overall < COMPLETE_THRESHOLD

      setState({
        needsOnboarding,
        sessionId,
        setupProgress: overall,
        loading: false,
      })

      if (!needsOnboarding && typeof window !== "undefined") {
        sessionStorage.setItem(ONBOARDING_CHECKED_KEY, "true")
      }
    } catch {
      setState((prev) => ({ ...prev, loading: false }))
    }
  }, [])

  useEffect(() => {
    if (typeof window !== "undefined" && sessionStorage.getItem(ONBOARDING_CHECKED_KEY)) {
      // Still evaluate so completion thresholds reflect later UI/chat edits in
      // this session, but skip the redirect-y "needs" flip on the first paint.
      evaluate()
      return
    }
    evaluate()
  }, [evaluate])

  // Re-evaluate whenever a settings save happens (UI or chat) — keeps the
  // banner/gate honest without relying on a hard reload.
  useEffect(() => {
    if (typeof window === "undefined") return
    const handler = () => {
      evaluate()
    }
    window.addEventListener("lia:settings-success", handler)
    window.addEventListener("lia:settings-updated", handler)
    return () => {
      window.removeEventListener("lia:settings-success", handler)
      window.removeEventListener("lia:settings-updated", handler)
    }
  }, [evaluate])

  const markComplete = useCallback(async () => {
    try {
      await fetch("/api/backend-proxy/onboarding/progress", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phase: "complete" }),
        credentials: "include",
      })
      setState((prev) => ({ ...prev, needsOnboarding: false }))
      if (typeof window !== "undefined") {
        sessionStorage.setItem(ONBOARDING_CHECKED_KEY, "true")
      }
    } catch {
      /* ignore */
    }
  }, [])

  return {
    ...state,
    activationState: state.needsOnboarding ? "onboarding" : "active",
    markComplete,
  }
}
