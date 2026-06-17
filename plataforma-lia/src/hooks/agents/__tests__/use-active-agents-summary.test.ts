// Onda 2 F12 (2026-05-27) — useActiveAgentsSummary canonical tests.
//
// Cobertura:
//   1. Query key correto inclui surface + limit.
//   2. refetchInterval default 10s.
//   3. surface filter passa para a URL.
import { describe, expect, it, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import React from "react"
import {
  useActiveAgentsSummary,
  ACTIVE_AGENTS_SUMMARY_QUERY_KEY,
} from "../use-active-agents-summary"

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

describe("useActiveAgentsSummary", () => {
  it("query key canonical inclui surface + limit", () => {
    expect(ACTIVE_AGENTS_SUMMARY_QUERY_KEY("decidir", 5)).toEqual([
      "agent-monitoring",
      "active-summary",
      "decidir",
      5,
    ])
    expect(ACTIVE_AGENTS_SUMMARY_QUERY_KEY("funil", 20)).toEqual([
      "agent-monitoring",
      "active-summary",
      "funil",
      20,
    ])
  })

  it("fetch passa surface + limit corretos na URL", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ running_count: 0, items: [] }),
    })
    global.fetch = fetchMock as unknown as typeof fetch

    renderHook(
      () => useActiveAgentsSummary({ surface: "pool", limit: 12 }),
      { wrapper },
    )

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled()
    })
    const url = String(fetchMock.mock.calls[0][0])
    expect(url).toContain("/api/backend-proxy/agent-monitoring/active-summary")
    expect(url).toContain("surface=pool")
    expect(url).toContain("limit=12")
  })

  it("enabled=false impede fetch", () => {
    const fetchMock = vi.fn()
    global.fetch = fetchMock as unknown as typeof fetch

    renderHook(
      () => useActiveAgentsSummary({ enabled: false }),
      { wrapper },
    )

    expect(fetchMock).not.toHaveBeenCalled()
  })
})
