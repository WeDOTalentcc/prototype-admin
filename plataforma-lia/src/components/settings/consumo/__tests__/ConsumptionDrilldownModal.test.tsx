// Onda 4 F8 (2026-05-28) — ConsumptionDrilldownModal canonical tests.
//
// Cobertura:
//   1. Open + render table com items
//   2. Empty state quando lista vazia
//   3. Pagination Anterior/Próximo
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import React from "react"

import { ConsumptionDrilldownModal } from "../ConsumptionDrilldownModal"

const MESSAGES = {
  settings: {
    consumption: {
      drilldown: {
        title: "Execuções de {agentType}",
        subtitle: "{total} execuções no período",
        column: {
          timestamp: "Quando",
          operation: "Operação",
          candidate: "Candidato",
          cost: "Custo",
          tokens: "Tokens",
        },
        empty: "Nenhuma execução encontrada",
        error: "Erro",
        pagination: {
          page: "Página {page} de {total}",
          prev: "Anterior",
          next: "Próxima",
        },
      },
    },
  },
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

function mockFetchDrilldown(items: unknown[], total: number = items.length) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () =>
      Promise.resolve({
        items,
        total_count: total,
        total_cost_cents: 0,
        total_tokens: 0,
      }),
  }) as unknown as typeof fetch
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

describe("ConsumptionDrilldownModal", () => {
  it("renderiza tabela com items", async () => {
    mockFetchDrilldown([
      {
        consumption_id: "c1",
        agent_type: "cv_screening",
        studio_agent_id: null,
        operation: "evaluate",
        model: "gpt-4o",
        input_tokens: 100,
        output_tokens: 50,
        total_tokens: 150,
        cost_cents: 5,
        candidate_id: "cand-12345678",
        vacancy_id: null,
        created_at: "2026-05-28T12:00:00Z",
      },
    ])
    const Wrapper = makeWrapper()
    render(
      <Wrapper>
        <ConsumptionDrilldownModal
          agentType="cv_screening"
          open={true}
          onOpenChange={vi.fn()}
        />
      </Wrapper>,
    )
    await waitFor(() => {
      expect(screen.getByTestId("drilldown-table")).toBeInTheDocument()
    })
    expect(screen.getByText("evaluate")).toBeInTheDocument()
  })

  it("renderiza empty state quando items vazio", async () => {
    mockFetchDrilldown([], 0)
    const Wrapper = makeWrapper()
    render(
      <Wrapper>
        <ConsumptionDrilldownModal
          agentType="cv_screening"
          open={true}
          onOpenChange={vi.fn()}
        />
      </Wrapper>,
    )
    await waitFor(() => {
      expect(screen.getByTestId("drilldown-empty")).toBeInTheDocument()
    })
  })

  it("paginação aparece quando total > 25", async () => {
    const items = Array.from({ length: 25 }, (_, i) => ({
      consumption_id: `c${i}`,
      agent_type: "cv_screening",
      studio_agent_id: null,
      operation: "evaluate",
      model: "gpt-4o",
      input_tokens: 100,
      output_tokens: 50,
      total_tokens: 150,
      cost_cents: 5,
      candidate_id: null,
      vacancy_id: null,
      created_at: "2026-05-28T12:00:00Z",
    }))
    mockFetchDrilldown(items, 100)
    const Wrapper = makeWrapper()
    render(
      <Wrapper>
        <ConsumptionDrilldownModal
          agentType="cv_screening"
          open={true}
          onOpenChange={vi.fn()}
        />
      </Wrapper>,
    )
    await waitFor(() => {
      expect(screen.getByTestId("drilldown-table")).toBeInTheDocument()
    })
    expect(screen.getByRole("button", { name: /próxima/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /anterior/i })).toBeInTheDocument()
  })
})
