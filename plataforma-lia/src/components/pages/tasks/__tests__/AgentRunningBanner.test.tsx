// Onda 2 F12 (2026-05-27) — AgentRunningBanner canonical tests.
//
// Cobertura:
//   1. Aparece quando running_count > 0.
//   2. Esconde quando running_count = 0.
//   3. Singular/plural correto.
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AgentRunningBanner } from "../AgentRunningBanner"
import type { ActiveSummaryResponse } from "@/types/agents/active-summary"

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

function mockFetchOnce(body: ActiveSummaryResponse) {
  global.fetch = vi.fn().mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  }) as unknown as typeof fetch
}

describe("AgentRunningBanner", () => {
  it("aparece quando running_count > 0", async () => {
    mockFetchOnce({ running_count: 3, items: [] })
    renderWithQuery(<AgentRunningBanner />)
    await waitFor(() => {
      expect(screen.getByText(/3 agentes trabalhando agora/)).toBeInTheDocument()
    })
    expect(screen.getByText(/Ver na Sala de Controle/)).toBeInTheDocument()
  })

  it("esconde quando running_count = 0", async () => {
    mockFetchOnce({ running_count: 0, items: [] })
    const { container } = renderWithQuery(<AgentRunningBanner />)
    await waitFor(() => {
      // Esperamos que o fetch resolva, depois o container fica vazio.
      expect(container.firstChild).toBeNull()
    })
  })

  it("usa singular para 1 agente", async () => {
    mockFetchOnce({ running_count: 1, items: [] })
    renderWithQuery(<AgentRunningBanner />)
    await waitFor(() => {
      expect(screen.getByText(/1 agente trabalhando agora/)).toBeInTheDocument()
    })
  })
})
