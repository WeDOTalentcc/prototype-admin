import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import React from "react"
import { useProjectDetail } from "../useProjectDetail"

const MOCK_PROJECT = {
  id: "abc-123",
  name: "Dev Hiring Q3",
  description: null,
  status: "active" as const,
  job_id: null,
  talent_pool_id: null,
  automation_level: "semi" as const,
  current_stage_index: 1,
  current_stage: "screening",
  stages: [
    { name: "sourcing", label: "Sourcing", status: "completed" as const },
    { name: "screening", label: "Triagem", status: "in_progress" as const },
    { name: "interview", label: "Entrevista", status: "pending" as const },
  ],
  progress_pct: 33.3,
  total_candidates: 42,
  candidates_screened: 18,
  candidates_contacted: 12,
  candidates_interviewed: 5,
  candidates_offered: 2,
  candidates_hired: 1,
  created_by: null,
  created_at: "2026-06-01T10:00:00Z",
  updated_at: "2026-06-14T08:00:00Z",
}

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return React.createElement(QueryClientProvider, { client: qc }, children)
}

describe("useProjectDetail", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("returns loading state initially", () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify(MOCK_PROJECT), { status: 200 })
    )
    const { result } = renderHook(() => useProjectDetail("abc-123"), { wrapper })
    expect(result.current.isLoading).toBe(true)
  })

  it("returns project data after successful fetch", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify(MOCK_PROJECT), { status: 200 })
    )
    const { result } = renderHook(() => useProjectDetail("abc-123"), { wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.project?.name).toBe("Dev Hiring Q3")
    expect(result.current.project?.stages).toHaveLength(3)
  })

  it("sets isError on fetch failure", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(
      new Response("error", { status: 500 })
    )
    const { result } = renderHook(() => useProjectDetail("abc-123"), { wrapper })
    await waitFor(() => expect(result.current.isError).toBe(true))
  })

  it("does not fetch when id is empty", () => {
    const spy = vi.spyOn(global, "fetch")
    renderHook(() => useProjectDetail(""), { wrapper })
    expect(spy).not.toHaveBeenCalled()
  })

  it("exposes advance and isAdvancing", () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify(MOCK_PROJECT), { status: 200 })
    )
    const { result } = renderHook(() => useProjectDetail("abc-123"), { wrapper })
    expect(typeof result.current.advance).toBe("function")
    expect(result.current.isAdvancing).toBe(false)
  })
})
