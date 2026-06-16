"use client"

import React, { useState, useCallback, useEffect, useRef } from "react"
import { TourSpotlight } from "./TourSpotlight"
import { useTourAutoFill } from "./TourAutoFill"

export interface TourStep {
  id: string
  /** Chat message LIA sends before this step */
  message: string
  /** Action type */
  type: "spotlight" | "autofill" | "screenshot" | "navigate" | "message_only"
  /** CSS selector for spotlight/autofill target */
  selector?: string
  /** Position for spotlight tooltip */
  position?: "top" | "bottom" | "left" | "right"
  /** Value to autofill */
  autofillValue?: string
  /** Autofill speed (ms per char) */
  autofillSpeed?: number
  /** Screenshot URL for inline chat image */
  screenshotUrl?: string
  /** Navigation target page */
  navigateTo?: string
  /** Auto-advance after N ms (0 = wait for user) */
  autoAdvanceMs?: number
  /** Spotlight tooltip text (if different from message) */
  spotlightText?: string
}

interface TourControllerProps {
  steps: TourStep[]
  onStepComplete: (stepId: string) => void
  onTourComplete: () => void
  /** Send message to chat as LIA */
  sendLiaMessage: (text: string, metadata?: Record<string, unknown>) => void
}

/**
 * TourController — orchestrates a sequence of tour steps.
 *
 * Coordinates: LIA chat messages → spotlight → autofill → screenshots.
 * Each step: LIA speaks in chat, then the visual action happens.
 */
export function TourController({
  steps,
  onStepComplete,
  onTourComplete,
  sendLiaMessage,
}: TourControllerProps) {
  const [currentIdx, setCurrentIdx] = useState(0)
  const [showSpotlight, setShowSpotlight] = useState(false)
  const { startAutoFill, cancelAutoFill } = useTourAutoFill()
  const advanceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const currentStep = steps[currentIdx] ?? null

  // Execute current step
  useEffect(() => {
    if (!currentStep) {
      onTourComplete()
      return
    }

    // Send LIA message first
    if (currentStep.message) {
      const metadata: Record<string, unknown> = {}
      if (currentStep.screenshotUrl) {
        metadata.screenshot = currentStep.screenshotUrl
      }
      sendLiaMessage(currentStep.message, Object.keys(metadata).length ? metadata : undefined)
    }

    // Brief delay, then execute visual action
    const actionTimer = setTimeout(() => {
      switch (currentStep.type) {
        case "spotlight":
          setShowSpotlight(true)
          break

        case "autofill":
          if (currentStep.selector && currentStep.autofillValue) {
            // Show spotlight first, then autofill
            setShowSpotlight(true)
            setTimeout(() => {
              setShowSpotlight(false)
              startAutoFill({
                selector: currentStep.selector!,
                value: currentStep.autofillValue!,
                typeSpeed: currentStep.autofillSpeed || 50,
                onComplete: () => advanceStep(),
              })
            }, 2000)
            return // Don't auto-advance yet
          }
          break

        case "navigate":
          if (currentStep.navigateTo) {
            window.dispatchEvent(new CustomEvent("lia:navigation-hint", {
              detail: { page: currentStep.navigateTo },
            }))
          }
          break

        case "screenshot":
        case "message_only":
          // Just the chat message, no visual action
          break
      }

      // Auto-advance if configured
      if (currentStep.autoAdvanceMs && currentStep.autoAdvanceMs > 0) {
        advanceTimerRef.current = setTimeout(() => advanceStep(), currentStep.autoAdvanceMs)
      }
    }, 800) // Delay after chat message

    return () => {
      clearTimeout(actionTimer)
      if (advanceTimerRef.current) clearTimeout(advanceTimerRef.current)
      cancelAutoFill()
    }
  }, [currentIdx])

  const advanceStep = useCallback(() => {
    if (!currentStep) return

    setShowSpotlight(false)
    onStepComplete(currentStep.id)

    if (currentIdx + 1 >= steps.length) {
      onTourComplete()
    } else {
      setCurrentIdx((prev) => prev + 1)
    }
  }, [currentIdx, currentStep, steps.length, onStepComplete, onTourComplete])

  return (
    <>
      {showSpotlight && currentStep?.selector && (
        <TourSpotlight
          selector={currentStep.selector}
          message={currentStep.spotlightText || currentStep.message}
          position={currentStep.position || "bottom"}
          onDismiss={advanceStep}
        />
      )}
    </>
  )
}
