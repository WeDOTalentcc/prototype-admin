"use client"

import { useCallback, useReducer } from "react"
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
}

const initialState: WizardState = {
  active: false,
  currentStage: null,
  stageData: {},
  completeness: 0,
  requiresApproval: false,
  stageHistory: [],
  threadId: null,
}

// --- Actions ---

type WizardAction =
  | { type: "STAGE_UPDATE"; payload: WizardStagePayload }
  | { type: "SET_THREAD"; threadId: string }
  | { type: "RESET" }

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
        stageHistory: state.currentStage && state.currentStage !== stage
          ? [...state.stageHistory, stage]
          : state.stageHistory.length === 0
            ? [stage]
            : state.stageHistory,
      }
    }
    case "SET_THREAD":
      return { ...state, threadId: action.threadId }
    case "RESET":
      return initialState
    default:
      return state
  }
}

// --- Hook ---

export function useWizardFlow() {
  const [state, dispatch] = useReducer(wizardReducer, initialState)

  const handleStagePayload = useCallback((payload: WizardStagePayload) => {
    dispatch({ type: "STAGE_UPDATE", payload })
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

    // Actions
    handleStagePayload,
    setThreadId,
    reset,
    isWizardMessage,
  }
}

export type WizardFlowReturn = ReturnType<typeof useWizardFlow>
