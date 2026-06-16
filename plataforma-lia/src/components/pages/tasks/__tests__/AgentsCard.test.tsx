// Onda 2 F12 (2026-05-27) — AgentsCard canonical tests.
//
// Cobertura mínima:
//   1. Renderiza skeleton em loading.
//   2. Empty state quando items = [].
//   3. Renderiza linhas + clique abre DecisionTreeDrawer (onOpenDecisionTree callback).
//   4. Badge "9+" para pending_approvals_count > 9.
//   5. Mostra status e target label corretos.
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import { AgentsCard } from "../AgentsCard"
import type { ActiveSummaryResponse } from "@/types/agents/active-summary"
import ptBRMessages from "../../../../../messages/pt-BR.json"

vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({ persona: { name: "Catarina", tone: "profissional" } }),
}))

// i18n canonical (P1-5, 2026-05-29): copy migrada pra agents.summary.*.
// Em vez de mockar next-intl, renderizamos com o messages real (pt-BR) via
// NextIntlClientProvider — garante que toda key resolve (contract test).

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
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
    },
  })
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={ptBRMessages}>
      <QueryClientProvider client={client}>{ui}</QueryClientProvider>
    </NextIntlClientProvider>,
  )
}

function mockFetchOnce(body: ActiveSummaryResponse | { error: true }) {
  const isError = (body as { error?: boolean }).error === true
  global.fetch = vi.fn().mockResolvedValueOnce({
    ok: !isError,
    status: isError ? 500 : 200,
    json: () => Promise.resolve(body),
  }) as unknown as typeof fetch
}

const SAMPLE: ActiveSummaryResponse = {
  running_count: 3,
  items: [
    {
      agent_id: "a1",
      agent_name: "Catarina",
      agent_category: "screening",
      status: "running",
      target_type: "job",
      target_id: "job-1",
      target_name: "Dev Sênior Backend",
      last_action_label: "3 candidatos novos",
      last_execution_id: "exec-1",
      pending_approvals_count: 0,
      last_activity_at: "2026-05-27T12:00:00Z",
    },
    {
      agent_id: "a2",
      agent_name: "Pedro",
      agent_category: "sourcing",
      status: "running",
      target_type: "talent_pool",
      target_id: "pool-1",
      target_name: "SP Tech Pros",
      last_action_label: "pesquisando agora",
      last_execution_id: "exec-2",
      pending_approvals_count: 0,
      last_activity_at: "2026-05-27T12:01:00Z",
    },
    {
      agent_id: "a3",
      agent_name: "Ana",
      agent_category: "communication",
      status: "pending_approval",
      target_type: null,
      target_id: null,
      target_name: null,
      last_action_label: "3 mensagens prontas",
      last_execution_id: null,
      pending_approvals_count: 12,
      last_activity_at: "2026-05-27T12:02:00Z",
    },
  ],
}

describe("AgentsCard", () => {
  it("renderiza skeleton em loading", () => {
    global.fetch = vi.fn(() => new Promise(() => {})) as unknown as typeof fetch
    renderWithQuery(<AgentsCard onOpenDecisionTree={() => {}} />)
    expect(screen.getByTestId("agents-card-loading")).toBeInTheDocument()
  })

  it("mostra empty state quando items=[]", async () => {
    mockFetchOnce({ running_count: 0, items: [] })
    renderWithQuery(<AgentsCard onOpenDecisionTree={() => {}} />)
    await waitFor(() => {
      expect(screen.getByText(/Nenhum agente ativo/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/Conhecer agentes/i)).toBeInTheDocument()
  })

  it("renderiza lista e clique chama onOpenDecisionTree(executionId)", async () => {
    mockFetchOnce(SAMPLE)
    const onOpen = vi.fn()
    renderWithQuery(<AgentsCard onOpenDecisionTree={onOpen} />)
    await waitFor(() => {
      expect(screen.getByTestId("agents-card-list")).toBeInTheDocument()
    })
    // Click na primeira linha (Catarina, exec-1).
    const catarinaRow = screen.getByLabelText(/Catarina.*trabalhando/i)
    fireEvent.click(catarinaRow)
    expect(onOpen).toHaveBeenCalledWith("exec-1")
  })

  it("mostra badge 9+ para pending_approvals_count > 9", async () => {
    mockFetchOnce(SAMPLE)
    renderWithQuery(<AgentsCard onOpenDecisionTree={() => {}} />)
    await waitFor(() => {
      expect(screen.getByText("9+")).toBeInTheDocument()
    })
  })

  it("mostra target label canonical (Vaga / Pool)", async () => {
    mockFetchOnce(SAMPLE)
    renderWithQuery(<AgentsCard onOpenDecisionTree={() => {}} />)
    await waitFor(() => {
      expect(
        screen.getByText(/Vaga: Dev Sênior Backend/),
      ).toBeInTheDocument()
    })
    expect(screen.getByText(/Pool: SP Tech Pros/)).toBeInTheDocument()
  })
})

describe("AgentsCard — i18n canonical contract", () => {
  it("nao emite MISSING_MESSAGE com messages/pt-BR.json real", async () => {
    const errors: Error[] = []
    mockFetchOnce(SAMPLE)
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: 0 } },
    })
    render(
      <NextIntlClientProvider
        locale="pt-BR"
        messages={ptBRMessages}
        onError={(err) => errors.push(err)}
      >
        <QueryClientProvider client={client}>
          <AgentsCard onOpenDecisionTree={() => {}} />
        </QueryClientProvider>
      </NextIntlClientProvider>,
    )
    await waitFor(() => {
      expect(screen.getByTestId("agents-card-list")).toBeInTheDocument()
    })
    const missing = errors.filter((e) =>
      e.message.includes("MISSING_MESSAGE"),
    )
    expect(missing).toEqual([])
  })
})
