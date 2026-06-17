"use client"

import { useState, useCallback, useEffect } from "react"

export interface TourState {
  active: boolean
  currentStepId: string | null
  completedSteps: string[]
  startedAt: number | null
}

const TOUR_STORAGE_KEY = "lia-onboarding-tour"

function loadTourState(): TourState {
  if (typeof window === "undefined") return { active: false, currentStepId: null, completedSteps: [], startedAt: null }
  try {
    const stored = localStorage.getItem(TOUR_STORAGE_KEY)
    if (stored) return JSON.parse(stored)
  } catch { /* ignore */ }
  return { active: false, currentStepId: null, completedSteps: [], startedAt: null }
}

function persistTourState(state: TourState): void {
  if (typeof window === "undefined") return
  try {
    if (state.active) {
      localStorage.setItem(TOUR_STORAGE_KEY, JSON.stringify(state))
    } else {
      localStorage.removeItem(TOUR_STORAGE_KEY)
    }
  } catch { /* ignore */ }
}

/**
 * useTourMode — manages tour state with localStorage persistence.
 *
 * Survives page reload. Tracks which steps are complete.
 */
export function useTourMode() {
  const [state, setState] = useState<TourState>(loadTourState)

  useEffect(() => {
    persistTourState(state)
  }, [state])

  const startTour = useCallback(() => {
    setState({
      active: true,
      currentStepId: null,
      completedSteps: [],
      startedAt: Date.now(),
    })
  }, [])

  const completeStep = useCallback((stepId: string) => {
    setState((prev) => ({
      ...prev,
      completedSteps: prev.completedSteps.includes(stepId)
        ? prev.completedSteps
        : [...prev.completedSteps, stepId],
      currentStepId: stepId,
    }))
  }, [])

  const endTour = useCallback(() => {
    setState({
      active: false,
      currentStepId: null,
      completedSteps: [],
      startedAt: null,
    })
  }, [])

  return {
    tourActive: state.active,
    currentStepId: state.currentStepId,
    completedSteps: state.completedSteps,
    startTour,
    completeStep,
    endTour,
  }
}
