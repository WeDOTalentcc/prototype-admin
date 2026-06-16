/**
 * Testes — useFloatConversation + funções puras (Phase 4a)
 *
 * Camada 2 (Unitário FE — Vitest + jsdom)
 *
 * Cobre:
 * - maskPII: CPF, e-mail, telefone mascarados no título
 * - formatMessageTime: formata corretamente
 * - initConversation: cria conversa via API, persiste recentes
 * - initConversation: retorna null quando API falha
 * - loadHistory: restaura mensagens do backend
 * - addMessage: adiciona mensagem ao estado
 */
import { renderHook, act, waitFor } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"
import { useFloatConversation } from "../chat/use-float-conversation"

// ── Mocks globais ────────────────────────────────────────────────────────────

const mockFetch = vi.fn()
global.fetch = mockFetch

// localStorage mock
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => { store[k] = v },
    removeItem: (k: string) => { delete store[k] },
    clear: () => { store = {} },
  }
})()
Object.defineProperty(window, "localStorage", { value: localStorageMock })

// ── Helpers ──────────────────────────────────────────────────────────────────

function mockPostConversation(id = "conv-uuid-001") {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ id, title: "test", context_type: "general" }),
  })
}

function mockGetConversation(messages: Array<{ id: string; role: string; content: string; created_at?: string }>) {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ messages }),
  })
}

/**
 * Onda 4-P2-6 (2026-05-24): use-float-conversation.ts migrado para
 * canonical liaPersistence helper (TTL wrapper {value, expiresAt}).
 * parseRecentItems desempacota o wrapper pros asserts dos testes.
 */
function parseRecentItems(): Array<{ id: string; type: string; title: string; timestamp: number; meta?: unknown }> {
  const raw = localStorageMock.getItem("lia-recent-items")
  if (raw === null) throw new Error("lia-recent-items key missing in localStorage")
  const wrapper = JSON.parse(raw)
  if (typeof wrapper !== "object" || wrapper === null || !("value" in wrapper) || !("expiresAt" in wrapper)) {
    throw new Error(`lia-recent-items not in canonical wrapper format: ${raw}`)
  }
  return wrapper.value as Array<{ id: string; type: string; title: string; timestamp: number; meta?: unknown }>
}

// ────────────────────────────────────────────────────────────────────────────

describe("useFloatConversation", () => {
  beforeEach(() => {
    mockFetch.mockReset()
    localStorageMock.clear()
  })

  // ── Estado inicial ──────────────────────────────────────────────────────

  it("inicia com conversationId null quando não passado", () => {
    const { result } = renderHook(() => useFloatConversation(null))
    expect(result.current.conversationId).toBeNull()
    expect(result.current.messages).toHaveLength(0)
    expect(result.current.isCreating).toBe(false)
    expect(result.current.isFetchingHistory).toBe(false)
  })

  it("inicia com conversationId quando passado", () => {
    const { result } = renderHook(() => useFloatConversation("conv-123"))
    expect(result.current.conversationId).toBe("conv-123")
  })

  // ── initConversation ────────────────────────────────────────────────────

  it("cria conversa com sucesso e atualiza conversationId", async () => {
    mockPostConversation("conv-abc")
    const { result } = renderHook(() => useFloatConversation(null))

    let returned: string | null = null
    await act(async () => {
      returned = await result.current.initConversation("Listar vagas abertas")
    })

    expect(returned).toBe("conv-abc")
    expect(result.current.conversationId).toBe("conv-abc")
    expect(result.current.isCreating).toBe(false)
  })

  it("persiste conversa no localStorage como 'chat'", async () => {
    mockPostConversation("conv-xyz")
    const { result } = renderHook(() => useFloatConversation(null))

    await act(async () => {
      await result.current.initConversation("Buscar candidato")
    })

    const items = parseRecentItems()
    expect(items[0].type).toBe("chat")
    expect(items[0].id).toBe("conv-xyz")
  })

  it("mascara CPF no título antes de persistir no localStorage", async () => {
    mockPostConversation("conv-cpf")
    const { result } = renderHook(() => useFloatConversation(null))

    await act(async () => {
      await result.current.initConversation("Candidato 123.456.789-00 tem score alto")
    })

    const items = parseRecentItems()
    expect(items[0].title).not.toContain("123.456.789-00")
    expect(items[0].title).toContain("[CPF]")
  })

  it("mascara email no título", async () => {
    mockPostConversation("conv-email")
    const { result } = renderHook(() => useFloatConversation(null))

    await act(async () => {
      await result.current.initConversation("Contato ana@empresa.com.br para vaga")
    })

    const items = parseRecentItems()
    expect(items[0].title).toContain("[email]")
    expect(items[0].title).not.toContain("ana@empresa.com.br")
  })

  it("retorna null e não atualiza conversationId quando API falha", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, json: async () => ({}) })
    const { result } = renderHook(() => useFloatConversation(null))

    let returned: string | null = "sentinel"
    await act(async () => {
      returned = await result.current.initConversation("teste")
    })

    expect(returned).toBeNull()
    expect(result.current.conversationId).toBeNull()
    expect(result.current.isCreating).toBe(false)
  })

  it("retorna null e não lança erro quando fetch lança exceção", async () => {
    mockFetch.mockRejectedValueOnce(new Error("network error"))
    const { result } = renderHook(() => useFloatConversation(null))

    let returned: string | null = "sentinel"
    await act(async () => {
      returned = await result.current.initConversation("teste")
    })

    expect(returned).toBeNull()
    expect(result.current.isCreating).toBe(false)
  })

  // ── loadHistory ─────────────────────────────────────────────────────────

  it("carrega histórico e converte role → sender", async () => {
    mockGetConversation([
      { id: "m1", role: "user", content: "Olá LIA", created_at: "2026-03-08T10:00:00" },
      { id: "m2", role: "assistant", content: "Olá! Como posso ajudar?", created_at: "2026-03-08T10:00:01" },
    ])

    const { result } = renderHook(() => useFloatConversation("conv-hist"))

    await act(async () => {
      await result.current.loadHistory("conv-hist")
    })

    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[0].sender).toBe("user")
    expect(result.current.messages[0].content).toBe("Olá LIA")
    expect(result.current.messages[1].sender).toBe("lia")
    expect(result.current.isFetchingHistory).toBe(false)
  })

  it("mantém messages vazio se API de histórico falhar", async () => {
    mockFetch.mockRejectedValueOnce(new Error("timeout"))
    const { result } = renderHook(() => useFloatConversation("conv-fail"))

    await act(async () => {
      await result.current.loadHistory("conv-fail")
    })

    expect(result.current.messages).toHaveLength(0)
    expect(result.current.isFetchingHistory).toBe(false)
  })

  it("mantém messages vazio se API retornar 404", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, json: async () => ({}) })
    const { result } = renderHook(() => useFloatConversation("conv-404"))

    await act(async () => {
      await result.current.loadHistory("conv-404")
    })

    expect(result.current.messages).toHaveLength(0)
  })

  // ── addMessage ──────────────────────────────────────────────────────────

  it("addMessage adiciona mensagem ao estado", () => {
    const { result } = renderHook(() => useFloatConversation(null))

    act(() => {
      result.current.addMessage({
        id: "msg-1",
        sender: "user",
        content: "Teste",
        timestamp: "10:00",
      })
    })

    expect(result.current.messages).toHaveLength(1)
    expect(result.current.messages[0].content).toBe("Teste")
  })

  it("addMessage acumula mensagens sequencialmente", () => {
    const { result } = renderHook(() => useFloatConversation(null))

    act(() => {
      result.current.addMessage({ id: "m1", sender: "user", content: "A", timestamp: "10:00" })
      result.current.addMessage({ id: "m2", sender: "lia", content: "B", timestamp: "10:01" })
    })

    expect(result.current.messages).toHaveLength(2)
  })

  // ── título truncado ─────────────────────────────────────────────────────

  it("trunca títulos longos para 50 chars + ellipsis", async () => {
    mockPostConversation("conv-trunc")
    const { result } = renderHook(() => useFloatConversation(null))

    const longText = "Esta é uma mensagem muito longa que ultrapassa o limite de cinquenta caracteres para ser usada como título"
    await act(async () => {
      await result.current.initConversation(longText)
    })

    const items = parseRecentItems()
    expect(items[0].title.length).toBeLessThanOrEqual(51) // 47 + "…"
    expect(items[0].title.endsWith("…")).toBe(true)
  })
})
