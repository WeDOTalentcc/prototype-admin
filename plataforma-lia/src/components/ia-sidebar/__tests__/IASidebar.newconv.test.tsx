import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import React from "react"

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockSwitchChatContext = vi.fn()
const mockSetChatMessages = vi.fn()
const mockCloseIASidebar = vi.fn()
const mockSetActiveConversation = vi.fn()
const mockOnNewConversation = vi.fn()

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => {
    const map: Record<string, string> = {
      newConversation: "Nova conversa",
      title: "Conversas",
      searchPlaceholder: "Buscar conversas...",
      "aria.collapsePanel": "Recolher painel",
      "sections.pinned": "FIXADAS",
      "sections.today": "HOJE",
      "sections.earlier": "ANTERIORES",
      "sections.inFocus": "EM FOCO",
      "emptyState.noConversations": "Nenhuma conversa",
      "emptyState.noResults": "Nenhum resultado",
      "emptyState.startNew": "Iniciar conversa",
      "contextMenu.pin": "Fixar",
      "contextMenu.unpin": "Desafixar",
      "contextMenu.rename": "Renomear",
      "contextMenu.addNote": "Nota",
      "contextMenu.archive": "Arquivar",
      "contextMenu.delete": "Excluir",
    }
    return map[key] ?? key
  },
}))

vi.mock("@/stores/ia-session-store", () => ({
  useIASessionStore: () => ({
    isIASidebarOpen: true,
    closeIASidebar: mockCloseIASidebar,
    activeConversationId: null,
    setActiveConversation: mockSetActiveConversation,
    localUnreadCounts: {},
  }),
}))

vi.mock("@/stores/ui-preferences-store", () => ({
  useUIPreferencesStore: (sel: (s: any) => any) =>
    sel({ liaRecentItems: [] }),
}))

vi.mock("@/contexts/lia-float-context", () => ({
  useLiaFloat: () => ({
    open: vi.fn(),
    switchChatContext: mockSwitchChatContext,
    loadChatHistory: vi.fn(),
    chatContextType: "general",
    setChatMessages: mockSetChatMessages,
  }),
}))

vi.mock("@/hooks/ia-sessions/useIASessions", () => ({
  useIASessions: () => ({ data: [], isLoading: false }),
  useUpdateSession: () => ({ mutate: vi.fn() }),
  useMarkSessionRead: () => ({ mutate: vi.fn() }),
  useDeleteSession: () => ({ mutateAsync: vi.fn() }),
  useArchiveSession: () => ({ mutateAsync: vi.fn() }),
}))

// ── Test ─────────────────────────────────────────────────────────────────────

describe("IASidebar — Nova conversa contract", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("S1: clicking 'Nova conversa' calls switchChatContext with resetConversation: true", async () => {
    const { IASidebar } = await import("../IASidebar")
    render(
      <IASidebar onNewConversation={mockOnNewConversation} />
    )

    const btn = screen.getByText("Nova conversa")
    fireEvent.click(btn)

    expect(mockSwitchChatContext).toHaveBeenCalledTimes(1)
    expect(mockSwitchChatContext).toHaveBeenCalledWith(
      "general",
      { conversationId: null, resetConversation: true },
    )
  })

  it("S2: clicking 'Nova conversa' clears messages", async () => {
    const { IASidebar } = await import("../IASidebar")
    render(<IASidebar onNewConversation={mockOnNewConversation} />)

    fireEvent.click(screen.getByText("Nova conversa"))
    expect(mockSetChatMessages).toHaveBeenCalledWith([])
  })

  it("S3: clicking 'Nova conversa' calls onNewConversation prop", async () => {
    const { IASidebar } = await import("../IASidebar")
    render(<IASidebar onNewConversation={mockOnNewConversation} />)

    fireEvent.click(screen.getByText("Nova conversa"))
    expect(mockOnNewConversation).toHaveBeenCalledTimes(1)
  })

  it("S4: clicking 'Nova conversa' clears active conversation", async () => {
    const { IASidebar } = await import("../IASidebar")
    render(<IASidebar onNewConversation={mockOnNewConversation} />)

    fireEvent.click(screen.getByText("Nova conversa"))
    expect(mockSetActiveConversation).toHaveBeenCalledWith(null)
  })

  it("S5: clicking 'Nova conversa' closes sidebar", async () => {
    const { IASidebar } = await import("../IASidebar")
    render(<IASidebar onNewConversation={mockOnNewConversation} />)

    fireEvent.click(screen.getByText("Nova conversa"))
    expect(mockCloseIASidebar).toHaveBeenCalledTimes(1)
  })
})
