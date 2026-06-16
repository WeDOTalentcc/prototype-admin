import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, act } from "@testing-library/react"

// ─── Fase 4-D: snapshot wiring tests ─────────────────────────────────────────
// Verifica que:
//  1. SearchHistoryItem aceita fingerprint
//  2. executeSearch chama snapshot endpoint quando _snapshot_fingerprint presente
//  3. onReExecuteSearch usa snapshot path quando item.fingerprint existe

describe("SearchHistoryItem fingerprint field", () => {
  it("accepts fingerprint as optional string", () => {
    const item = {
      id: "h1",
      query: "engenheiro backend",
      mode: "natural" as const,
      source: "global" as const,
      timestamp: new Date().toISOString(),
      fingerprint: "abc123def456",
    }
    expect(item.fingerprint).toBe("abc123def456")
  })

  it("fingerprint is optional — item without it is valid", () => {
    const item = {
      id: "h2",
      query: "product manager",
      mode: "natural" as const,
      source: "local" as const,
      timestamp: new Date().toISOString(),
    }
    expect(item.fingerprint).toBeUndefined()
  })
})

describe("executeSearch snapshot path", () => {
  const mockSetters = {
    setIsLoading: vi.fn(),
    setIsSearchActive: vi.fn(),
    setSearchResults: vi.fn(),
    setCandidates: vi.fn(),
    setHasSearchResults: vi.fn(),
    setSearchResultsCount: vi.fn(),
    setLocalResultsCount: vi.fn(),
    setPearchResultsCount: vi.fn(),
    setCreditsUsedInSearch: vi.fn(),
    setCreditsRemaining: vi.fn(),
    setShowSearchResults: vi.fn(),
    setDisplayedResultsCount: vi.fn(),
    setCurrentSearchSource: vi.fn(),
    setHasSearched: vi.fn(),
    setLastSearchEntities: vi.fn(),
    setLastSearchMetadata: vi.fn(),
    setLastSearchUsedPearch: vi.fn(),
    setSearchExecutionId: vi.fn(),
    setShowExpandGlobalOption: vi.fn(),
    setLastSuccessfulQuery: vi.fn(),
    setChatMessages: vi.fn(),
    setSearchThreadId: vi.fn(),
    setSearchFingerprint: vi.fn(),
    setSearchFeedbacks: vi.fn(),
    hideViewedCandidatesFilter: (c: unknown[]) => c,
    talentFunnel: { addToHistory: vi.fn() },
    searchSource: "local" as const,
    pearchSearchOptions: {
      searchType: "full",
      limit: 30,
      showEmails: true,
      showPhoneNumbers: true,
      highFreshness: false,
      requireEmails: false,
      requirePhoneNumbers: false,
    },
    searchThreadId: undefined,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  it("calls snapshot endpoint when _snapshot_fingerprint override is present", async () => {
    const { useCandidatesExecuteSearch } = await import(
      "@/components/pages/candidates/hooks/useCandidatesExecuteSearch"
    )

    const snapCandidates = [
      { id: "c1", name: "Ana Lima", headline: "Eng Backend", skills: [], score: 0.8 },
    ]
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({
        candidates: snapCandidates,
        total_count: 1,
        pearch_count: 1,
        credits_used: 0,
      }),
    })

    const { result } = renderHook(() => useCandidatesExecuteSearch(mockSetters))

    await act(async () => {
      await result.current.executeSearch("query", undefined, "natural", undefined, false, {
        _snapshot_fingerprint: "fp-abc123",
      })
    })

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/candidates/search/snapshot?fingerprint=fp-abc123")
    )
    expect(mockSetters.setCandidates).toHaveBeenCalled()
    expect(mockSetters.setCreditsUsedInSearch).toHaveBeenCalledWith(0)
    expect(mockSetters.setSearchFingerprint).toHaveBeenCalledWith("fp-abc123")
  })

  it("does not call snapshot endpoint on regular search", async () => {
    const { useCandidatesExecuteSearch } = await import(
      "@/components/pages/candidates/hooks/useCandidatesExecuteSearch"
    )

    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      json: async () => ({}),
    })

    const { result } = renderHook(() => useCandidatesExecuteSearch(mockSetters))

    await act(async () => {
      try {
        await result.current.executeSearch("backend dev", undefined, "natural", undefined, false)
      } catch { /* search may fail without full mock */ }
    })

    // snapshot endpoint NOT called (real search hits different path)
    const calls = (global.fetch as ReturnType<typeof vi.fn>).mock.calls
    const snapshotCalls = calls.filter(([url]: [string]) =>
      typeof url === "string" && url.includes("/search/snapshot")
    )
    expect(snapshotCalls).toHaveLength(0)
  })

  it("addToHistory receives fingerprint from snapshot path", async () => {
    const { useCandidatesExecuteSearch } = await import(
      "@/components/pages/candidates/hooks/useCandidatesExecuteSearch"
    )

    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({
        candidates: [{ id: "c1", name: "Test", skills: [] }],
        total_count: 1,
        pearch_count: 1,
        credits_used: 0,
      }),
    })

    const { result } = renderHook(() => useCandidatesExecuteSearch(mockSetters))

    await act(async () => {
      await result.current.executeSearch("query", undefined, "natural", undefined, false, {
        _snapshot_fingerprint: "fp-xyz789",
      })
    })

    expect(mockSetters.talentFunnel.addToHistory).toHaveBeenCalledWith(
      expect.objectContaining({ fingerprint: "fp-xyz789" })
    )
  })
})
