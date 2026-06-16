"use client"

import { useCallback, useReducer, useEffect, useRef } from "react"
import type {
  WizardStage,
  WizardStagePayload,
  ScreeningMode,
  WizardPipelineTemplateSuggestion,
  WizardStagePayloadWithUiAction,
} from "./wizard-types"
import { SPLIT_STAGES } from "./DynamicContextPanel"

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

/**
 * Task #1112 — mapa estável `WizardStage → flag *_used_fallback` no
 * payload do node correspondente. Se o backend adicionar um 5º node com
 * fallback determinístico, basta acrescentar uma entrada aqui (e a
 * sentinela em `panels/AiDegradedModeBanner.test.tsx`).
 *
 * Espelha `_WIZARD_FALLBACK_NODES` em
 * `lia-agent-system/app/domains/job_creation/graph.py` — qualquer
 * divergência significa que o backend marcou um stage como degradado e
 * o painel não exibirá o aviso "IA degradada nessa etapa".
 */
export const FALLBACK_FLAG_BY_STAGE: Partial<Record<WizardStage, string>> = {
  jd_enrichment: "jd_enrichment_used_fallback",
  bigfive: "bigfive_used_fallback",
  salary: "salary_used_fallback",
  wsi_questions: "wsi_questions_used_fallback",
}

const FALLBACK_REASON_KEY_BY_STAGE: Partial<Record<WizardStage, string>> = {
  jd_enrichment: "jd_enrichment_fallback_reason",
  bigfive: "bigfive_fallback_reason",
  salary: "salary_fallback_reason",
  wsi_questions: "wsi_questions_fallback_reason",
}

/** Per-stage degraded marker: `true` = generic degraded, string = root-cause label. */
export type DegradedStageEntry = string | true

interface WizardState {
  active: boolean
  currentStage: WizardStage | null
  stageData: Record<string, unknown>
  completeness: number
  requiresApproval: boolean
  stageHistory: WizardStage[]
  /**
   * Task #1112 — quais stages do wizard rodaram em modo degradado
   * (i.e. caíram no fallback determinístico no backend). Persiste entre
   * STAGE_UPDATE: uma vez marcado, o badge fica visível na ProgressBar
   * mesmo após o wizard avançar de stage, para o recrutador notar ao
   * revisar.
   */
  degradedStages: Partial<Record<WizardStage, DegradedStageEntry>>
  threadId: string | null
  error: string | null
  /**
   * Fase 3 (Pipeline Template auto-suggest) — populated when the backend
   * emits a wizard_stage payload with ui_action="suggest_pipeline_template".
   * The chat surface renders <PipelineTemplateSuggestion> while this is
   * non-empty. Skipped/applied actions clear it back to [].
   */
  pipelineTemplateSuggestions: WizardPipelineTemplateSuggestion[]
}

const initialState: WizardState = {
  active: false,
  currentStage: null,
  stageData: {},
  completeness: 0,
  requiresApproval: false,
  stageHistory: [],
  degradedStages: {},
  threadId: null,
  error: null,
  pipelineTemplateSuggestions: [],
}

/**
 * Task #1112 — extrai `*_used_fallback` do payload (se existir) e devolve
 * o reason quando disponível. Pure helper, exportado para os testes.
 */
export function extractDegradedStage(
  stage: WizardStage,
  data: Record<string, unknown> | null | undefined,
): DegradedStageEntry | null {
  const flagKey = FALLBACK_FLAG_BY_STAGE[stage]
  if (!flagKey || !data) return null
  if (data[flagKey] !== true) return null
  const reasonKey = FALLBACK_REASON_KEY_BY_STAGE[stage]
  const reason = reasonKey ? data[reasonKey] : null
  return typeof reason === "string" && reason.length > 0 ? reason : true
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
  | { type: "SET_PIPELINE_TEMPLATE_SUGGESTIONS"; suggestions: WizardPipelineTemplateSuggestion[] }
  | { type: "CLEAR_PIPELINE_TEMPLATE_SUGGESTIONS" }

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
      const safeData: Record<string, unknown> = (data ?? {}) as Record<string, unknown>
      // Bug 2 (2026-05-29): dedup estrutural. Se o payload e identico ao
      // estado atual, retorna o MESMO objeto state (sem novo stageData) —
      // quebra o ciclo auto-alimentado de re-render quando o mesmo
      // wizard_stage (ex: wsi_questions requires_approval) e re-emitido.
      if (
        state.active &&
        state.currentStage === stage &&
        state.completeness === completeness &&
        state.requiresApproval === (requires_approval ?? false) &&
        JSON.stringify(state.stageData) === JSON.stringify(safeData)
      ) {
        return state
      }
      const degraded = extractDegradedStage(stage, safeData)
      const nextDegraded = degraded
        ? { ...state.degradedStages, [stage]: degraded }
        : state.degradedStages
      // Fase 3 — captura ui_action="suggest_pipeline_template" sem
      // perturbar a transição de stage. O payload "with ui_action" é
      // estruturalmente compatível com WizardStagePayload (ui_action é
      // optional), então cast é seguro.
      const payloadWithAction = action.payload as WizardStagePayloadWithUiAction
      let nextTemplates = state.pipelineTemplateSuggestions
      if (
        payloadWithAction.ui_action === "suggest_pipeline_template" &&
        safeData &&
        Array.isArray((safeData as { templates?: unknown }).templates)
      ) {
        nextTemplates = (safeData as { templates: WizardPipelineTemplateSuggestion[] })
          .templates
      }
      return {
        ...state,
        active: true,
        currentStage: stage,
        stageData: safeData,
        completeness,
        requiresApproval: requires_approval ?? false,
        stageHistory: buildHistory(state.currentStage, stage, state.stageHistory),
        degradedStages: nextDegraded,
        error: null,
        pipelineTemplateSuggestions: nextTemplates,
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
    case "SET_PIPELINE_TEMPLATE_SUGGESTIONS":
      return { ...state, pipelineTemplateSuggestions: action.suggestions }
    case "CLEAR_PIPELINE_TEMPLATE_SUGGESTIONS":
      return { ...state, pipelineTemplateSuggestions: [] }
    case "RESET":
      return initialState
    default:
      return state
  }
}

// --- Persistence (REMOVED — Task #1128) ---
//
// Until Task #1128 this file kept wizard state in
// `localStorage["lia-wizard-state-<userId>"]` and treated that cache as
// the source of truth. The result was the bug "Nova conversa keeps
// resurrecting the wizard": clearing chat messages did NOT clear the
// cache, the next `ws_stage_payload` rehydrated from disk, and the
// recruiter was stuck in the same stage they thought they had left.
//
// The canonical source of truth now lives in the LangGraph checkpointer
// on the backend, addressed by `(company_id, session_id)` via
// `app.shared.sessions.thread_id.derive_thread_id`. The chat surface
// rehydrates from `GET /api/v1/lia/job-wizard/session/{session_id}` on
// mount and calls `DELETE` on "Nova conversa" / "Cancelar wizard".
//
// `getWizardStorageKey` is retained ONLY to compute legacy keys the chat
// surface purges on first mount (see `purgeLegacyWizardStorage` in
// `useWizardSessionApi.ts`). Do NOT reintroduce read/write here — the
// sentinel `useWizardFlow.test.ts` greps this file for forbidden tokens
// (`localStorage.setItem`, `loadPersistedState`, `persistState`).

const LEGACY_WIZARD_STORAGE_KEY_PREFIX = "lia-wizard-state"

/**
 * Compute the legacy per-user storage key. Kept exported so the one-shot
 * purger in `useWizardSessionApi.ts` and the existing unit tests can name
 * the migration target; nothing in this file reads or writes that key.
 */
export function getWizardStorageKey(userId: string | null | undefined): string | null {
  if (typeof userId !== "string") return null
  const trimmed = userId.trim()
  if (trimmed === "") return null
  return `${LEGACY_WIZARD_STORAGE_KEY_PREFIX}-${trimmed}`
}

// --- Hook ---

export interface UseWizardFlowOptions {
  /**
   * Task #1128 — kept ONLY for backward compatibility with existing
   * call-sites (chat surface, tests). The wizard no longer persists to
   * localStorage; the LangGraph checkpointer on the backend, keyed by
   * `(company_id, session_id)` via `derive_thread_id`, is the only
   * source of truth. Tenant isolation that this prop used to provide is
   * now enforced server-side.
   */
  userId?: string | null
}

export function useWizardFlow(_options: UseWizardFlowOptions = {}) {
  const [state, dispatch] = useReducer(wizardReducer, initialState)

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
   * Fase 3 — aplica um template de pipeline customizado (vindo de
   * Configurações) à vaga em curso. Faz POST direto ao proxy
   * `/api/backend-proxy/job-vacancies/{id}/apply-pipeline-template`.
   * Retorna a Response pra o caller exibir toast/erro. Limpa o card de
   * sugestão em caso de sucesso.
   */
  const applyPipelineTemplateFromWizard = useCallback(
    async (
      vacancyId: string,
      templateId: string,
      source: "wizard_explicit" | "wizard_auto" = "wizard_explicit",
    ): Promise<Response> => {
      const response = await fetch(
        `/api/backend-proxy/job-vacancies/${vacancyId}/apply-pipeline-template`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ template_id: templateId, source }),
        },
      )
      if (response.ok) {
        dispatch({ type: "CLEAR_PIPELINE_TEMPLATE_SUGGESTIONS" })
      }
      return response
    },
    [],
  )

  /** Fase 3 — dispensa a sugestão sem aplicar (recrutador escolhe customizar). */
  const skipPipelineTemplateSuggestion = useCallback(() => {
    dispatch({ type: "CLEAR_PIPELINE_TEMPLATE_SUGGESTIONS" })
  }, [])

  // Task #1165 — quando o stage transitar para uma SPLIT_STAGE (review →
  // publish → calibration → handoff → done / scheduling) o wizard passa a
  // ter UI dedicada (split view 340/420px). Emitimos um
  // `lia:navigation-hint` com `mode: "ask"` para que o `DashboardApp`
  // proponha mover o recrutador para `/vagas`. O recrutador confirma no
  // chat (PT-BR livre). Se já estiver em `/vagas`, o handler suprime.
  // Disparamos apenas na transição (não a cada update do mesmo stage).
  const lastEmittedStageRef = useRef<WizardStage | null>(null)
  useEffect(() => {
    if (typeof window === "undefined") return
    const stage = state.currentStage
    if (!stage) {
      lastEmittedStageRef.current = null
      return
    }
    if (!SPLIT_STAGES.includes(stage)) {
      lastEmittedStageRef.current = stage
      return
    }
    if (lastEmittedStageRef.current === stage) return
    lastEmittedStageRef.current = stage
    window.dispatchEvent(
      new CustomEvent("lia:navigation-hint", {
        detail: {
          page: "Vagas",
          hint: `wizard:${stage}`,
          mode: "ask" as const,
        },
      }),
    )
  }, [state.currentStage])

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
    degradedStages: state.degradedStages,
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

    // Fase 3 — pipeline template auto-suggest
    pipelineTemplateSuggestions: state.pipelineTemplateSuggestions,
    applyPipelineTemplateFromWizard,
    skipPipelineTemplateSuggestion,
  }
}

export type WizardFlowReturn = ReturnType<typeof useWizardFlow>
