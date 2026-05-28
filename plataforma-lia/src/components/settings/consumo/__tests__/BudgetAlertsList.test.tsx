// Onda 4 F8 (2026-05-28) — BudgetAlertsList canonical tests.
//
// Cobertura:
//   1. Severity info renderiza com style azul
//   2. Severity warning renderiza com style amber
//   3. Severity critical renderiza com style red
//   4. projected_to_exceed text aparece
//   5. Sem alerts → não renderiza nada
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import React from "react"

import { BudgetAlertsList } from "../BudgetAlertsList"

const MESSAGES = {
  settings: {
    consumption: {
      budgetAlerts: {
        title: "Alertas",
        info: { global: "Você consumiu {pct}% do orçamento mensal" },
        warning: { global: "Atenção: você consumiu {pct}% do orçamento mensal" },
        critical: { global: "Crítico: você consumiu {pct}% do orçamento mensal" },
        projected: "Projeção: ultrapassará o limite em ~{days} dias",
        perAgent: "Agente {agentName} consumiu {pct}% do orçamento global",
        viewExecutions: "Ver execuções deste agente",
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

function mockFetchAlerts(alerts: unknown[]) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () =>
      Promise.resolve({
        alerts,
        period_start: "2026-05-01",
        period_end: "2026-05-31",
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

describe("BudgetAlertsList", () => {
  it("não renderiza quando alerts vazio", async () => {
    mockFetchAlerts([])
    const Wrapper = makeWrapper()
    const { container } = render(
      <Wrapper>
        <BudgetAlertsList />
      </Wrapper>,
    )
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
    })
    expect(
      container.querySelector("[data-testid='budget-alerts-list']"),
    ).toBeNull()
  })

  it("renderiza alert info global", async () => {
    mockFetchAlerts([
      {
        severity: "info",
        scope: "global",
        studio_agent_id: null,
        agent_name: null,
        used_pct: 0.6,
        used_cents: 6_000,
        limit_cents: 10_000,
        days_in_period: 31,
        days_remaining: 15,
        projected_to_exceed: false,
      },
    ])
    const Wrapper = makeWrapper()
    render(
      <Wrapper>
        <BudgetAlertsList />
      </Wrapper>,
    )
    await waitFor(() => {
      expect(screen.getByTestId("budget-alerts-list")).toBeInTheDocument()
    })
    expect(screen.getByTestId("budget-alert-info")).toBeInTheDocument()
    expect(screen.getByText(/60%/i)).toBeInTheDocument()
  })

  it("renderiza alert critical com projected_to_exceed", async () => {
    mockFetchAlerts([
      {
        severity: "critical",
        scope: "global",
        studio_agent_id: null,
        agent_name: null,
        used_pct: 0.97,
        used_cents: 9_700,
        limit_cents: 10_000,
        days_in_period: 31,
        days_remaining: 3,
        projected_to_exceed: true,
      },
    ])
    const Wrapper = makeWrapper()
    render(
      <Wrapper>
        <BudgetAlertsList />
      </Wrapper>,
    )
    await waitFor(() => {
      expect(screen.getByTestId("budget-alert-critical")).toBeInTheDocument()
    })
    expect(screen.getByText(/Projeção: ultrapassará/i)).toBeInTheDocument()
  })

  it("renderiza alert per-agent com viewExecutions button", async () => {
    const onView = vi.fn()
    mockFetchAlerts([
      {
        severity: "warning",
        scope: "agent",
        studio_agent_id: "agent-123",
        agent_name: "Catarina",
        used_pct: 0.32,
        used_cents: 3_200,
        limit_cents: 10_000,
        days_in_period: 31,
        days_remaining: 12,
        projected_to_exceed: false,
      },
    ])
    const Wrapper = makeWrapper()
    render(
      <Wrapper>
        <BudgetAlertsList onViewExecutions={onView} />
      </Wrapper>,
    )
    await waitFor(() => {
      expect(screen.getByTestId("budget-alert-warning")).toBeInTheDocument()
    })
    expect(screen.getByText(/Catarina/)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /execuções/i })).toBeInTheDocument()
  })
})
