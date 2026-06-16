import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import React from "react"
import { useJobDraftsList } from "../useJobDraftsList"

// ── Helpers ────────────────────────────────────────────────────────────────

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  const Wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children)
  Wrapper.displayName = "QueryWrapper"
  return Wrapper
}

const MOCK_DRAFT = {
  id: "draft-uuid-1",
  job_title: "Engenheiro de Software",
  department: "Engenharia",
  seniority: "senior",
  status: "draft",
  current_step: 2,
  total_steps: 8,
  published_job_id: null,
  created_at: "2026-06-14T10:00:00Z",
  updated_at: "2026-06-14T10:05:00Z",
}

// ── Mocks ──────────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks()
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ drafts: [MOCK_DRAFT], total: 1, page: 1 }),
  })
})

// ── Tests ──────────────────────────────────────────────────────────────────

describe("useJobDraftsList", () => {
  it("mounts without throwing", () => {
    const { result } = renderHook(() => useJobDraftsList(), {
      wrapper: makeWrapper(),
    })
    expect(result.current).toBeDefined()
  })

  it("returns isLoading=true initially", () => {
    const { result } = renderHook(() => useJobDraftsList(), {
      wrapper: makeWrapper(),
    })
    expect(result.current.isLoading).toBe(true)
  })

  it("returns drafts from API after fetch", async () => {
    const { result } = renderHook(() => useJobDraftsList(), {
      wrapper: makeWrapper(),
    })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.drafts).toHaveLength(1)
    expect(result.current.drafts[0].id).toBe("draft-uuid-1")
    expect(result.current.drafts[0].job_title).toBe("Engenheiro de Software")
    expect(result.current.total).toBe(1)
  })

  it("returns empty array when API returns empty drafts", async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ drafts: [], total: 0, page: 1 }),
    })
    const { result } = renderHook(() => useJobDraftsList(), {
      wrapper: makeWrapper(),
    })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.drafts).toHaveLength(0)
    expect(result.current.total).toBe(0)
  })

  it("sets isError=true on fetch failure", async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: "Internal error" }),
    })
    const { result } = renderHook(() => useJobDraftsList(), {
      wrapper: makeWrapper(),
    })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.isError).toBe(true)
    expect(result.current.drafts).toHaveLength(0)
  })

  it("exposes refetch function", async () => {
    const { result } = renderHook(() => useJobDraftsList(), {
      wrapper: makeWrapper(),
    })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(typeof result.current.refetch).toBe("function")
  })

  it("fetches from correct proxy endpoint", async () => {
    const { result } = renderHook(() => useJobDraftsList(), {
      wrapper: makeWrapper(),
    })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/backend-proxy/job-drafts"),
    )
  })
})
