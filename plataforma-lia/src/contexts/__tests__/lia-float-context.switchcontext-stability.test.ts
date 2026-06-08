// @vitest-environment jsdom
/**
 * Regressão Bug 2026-06-08 — "Maximum update depth exceeded".
 *
 * O commit 9876f839c adicionou `switchChatContext` ao dep array de um
 * useEffect em dashboard-app.tsx que chama setState incondicionalmente
 * (setContextPage + openFloat). `switchChatContext` era `useCallback([connection])`
 * e `connection` é um objeto NAO-memoizado (nova ref a cada render) ->
 * switchChatContext mudava de identidade a cada render -> o effect re-rodava
 * a cada render -> setState incondicional -> loop infinito -> crash em TODAS
 * as páginas (o provider envolve a app inteira).
 *
 * Fix de raiz: depender só de `connection.setConversationId` (setter de useState,
 * estável). Este sensor pina a estabilidade: trocar outro estado do provider
 * NAO pode mudar a identidade de switchChatContext.
 */
import { act, renderHook } from "@testing-library/react"
import React from "react"
import { describe, expect, it, vi } from "vitest"

// Mock fiel: setConversationId é ESTÁVEL (como o setter de useState real),
// mas o OBJETO connection é recriado a cada render (como em produção, pois
// useLiaChatConnection retorna objeto literal sem useMemo).
const stableSetConversationId = vi.fn((_id: string | null) => {})
vi.mock("@/hooks/chat/use-lia-chat-connection", () => ({
  useLiaChatConnection: () => ({
    conversationId: null,
    setConversationId: stableSetConversationId,
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
}))

vi.mock("@/hooks/chat/useUIAction", () => ({
  useUIAction: () => ({ dispatchOrEmit: vi.fn() }),
}))

import { LiaFloatProvider, useLiaFloat } from "@/contexts/lia-float-context"

function wrapper({ children }: { children: React.ReactNode }) {
  return React.createElement(LiaFloatProvider, null, children)
}

describe("lia-float-context — switchChatContext reference stability (Bug 2026-06-08)", () => {
  it("mantém identidade de switchChatContext quando outro estado do provider muda", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })

    const first = result.current.switchChatContext

    // Muda outro estado do provider (força re-render do provider).
    act(() => {
      result.current.setContextPage("Gestao de Vagas")
    })
    expect(result.current.switchChatContext).toBe(first)

    act(() => {
      result.current.setContextPage("Funil de Talentos")
    })
    expect(result.current.switchChatContext).toBe(first)
  })

  it("setContextPage é idempotente: chamar com o mesmo valor não troca a referência de estado observável", () => {
    const { result } = renderHook(() => useLiaFloat(), { wrapper })
    act(() => {
      result.current.setContextPage("Pipeline")
    })
    const cb = result.current.switchChatContext
    act(() => {
      result.current.setContextPage("Pipeline") // mesmo valor -> bail
    })
    expect(result.current.switchChatContext).toBe(cb)
  })
})
