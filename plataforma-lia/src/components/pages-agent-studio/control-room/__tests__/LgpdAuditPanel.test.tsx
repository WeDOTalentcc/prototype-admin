// Onda 1 F10 (2026-05-27) — LgpdAuditPanel canonical tests.
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { LgpdAuditPanel } from "../LgpdAuditPanel"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
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

function renderWith() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <LgpdAuditPanel />
    </QueryClientProvider>,
  )
}

describe("LgpdAuditPanel — canonical Onda 1", () => {
  it("inicia collapsed, expande ao clicar no toggle", async () => {
    global.fetch = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => [],
    })) as unknown as typeof fetch

    renderWith()
    const toggle = screen.getByTestId("lgpd-audit-toggle")
    expect(toggle.getAttribute("aria-expanded")).toBe("false")
    fireEvent.click(toggle)
    await waitFor(() => {
      expect(toggle.getAttribute("aria-expanded")).toBe("true")
    })
  })

  it("não chama fetch enquanto collapsed (enabled: expanded)", () => {
    const fetchSpy = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => [],
    }))
    global.fetch = fetchSpy as unknown as typeof fetch
    renderWith()
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it("export all gera Blob CSV", async () => {
    const createObjectURL = vi.fn(() => "blob:fake")
    const revokeObjectURL = vi.fn()
    Object.defineProperty(URL, "createObjectURL", {
      value: createObjectURL,
      configurable: true,
    })
    Object.defineProperty(URL, "revokeObjectURL", {
      value: revokeObjectURL,
      configurable: true,
    })

    // recent-executions: 1 row
    global.fetch = vi.fn(async (url: string) => {
      if (url.includes("/reasoning")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            execution_id: "exec-1",
            agent_id: "agent-1",
            agent_name: "Catarina",
            started_at: null,
            completed_at: null,
            model_used: null,
            cost_usd: null,
            latency_ms: null,
            input_tokens: null,
            output_tokens: null,
            reasoning_trace: [],
            data_fields_accessed_summary: ["nome"],
            data_fields_NOT_accessed: ["cpf"],
          }),
        }
      }
      return {
        ok: true,
        status: 200,
        json: async () => [
          {
            execution_id: "exec-1",
            agent_id: "agent-1",
            agent_name: "Catarina",
            target_type: "talent_pool",
            target_id: "pool-1",
            target_name: "SP Tech Pros",
            status: "success",
            started_at: new Date().toISOString(),
            finished_at: null,
            latency_ms: 1000,
            success_summary: null,
          },
        ],
      }
    }) as unknown as typeof fetch

    renderWith()
    fireEvent.click(screen.getByTestId("lgpd-audit-toggle"))
    await waitFor(() => {
      expect(screen.getByTestId(/lgpd-audit-export-exec-1/)).toBeTruthy()
    })
    fireEvent.click(screen.getByTestId("lgpd-audit-export-all"))
    await waitFor(() => {
      expect(createObjectURL).toHaveBeenCalled()
    })
  })
})
