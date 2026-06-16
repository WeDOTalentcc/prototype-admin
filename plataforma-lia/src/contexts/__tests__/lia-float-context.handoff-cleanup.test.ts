// @vitest-environment jsdom
/**
 * Sensor: stage "handoff" via lia:wizard-stage-payload limpa o dynamicPanel
 * (closeDynamicPanel), evitando que nova sessão do wizard herde dados stale
 * (ex: perguntas WSI do wizard anterior).
 *
 * Bug confirmado: o handler só executava closeDynamicPanel em stage === "done",
 * mas o orchestrator emite "handoff" como stage terminal (quando job_id existe
 * e navega pro /jobs). O "done" raramente é emitido. Resultado: painel WSI do
 * wizard anterior persistia ao iniciar novo wizard.
 *
 * Fix (lia-float-context.tsx): condição ampliada para
 *   if (stage === "done" || stage === "handoff") { closeDynamicPanel() ... }
 *
 * Skill canônica: harness-engineering [sensor comportamental].
 */
import { act, renderHook } from "@testing-library/react"
import React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/hooks/chat/use-lia-chat-connection", () => {
  let conversationId: string | null = null
  return {
    useLiaChatConnection: () => ({
      conversationId,
      setConversationId: (id: string | null) => {
        conversationId = id
      },
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
    }),
  }
})

vi.mock("@/hooks/chat/useUIAction", () => ({
  useUIAction: () => ({ dispatchOrEmit: vi.fn() }),
}))

vi.mock("next/navigation", () => ({
  usePathname: () => "/pt/recrutar",
}))

import {
  LiaFloatProvider,
  useLiaFloat,
  type DynamicPanelData,
} from "@/contexts/lia-float-context"

function wrapper({ children }: { children: React.ReactNode }) {
  return React.createElement(LiaFloatProvider, null, children)
}

function dispatchStagePayload(detail: Record<string, unknown>) {
  act(() => {
    window.dispatchEvent(
      new CustomEvent("lia:wizard-stage-payload", { detail }),
    )
  })
}

const WSI_PANEL: DynamicPanelData = {
  panelType: "job_creation",
  data: { stage: "wsi_questions", questions: [{ id: "q1", text: "Teste" }] },
  stage: "wsi_questions",
  requires_approval: false,
}

describe("Bug 4 — stage handoff limpa dynamicPanel (sem dados stale)", () => {
  beforeEach(() => {
    window.sessionStorage.clear()
  })

  it("stage handoff limpa dynamicPanel (fecha painel stale)", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    // Simula wizard anterior: painel WSI aberto
    act(() => {
      result.current.openDynamicPanel(WSI_PANEL)
    })
    expect(result.current.dynamicPanel).not.toBeNull()
    expect(result.current.dynamicPanel?.stage).toBe("wsi_questions")

    // Wizard termina com stage "handoff" (caminho terminal do orchestrator)
    dispatchStagePayload({ stage: "handoff", data: {} })

    // Invariante: dynamicPanel deve ser null (dados stale limpos)
    expect(result.current.dynamicPanel).toBeNull()
  })

  it("stage done também limpa dynamicPanel (regressão)", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.openDynamicPanel(WSI_PANEL)
    })
    expect(result.current.dynamicPanel).not.toBeNull()

    dispatchStagePayload({ stage: "done", data: {} })

    expect(result.current.dynamicPanel).toBeNull()
  })

  it("stage wsi_questions NÃO limpa dynamicPanel (não-terminal)", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    // Painel de outra sessão abertas
    act(() => {
      result.current.openDynamicPanel(WSI_PANEL)
    })

    // Chega novo stage intermediário — NÃO deve limpar
    dispatchStagePayload({ stage: "jd_review", data: {} })

    expect(result.current.dynamicPanel).not.toBeNull()
  })

  it("novo wizard após handoff começa com painel limpo (regressão stale data)", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    // Sessão 1: WSI com perguntas
    act(() => {
      result.current.openDynamicPanel(WSI_PANEL)
    })
    expect(result.current.dynamicPanel?.stage).toBe("wsi_questions")

    // Sessão 1 termina com handoff
    dispatchStagePayload({ stage: "handoff", data: {} })
    expect(result.current.dynamicPanel).toBeNull()

    // Sessão 2: começa com stage intake (dados frescos)
    dispatchStagePayload({ stage: "intake", data: { job_title: "Novo cargo" } })

    // Painel deve ter os dados da sessão 2, não da sessão 1
    expect(result.current.dynamicPanel).not.toBeNull()
    expect(result.current.dynamicPanel?.stage).toBe("intake")
  })
})
