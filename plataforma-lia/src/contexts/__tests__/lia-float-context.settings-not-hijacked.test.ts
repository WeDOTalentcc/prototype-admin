// @vitest-environment jsdom
/**
 * Fix 2026-06-01 — chat de Configurações não pode ser sequestrado por um painel
 * de wizard de vaga que "ficou preso".
 *
 * Bug reportado por Paulo: após abrir um wizard de vaga, o painel job_creation
 * persiste no chat flutuante. Como o painel vence o contexto na resolução do
 * domain_hint (PANEL_TYPE_TO_DOMAIN_HINT.job_creation = "wizard"), TODO turno em
 * /configuracoes ia pro agente `wizard` (que não tem save_company_field), então
 * os saves de empresa via chat nunca persistiam.
 *
 * Fix canônico: a superfície explícita `settings_config` vence o painel preso.
 * Demais contextos (ex.: "general" durante o wizard) mantêm a prioridade do
 * painel — guard do leak 2026-04-29 preservado.
 */
import { act, renderHook } from "@testing-library/react"
import React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"

const sendMessageSpy = vi.fn(async () => {})

vi.mock("@/hooks/chat/use-lia-chat-connection", () => ({
  useLiaChatConnection: () => ({
    conversationId: "conv-1",
    setConversationId: vi.fn(),
    sendMessage: sendMessageSpy,
    initConversation: vi.fn(async () => "conv-1"),
    loadHistory: vi.fn(async () => []),
    sendApproval: vi.fn(),
    isConnected: true,
    transportMode: "ws" as const,
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
}))

vi.mock("@/hooks/chat/useUIAction", () => ({
  useUIAction: () => ({ dispatchOrEmit: vi.fn() }),
}))

import { LiaFloatProvider, useLiaFloat } from "@/contexts/lia-float-context"

function wrapper({ children }: { children: React.ReactNode }) {
  return React.createElement(LiaFloatProvider, null, children)
}

function activateStaleWizardPanel() {
  window.dispatchEvent(
    new CustomEvent("lia:wizard-stage-payload", {
      detail: { stage: "intake", data: {}, requires_approval: false },
    }),
  )
}

describe("settings_config não é sequestrado por painel de wizard preso", () => {
  beforeEach(() => {
    sendMessageSpy.mockClear()
    window.sessionStorage.clear()
  })

  it("painel job_creation ativo + contexto settings_config → domain_hint=company_settings", async () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      activateStaleWizardPanel()
    })
    act(() => {
      result.current.switchChatContext("settings_config", { continuePrevious: true })
    })

    await act(async () => {
      // texto puro (ex.: CNPJ digitado) — sem tag estruturada
      await result.current.sendChatMessage("12.345.678/0001-90")
    })

    expect(sendMessageSpy).toHaveBeenCalledTimes(1)
    const metadata = sendMessageSpy.mock.calls[0][3] as Record<string, unknown> | undefined
    expect(metadata?.domain_hint).toBe("company_settings")
  })

  it("contexto general (wizard normal) mantém domain_hint=wizard", async () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      activateStaleWizardPanel()
    })
    // contexto permanece "general" (default do float chat durante o wizard)

    await act(async () => {
      await result.current.sendChatMessage("qual competencia exigir?")
    })

    const metadata = sendMessageSpy.mock.calls[0][3] as Record<string, unknown> | undefined
    expect(metadata?.domain_hint).toBe("wizard")
  })
})
