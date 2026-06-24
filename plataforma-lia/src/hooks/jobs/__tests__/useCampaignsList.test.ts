import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import React from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useCampaignsList, type CampaignItem } from "../useCampaignsList"

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
}

const mockCampaign: CampaignItem = {
  id: "camp-1",
  name: "Campanha Engenharia Q3",
  description: null,
  status: "active",
  job_id: null,
  talent_pool_id: null,
  automation_level: "semi",
  current_stage_index: 0,
  current_stage: "sourcing",
  stages: [
    { name: "sourcing", label: "Sourcing", status: "in_progress" },
    { name: "screening", label: "Triagem", status: "pending" },
  ],
  progress_pct: 0,
  total_candidates: 5,
  candidates_screened: 0,
  candidates_contacted: 0,
  candidates_interviewed: 0,
  candidates_offered: 0,
  candidates_hired: 0,
  created_by: "test@wedotalent.cc",
  created_at: "2026-06-14T10:00:00Z",
  updated_at: "2026-06-14T10:00:00Z",
}

describe("useCampaignsList", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("mounts without crashing", () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ data: [], total: 0, limit: 50, offset: 0 }),
    } as Response)

    const { result } = renderHook(() => useCampaignsList(), { wrapper: makeWrapper() })
    expect(result.current).toBeDefined()
  })

  it("returns isLoading=true initially", () => {
    vi.spyOn(global, "fetch").mockReturnValue(new Promise(() => {}))

    const { result } = renderHook(() => useCampaignsList(), { wrapper: makeWrapper() })
    expect(result.current.isLoading).toBe(true)
  })

  it("returns campaigns from API", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ data: [mockCampaign], total: 1, limit: 50, offset: 0 }),
    } as Response)

    const { result } = renderHook(() => useCampaignsList(), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.campaigns).toHaveLength(1)
    expect(result.current.campaigns[0].name).toBe("Campanha Engenharia Q3")
    expect(result.current.total).toBe(1)
  })

  it("returns empty array on empty response", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ data: [], total: 0, limit: 50, offset: 0 }),
    } as Response)

    const { result } = renderHook(() => useCampaignsList(), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.campaigns).toEqual([])
    expect(result.current.total).toBe(0)
  })

  it("returns isError=true on fetch failure", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
    } as Response)

    const { result } = renderHook(() => useCampaignsList(), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.isError).toBe(true)
  })

  it("exposes refetch function", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ data: [], total: 0, limit: 50, offset: 0 }),
    } as Response)

    const { result } = renderHook(() => useCampaignsList(), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(typeof result.current.refetch).toBe("function")
  })

  it("fetches from correct endpoint", async () => {
    const mockFetch = vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ data: [], total: 0, limit: 50, offset: 0 }),
    } as Response)

    const { result } = renderHook(() => useCampaignsList(), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(mockFetch).toHaveBeenCalledWith("/api/backend-proxy/recruitment-campaigns")
  })

  it("exposes stage details from campaign", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ data: [mockCampaign], total: 1, limit: 50, offset: 0 }),
    } as Response)

    const { result } = renderHook(() => useCampaignsList(), { wrapper: makeWrapper() })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    const camp = result.current.campaigns[0]
    expect(camp.stages[0].status).toBe("in_progress")
    expect(camp.stages[1].status).toBe("pending")
  })
})
