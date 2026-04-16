/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import React from "react"

// -- Module mocks ------------------------------------------------------------
vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
  useLocale: () => "pt-BR",
}))

vi.mock("next/dynamic", () => ({
  default: () => {
    const Stub = () => null
    return Stub
  },
}))

const mockRefresh = vi.fn()
const hookState: Record<string, unknown> = {
  candidates: [],
  loading: false,
  error: null,
  errorKind: null,
  total: 0,
  currentPage: 1,
  totalPages: 1,
  filters: { search: "", status: "", tags: [], seniority: "" },
  goToPage: vi.fn(),
  setFilters: vi.fn(),
  updateFilter: vi.fn(),
  refresh: mockRefresh,
}

vi.mock("@/hooks/candidates/use-candidates-list", () => ({
  useCandidatesList: () => hookState,
}))

vi.mock("@/hooks/candidates/use-bulk-selection", () => ({
  useBulkSelection: () => ({
    selectedCandidates: new Set<string>(),
    toggleCandidate: vi.fn(),
    selectAll: vi.fn(),
    clearSelection: vi.fn(),
  }),
}))

vi.mock("@/hooks/candidates/use-talent-funnel", () => ({
  useTalentFunnel: () => ({
    savedSearches: [],
    addSavedSearch: vi.fn(),
    updateSavedSearch: vi.fn(),
    removeSavedSearch: vi.fn(),
    toggleSavedSearchFavorite: vi.fn(),
    getFavoriteIds: () => [],
    getPinnedIds: () => [],
    getFavoriteNotes: () => ({}),
    toggleFavoriteCandidate: vi.fn(),
    togglePinnedCandidate: vi.fn(),
    favoriteCandidatesData: [],
  }),
}))

vi.mock("@/components/pages/candidates/CandidatesTable", () => ({
  CandidatesTable: () => <div data-testid="candidates-table" />,
}))

vi.mock("@/components/ui/bulk-actions-bar", () => ({
  BulkActionsBar: () => null,
}))

vi.mock("@/components/ui/loading", () => ({
  LoadingFallback: () => null,
}))

// ---------------------------------------------------------------------------
import FunilDeTalentosClient from "../FunilDeTalentosClient"

function resetHookState(overrides: Partial<typeof hookState> = {}) {
  hookState.candidates = []
  hookState.loading = false
  hookState.error = null
  hookState.errorKind = null
  hookState.total = 0
  hookState.currentPage = 1
  hookState.totalPages = 1
  hookState.goToPage = vi.fn()
  hookState.setFilters = vi.fn()
  hookState.updateFilter = vi.fn()
  hookState.refresh = mockRefresh
  Object.assign(hookState, overrides)
}

describe("FunilDeTalentosClient — estados de erro (task #293)", () => {
  beforeEach(() => {
    mockRefresh.mockReset()
    resetHookState()
    // jsdom: window.location mocked for CTA handler
    delete (window as unknown as { location?: unknown }).location
    ;(window as unknown as { location: { pathname: string; search: string; href: string } }).location = {
      pathname: "/pt-BR/funil-de-talentos",
      search: "",
      href: "",
    }
  })

  it("401 → renderiza funil-relogin-state e oculta tabela", () => {
    resetHookState({ error: "HTTP 401", errorKind: "unauthorized" })
    render(<FunilDeTalentosClient />)

    const relogin = screen.getByTestId("funil-relogin-state")
    expect(relogin).toBeTruthy()
    expect(relogin.getAttribute("role")).toBe("alert")
    expect(screen.queryByTestId("candidates-table")).toBeNull()
    expect(screen.queryByTestId("funil-error-state")).toBeNull()
  })

  it("403 → também renderiza estado de relogin", () => {
    resetHookState({ error: "HTTP 403", errorKind: "forbidden" })
    render(<FunilDeTalentosClient />)
    expect(screen.getByTestId("funil-relogin-state")).toBeTruthy()
    expect(screen.queryByTestId("candidates-table")).toBeNull()
  })

  it("500 → renderiza funil-error-state com botão de retry; tabela permanece", () => {
    resetHookState({ error: "HTTP 500", errorKind: "server" })
    render(<FunilDeTalentosClient />)

    expect(screen.getByTestId("funil-error-state")).toBeTruthy()
    expect(screen.queryByTestId("funil-relogin-state")).toBeNull()
    expect(screen.queryByTestId("candidates-table")).not.toBeNull()
  })

  it("5xx retry aciona refresh() do hook", async () => {
    resetHookState({ error: "HTTP 503", errorKind: "server" })
    render(<FunilDeTalentosClient />)

    const retryButton = screen
      .getByTestId("funil-error-state")
      .querySelector("button")
    expect(retryButton).not.toBeNull()
    await userEvent.click(retryButton as HTMLButtonElement)
    expect(mockRefresh).toHaveBeenCalledTimes(1)
  })

  it("network error → funil-error-state (não relogin)", () => {
    resetHookState({ error: "Network", errorKind: "network" })
    render(<FunilDeTalentosClient />)
    expect(screen.getByTestId("funil-error-state")).toBeTruthy()
    expect(screen.queryByTestId("funil-relogin-state")).toBeNull()
  })

  it("sem erro → tabela visível, nenhum estado de erro renderizado", () => {
    resetHookState()
    render(<FunilDeTalentosClient />)
    expect(screen.queryByTestId("funil-error-state")).toBeNull()
    expect(screen.queryByTestId("funil-relogin-state")).toBeNull()
  })
})
