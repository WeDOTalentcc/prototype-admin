// Onda 1 F10 (2026-05-27) — LiveAgentsList canonical tests.
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { LiveAgentsList } from "../LiveAgentsList"
import type { ActiveExecution } from "../../decision-tree/types"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, vars?: Record<string, unknown>) => {
    if (vars && "count" in vars) return `processed:${vars.count}`
    if (vars && "value" in vars) return `~${vars.value}`
    return key
  },
}))

vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({ persona: { name: "Lia", tone: "profissional" } }),
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

describe("LiveAgentsList — canonical Onda 1", () => {
  it("renderiza empty state quando backend retorna []", async () => {
    global.fetch = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => [],
    })) as unknown as typeof fetch

    renderWith(<LiveAgentsList onOpenReasoning={() => {}} />)
    await waitFor(() => {
      expect(screen.getByTestId("live-agents-empty")).toBeTruthy()
    })
  })

  it("renderiza lista com agent_name + processed count + ETA", async () => {
    const exec: ActiveExecution = {
      execution_id: "exec-1",
      agent_id: "agent-1",
      agent_name: "Catarina",
      target_type: "talent_pool",
      target_id: "pool-1",
      target_name: "SP Tech Pros",
      status: "running",
      started_at: "2026-05-27T12:00:00Z",
      progress_pct: 17,
      candidates_processed: 4,
      eta_seconds: 120,
    }
    global.fetch = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => [exec],
    })) as unknown as typeof fetch

    renderWith(<LiveAgentsList onOpenReasoning={() => {}} />)
    await waitFor(() => {
      expect(screen.getByText("Catarina")).toBeTruthy()
      expect(screen.getByText(/SP Tech Pros/)).toBeTruthy()
      expect(screen.getByText("processed:4")).toBeTruthy()
      // ETA 120s → "2min"
      expect(screen.getByText("~2min")).toBeTruthy()
    })
  })

  it("ul container tem aria-live polite (a11y canonical)", async () => {
    const exec: ActiveExecution = {
      execution_id: "exec-1",
      agent_id: "agent-1",
      agent_name: "Catarina",
      target_type: "talent_pool",
      target_id: "pool-1",
      target_name: null,
      status: "running",
      started_at: "2026-05-27T12:00:00Z",
      progress_pct: null,
      candidates_processed: null,
      eta_seconds: null,
    }
    global.fetch = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => [exec],
    })) as unknown as typeof fetch

    renderWith(<LiveAgentsList onOpenReasoning={() => {}} />)
    await waitFor(() => {
      const list = screen.getByTestId("live-agents-list")
      expect(list.getAttribute("aria-live")).toBe("polite")
    })
  })
})
