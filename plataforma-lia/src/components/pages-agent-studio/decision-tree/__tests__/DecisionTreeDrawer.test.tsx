// Onda 1 F10 (2026-05-27) — DecisionTreeDrawer canonical tests.
//
// Cobertura mínima exigida (5 cenários):
//   1. Renderiza com executionId e fica em loading.
//   2. Mostra metadados (modelo, custo, tokens, duração) após carregar.
//   3. Mostra "legacy notice" quando backend retorna 404.
//   4. Expande "Ver detalhes técnicos" → renderiza todos os steps.
//   5. Export CSV gera Blob (mock URL.createObjectURL).
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { DecisionTreeDrawer } from "../DecisionTreeDrawer"
import type { ExecutionReasoningResponse } from "../types"

// ──────────────────────────────────────────────────────────────────────────
// Mocks
// ──────────────────────────────────────────────────────────────────────────
vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, vars?: Record<string, unknown>) => {
    if (vars && "score" in vars) return `Score: ${vars.score}`
    return key
  },
}))

vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({ persona: { name: "Lia", tone: "profissional" } }),
}))

// Garante localStorage para fetchReasoning. Fake timers ficam OFF — React Query
// usa Promise scheduling internamente, que interage mal com useFakeTimers.
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

afterEach(() => {
  vi.restoreAllMocks()
})

function makeReasoning(): ExecutionReasoningResponse {
  return {
    execution_id: "exec-1",
    agent_id: "agent-1",
    agent_name: "Catarina",
    started_at: "2026-05-27T11:59:55Z",
    completed_at: "2026-05-27T12:00:00Z",
    model_used: "claude-sonnet-4.7",
    cost_usd: 0.012,
    latency_ms: 5000,
    input_tokens: 800,
    output_tokens: 400,
    reasoning_trace: [
      {
        step_type: "thought",
        label: "Analisando perfil",
        score: null,
        matched: null,
        detail: "Verifico fit cultural e técnico",
        data_fields_accessed: ["nome", "experiencia"],
        timestamp: null,
      },
      {
        step_type: "criterion",
        label: "Skills Python",
        score: 0.91,
        matched: true,
        detail: null,
        data_fields_accessed: ["habilidades"],
        timestamp: null,
      },
    ],
    data_fields_accessed_summary: ["nome", "experiencia", "habilidades"],
    data_fields_NOT_accessed: ["cpf", "raca", "religiao", "genero", "estado_civil"],
  }
}

function renderWithProvider(ui: React.ReactNode) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

// ──────────────────────────────────────────────────────────────────────────
// Tests
// ──────────────────────────────────────────────────────────────────────────
describe("DecisionTreeDrawer — canonical Onda 1", () => {
  it("1) renderiza loading enquanto fetch está pendente", () => {
    global.fetch = vi.fn(() => new Promise(() => {})) as unknown as typeof fetch
    renderWithProvider(<DecisionTreeDrawer executionId="exec-1" onClose={() => {}} />)
    expect(screen.getByTestId("decision-tree-loading")).toBeTruthy()
  })

  it("2) mostra metadados (modelo, tokens, custo) após carregar", async () => {
    global.fetch = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => makeReasoning(),
    })) as unknown as typeof fetch

    renderWithProvider(<DecisionTreeDrawer executionId="exec-1" onClose={() => {}} />)
    await waitFor(() => {
      expect(screen.getByText("Catarina")).toBeTruthy()
    })
    expect(screen.getByText("claude-sonnet-4.7")).toBeTruthy()
    // tokens 800+400 = 1200 → 1.2k
    expect(screen.getByText("1.2k")).toBeTruthy()
    // custo 0.012 < 0.01? não → 3 decimals → $0.012
    expect(screen.getByText("$0.012")).toBeTruthy()
  })

  it("3) mostra legacy notice quando backend retorna 404", async () => {
    global.fetch = vi.fn(async () => ({
      ok: false,
      status: 404,
      json: async () => ({ detail: "no reasoning_payload" }),
    })) as unknown as typeof fetch

    renderWithProvider(<DecisionTreeDrawer executionId="exec-legacy" onClose={() => {}} />)
    await waitFor(() => {
      expect(screen.getByTestId("decision-tree-legacy")).toBeTruthy()
    })
  })

  it("4) expande detalhes técnicos e renderiza todos os steps", async () => {
    global.fetch = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => makeReasoning(),
    })) as unknown as typeof fetch

    renderWithProvider(<DecisionTreeDrawer executionId="exec-1" onClose={() => {}} />)
    await waitFor(() => {
      expect(screen.getByTestId("decision-tree-technical-toggle")).toBeTruthy()
    })
    const toggle = screen.getByTestId("decision-tree-technical-toggle")
    expect(toggle.getAttribute("aria-expanded")).toBe("false")
    fireEvent.click(toggle)
    await waitFor(() => {
      expect(toggle.getAttribute("aria-expanded")).toBe("true")
    })
    // Após expandir, a lista de steps deve existir no DOM. Radix Collapsible
    // remove `hidden` attribute quando open=true, mas no JSDOM o conteúdo já
    // está no DOM mesmo antes (CSS-only hide). Acessamos via testid + count.
    const list = screen.getByTestId("decision-tree-steps-list")
    expect(list.querySelectorAll("li").length).toBe(2)
  })

  it("5) export LGPD CSV gera Blob e dispara download", async () => {
    global.fetch = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => makeReasoning(),
    })) as unknown as typeof fetch

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

    renderWithProvider(<DecisionTreeDrawer executionId="exec-1" onClose={() => {}} />)
    await waitFor(() => {
      expect(screen.getByTestId("decision-tree-export-lgpd")).toBeTruthy()
    })
    fireEvent.click(screen.getByTestId("decision-tree-export-lgpd"))

    expect(createObjectURL).toHaveBeenCalledTimes(1)
    const blob = createObjectURL.mock.calls[0][0] as Blob
    expect(blob).toBeInstanceOf(Blob)
    expect(blob.type).toContain("text/csv")
  })
})
