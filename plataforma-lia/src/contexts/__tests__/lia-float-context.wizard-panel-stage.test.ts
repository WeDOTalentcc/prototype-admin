// @vitest-environment jsdom
/**
 * Sensor: handlePanelUpdate NAO pode reivindicar frames panel_update com
 * panel_type "wizard_stage". O painel do wizard e propriedade EXCLUSIVA da
 * ponte lia:wizard-stage-payload (openDynamicPanel COM o campo `stage`).
 *
 * Bug confirmado (2026-06-05, chat full): o painel abria no "criar vaga" e
 * FECHAVA ao digitar o titulo. Kill chain:
 *   1. Backend (agent_chat_sse.py) emite, a cada turno do wizard, um frame
 *      panel_update(panel_type="wizard_stage") SEM thread_id/completeness.
 *   2. No FE, o MESMO frame dispara DOIS escritores de `dynamicPanel`:
 *      (a) handlePanelUpdate -> grava shape SEM `stage`;
 *      (b) maybeDispatchWizardStage -> ponte COM `stage`, mas deduplicada por
 *          chave thread_id:stage:completeness.
 *   3. 2o turno do mesmo stage: a chave colapsa (":intake:0" === ":intake:0"),
 *      a ponte e suprimida, sobra so o shape stage-less -> gate hasDynamicPanel
 *      (SPLIT_STAGES.includes(undefined)) falha -> painel some.
 *
 * Fix canonico (single source of truth): handlePanelUpdate ignora
 * panel_type === "wizard_stage". Sem o escritor concorrente, o painel do turno
 * 1 (sticky) sobrevive ao 2o turno mesmo quando a ponte e deduplicada.
 *
 * Skill: harness-engineering [sensor comportamental] + canonical-fix.
 */
import { act, renderHook } from "@testing-library/react"
import React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"

// Captura o callback onPanelUpdate que o provider passa para a conexao, para
// simular a chegada de um frame panel_update do backend (caminho real do bug).
let capturedOnPanelUpdate:
  | ((e: { panel_type: string; panel_data: Record<string, unknown>; panel_title?: string; action?: string }) => void)
  | null = null

vi.mock("@/hooks/chat/use-lia-chat-connection", () => {
  let conversationId: string | null = null
  return {
    useLiaChatConnection: (opts: { onPanelUpdate?: typeof capturedOnPanelUpdate }) => {
      capturedOnPanelUpdate = opts?.onPanelUpdate ?? null
      return {
        conversationId,
        setConversationId: (id: string | null) => { conversationId = id },
        sendMessage: vi.fn(async () => {}),
        initConversation: vi.fn(async () => null),
        loadHistory: vi.fn(async () => []),
        sendApproval: vi.fn(),
        isConnected: false,
        transportMode: "sse" as const,
        isReconnecting: false,
        isStreaming: false,
        streamingContent: "",
        hitlPending: null,
        backgroundTasks: [],
        clearBackgroundTask: vi.fn(),
        resetBackgroundTasks: vi.fn(),
        seedBackgroundTask: vi.fn(),
        isCreating: false,
        isFetchingHistory: false,
        isThinking: false,
        thinkingSteps: [],
        planProgressSteps: [],
        activePlanId: null,
        fairnessWarnings: [],
        dismissFairnessWarnings: vi.fn(),
        connect: vi.fn(),
        disconnect: vi.fn(),
      }
    },
  }
})

vi.mock("@/hooks/chat/useUIAction", () => ({
  useUIAction: () => ({ dispatchOrEmit: vi.fn() }),
}))

import {
  LiaFloatProvider,
  useLiaFloat,
  type DynamicPanelData,
} from "@/contexts/lia-float-context"

function wrapper({ children }: { children: React.ReactNode }) {
  return React.createElement(LiaFloatProvider, null, children)
}

const WIZARD_PANEL: DynamicPanelData = {
  panelType: "job_creation",
  data: { stage: "intake" },
  stage: "intake",
  requires_approval: false,
}

describe("handlePanelUpdate NAO derruba o painel do wizard (single source of truth)", () => {
  beforeEach(() => {
    window.sessionStorage.clear()
    capturedOnPanelUpdate = null
  })

  it("um frame panel_update(wizard_stage) NAO sobrescreve o stage ja aberto pela ponte", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    // Turno 1: a ponte abre o painel COM stage.
    act(() => {
      result.current.openDynamicPanel(WIZARD_PANEL)
    })
    expect(result.current.dynamicPanel?.stage).toBe("intake")

    // Turno 2 (mesmo stage): chega o frame panel_update(wizard_stage) e a ponte
    // foi deduplicada. handlePanelUpdate DEVE ignora-lo, preservando o stage.
    expect(capturedOnPanelUpdate).toBeTypeOf("function")
    act(() => {
      capturedOnPanelUpdate?.({
        panel_type: "wizard_stage",
        panel_data: { message: "Perfeito, vou registrar..." },
        panel_title: "intake",
        action: "open",
      })
    })

    // Invariante: o painel do wizard CONTINUA com stage -> gate hasDynamicPanel
    // segue valido -> painel permanece. (Antes do fix: stage virava undefined.)
    expect(result.current.dynamicPanel).not.toBeNull()
    expect(result.current.dynamicPanel?.stage).toBe("intake")
  })

  it("panel_update NAO-wizard continua funcionando (regressao)", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      capturedOnPanelUpdate?.({
        panel_type: "candidate_profile",
        panel_data: { id: "cand-1" },
        panel_title: "Candidato",
        action: "open",
      })
    })

    expect(result.current.dynamicPanel).not.toBeNull()
    expect(result.current.dynamicPanel?.panelType).toBe("candidate_profile")
  })
})
