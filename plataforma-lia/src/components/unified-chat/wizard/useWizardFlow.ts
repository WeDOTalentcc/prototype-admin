"use client"

import { useCallback, useReducer, useEffect, useState } from "react"
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
  // Replace the in-memory state wholesale with one rehydrated from the
  // active storage namespace. Used when `userId` flips mid-session so we
  // never carry recruiter A's state into recruiter B's session (LGPD).
  | { type: "REHYDRATE"; state: WizardState }

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
    case "REHYDRATE":
      return action.state
    default:
      return state
  }
}

// --- Persistence ---
//
// Wizard state contains the in-flight job posting (raw input, JD draft,
// competencies, salary band, etc.) and may include candidate-shaped data
// once calibration starts — i.e. data of the recruiter's tenant. To avoid
// leaking that across users on a shared browser (LGPD + multi-tenant),
// the localStorage key is namespaced by `userId`. Without a `userId`
// (logged-out / SSR / pre-auth render) we **do not persist at all** — a
// global "lia-wizard-state" key would silently bleed between sessions.

const WIZARD_STORAGE_KEY_PREFIX = "lia-wizard-state"

/** Returns the per-user storage key, or `null` when persistence must be skipped. */
export function getWizardStorageKey(userId: string | null | undefined): string | null {
  if (typeof userId !== "string") return null
  const trimmed = userId.trim()
  if (trimmed === "") return null
  return `${WIZARD_STORAGE_KEY_PREFIX}-${trimmed}`
}

function loadPersistedState(storageKey: string | null): WizardState {
  if (storageKey === null) return initialState
  if (typeof window === "undefined") return initialState
  try {
    const stored = localStorage.getItem(storageKey)
    if (stored) {
      const parsed = JSON.parse(stored) as WizardState
      if (parsed.active && parsed.currentStage) return parsed
    }
  } catch { /* ignore */ }
  return initialState
}

function persistState(state: WizardState, storageKey: string | null): void {
  if (storageKey === null) return
  if (typeof window === "undefined") return
  try {
    if (state.active) {
      localStorage.setItem(storageKey, JSON.stringify(state))
    } else {
      localStorage.removeItem(storageKey)
    }
  } catch { /* ignore */ }
}

// --- Hook ---

export interface UseWizardFlowOptions {
  /**
   * User identifier used to namespace the wizard's localStorage key so
   * recruiter A's in-flight job doesn't bleed to recruiter B on a shared
   * browser (LGPD + multi-tenant). When omitted/null the wizard works
   * normally but its state is **not persisted** across reloads.
   */
  userId?: string | null
}

export function useWizardFlow(options: UseWizardFlowOptions = {}) {
  const { userId = null } = options
  const storageKey = getWizardStorageKey(userId)
  const [state, dispatch] = useReducer(
    wizardReducer,
    initialState,
    () => loadPersistedState(storageKey),
  )

  // Track which `storageKey` the current `state` belongs to. When the
  // identity changes mid-session (recruiter A logs out → B logs in,
  // hydration finally produces a userId, etc.) we must (1) drop A's
  // in-memory wizard state and (2) hydrate B's namespace from disk
  // **before** any persist effect runs — otherwise the persist effect
  // would write A's stale state under B's storage key, defeating the
  // whole namespacing exercise (LGPD cross-tenant bleed). Doing the
  // dispatch during render via the "Adjusting state during rendering"
  // pattern guarantees React commits the rehydrated state before the
  // persist effect fires, so no intermediate write happens.
  const [prevStorageKey, setPrevStorageKey] = useState<string | null>(storageKey)
  if (prevStorageKey !== storageKey) {
    setPrevStorageKey(storageKey)
    dispatch({ type: "REHYDRATE", state: loadPersistedState(storageKey) })
  }

  // Persist state changes to localStorage (no-op when storageKey is null)
  useEffect(() => {
    persistState(state, storageKey)
  }, [state, storageKey])

  // Subscribe to the canonical `lia:wizard-stage-payload` window event so the
  // hook is self-sufficient when mounted on the chat surface. The event is
  // emitted by `useChatSocket` for every backend `ws_stage_payload`. We update
  // local state directly via `dispatch` here (no re-dispatch) to avoid the
  // feedback loop with `handleStagePayload` below.
  useEffect(() => {
    if (typeof window === "undefined") return
    function handle(event: Event) {
      const payload = (event as CustomEvent).detail as WizardStagePayload | undefined
      if (!payload || payload.type !== "wizard_stage" || typeof payload.stage !== "string") return
      // Onda 2 (PLAN_FIX_wizard_memory_loss 2026-05-10): if backend ships
      // thread_id, persist it via SET_THREAD so HITL approval and refresh
      // can recover the LangGraph checkpointer thread.
      if (typeof payload.thread_id === "string" && payload.thread_id.length > 0) {
        dispatch({ type: "SET_THREAD", threadId: payload.thread_id })
      }
      dispatch({ type: "STAGE_UPDATE", payload })
    }
    window.addEventListener("lia:wizard-stage-payload", handle as EventListener)
    return () => window.removeEventListener("lia:wizard-stage-payload", handle as EventListener)
  }, [])

  const handleStagePayload = useCallback((payload: WizardStagePayload) => {
    dispatch({ type: "STAGE_UPDATE", payload })
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("lia:wizard-stage-payload", { detail: payload }),
      )
    }
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
  const isWizardMessage = useCallback((msg: Record<string, unknown>): msg is Record<string, unknown> & WizardStagePayload => {
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
