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
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"

// jsdom não implementa scrollIntoView — mockar globalmente
window.HTMLElement.prototype.scrollIntoView = vi.fn()

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock("next/navigation", () => ({
  usePathname: vi.fn().mockReturnValue("/"),
  useRouter: vi.fn().mockReturnValue({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: vi.fn().mockReturnValue(new URLSearchParams()),
}))

// Task #817 (post-merge fix): `LiaChatPanel` consome 2 hooks distintos do
// mesmo módulo `@/contexts/lia-float-context`:
//   • `useLiaFloat()`  — estado de UI (open/close, painel dinâmico, mensagens
//     compartilhadas com SplitView, conversationId compartilhada).
//   • `useLiaChatContext()` — estado da conexão WS de chat (connect/disconnect,
//     streaming, fairness warnings, send/approval, init/loadHistory).
// O hook `useLiaChatPanelState` desestrutura ambos. Antes da Task #817 esta
// suíte só mockava `useLiaFloat` e o teste falhava 12/12 com "No
// useLiaChatContext export …". Agora declaramos os 2 mocks no mesmo factory
// (vi.mock é hoisted, então usamos `vi.hoisted()` para os doubles que precisam
// ser referenciados aqui em cima e re-acessados nos testes lá embaixo).

const _hoisted = vi.hoisted(() => ({
  setMessages: vi.fn(),
  setConversationId: vi.fn(),
  loadHistory: vi.fn().mockResolvedValue(undefined),
  addMessage: vi.fn(),
  initConversation: vi.fn().mockResolvedValue("conv-123"),
  wsDisconnect: vi.fn(),
  wsConnect: vi.fn().mockResolvedValue(undefined),
  sendApproval: vi.fn(),
  wsSend: vi.fn().mockResolvedValue(undefined),
  loadChatHistory: vi.fn().mockResolvedValue([]),
  initChatConversation: vi.fn().mockResolvedValue("conv-123"),
  setChatConversationId: vi.fn(),
  addChatMessage: vi.fn(),
  dismissFairnessWarnings: vi.fn(),
  clearBackgroundTask: vi.fn(),
  resetBackgroundTasks: vi.fn(),
  closeDynamicPanel: vi.fn(),
  msgs: [] as { id: string; sender: string; content: string; timestamp: string }[],
}))

vi.mock("@/contexts/lia-float-context", () => ({
  useLiaFloat: () => ({
    isOpen: true,
    conversationId: null,
    close: vi.fn(),
    expand: vi.fn(),
    openSplitView: vi.fn(),
    navigateToChat: vi.fn(),
    contextPage: null,
    entityContext: null,
    dynamicPanel: { isOpen: false, type: null, data: null },
    openDynamicPanel: vi.fn(),
    closeDynamicPanel: _hoisted.closeDynamicPanel,
    updateDynamicPanelData: vi.fn(),
    sharedMessages: _hoisted.msgs,
    addSharedMessage: vi.fn(),
    setSharedMessages: _hoisted.setMessages,
    sharedConversationId: null,
    setSharedConversationId: _hoisted.setConversationId,
  }),
  useLiaChatContext: () => ({
    chatConversationId: null,
    setChatConversationId: _hoisted.setChatConversationId,
    chatIsConnected: false,
    chatIsStreaming: false,
    chatStreamingContent: "",
    chatHitlPending: null,
    chatBackgroundTasks: [],
    chatFairnessWarnings: [],
    dismissFairnessWarnings: _hoisted.dismissFairnessWarnings,
    clearBackgroundTask: _hoisted.clearBackgroundTask,
    resetBackgroundTasks: _hoisted.resetBackgroundTasks,
    chatIsCreating: false,
    chatIsFetchingHistory: false,
    sendChatMessage: _hoisted.wsSend,
    sendApproval: _hoisted.sendApproval,
    connectChat: _hoisted.wsConnect,
    disconnectChat: _hoisted.wsDisconnect,
    initChatConversation: _hoisted.initChatConversation,
    loadChatHistory: _hoisted.loadChatHistory,
    addChatMessage: _hoisted.addChatMessage,
    chatMessages: [],
  }),
}))

const mockWsDisconnect = _hoisted.wsDisconnect
const mockWsConnect = _hoisted.wsConnect
const mockSendApproval = _hoisted.sendApproval
const mockWsSend = _hoisted.wsSend
void mockWsConnect; void mockSendApproval; void mockWsSend;

const mockSetMessages = _hoisted.setMessages
const mockSetConversationId = _hoisted.setConversationId
const mockLoadHistory = _hoisted.loadChatHistory
const mockAddMessage = _hoisted.addMessage
const mockInitConversation = _hoisted.initConversation
void mockAddMessage; void mockInitConversation;

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

// Task #817 (post-merge fix): histórico foi migrado de localStorage para o
// zustand store `useUIPreferencesStore` (chave `liaRecentItems`). O mock
// abaixo expõe `getState()` controlável pelos testes via `_recentStore`.
const _recentStore = vi.hoisted(() => ({
  items: [] as Array<{ id: string; type: string; title: string; timestamp: number }>,
}))
vi.mock("@/stores/ui-preferences-store", () => {
  const buildState = () => ({
    liaRecentItems: _recentStore.items,
    setLiaRecentItems: (items: typeof _recentStore.items) => {
      _recentStore.items = items
    },
    addLiaRecentItem: vi.fn(),
    removeLiaRecentItem: vi.fn(),
  })
  // zustand stores são funções: usadas como hook `useStore(selector)` E como
  // `useStore.getState()`. O mock cobre os 2 padrões (selector opcional).
  function useUIPreferencesStore<T = ReturnType<typeof buildState>>(
    selector?: (state: ReturnType<typeof buildState>) => T,
  ): T {
    const state = buildState()
    return selector ? selector(state) : (state as unknown as T)
  }
  ;(useUIPreferencesStore as unknown as { getState: typeof buildState }).getState = buildState
  return { useUIPreferencesStore }
})

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
    _hoisted.msgs.length = 0
    _recentStore.items = []
    localStorageMock.clear()
    // Stub global fetch — LiaChatMessageList chama
    // /api/backend-proxy/lia/context-suggestions no mount, gerando stderr
    // sem este mock. Cada chamada recebe um Response novo (Response.json()
    // só pode ser consumido uma vez), evitando "Body has already been read".
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      new Response(JSON.stringify({ suggestions: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
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

  it("8. Limpar chama setMessages([]) e reseta conversationId (fresh session)", () => {
    // Comportamento canônico (useLiaChatPanelState.handleClear): limpar
    // mensagens equivale a iniciar uma nova sessão, então `conversationId`
    // também é resetado para null junto com o disconnect/reset de tasks.
    _hoisted.msgs.push({ id: "1", sender: "user", content: "oi", timestamp: "10:00" })
    render(<LiaChatPanel />)
    fireEvent.click(screen.getByRole("button", { name: /limpar mensagens/i }))
    expect(mockSetMessages).toHaveBeenCalledWith([])
    expect(mockSetConversationId).toHaveBeenCalledWith(null)
  })

  it("9. Histórico vazio mostra mensagem 'Nenhuma conversa anterior'", () => {
    render(<LiaChatPanel />)
    fireEvent.click(screen.getByRole("button", { name: /ver histórico/i }))
    expect(screen.getByText(/nenhuma conversa anterior encontrada/i)).toBeInTheDocument()
  })

  it("10. Histórico exibe conversas do zustand store (liaRecentItems)", () => {
    _recentStore.items = [
      { id: "c1", type: "chat", title: "Busca candidatos React", timestamp: Date.now() },
      { id: "c2", type: "chat", title: "Vaga de designer", timestamp: Date.now() - 3600000 },
    ]

    render(<LiaChatPanel />)
    fireEvent.click(screen.getByRole("button", { name: /ver histórico/i }))

    expect(screen.getByText("Busca candidatos React")).toBeInTheDocument()
    expect(screen.getByText("Vaga de designer")).toBeInTheDocument()
  })

  it("11. Clicar em conversa do histórico chama setConversationId e loadHistory", async () => {
    _recentStore.items = [
      { id: "conv-abc", type: "chat", title: "Triagem automática", timestamp: Date.now() },
    ]

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
