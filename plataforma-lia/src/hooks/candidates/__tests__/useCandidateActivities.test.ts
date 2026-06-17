/**
 * Tests — useCandidateActivities hook
 *
 * Verifies: real API call, correct candidate_id param, empty state when
 * candidateId missing, error state on non-ok response.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { useCandidateActivities } from "@/hooks/candidates/use-candidate-activities"

const mockFetch = vi.fn()

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch)
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
  mockFetch.mockClear()
})

const makeCandidate = (id: string) => ({ id, name: "Test Candidate" })

describe("useCandidateActivities", () => {
  it("fetches activities for a given candidate_id", async () => {
    const fakeActivities = [
      {
        id: "act_1",
        type: "email_sent",
        title: "E-mail enviado",
        summary: "Convite para entrevista",
        timestamp: new Date().toISOString(),
        author: "LIA",
        status: "completed",
      },
    ]
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ activities: fakeActivities, total: 1 }),
    })

    const { result } = renderHook(() =>
      useCandidateActivities(makeCandidate("cand_abc")),
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("candidate_id=cand_abc"),
    )
    expect(result.current.activities).toHaveLength(1)
    expect(result.current.activities[0].type).toBe("email_sent")
    expect(result.current.total).toBe(1)
    expect(result.current.error).toBeNull()
  })

  it("returns empty state when candidateId is absent (no fetch)", () => {
    const { result } = renderHook(() => useCandidateActivities(null))
    // No fetch should be called, returns empty immediately
    expect(result.current.activities).toEqual([])
    expect(result.current.isLoading).toBe(false)
    expect(mockFetch).not.toHaveBeenCalled()
  })

  it("sets error state on non-ok response (fails loud, no silent fallback)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => "Internal Server Error",
    })

    const { result } = renderHook(() =>
      useCandidateActivities(makeCandidate("cand_err")),
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.error).toMatch(/500/)
    expect(result.current.activities).toEqual([])
  })

  it("handles array response format (legacy backend shape)", async () => {
    const fakeActivities = [
      { id: "a1", type: "lia_analysis", title: "Análise LIA" },
    ]
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => fakeActivities, // array, not { activities: [...] }
    })

    const { result } = renderHook(() =>
      useCandidateActivities(makeCandidate("cand_arr")),
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.activities).toHaveLength(1)
  })

  it("uses candidateId from candidateId field as fallback", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ activities: [], total: 0 }),
    })

    renderHook(() =>
      useCandidateActivities({ candidateId: "cand_fallback", name: "X" }),
    )

    await waitFor(() => expect(mockFetch).toHaveBeenCalled())
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("candidate_id=cand_fallback"),
    )
  })
})
