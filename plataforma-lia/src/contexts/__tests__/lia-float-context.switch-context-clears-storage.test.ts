// @vitest-environment jsdom
/**
 * Task #1103 — switchChatContext deve limpar/atualizar a key
 * `lia.chat.conversation_id` em sessionStorage.
 *
 * Cenário coberto:
 *   1. O usuário está numa conversa ativa (key persistida).
 *   2. Chama switchChatContext("kanban_chat") sem informar conversationId.
 *   3. Simula um reload — a key NÃO pode mais apontar para a conversa antiga,
 *      caso contrário o efeito de restauração hidrataria o histórico errado.
 *
 * Sem o fix, persistConversationId só era invocada por setChatConversationId
 * (chamado em sendOrchestratedMessage / setChatConversationId direto). O caller
 * switchChatContext usava connection.setConversationId direto, então a key
 * ficava grudada na conversa anterior até a aba ser fechada.
 */
import { act, renderHook } from "@testing-library/react"
import React from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"

const STORAGE_KEY = "lia.chat.conversation_id"

// Mock the chat connection hook — we only care about state held in the
// provider + sessionStorage side effects, not the WS layer.
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

describe("Task #1103 — switchChatContext clears persisted conversation id", () => {
  beforeEach(() => {
    window.sessionStorage.clear()
  })

  it("limpa lia.chat.conversation_id ao trocar de contexto sem conversationId explícita", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.setChatConversationId("conv-old-general")
    })
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBe("conv-old-general")

    act(() => {
      result.current.switchChatContext("kanban_chat")
    })

    // Sem conversationId nem continuePrevious → próximo contexto começa zerado
    // e a key persistida NÃO pode mais apontar para a conversa anterior.
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBeNull()
  })

  it("atualiza a key quando switchChatContext recebe uma nova conversationId", () => {
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

  it("após troca de contexto + reload, o provider remontado NÃO restaura a conversa antiga", async () => {
    const { result, unmount } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.setChatConversationId("conv-old-general")
    })
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBe("conv-old-general")

    act(() => {
      result.current.switchChatContext("kanban_chat")
    })
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBeNull()

    // Simula reload: desmonta + remonta o provider. O efeito de restauração
    // (didRestoreConversationRef) deve achar a key zerada e não hidratar nada.
    unmount()
    const { result: remounted } = renderHook(() => useLiaFloat(), { wrapper })

    // Pequeno tick para deixar o useEffect de restauração rodar.
    await act(async () => {
      await Promise.resolve()
    })

    expect(remounted.current.chatConversationId).toBeNull()
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBeNull()
  })

  it("limpa a key quando continuePrevious=true mas o novo contexto não tem conversa salva", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    act(() => {
      result.current.setChatConversationId("conv-general")
    })
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBe("conv-general")

    act(() => {
      result.current.switchChatContext("talent_chat", { continuePrevious: true })
    })

    // talent_chat nunca teve conversa anterior → cai para null e a key
    // antiga (de "general") não pode sobreviver.
    expect(window.sessionStorage.getItem(STORAGE_KEY)).toBeNull()
  })
})
