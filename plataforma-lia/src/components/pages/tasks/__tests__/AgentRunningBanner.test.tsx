// Onda 2 F12 (2026-05-27) — AgentRunningBanner canonical tests.
//
// Cobertura:
//   1. Aparece quando running_count > 0.
//   2. Esconde quando running_count = 0.
//   3. Singular/plural correto.
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import { AgentRunningBanner } from "../AgentRunningBanner"
import type { ActiveSummaryResponse } from "@/types/agents/active-summary"
import ptBRMessages from "../../../../../messages/pt-BR.json"

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
    <NextIntlClientProvider locale="pt-BR" messages={ptBRMessages}>
      <QueryClientProvider client={client}>{ui}</QueryClientProvider>
    </NextIntlClientProvider>,
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

  it("i18n canonical contract — sem MISSING_MESSAGE (pt-BR real)", async () => {
    const errors: Error[] = []
    mockFetchOnce({ running_count: 3, items: [] })
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
          <AgentRunningBanner />
        </QueryClientProvider>
      </NextIntlClientProvider>,
    )
    await waitFor(() => {
      expect(
        screen.getByText(/3 agentes trabalhando agora/),
      ).toBeInTheDocument()
    })
    expect(
      errors.filter((e) => e.message.includes("MISSING_MESSAGE")),
    ).toEqual([])
  })
})
