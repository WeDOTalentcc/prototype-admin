/**
 * Tests — useShortList hook (F4)
 *
 * Cobre:
 * - Estado inicial
 * - Fetch de short lists ao montar
 * - Erro no fetch
 * - createShortList chama POST e atualiza estado
 * - addCandidate chama POST /candidates e dispara refresh
 * - removeCandidate chama DELETE e dispara refresh
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { renderHook, act, waitFor } from "@testing-library/react"
import { useShortList } from "../candidates/use-short-list"

const mockShortListRaw = {
  id: "sl-001",
  job_id: "job-001",
  name: "Short List Principal",
  description: "Top candidatos",
  created_by: "user-1",
  created_at: "2026-03-12T10:00:00Z",
  candidate_count: 3,
}

const mappedShortList = {
  id: "sl-001",
  jobId: "job-001",
  name: "Short List Principal",
  description: "Top candidatos",
  createdBy: "user-1",
  createdAt: "2026-03-12T10:00:00Z",
  candidateCount: 3,
}

describe("useShortList", () => {
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockFetch = vi.fn()
    global.fetch = mockFetch
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("estado inicial: isLoading=false, shortLists=[], error=null", () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
      status: 200,
    })
    const { result } = renderHook(() => useShortList("", undefined))
    expect(result.current.shortLists).toEqual([])
    expect(result.current.error).toBeNull()
  })

  it("busca short lists ao montar com companyId", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [mockShortListRaw],
      status: 200,
    })
    const { result } = renderHook(() => useShortList("company-001", "job-001"))
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.shortLists).toHaveLength(1)
    expect(result.current.shortLists[0]).toMatchObject(mappedShortList)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("company_id=company-001"),
      undefined,
    )
  })

  it("seta error quando fetch falha", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ error: "Internal Server Error" }),
    })
    const { result } = renderHook(() => useShortList("company-001", "job-001"))
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.error).toBeTruthy()
  })

  it("createShortList faz POST e adiciona lista ao estado", async () => {
    // Fetch inicial (lista vazia)
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => [], status: 200 })
    // POST de criação
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => mockShortListRaw, status: 201 })

    const { result } = renderHook(() => useShortList("company-001", "job-001"))
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    let newList: Record<string, unknown>
    await act(async () => {
      newList = await result.current.createShortList("job-001", "Short List Principal")
    })

    expect(newList).toMatchObject(mappedShortList)
    expect(result.current.shortLists).toHaveLength(1)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("short-lists"),
      expect.objectContaining({ method: "POST" }),
    )
  })

  it("addCandidate faz POST e incrementa refresh", async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => [mockShortListRaw], status: 200 })
      .mockResolvedValueOnce({ ok: true, json: async () => ({}), status: 200 })
      .mockResolvedValueOnce({ ok: true, json: async () => [mockShortListRaw], status: 200 })

    const { result } = renderHook(() => useShortList("company-001", "job-001"))
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    let ok: boolean
    await act(async () => {
      ok = await result.current.addCandidate("sl-001", "cand-999")
    })

    expect(ok!).toBe(true)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("sl-001/candidates"),
      expect.objectContaining({ method: "POST" }),
    )
  })

  it("removeCandidate faz DELETE e incrementa refresh", async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => [mockShortListRaw], status: 200 })
      .mockResolvedValueOnce({ ok: false, status: 204, json: async () => ({}) })
      .mockResolvedValueOnce({ ok: true, json: async () => [mockShortListRaw], status: 200 })

    const { result } = renderHook(() => useShortList("company-001", "job-001"))
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await act(async () => {
      await result.current.removeCandidate("sl-001", "cand-999")
    })

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("sl-001/candidates/cand-999"),
      expect.objectContaining({ method: "DELETE" }),
    )
  })
})
