import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, act } from "@testing-library/react"

// Pina o contrato E2E do handleLoadMore:
// 1. Não chama refineSearch enquanto há buffer local (displayedResultsCount < candidates.length)
// 2. Chama refineSearch quando buffer esgotado + canLoadMore=true
// 3. Passa dislikedDocids como docidBlacklist
// 4. Passa searchFingerprint da busca inicial

vi.mock("@/lib/api/candidate-search", () => ({
  searchCandidates: vi.fn(),
  refineSearch: vi.fn(),
}))

vi.mock("@/lib/utils/source-detection", () => ({
  isGlobalSource: vi.fn(() => false),
}))

import type { CandidatesSearchContext } from "@/components/pages/candidates/hooks/useCandidatesSearch"
import type { Candidate } from "@/components/pages/candidates/types"

const LOAD_MORE_STEP = 15

function buildCtx(overrides: Partial<CandidatesSearchContext> = {}): CandidatesSearchContext {
  return {
    candidates: [] as Candidate[],
    setCandidates: vi.fn(),
    searchResults: {
      local: [], global: [], localCount: 0, globalCount: 0, query: "",
      isLoading: false, showGlobalResults: false, globalDismissed: false,
      isEnrichingContacts: false, filteredNoContact: 0, enrichmentAttempted: 0,
    },
    setSearchResults: vi.fn(),
    searchTerm: "",
    lastSearchQuery: "dev backend",
    lastSearchEntities: null,
    lastSearchMode: "natural",
    lastSearchMetadata: undefined,
    lastSearchUsedPearch: false,
    searchSource: "hybrid",
    setSearchSource: vi.fn(),
    currentSearchSource: "hybrid",
    setCurrentSearchSource: vi.fn(),
    openCreditModals: { hybrid: false, global: false, email: false, phone: false },
    setOpenCreditModals: vi.fn(),
    pearchSearchOptions: {
      searchType: "fast", limit: 30, showEmails: true, showPhoneNumbers: true,
      highFreshness: false, requireEmails: false, requirePhoneNumbers: false,
    },
    setPearchSearchOptions: vi.fn(),
    creditsRemaining: null,
    setCreditsRemaining: vi.fn(),
    creditsUsedInSearch: 0,
    setCreditsUsedInSearch: vi.fn(),
    pearchResultsCount: 0,
    setPearchResultsCount: vi.fn(),
    localResultsCount: 0,
    setLocalResultsCount: vi.fn(),
    searchResultsCount: 0,
    setSearchResultsCount: vi.fn(),
    showSearchResults: false,
    setShowSearchResults: vi.fn(),
    hasSearchResults: true,
    setHasSearchResults: vi.fn(),
    showGlobalExpansionConfirm: false,
    setShowGlobalExpansionConfirm: vi.fn(),
    isExpandingToGlobal: false,
    setIsExpandingToGlobal: vi.fn(),
    displayedResultsCount: 0,
    setDisplayedResultsCount: vi.fn(),
    isLoadingMore: false,
    setIsLoadingMore: vi.fn(),
    canLoadMore: true,
    setCanLoadMore: vi.fn(),
    searchFeedbacks: {},
    setSearchFeedbacks: vi.fn(),
    hasSearched: true,
    lastSuccessfulQuery: "dev backend",
    setSearchThreadId: vi.fn(),
    setSearchFingerprint: vi.fn(),
    searchThreadId: "thread-123",
    searchFingerprint: "fp-abc123",
    showExpandGlobalOption: false,
    setShowExpandGlobalOption: vi.fn(),
    setChatMessages: vi.fn(),
    showSourceChangeModal: false,
    setShowSourceChangeModal: vi.fn(),
    pendingSourceChange: null,
    setPendingSourceChange: vi.fn(),
    showContactFilterModal: false,
    setShowContactFilterModal: vi.fn(),
    pendingContactFilter: null,
    setPendingContactFilter: vi.fn(),
    showCreditConfirmation: false,
    setShowCreditConfirmation: vi.fn(),
    pendingSearchRequest: null,
    setPendingSearchRequest: vi.fn(),
    activeSearchFilters: {} as CandidatesSearchContext["activeSearchFilters"],
    setActiveSearchFilters: vi.fn(),
    setSelectedTemplate: vi.fn(),
    executeSearch: vi.fn(),
    user: null,
    ...overrides,
  }
}

describe("handleLoadMore — contrato E2E (Task 3)", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("revela buffer local sem chamar refineSearch quando candidates.length > displayedResultsCount", async () => {
    const { refineSearch } = await import("@/lib/api/candidate-search")
    const { useCandidatesSearch } = await import(
      "@/components/pages/candidates/hooks/useCandidatesSearch"
    )

    const mockCandidates = Array.from({ length: 20 }, (_, i) => ({ id: `c${i}` } as unknown as Candidate))
    const setDisplayedResultsCount = vi.fn()

    const ctx = buildCtx({
      candidates: mockCandidates,
      displayedResultsCount: 5, // 5 revealed, 20 total → buffer available
      setDisplayedResultsCount,
    })

    const { result } = renderHook(() => useCandidatesSearch(ctx))

    await act(async () => {
      await result.current.handleLoadMore()
    })

    expect(refineSearch).not.toHaveBeenCalled()
    expect(setDisplayedResultsCount).toHaveBeenCalled()
  })

  it("chama refineSearch quando buffer local esgotado e canLoadMore=true", async () => {
    const { refineSearch } = await import("@/lib/api/candidate-search")
    ;(refineSearch as ReturnType<typeof vi.fn>).mockResolvedValue({
      candidates: [{ id: "new1", name: "Novo Candidato", skills: [], score: 0.7 }],
      can_load_more: false,
      total_count: 1,
    })

    const { useCandidatesSearch } = await import(
      "@/components/pages/candidates/hooks/useCandidatesSearch"
    )

    const mockCandidates = Array.from({ length: 10 }, (_, i) => ({ id: `c${i}` } as unknown as Candidate))
    const ctx = buildCtx({
      candidates: mockCandidates,
      displayedResultsCount: 10, // all revealed = buffer exhausted
      canLoadMore: true,
      searchThreadId: "thread-abc",
      lastSearchQuery: "dev backend",
    })

    const { result } = renderHook(() => useCandidatesSearch(ctx))

    await act(async () => {
      await result.current.handleLoadMore()
    })

    expect(refineSearch).toHaveBeenCalledWith(
      "thread-abc",
      "dev backend",
      LOAD_MORE_STEP,
      expect.objectContaining({})
    )
  })

  it("passa docidBlacklist com IDs dos candidatos com dislike", async () => {
    const { refineSearch } = await import("@/lib/api/candidate-search")
    ;(refineSearch as ReturnType<typeof vi.fn>).mockResolvedValue({
      candidates: [],
      can_load_more: false,
    })

    const { useCandidatesSearch } = await import(
      "@/components/pages/candidates/hooks/useCandidatesSearch"
    )

    const mockCandidates = Array.from({ length: 10 }, (_, i) => ({ id: `c${i}` } as unknown as Candidate))
    const ctx = buildCtx({
      candidates: mockCandidates,
      displayedResultsCount: 10,
      canLoadMore: true,
      searchFeedbacks: {
        "cand-001": "dislike",
        "cand-002": "like",
        "cand-003": "dislike",
      },
    })

    const { result } = renderHook(() => useCandidatesSearch(ctx))

    await act(async () => {
      await result.current.handleLoadMore()
    })

    expect(refineSearch).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(String),
      LOAD_MORE_STEP,
      expect.objectContaining({
        docidBlacklist: expect.arrayContaining(["cand-001", "cand-003"]),
      })
    )
    const callArgs = (refineSearch as ReturnType<typeof vi.fn>).mock.calls[0][3]
    expect(callArgs.docidBlacklist).not.toContain("cand-002")
  })

  it("NÃO chama refineSearch quando canLoadMore=false", async () => {
    const { refineSearch } = await import("@/lib/api/candidate-search")
    const { useCandidatesSearch } = await import(
      "@/components/pages/candidates/hooks/useCandidatesSearch"
    )

    const mockCandidates = Array.from({ length: 10 }, (_, i) => ({ id: `c${i}` } as unknown as Candidate))
    const ctx = buildCtx({
      candidates: mockCandidates,
      displayedResultsCount: 10,
      canLoadMore: false, // backend says no more
    })

    const { result } = renderHook(() => useCandidatesSearch(ctx))

    await act(async () => {
      await result.current.handleLoadMore()
    })

    expect(refineSearch).not.toHaveBeenCalled()
  })
})
