// Onda 4 F8 (2026-05-28) — AgentKpisClient canonical tests.
//
// Cobertura:
//   1. Loading state renderiza skeleton
//   2. Period selector troca period (queryKey muda)
//   3. is_learning badge aparece quando flag true
//   4. Heatmap renderiza 24 bars
//   5. Empty state quando total_executions = 0
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import React from "react"

import AgentKpisClient from "../AgentKpisClient"

// Mock next/navigation (App Router)
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/pt/agent-studio/abc/kpis",
}))

// Mock useAiPersona
vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({ persona: { name: "LIA", tone: "profissional" } }),
}))

const MESSAGES = {
  agents: {
    studio: {
      kpis: {
        title: "Métricas do agente",
        period: {
          "7d": "Últimos 7 dias",
          "30d": "Últimos 30 dias",
          "90d": "Últimos 90 dias",
          all: "Todos",
        },
        cards: {
          candidatesProcessed: "Candidatos processados",
          executions: "{count} execuções",
          avgTime: "Tempo médio",
          p95: "p95: {value}",
          approved: "Aprovados",
          approvedPct: "{pct}%",
          rejected: "Rejeitados",
          rejectedPct: "{pct}%",
          totalCost: "Custo total",
          tokens: "{value} tokens",
        },
        heatmap: {
          title: "Atividade por hora do dia",
          ariaLabel: "Distribuição",
        },
        tools: { title: "Uso por ferramenta", successRate: "{rate}% sucesso" },
        empty: {
          title: "KPIs em breve",
          description: "Este agente ainda não foi executado.",
        },
        error: { title: "Não foi possível carregar" },
        learning: {
          badge: "🩵 aprendendo",
          tooltip: "Agente com menos de 5 execuções.",
        },
        viewConsumption: "Ver consumo financeiro deste agente",
        a11y: { summary: "{personaName} reportando KPIs" },
      },
    },
  },
}

function makeKpiResponse(overrides: Record<string, unknown> = {}) {
  const heatmap = Array.from({ length: 24 }, (_, h) => ({
    hour_of_day: h,
    executions_count: h % 4 === 0 ? 5 : 1,
  }))
  return {
    agent_id: "abc-123",
    agent_name: "Catarina",
    agent_category: "screening",
    period: "30d",
    bucket: {
      period: "30d",
      candidates_processed: 247,
      candidates_approved: 152,
      candidates_rejected: 85,
      candidates_pending: 10,
      avg_execution_seconds: 3.4,
      p95_execution_seconds: 5.8,
      total_executions: 247,
      error_count: 0,
      total_cost_usd: 4.23,
      total_tokens_input: 800_000,
      total_tokens_output: 400_000,
    },
    hour_heatmap: heatmap,
    tool_breakdown: [
      { tool_name: "evaluate", count: 89, success_rate: 0.88 },
    ],
    last_run_at: "2026-05-28T12:00:00Z",
    is_learning: false,
    ...overrides,
  }
}

function makeWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <NextIntlClientProvider locale="pt-BR" messages={MESSAGES}>
        <QueryClientProvider client={client}>{children}</QueryClientProvider>
      </NextIntlClientProvider>
    )
  }
}

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

describe("AgentKpisClient", () => {
  it("renderiza loading skeleton inicialmente", () => {
    global.fetch = vi
      .fn()
      .mockReturnValue(new Promise(() => {})) as unknown as typeof fetch
    const Wrapper = makeWrapper()
    render(
      <Wrapper>
        <AgentKpisClient agentId="abc-123" />
      </Wrapper>,
    )
    expect(screen.getByTestId("agent-kpis-loading")).toBeInTheDocument()
  })

  it("renderiza badge is_learning quando flag true", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(makeKpiResponse({ is_learning: true })),
    }) as unknown as typeof fetch
    const Wrapper = makeWrapper()
    render(
      <Wrapper>
        <AgentKpisClient agentId="abc-123" />
      </Wrapper>,
    )
    await waitFor(() => {
      expect(
        screen.getByTestId("agent-kpis-content"),
      ).toBeInTheDocument()
    })
    expect(screen.getByText(/aprendendo/i)).toBeInTheDocument()
  })

  it("renderiza heatmap com role=img", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(makeKpiResponse()),
    }) as unknown as typeof fetch
    const Wrapper = makeWrapper()
    render(
      <Wrapper>
        <AgentKpisClient agentId="abc-123" />
      </Wrapper>,
    )
    await waitFor(() => {
      expect(screen.getByTestId("kpi-heatmap")).toBeInTheDocument()
    })
    expect(screen.getByTestId("kpi-heatmap")).toHaveAttribute(
      "role",
      "img",
    )
  })

  it("empty state quando total_executions = 0", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve(
          makeKpiResponse({
            bucket: {
              period: "30d",
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
            is_learning: true,
          }),
        ),
    }) as unknown as typeof fetch
    const Wrapper = makeWrapper()
    render(
      <Wrapper>
        <AgentKpisClient agentId="abc-123" />
      </Wrapper>,
    )
    await waitFor(() => {
      expect(screen.getByTestId("agent-kpis-empty")).toBeInTheDocument()
    })
    expect(screen.getByText(/KPIs em breve/i)).toBeInTheDocument()
  })

  it("period selector tem 4 botões e troca seleção", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(makeKpiResponse()),
    }) as unknown as typeof fetch
    const Wrapper = makeWrapper()
    const user = userEvent.setup()
    render(
      <Wrapper>
        <AgentKpisClient agentId="abc-123" />
      </Wrapper>,
    )
    await waitFor(() => {
      expect(
        screen.getByTestId("agent-kpis-content"),
      ).toBeInTheDocument()
    })
    const tablist = screen.getByRole("tablist", { name: /period/i })
    const tabs = within(tablist).getAllByRole("tab")
    expect(tabs).toHaveLength(4)
    await user.click(tabs[2]) // "90d"
    // Refetch deve ter sido disparado
    await waitFor(() => {
      const calls = (global.fetch as unknown as { mock: { calls: unknown[][] } })
        .mock.calls
      const lastUrl = String(calls[calls.length - 1][0])
      expect(lastUrl).toContain("period=90d")
    })
  })
})
