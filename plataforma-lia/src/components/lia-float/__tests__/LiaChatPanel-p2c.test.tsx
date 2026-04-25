/**
 * P2-C — Testes unitários: Botões Novo Chat / Limpar / Histórico no LiaChatPanel
 *
 * Camada 2 — Unitária (jsdom)
 * Cobre:
 * 1. Botão "Novo Chat" existe no header (aria-label)
 * 2. Botão "Limpar" existe no header
 * 3. Botão "Histórico" existe no header
 * 4. "Limpar" desabilitado quando não há mensagens
 * 5. Botão "Histórico" tem aria-expanded=false inicial
 * 6. handleNewChat: desconecta WS e limpa estado
 * 7. handleClear: limpa apenas messages
 * 8. handleToggleHistory: lê localStorage e mostra painel
 * 9. História vazia mostra mensagem apropriada
 * 10. handleLoadConversation: chama setConversationId e loadHistory
 * 11. Painel de histórico mostra conversas do localStorage
 * 12. Fechar histórico via segundo clique no botão
 */

import React from "react"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach } from "vitest"

// jsdom não implementa scrollIntoView — mockar globalmente
window.HTMLElement.prototype.scrollIntoView = vi.fn()

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock("next/navigation", () => ({ usePathname: vi.fn().mockReturnValue("/") }))

vi.mock("@/contexts/lia-float-context", () => ({
  useLiaFloat: () => ({
    isOpen: true,
    conversationId: null,
    close: vi.fn(),
    expand: vi.fn(),
    openSplitView: vi.fn(),
    sharedMessages: _msgStore.messages,
    addSharedMessage: vi.fn(),
    setSharedMessages: mockSetMessages,
    sharedConversationId: null,
    setSharedConversationId: mockSetConversationId,
  }),
}))

const mockWsDisconnect = vi.fn()
const mockWsConnect = vi.fn()
const mockSendApproval = vi.fn()
const mockWsSend = vi.fn()

// Task #817: hook `@/hooks/ai/use-float-streaming` removido (código morto, 0
// consumidores em produção). O mock era órfão — `LiaChatPanel` consome chat
// via `useLiaChatContext`, não diretamente via streaming hook. Mantemos os
// stubs locais (`mockWsDisconnect`, `mockWsConnect`, `mockSendApproval`,
// `mockWsSend`) caso testes futuros precisem injetá-los pelo contexto.
void mockWsDisconnect; void mockWsConnect; void mockSendApproval; void mockWsSend;

const mockSetMessages = vi.fn()
const mockSetConversationId = vi.fn()
const mockLoadHistory = vi.fn().mockResolvedValue(undefined)
const mockAddMessage = vi.fn()
const mockInitConversation = vi.fn().mockResolvedValue("conv-123")

const _msgStore = vi.hoisted(() => ({ messages: [] as { id: string; sender: string; content: string; timestamp: string }[] }))

vi.mock("@/hooks/chat/use-float-conversation", () => ({
  useFloatConversation: () => ({
    conversationId: null,
    messages: _msgStore.messages,
    isCreating: false,
    isFetchingHistory: false,
    initConversation: mockInitConversation,
    loadHistory: mockLoadHistory,
    addMessage: mockAddMessage,
    setMessages: mockSetMessages,
    setConversationId: mockSetConversationId,
  }),
  formatMessageTime: () => "10:00",
}))

vi.mock("@/hooks/shared/use-navigation-intent", () => ({
  useNavigationIntent: () => ({
    result: null,
    detect: vi.fn().mockResolvedValue(null),
    clear: vi.fn(),
  }),
}))

vi.mock("@/hooks/shared/use-action-intent", () => ({
  useActionIntent: () => ({
    detect: vi.fn().mockReturnValue({ actionType: null, label: null }),
  }),
  actionTypeToDomain: () => "",
}))

vi.mock("@/hooks/company/use-current-scope", () => ({
  useCurrentScope: () => ({ scope: "global", scopeName: "Global" }),
  resolveScopeFromPathname: vi.fn().mockReturnValue("global"),
}))

vi.mock("@/components/lia-float/HITLConfirmCard", () => ({
  HITLConfirmCard: () => <div data-testid="hitl-card" />,
}))

vi.mock("@/components/ui/audio-record-button", () => ({
  AudioRecordButton: () => <button aria-label="Gravar áudio" />,
}))

// ── Setup ─────────────────────────────────────────────────────────────────────

// Provide local storage mock
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value },
    clear: () => { store = {} },
    removeItem: (key: string) => { delete store[key] },
  }
})()
Object.defineProperty(window, "localStorage", { value: localStorageMock })

import { LiaChatPanel } from "../LiaChatPanel"

// ── Tests ────────────────────────────────────────────────────────────────────

describe("P2-C — LiaChatPanel: Novo Chat / Limpar / Histórico", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    _msgStore.messages = []
    localStorageMock.clear()
  })

  it("1. botão Novo Chat presente no header", () => {
    render(<LiaChatPanel />)
    expect(screen.getByRole("button", { name: /iniciar novo chat/i })).toBeInTheDocument()
  })

  it("2. botão Limpar presente no header", () => {
    render(<LiaChatPanel />)
    expect(screen.getByRole("button", { name: /limpar mensagens/i })).toBeInTheDocument()
  })

  it("3. botão Histórico presente no header", () => {
    render(<LiaChatPanel />)
    expect(screen.getByRole("button", { name: /ver histórico/i })).toBeInTheDocument()
  })

  it("4. botão Limpar desabilitado quando sem mensagens", () => {
    _msgStore.messages = []
    render(<LiaChatPanel />)
    const clearBtn = screen.getByRole("button", { name: /limpar mensagens/i })
    expect(clearBtn).toBeDisabled()
  })

  it("5. botão Histórico tem aria-expanded=false inicial", () => {
    render(<LiaChatPanel />)
    const histBtn = screen.getByRole("button", { name: /ver histórico/i })
    expect(histBtn).toHaveAttribute("aria-expanded", "false")
  })

  it("6. Novo Chat chama wsDisconnect e setMessages([])", () => {
    render(<LiaChatPanel />)
    fireEvent.click(screen.getByRole("button", { name: /iniciar novo chat/i }))
    expect(mockWsDisconnect).toHaveBeenCalledTimes(1)
    expect(mockSetMessages).toHaveBeenCalledWith([])
  })

  it("7. Novo Chat chama setConversationId(null)", () => {
    render(<LiaChatPanel />)
    fireEvent.click(screen.getByRole("button", { name: /iniciar novo chat/i }))
    expect(mockSetConversationId).toHaveBeenCalledWith(null)
  })

  it("8. Limpar chama setMessages([]) sem tocar no conversationId", () => {
    _msgStore.messages = [{ id: "1", sender: "user", content: "oi", timestamp: "10:00" }]
    render(<LiaChatPanel />)
    fireEvent.click(screen.getByRole("button", { name: /limpar mensagens/i }))
    expect(mockSetMessages).toHaveBeenCalledWith([])
    expect(mockSetConversationId).not.toHaveBeenCalled()
  })

  it("9. Histórico vazio mostra mensagem 'Nenhuma conversa anterior'", () => {
    render(<LiaChatPanel />)
    fireEvent.click(screen.getByRole("button", { name: /ver histórico/i }))
    expect(screen.getByText(/nenhuma conversa anterior encontrada/i)).toBeInTheDocument()
  })

  it("10. Histórico exibe conversas do localStorage", () => {
    const chats = [
      { id: "c1", type: "chat", title: "Busca candidatos React", timestamp: Date.now() },
      { id: "c2", type: "chat", title: "Vaga de designer", timestamp: Date.now() - 3600000 },
    ]
    localStorageMock.setItem("lia-recent-items", JSON.stringify(chats))

    render(<LiaChatPanel />)
    fireEvent.click(screen.getByRole("button", { name: /ver histórico/i }))

    expect(screen.getByText("Busca candidatos React")).toBeInTheDocument()
    expect(screen.getByText("Vaga de designer")).toBeInTheDocument()
  })

  it("11. Clicar em conversa do histórico chama setConversationId e loadHistory", async () => {
    const chats = [
      { id: "conv-abc", type: "chat", title: "Triagem automática", timestamp: Date.now() },
    ]
    localStorageMock.setItem("lia-recent-items", JSON.stringify(chats))

    render(<LiaChatPanel />)
    fireEvent.click(screen.getByRole("button", { name: /ver histórico/i }))
    fireEvent.click(screen.getByText("Triagem automática"))

    expect(mockSetConversationId).toHaveBeenCalledWith("conv-abc")
    await waitFor(() => {
      expect(mockLoadHistory).toHaveBeenCalledWith("conv-abc")
    })
  })

  it("12. Clicar histórico novamente fecha o painel (toggle)", () => {
    render(<LiaChatPanel />)
    const histBtn = screen.getByRole("button", { name: /ver histórico/i })
    fireEvent.click(histBtn) // abre
    expect(screen.getByText(/conversas recentes/i)).toBeInTheDocument()
    fireEvent.click(histBtn) // fecha
    expect(screen.queryByText(/conversas recentes/i)).not.toBeInTheDocument()
  })
})
