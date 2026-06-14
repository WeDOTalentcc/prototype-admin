"use client"

import React, { useEffect, useState, useCallback } from "react"
import { useTourMode } from "./tour/useTourMode"
import { TourController } from "./tour/TourController"
import { ONBOARDING_TOUR_STEPS } from "./tour/tour-steps"
import { OnboardingActionOrchestrator } from "./OnboardingActionOrchestrator"

/**
 * OnboardingChatPage — fullscreen chat wrapper for onboarding.
 *
 * 1. Fetches WhatsApp context from FastAPI
 * 2. Injects prior messages into chat
 * 3. Runs guided tour with TourController
 * 4. On complete, marks onboarding done
 *
 * Apply to: plataforma-lia/src/app/(dashboard)/onboarding/page.tsx
 * Wraps existing ChatPageFullscreen with onboarding context.
 */

interface Props {
  sessionId: string
  userId: number
  children?: React.ReactNode  // Slot for UnifiedChat component
}

interface OnboardingContext {
  whatsapp_messages: Array<{ direction: string; content: string; timestamp: string }>
  onboarding_data: Record<string, unknown>
}

export function OnboardingChatPage({ sessionId, userId, children }: Props) {
  const [context, setContext] = useState<OnboardingContext | null>(null)
  const [tourReady, setTourReady] = useState(false)
  const { tourActive, startTour, completeStep, endTour } = useTourMode()

  // Fetch WhatsApp context for handoff
  useEffect(() => {
    async function loadContext() {
      try {
        const resp = await fetch(`/api/backend-proxy/onboarding/${userId}/context`)
        if (resp.ok) {
          const data = await resp.json()
          setContext(data)
        }
      } catch (e) {
        console.warn("[Onboarding] Failed to load context:", e)
      }
      setTourReady(true)
    }
    loadContext()
  }, [userId])

  // Start tour when ready
  useEffect(() => {
    if (tourReady && !tourActive) {
      startTour()
    }
  }, [tourReady, tourActive, startTour])

  const handleStepComplete = useCallback((stepId: string) => {
    completeStep(stepId)
    // Report to backend
    fetch(`/api/backend-proxy/onboarding/progress`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ step_id: stepId }),
    }).catch(() => {})
  }, [completeStep])

  const handleTourComplete = useCallback(() => {
    endTour()
    // Report to backend
    fetch(`/api/backend-proxy/onboarding/progress`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phase: "action_choice" }),
    }).catch(() => {})
  }, [endTour])

  const sendLiaMessage = useCallback((text: string, metadata?: Record<string, unknown>) => {
    // Dispatch as chat message from LIA
    // The UnifiedChat component listens for these
    window.dispatchEvent(new CustomEvent("lia:onboarding-message", {
      detail: { text, metadata, sender: "assistant" },
    }))
  }, [])

  return (
    <div className="fixed inset-0 z-40 bg-lia-bg-primary flex flex-col">
      {/* Onboarding progress bar */}
      <OnboardingProgressBar
        completedSteps={tourActive ? [] : ["welcome", "tour"]}
        totalSteps={5}
      />

      {/* Body: orchestrator (left) + chat (right) */}
      <div className="flex-1 flex relative min-h-0">
        {tourReady && <OnboardingActionOrchestrator />}

        <div className="flex-1 relative min-w-0">
          {!tourReady ? (
            <div className="flex items-center justify-center h-full text-lia-text-secondary">
              <div className="text-center">
                <div className="w-6 h-6 mx-auto mb-3 border-2 border-wedo-cyan border-t-transparent rounded-full animate-spin" />
                <p className="text-sm">Preparando sua experiencia...</p>
              </div>
            </div>
          ) : (
            <div className="h-full">{children}</div>
          )}

          {tourActive && (
            <TourController
              steps={ONBOARDING_TOUR_STEPS}
              onStepComplete={handleStepComplete}
              onTourComplete={handleTourComplete}
              sendLiaMessage={sendLiaMessage}
            />
          )}
        </div>
      </div>
    </div>
  )
}

// === Progress bar ===

function OnboardingProgressBar({
  completedSteps,
  totalSteps,
}: {
  completedSteps: string[]
  totalSteps: number
}) {
  const STEPS = [
    { id: "whatsapp", label: "Conhecendo a LIA" },
    { id: "login", label: "Primeiro acesso" },
    { id: "tour", label: "Tour da plataforma" },
    { id: "action", label: "Primeira acao" },
    { id: "done", label: "Pronto!" },
  ]

  return (
    <div className="flex-shrink-0 px-6 py-3 bg-lia-bg-secondary">
      <div className="flex items-center gap-2 max-w-2xl mx-auto">
        {STEPS.map((step, i) => {
          const completed = completedSteps.includes(step.id) || i < completedSteps.length
          const active = i === completedSteps.length
          return (
            <React.Fragment key={step.id}>
              {i > 0 && (
                <div className={`flex-1 h-0.5 ${completed ? "bg-wedo-cyan" : "bg-lia-bg-tertiary"}`} />
              )}
              <div className="flex flex-col items-center gap-1">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-medium ${
                    completed
                      ? "bg-wedo-cyan text-white"
                      : active
                        ? "border-2 border-wedo-cyan text-wedo-cyan-text"
                        : "bg-lia-bg-tertiary text-lia-text-disabled"
                  }`}
                >
                  {completed ? "✓" : i + 1}
                </div>
                <span className={`text-[9px] whitespace-nowrap ${
                  completed || active ? "text-lia-text-primary" : "text-lia-text-disabled"
                }`}>
                  {step.label}
                </span>
              </div>
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}
