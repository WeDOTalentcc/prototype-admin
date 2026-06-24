import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, act } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import React from "react"

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockRequestNewConversation = vi.fn().mockResolvedValue(true)
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
    switchChatContext: vi.fn(),
    loadChatHistory: vi.fn(),
    chatContextType: "general",
    setChatMessages: vi.fn(),
    requestNewConversation: mockRequestNewConversation,
  }),
}))

vi.mock("@/hooks/ia-sessions/useIASessions", () => ({
  useIASessions: () => ({ data: [], isLoading: false }),
  useUpdateSession: () => ({ mutate: vi.fn() }),
  useMarkSessionRead: () => ({ mutate: vi.fn() }),
  useDeleteSession: () => ({ mutateAsync: vi.fn() }),
  useArchiveSession: () => ({ mutateAsync: vi.fn() }),
}))

// ── Tests ────────────────────────────────────────────────────────────────────

describe("IASidebar — Nova conversa contract (wizard guard lift)", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRequestNewConversation.mockResolvedValue(true)
  })

  it("S1: clicking Nova conversa calls requestNewConversation from context", async () => {
    const { IASidebar } = await import("../IASidebar")
    render(<IASidebar onNewConversation={mockOnNewConversation} />)

    await act(async () => {
      screen.getByText("Nova conversa").click()
    })

    expect(mockRequestNewConversation).toHaveBeenCalledTimes(1)
  })

  it("S2: when requestNewConversation resolves true, clears active conversation", async () => {
    const { IASidebar } = await import("../IASidebar")
    render(<IASidebar onNewConversation={mockOnNewConversation} />)

    await act(async () => {
      screen.getByText("Nova conversa").click()
    })

    expect(mockSetActiveConversation).toHaveBeenCalledWith(null)
  })

  it("S3: when requestNewConversation resolves true, calls onNewConversation prop", async () => {
    const { IASidebar } = await import("../IASidebar")
    render(<IASidebar onNewConversation={mockOnNewConversation} />)

    await act(async () => {
      screen.getByText("Nova conversa").click()
    })

    expect(mockOnNewConversation).toHaveBeenCalledTimes(1)
  })

  it("S4: when requestNewConversation resolves true, closes sidebar", async () => {
    const { IASidebar } = await import("../IASidebar")
    render(<IASidebar onNewConversation={mockOnNewConversation} />)

    await act(async () => {
      screen.getByText("Nova conversa").click()
    })

    expect(mockCloseIASidebar).toHaveBeenCalledTimes(1)
  })

  it("S5: when requestNewConversation resolves false (wizard denied), does NOTHING", async () => {
    mockRequestNewConversation.mockResolvedValue(false)

    const { IASidebar } = await import("../IASidebar")
    render(<IASidebar onNewConversation={mockOnNewConversation} />)

    await act(async () => {
      screen.getByText("Nova conversa").click()
    })

    expect(mockSetActiveConversation).not.toHaveBeenCalled()
    expect(mockOnNewConversation).not.toHaveBeenCalled()
    expect(mockCloseIASidebar).not.toHaveBeenCalled()
  })
})
