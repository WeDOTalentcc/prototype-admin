"use client"

import { useCallback, useReducer, useEffect } from "react"
import type {
  WizardStage,
  WizardStagePayload,
  ScreeningMode,
} from "./wizard-types"

/**
 * useWizardFlow — manages wizard state from wizard_stage WS messages.
 *
 * Listens for wizard_stage payloads dispatched by the backend graph.
 * Provides stage data, completeness, and HITL approval helpers.
 *
 * Usage:
 *   const wizard = useWizardFlow()
 *   // When WS message arrives:
 *   wizard.handleStagePayload(payload)
 *   // In panels:
 *   wizard.currentStage, wizard.stageData, wizard.completeness
 */

// --- State ---

interface WizardState {
  active: boolean
  currentStage: WizardStage | null
  stageData: Record<string, unknown>
  completeness: number
  requiresApproval: boolean
  stageHistory: WizardStage[]
  threadId: string | null
  error: string | null
}

const initialState: WizardState = {
  active: false,
  currentStage: null,
  stageData: {},
  completeness: 0,
  requiresApproval: false,
  stageHistory: [],
  threadId: null,
  error: null,
}

// --- Actions ---

type WizardAction =
  | { type: "STAGE_UPDATE"; payload: WizardStagePayload }
  | { type: "APPROVE_STAGE" }
  | { type: "REJECT_STAGE" }
  | { type: "UPDATE_STAGE_DATA"; updates: Record<string, unknown> }
  | { type: "SET_ERROR"; error: string }
  | { type: "CLEAR_ERROR" }
  | { type: "SET_THREAD"; threadId: string }
  | { type: "RESET" }

function buildHistory(current: WizardStage | null, next: WizardStage, history: WizardStage[]): WizardStage[] {
  // Always include all visited stages in order
  if (history.length === 0) {
    return [next]
  }
  if (current && current !== next && !history.includes(next)) {
    return [...history, next]
  }
  return history
}

function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case "STAGE_UPDATE": {
      const { stage, data, completeness, requires_approval } = action.payload
      return {
        ...state,
        active: true,
        currentStage: stage,
        stageData: data,
        completeness,
        requiresApproval: requires_approval,
        stageHistory: buildHistory(state.currentStage, stage, state.stageHistory),
        error: null,
      }
    }
    case "APPROVE_STAGE":
      return {
        ...state,
        requiresApproval: false,
      }
    case "REJECT_STAGE":
      return {
        ...state,
        requiresApproval: false,
      }
    case "UPDATE_STAGE_DATA":
      return {
        ...state,
        stageData: { ...state.stageData, ...action.updates },
      }
    case "SET_ERROR":
      return {
        ...state,
        error: action.error,
      }
    case "CLEAR_ERROR":
      return {
        ...state,
        error: null,
      }
    case "SET_THREAD":
      return { ...state, threadId: action.threadId }
    case "RESET":
      return initialState
    default:
      return state
  }
}

// --- Persistence ---

const WIZARD_STORAGE_KEY = "lia-wizard-state"

function loadPersistedState(): WizardState {
  if (typeof window === "undefined") return initialState
  try {
    const stored = localStorage.getItem(WIZARD_STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored) as WizardState
      if (parsed.active && parsed.currentStage) return parsed
    }
  } catch { /* ignore */ }
  return initialState
}

function persistState(state: WizardState): void {
  if (typeof window === "undefined") return
  try {
    if (state.active) {
      localStorage.setItem(WIZARD_STORAGE_KEY, JSON.stringify(state))
    } else {
      localStorage.removeItem(WIZARD_STORAGE_KEY)
    }
  } catch { /* ignore */ }
}

// --- Hook ---

export function useWizardFlow() {
  const [state, dispatch] = useReducer(wizardReducer, initialState, loadPersistedState)

  // Persist state changes to localStorage
  useEffect(() => {
    persistState(state)
  }, [state])

  const handleStagePayload = useCallback((payload: WizardStagePayload) => {
    dispatch({ type: "STAGE_UPDATE", payload })
  }, [])

  const approveStage = useCallback(() => {
    dispatch({ type: "APPROVE_STAGE" })
  }, [])

  const rejectStage = useCallback(() => {
    dispatch({ type: "REJECT_STAGE" })
  }, [])

  const updateStageData = useCallback((updates: Record<string, unknown>) => {
    dispatch({ type: "UPDATE_STAGE_DATA", updates })
  }, [])

  const setError = useCallback((error: string) => {
    dispatch({ type: "SET_ERROR", error })
  }, [])

  const clearError = useCallback(() => {
    dispatch({ type: "CLEAR_ERROR" })
  }, [])

  const setThreadId = useCallback((threadId: string) => {
    dispatch({ type: "SET_THREAD", threadId })
  }, [])

  const reset = useCallback(() => {
    dispatch({ type: "RESET" })
  }, [])

  /**
   * Check if a WS message is a wizard_stage payload.
   * Call from the WS message handler in useLiaChatContext.
   */
  const isWizardMessage = useCallback((msg: Record<string, unknown>): msg is WizardStagePayload => {
    return msg?.type === "wizard_stage" && typeof msg?.stage === "string"
  }, [])

  return {
    // State
    active: state.active,
    currentStage: state.currentStage,
    stageData: state.stageData,
    completeness: state.completeness,
    requiresApproval: state.requiresApproval,
    stageHistory: state.stageHistory,
    threadId: state.threadId,
    error: state.error,

    // Actions
    handleStagePayload,
    approveStage,
    rejectStage,
    updateStageData,
    setError,
    clearError,
    setThreadId,
    reset,
    isWizardMessage,
  }
}

export type WizardFlowReturn = ReturnType<typeof useWizardFlow>
