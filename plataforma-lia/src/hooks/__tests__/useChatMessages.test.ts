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
  // Isolamento de transporte: o Secret NEXT_PUBLIC_CHAT_TRANSPORT=sse do ambiente
  // Replit (Fase C SSE-e2e, 2026-06-04) ligaria o early-return SSE em
  // useChatMessages e pularia os branches WS/REST que estes testes exercitam.
  // Fixamos vazio para selecionar o caminho WS/REST de forma determinística.
  vi.stubEnv("NEXT_PUBLIC_CHAT_TRANSPORT", "")
  global.fetch = mockFetch as unknown as typeof fetch
})
afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllEnvs()
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
    // Contrato canonical (PR-D): onMessageComplete recebe
    // (content, executionPlan?, extras?). O conteúdo entregue à UI é o 1º
    // argumento; os demais são metadata opcional (ui_action etc.).
    expect(onMessageComplete.mock.calls[0][0]).toBe("Olá!")
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
    // (content, executionPlan?, extras?) — checamos o conteúdo (1º arg).
    expect(onMessageComplete.mock.calls[0][0]).toBe("Confirma criar a vaga?")
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

  it("WS aceito mas sem evento dentro do timeout → bolha de aviso + REST fallback (Task #383/F2)", async () => {
    vi.useFakeTimers()
    try {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ content: "Resposta tardia via REST" }),
      })

      const onMessageComplete = vi.fn()
      const wsSend = vi.fn(() => true)
      const wsEventTickRef = { current: 0 }
      const opts = makeOptions({
        isConnected: true,
        transportMode: "ws",
        wsSend,
        wsEventTickRef,
        onMessageComplete,
      })

      const { result } = renderHook(() => useChatMessages(opts))

      await act(async () => {
        await result.current.sendMessage("oi via ws")
      })

      // O send foi aceito pelo socket — nenhum fetch ainda, nenhum aviso ainda.
      expect(wsSend).toHaveBeenCalledTimes(1)
      expect(mockFetch).not.toHaveBeenCalled()
      expect(onMessageComplete).not.toHaveBeenCalled()

      // Tick permanece 0 (nenhum evento WS chegou). Avança o relógio além do
      // timeout do watchdog (default 8000ms).
      await act(async () => {
        vi.advanceTimersByTime(8001)
        await Promise.resolve()
      })

      // (a) bolha "Conexão instável" emitida via onMessageComplete.
      expect(onMessageComplete).toHaveBeenCalledWith(
        expect.stringMatching(/conex[aã]o inst[aá]vel/i),
      )

      // (b) REST POST disparado pelo fallback.
      await act(async () => {
        await Promise.resolve()
        await Promise.resolve()
      })
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/backend-proxy/chat/message",
        expect.objectContaining({ method: "POST" }),
      )
    } finally {
      vi.useRealTimers()
    }
  })

  it("WS com evento chegando antes do timeout → não cai pra REST (sem bolha de aviso)", async () => {
    vi.useFakeTimers()
    try {
      const onMessageComplete = vi.fn()
      const wsSend = vi.fn(() => true)
      const wsEventTickRef = { current: 0 }
      const opts = makeOptions({
        isConnected: true,
        transportMode: "ws",
        wsSend,
        wsEventTickRef,
        onMessageComplete,
      })

      const { result } = renderHook(() => useChatMessages(opts))

      await act(async () => {
        await result.current.sendMessage("oi via ws")
      })

      // Simula um evento WS chegando (thinking/message/...): incrementa o tick.
      wsEventTickRef.current = 1

      await act(async () => {
        vi.advanceTimersByTime(8001)
        await Promise.resolve()
      })

      expect(mockFetch).not.toHaveBeenCalled()
      expect(onMessageComplete).not.toHaveBeenCalled()
    } finally {
      vi.useRealTimers()
    }
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

describe("useChatMessages — transporte SSE via flag (Fase C 2026-06-04)", () => {
  it("flag NEXT_PUBLIC_CHAT_TRANSPORT=sse → roteia por sendMessageViaSSE e pula WS/REST", async () => {
    // Override do stub vazio do beforeEach: liga o transporte SSE.
    vi.stubEnv("NEXT_PUBLIC_CHAT_TRANSPORT", "sse")

    const sendMessageViaSSE = vi.fn()
    const wsSend = vi.fn(() => true)
    const opts = makeOptions({
      isConnected: true,
      transportMode: "ws",
      wsSend,
      sendMessageViaSSE,
    })
    const { result } = renderHook(() => useChatMessages(opts))

    await act(async () => {
      await result.current.sendMessage("oi via sse", "recruiter_assistant")
    })

    // O early-return da flag roteia o turno por SSE e pula WS e REST por completo.
    expect(sendMessageViaSSE).toHaveBeenCalledTimes(1)
    expect(wsSend).not.toHaveBeenCalled()
    expect(mockFetch).not.toHaveBeenCalled()
    // Defesa anti-silent-drop: passa um callback de fallback REST como 6º argumento.
    const fallbackArg = sendMessageViaSSE.mock.calls[0][5]
    expect(typeof fallbackArg).toBe("function")
  })
})

describe("useChatMessages — Fase 5b right_panel_form promotion", () => {
  it("promove metadata.right_panel_form para context.right_panel_form no wsSend", async () => {
    const wsSend = vi.fn(() => true)
    const opts = makeOptions({ isConnected: true, transportMode: "ws", wsSend })
    const { result } = renderHook(() => useChatMessages(opts))
    await act(async () => {
      await result.current.sendMessage("confirmei competências", "wizard", undefined, {
        right_panel_form: { confirmed_technical_competencies: [{ skill: "Python" }] },
      })
    })
    expect(wsSend).toHaveBeenCalled()
    const ctx = (wsSend.mock.calls[0] as unknown[])[1] as Record<string, unknown>
    expect(ctx.right_panel_form).toEqual({ confirmed_technical_competencies: [{ skill: "Python" }] })
  })
})
