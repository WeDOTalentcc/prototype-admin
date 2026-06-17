// Onda 1 F10 (2026-05-27) — RecentExecutionsTable canonical tests.
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { RecentExecutionsTable } from "../RecentExecutionsTable"
import type { RecentExecution } from "../../decision-tree/types"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({ persona: { name: "Lia", tone: "profissional" } }),
}))

vi.mock("@/hooks/agents", () => ({
  useCustomAgents: () => ({ agents: [], total: 0, isLoading: false, isError: false, mutate: () => {} }),
}))

beforeEach(() => {
  Object.defineProperty(window, "localStorage", {
    value: { getItem: vi.fn(() => "token") },
    configurable: true,
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

function renderWith(ui: React.ReactNode) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

const ROW: RecentExecution = {
  execution_id: "exec-1",
  agent_id: "agent-1",
  agent_name: "Catarina",
  target_type: "talent_pool",
  target_id: "pool-1",
  target_name: "SP Tech Pros",
  status: "success",
  started_at: "2026-05-27T11:00:00Z",
  finished_at: "2026-05-27T11:00:05Z",
  latency_ms: 5000,
  success_summary: "Processed 4 candidates",
}

describe("RecentExecutionsTable — canonical Onda 1", () => {
  it("renderiza empty state quando backend retorna []", async () => {
    global.fetch = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => [],
    })) as unknown as typeof fetch

    renderWith(<RecentExecutionsTable onOpenReasoning={() => {}} />)
    await waitFor(() => {
      expect(screen.getByTestId("recent-executions-empty")).toBeTruthy()
    })
  })

  it("renderiza tabela com linhas + status chip", async () => {
    global.fetch = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => [ROW],
    })) as unknown as typeof fetch

    renderWith(<RecentExecutionsTable onOpenReasoning={() => {}} />)
    await waitFor(() => {
      expect(screen.getByText("Catarina")).toBeTruthy()
      expect(screen.getByText("SP Tech Pros")).toBeTruthy()
      expect(screen.getByTestId(/recent-row-exec-1/)).toBeTruthy()
    })
  })

  it("clicar na linha dispara onOpenReasoning com executionId", async () => {
    global.fetch = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => [ROW],
    })) as unknown as typeof fetch

    const handler = vi.fn()
    renderWith(<RecentExecutionsTable onOpenReasoning={handler} />)
    await waitFor(() => {
      expect(screen.getByTestId("recent-row-exec-1")).toBeTruthy()
    })
    fireEvent.click(screen.getByTestId("recent-row-exec-1"))
    expect(handler).toHaveBeenCalledWith("exec-1")
  })
})
