/**
 * Testes — useChatMessages (Task #248)
 *
 * Camada 2 (Unitário FE — Vitest + @testing-library/react)
 *
 * Cobre o caminho REST fallback (isConnected=false), incluindo:
 *  - Sucesso simples com `content` → onMessageComplete chamado.
 *  - Resposta com pending_action (HITL awaiting_confirmation) → hitlRef e
 *    setHitlPending são populados a partir do payload do servidor.
 *  - Erros HTTP (401/5xx) → bolha de aviso pelo onMessageComplete.
 *  - Resposta 2xx sem `content` e sem pending → mensagem de fallback.
 */
import { renderHook, act } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"
import { useChatMessages } from "../chat/useChatMessages"
import type { HITLPending } from "../chat/lia-chat-connection-types"

vi.mock("@/stores/recent-items-store", () => ({
  useRecentItemsStore: () => ({ addItem: vi.fn() }),
}))

const mockFetch = vi.fn()
const originalFetch = global.fetch
beforeEach(() => {
  vi.clearAllMocks()
  global.fetch = mockFetch as unknown as typeof fetch
})
afterEach(() => {
  vi.restoreAllMocks()
  global.fetch = originalFetch
})

type Options = Parameters<typeof useChatMessages>[0]

function makeOptions(overrides: Partial<Options> = {}): Options {
  const hitlRef = { current: null as HITLPending | null }
  return {
    sessionId: "sess-1",
    isConnected: false, // força caminho REST fallback
    transportMode: "disconnected",
    wsSend: vi.fn(() => true),
    sendRaw: vi.fn(),
    clearTokens: vi.fn(),
    sendMessageViaSSE: vi.fn(),
    wsEventTickRef: { current: 0 },
    hitlRef,
    setHitlPending: vi.fn(),
    onMessageComplete: vi.fn(),
    conversationIdFromWs: null,
    setIsThinking: vi.fn(),
    ...overrides,
  }
}

describe("useChatMessages — REST fallback", () => {
  it("sucesso 2xx com content chama onMessageComplete e atualiza conversationId", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({ content: "Olá!", conversation_id: "conv-99" }),
    })

    const onMessageComplete = vi.fn()
    const opts = makeOptions({ onMessageComplete })
    const { result } = renderHook(() => useChatMessages(opts))

    await act(async () => {
      await result.current.sendMessage("oi")
    })

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/backend-proxy/chat/message",
      expect.objectContaining({ method: "POST" }),
    )
    expect(onMessageComplete).toHaveBeenCalledWith("Olá!")
    expect(result.current.conversationId).toBe("conv-99")
    expect(opts.clearTokens).toHaveBeenCalled()
    expect(opts.setIsThinking).toHaveBeenCalledWith(true)
    expect(opts.setIsThinking).toHaveBeenCalledWith(false)
  })

  it("pending_action awaiting_confirmation → hitlRef e setHitlPending são populados", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          content: "Confirma criar a vaga?",
          conversation_id: "conv-1",
          message_metadata: {
            pending_action: {
              pending_id: "pa-1",
              action_id: "create_job",
              awaiting_confirmation: true,
              collected_params: { title: "Dev Sr" },
            },
          },
        }),
    })

    const setHitlPending = vi.fn()
    const hitlRef = { current: null as HITLPending | null }
    const onMessageComplete = vi.fn()
    const opts = makeOptions({ hitlRef, setHitlPending, onMessageComplete })

    const { result } = renderHook(() => useChatMessages(opts))
    await act(async () => {
      await result.current.sendMessage("cria vaga dev sr")
    })

    expect(setHitlPending).toHaveBeenCalledTimes(1)
    const pending = setHitlPending.mock.calls[0][0]
    expect(pending).toMatchObject({
      pendingId: "pa-1",
      threadId: "conv-1",
      action: "create_job",
      description: "Confirma criar a vaga?",
      data: { title: "Dev Sr" },
    })
    expect(hitlRef.current).toEqual(pending)
    // Quando há content, ele também é passado pra UI (bolha + cartão de aprovação).
    expect(onMessageComplete).toHaveBeenCalledWith("Confirma criar a vaga?")
  })

  it("HTTP 401 → bolha pt-BR de auth, sem tentar parsear JSON", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 })

    const onMessageComplete = vi.fn()
    const opts = makeOptions({ onMessageComplete })
    const { result } = renderHook(() => useChatMessages(opts))

    await act(async () => {
      await result.current.sendMessage("oi")
    })

    expect(onMessageComplete).toHaveBeenCalledWith(
      expect.stringMatching(/autentica/i),
    )
  })

  it("HTTP 500 → bolha pt-BR de servidor", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 })

    const onMessageComplete = vi.fn()
    const opts = makeOptions({ onMessageComplete })
    const { result } = renderHook(() => useChatMessages(opts))

    await act(async () => {
      await result.current.sendMessage("oi")
    })

    expect(onMessageComplete).toHaveBeenCalledWith(
      expect.stringMatching(/servidor/i),
    )
  })

  it("2xx sem content e sem pending → fallback explícito (sem silent drop)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({}),
    })

    const onMessageComplete = vi.fn()
    const opts = makeOptions({ onMessageComplete })
    const { result } = renderHook(() => useChatMessages(opts))

    await act(async () => {
      await result.current.sendMessage("oi")
    })

    expect(onMessageComplete).toHaveBeenCalledWith(
      expect.stringMatching(/não retornou/i),
    )
  })
})
