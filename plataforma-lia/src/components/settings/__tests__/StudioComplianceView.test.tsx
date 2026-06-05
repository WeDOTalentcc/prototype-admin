/**
 * Task #1314 — StudioComplianceView sobrevive a dados quebrados ou vazios.
 *
 * Task #1313 corrigiu um white-screen onde a aba Studio Compliance derrubava
 * toda a página de Configurações quando o backend devolvia payload parcial
 * (sem `trend` / `top_blocked_agents`), vazio (`total_executions: 0`) ou erro
 * (timeout / 502 / 504). O render agora é blindado com o padrão canônico
 * `?? []` / `?? 0`. Estes testes travam esse comportamento — um refactor que
 * reintroduza o deref cru de `.length` quebra a build aqui antes de chegar ao
 * usuário.
 */
import React from "react"
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import "@testing-library/jest-dom/vitest"

vi.mock("next-intl", () => {
  const tFn = (k: string) => k
  return { useTranslations: () => tFn }
})

const apiFetchMock = vi.fn()
vi.mock("@/lib/api/api-fetch", () => ({
  apiFetch: (...args: unknown[]) => apiFetchMock(...args),
}))

import { StudioComplianceView } from "@/components/settings/StudioComplianceView"

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const FULL_PAYLOAD = {
  period_days: 30,
  total_executions: 120,
  blocked_executions: 8,
  block_rate_pct: 6.67,
  avg_confidence: 0.91,
  active_agents: 4,
  by_status: { approved: 112, blocked: 8 },
  top_blocked_agents: [
    { agent_id: "a1", agent_name: "Sourcing Bot", blocked_count: 5 },
    { agent_id: "a2", agent_name: "Screening Bot", blocked_count: 3 },
  ],
  trend: [
    { day: "2026-06-01", executions: 40, blocked: 2 },
    { day: "2026-06-02", executions: 80, blocked: 6 },
  ],
}

const EMPTY_PAYLOAD = {
  period_days: 30,
  total_executions: 0,
  blocked_executions: 0,
  block_rate_pct: 0,
  avg_confidence: 0,
  active_agents: 0,
  by_status: {},
  top_blocked_agents: [],
  trend: [],
}

// Causa raiz do white-screen: backend devolve payload parcial SEM `trend` e
// SEM `top_blocked_agents`. O render antigo fazia `.length` direto nesses
// campos `undefined` e estourava.
const PARTIAL_PAYLOAD = {
  period_days: 30,
  total_executions: 50,
  blocked_executions: 4,
  block_rate_pct: 8,
  avg_confidence: 0.8,
  active_agents: 2,
}

describe("StudioComplianceView — Task #1314 (resiliência a dados quebrados)", () => {
  beforeEach(() => {
    apiFetchMock.mockReset()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("(a) payload completo: renderiza KPIs, gráfico e top blocked agents", async () => {
    apiFetchMock.mockResolvedValue(jsonResponse(FULL_PAYLOAD))

    render(<StudioComplianceView />)

    await waitFor(() => {
      expect(screen.getByTestId("studio-compliance-view")).toBeInTheDocument()
    })

    // KPI de execuções totais aparece; não há empty-state.
    expect(screen.getByText("120")).toBeInTheDocument()
    expect(screen.getByText("topBlockedAgents")).toBeInTheDocument()
    expect(screen.queryByText("noExecutions")).not.toBeInTheDocument()
  })

  it("(b) payload vazio (total_executions: 0): renderiza empty-state sem estourar", async () => {
    apiFetchMock.mockResolvedValue(jsonResponse(EMPTY_PAYLOAD))

    render(<StudioComplianceView />)

    await waitFor(() => {
      expect(screen.getByTestId("studio-compliance-view")).toBeInTheDocument()
    })

    // Empty-state visível; gráfico e lista de bloqueados suprimidos.
    expect(screen.getByText("noExecutions")).toBeInTheDocument()
    expect(screen.queryByText("topBlockedAgents")).not.toBeInTheDocument()
    expect(screen.queryByText("executionsByDay")).not.toBeInTheDocument()
  })

  it("(c) payload parcial (sem trend nem top_blocked_agents): não white-screena", async () => {
    apiFetchMock.mockResolvedValue(jsonResponse(PARTIAL_PAYLOAD))

    // Se o guard `?? []` regredir para `.length` cru, este render lança e o
    // teste falha — exatamente a regressão que estamos travando.
    render(<StudioComplianceView />)

    await waitFor(() => {
      expect(screen.getByTestId("studio-compliance-view")).toBeInTheDocument()
    })

    // KPIs derivados renderizam mesmo com campos de array ausentes.
    expect(screen.getByText("50")).toBeInTheDocument()
    // Sem trend nem top_blocked_agents, esses cards não aparecem.
    expect(screen.queryByText("executionsByDay")).not.toBeInTheDocument()
    expect(screen.queryByText("topBlockedAgents")).not.toBeInTheDocument()
    // total_executions > 0 → não mostra empty-state.
    expect(screen.queryByText("noExecutions")).not.toBeInTheDocument()
  })

  it("(c') payload completamente vazio ({}): sobrevive com todos os fallbacks", async () => {
    apiFetchMock.mockResolvedValue(jsonResponse({}))

    render(<StudioComplianceView />)

    await waitFor(() => {
      expect(screen.getByTestId("studio-compliance-view")).toBeInTheDocument()
    })

    // total_executions ?? 0 === 0 → empty-state, sem throw.
    expect(screen.getByText("noExecutions")).toBeInTheDocument()
  })

  it("backend erro (502/504): renderiza error-state, não derruba a página", async () => {
    apiFetchMock.mockResolvedValue(
      jsonResponse({ error: "Backend timeout" }, 504),
    )

    render(<StudioComplianceView />)

    await waitFor(() => {
      expect(screen.getByText("loadError")).toBeInTheDocument()
    })

    expect(screen.queryByTestId("studio-compliance-view")).not.toBeInTheDocument()
  })
})
