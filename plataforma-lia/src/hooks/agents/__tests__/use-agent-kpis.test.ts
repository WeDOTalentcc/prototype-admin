// Onda 4 F8 (2026-05-28) — useAgentKpis canonical tests.
//
// Cobertura:
//   1. Query key canonical inclui agentId + period.
//   2. URL inclui period param corretamente.
import { describe, expect, it, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import React from "react"
import {
  useAgentKpis,
  AGENT_KPIS_QUERY_KEY,
} from "../use-agent-kpis"

beforeEach(() => {
  Object.defineProperty(window, "localStorage", {
    value: {
      getItem: vi.fn(() => "token-fake"),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    },
    configurable: true,
  })
})

function wrapper({ children }: { children: React.ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return React.createElement(QueryClientProvider, { client }, children)
}

describe("useAgentKpis", () => {
  it("query key canonical inclui agentId + period", () => {
    expect(AGENT_KPIS_QUERY_KEY("abc-123", "30d")).toEqual([
      "agents",
      "kpis",
      "abc-123",
      "30d",
    ])
    expect(AGENT_KPIS_QUERY_KEY("xyz", "7d")).toEqual([
      "agents",
      "kpis",
      "xyz",
      "7d",
    ])
  })

  it("URL inclui period param corretamente", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          agent_id: "abc",
          agent_name: "Catarina",
          agent_category: "screening",
          period: "90d",
          bucket: {
            period: "90d",
            candidates_processed: 0,
            candidates_approved: 0,
            candidates_rejected: 0,
            candidates_pending: 0,
            avg_execution_seconds: 0,
            p95_execution_seconds: 0,
            total_executions: 0,
            error_count: 0,
            total_cost_usd: 0,
            total_tokens_input: 0,
            total_tokens_output: 0,
          },
          hour_heatmap: [],
          tool_breakdown: [],
          last_run_at: null,
          is_learning: true,
        }),
    })
    global.fetch = fetchMock as unknown as typeof fetch

    renderHook(() => useAgentKpis("abc-123", "90d"), { wrapper })

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled()
    })
    const url = String(fetchMock.mock.calls[0][0])
    expect(url).toContain("/api/backend-proxy/custom-agents/abc-123/kpis")
    expect(url).toContain("period=90d")
  })
})
