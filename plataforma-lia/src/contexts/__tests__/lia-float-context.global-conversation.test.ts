// @vitest-environment jsdom
/**
 * Opção A (Paulo 2026-05-29) — conversa GLOBAL contínua.
 *
 * A LIA flutuante é UMA conversa que segue o recrutador por todas as páginas.
 * Navegar / trocar de contexto NUNCA descarta a conversa (reverte o modelo
 * thread-por-contexto da Task #1103, que era a causa raiz do "chat reset" —
 * Bug 4 — e da perda de histórico no reload — Bug 1).
 *
 * O contexto vira metadado (domain hint por mensagem), não um thread separado.
 * Só dois caminhos mexem na conversa:
 *   (1) carregar uma conversa específica (conversationId string) — URL/sidebar;
 *   (2) reset explícito (resetConversation:true) — "Nova conversa".
 */
import { act, renderHook } from "@testing-library/react"
import React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"

const STORAGE_KEY = "lia.chat.conversation_id"

// Mock the chat connection hook — só nos importa o state do provider + os
// side effects em sessionStorage, não a camada WS.
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
  }
})

vi.mock("@/hooks/chat/useUIAction", () => ({
  useUIAction: () => ({ dispatchOrEmit: vi.fn() }),
}))

import {
  LiaFloatProvider,
  useLiaFloat,
} from "@/contexts/lia-float-context"

function wrapper({ children }: { children: React.ReactNode }) {
  return React.createElement(LiaFloatProvider, null, children)
}

describe("Opção A — switchChatContext preserva a conversa global", () => {
  beforeEach(() => {
    window.sessionStorage.clear()
  })

  it("trocar de contexto SEM conversationId PRESERVA a conversa ativa", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.setChatConversationId("conv-global")
    })
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBe("conv-global")

    act(() => {
      result.current.switchChatContext("kanban_chat")
    })

    // Bug 4 fix: navegar pro contexto kanban NÃO descarta a conversa.
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBe("conv-global")
    // O tipo de contexto (metadado) atualiza normalmente.
    expect(result.current.chatContextType).toBe("kanban_chat")
  })

  it("continuePrevious sem conversa nova também PRESERVA (não zera)", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.setChatConversationId("conv-global")
    })

    act(() => {
      result.current.switchChatContext("talent_chat", { continuePrevious: true })
    })

    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBe("conv-global")
  })

  it("carregar uma conversa específica (conversationId string) ATUALIZA a conversa", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.setChatConversationId("conv-A")
    })
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBe("conv-A")

    act(() => {
      result.current.switchChatContext("job_chat", { conversationId: "conv-B" })
    })

    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBe("conv-B")
  })

  it("resetConversation:true é a ÚNICA forma de zerar a conversa (Nova conversa)", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.setChatConversationId("conv-global")
    })
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBe("conv-global")

    act(() => {
      result.current.switchChatContext("general", {
        conversationId: null,
        resetConversation: true,
      })
    })

    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBeNull()
  })

  it("conversationId:null SEM resetConversation NÃO zera (mount/navegação)", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.setChatConversationId("conv-global")
    })

    // Caso dos call-sites de mount (useChatSession sem URL, AgentStudio):
    // passam conversationId:null só pra setar o tipo de contexto.
    act(() => {
      result.current.switchChatContext("general", { conversationId: null })
    })

    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBe("conv-global")
  })
})
