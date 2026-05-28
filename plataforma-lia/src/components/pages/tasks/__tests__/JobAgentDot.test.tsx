// Onda 2 F12 (2026-05-27) — JobAgentDot canonical tests.
//
// Cobertura:
//   1. Renderiza pingo quando há deployments ativos.
//   2. Oculto quando deployments vazio.
//   3. Oculto quando targetId null (sem fetch).
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { JobAgentDot } from "../JobAgentDot"
import type { DeploymentListResponse } from "@/types/agents/agent-deployment"

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

function renderWithQuery(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  )
}

function mockFetchOnce(body: DeploymentListResponse) {
  global.fetch = vi.fn().mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  }) as unknown as typeof fetch
}

describe("JobAgentDot", () => {
  it("renderiza pingo quando há deployments ativos", async () => {
    mockFetchOnce({
      total: 2,
      deployments: [
        {
          id: "d1",
          agent_id: "a1",
          target_type: "job",
          target_id: "job-1",
          target_name: null,
          is_active: true,
          created_at: null,
          updated_at: null,
        },
        {
          id: "d2",
          agent_id: "a2",
          target_type: "job",
          target_id: "job-1",
          target_name: null,
          is_active: true,
          created_at: null,
          updated_at: null,
        },
      ],
    })
    const { container } = renderWithQuery(
      <JobAgentDot targetId="job-1" />,
    )
    await waitFor(() => {
      const dot = container.querySelector("span[role='img']")
      expect(dot).not.toBeNull()
      expect(dot?.getAttribute("title")).toMatch(/2 agentes acoplados/)
    })
  })

  it("oculto quando deployments vazio", async () => {
    mockFetchOnce({ total: 0, deployments: [] })
    const { container } = renderWithQuery(
      <JobAgentDot targetId="job-1" />,
    )
    await waitFor(() => {
      expect(container.querySelector("span[role='img']")).toBeNull()
    })
  })

  it("oculto quando targetId null (sem fetch)", () => {
    const fetchMock = vi.fn()
    global.fetch = fetchMock as unknown as typeof fetch
    const { container } = renderWithQuery(<JobAgentDot targetId={null} />)
    expect(container.querySelector("span[role='img']")).toBeNull()
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
