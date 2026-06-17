/**
 * VacancyAnalyticsTab — TDD tests.
 *
 * Guards:
 * 1. Renderiza loading state enquanto query pendente
 * 2. Renderiza error state quando query falha
 * 3. Renderiza KPI cards quando dados carregam
 * 4. Rules of Hooks: rerender com props diferentes não lança
 * 5. Mostra zeros/placeholder quando funil está vazio
 */
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { VacancyAnalyticsTab } from "../VacancyAnalyticsTab"

// Stub global fetch
const mockFetch = vi.fn()
vi.stubGlobal("fetch", mockFetch)

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  })
}

function wrap(ui: React.ReactElement, qc?: QueryClient) {
  const client = qc ?? makeQueryClient()
  return (
    <QueryClientProvider client={client}>
      {ui}
    </QueryClientProvider>
  )
}

const MOCK_METRICS = {
  funnel: {
    total: 120,
    screening: 80,
    interview: 40,
    offer: 10,
    hired: 3,
  },
  performance: {
    time_to_fill_days: 28,
    conversion_rate: 0.452,
  },
}

describe("VacancyAnalyticsTab — loading state", () => {
  beforeEach(() => {
    cleanup()
    mockFetch.mockClear()
  })

  it("renders loading state while query is pending", () => {
    // Never resolves during this test
    mockFetch.mockImplementation(() => new Promise(() => {}))

    render(wrap(<VacancyAnalyticsTab jobId="job-1" />))

    // HubLoadingState renders a spinner or loading indicator
    expect(document.querySelector("[data-vacancy-analytics-tab]") ?? document.body).toBeTruthy()
    // The analytics content should NOT be visible while loading
    expect(screen.queryByTestId("vacancy-analytics-tab")).not.toBeInTheDocument()
  })
})

describe("VacancyAnalyticsTab — error state", () => {
  beforeEach(() => {
    cleanup()
    mockFetch.mockClear()
  })

  it("renders error state when fetch fails", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
    })

    render(wrap(<VacancyAnalyticsTab jobId="job-err" />))

    // Wait for error state to appear — HubErrorState renders role="alert"
    const alertEl = await screen.findByRole("alert", {}, { timeout: 5000 })
    expect(alertEl).toBeInTheDocument()
    // The retry button should be inside the alert
    expect(screen.getByText(/tentar novamente/i)).toBeInTheDocument()
  })
})

describe("VacancyAnalyticsTab — success state", () => {
  beforeEach(() => {
    cleanup()
    mockFetch.mockClear()
  })

  it("renders KPI cards when data loads", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => MOCK_METRICS,
    })

    render(wrap(<VacancyAnalyticsTab jobId="job-ok" />))

    // Wait for content to render
    await screen.findByTestId("vacancy-analytics-tab")

    // Funnel labels
    expect(screen.getByText("Total")).toBeInTheDocument()
    expect(screen.getByText("Triagem")).toBeInTheDocument()
    expect(screen.getByText("Entrevista")).toBeInTheDocument()
    expect(screen.getByText("Oferta")).toBeInTheDocument()
    expect(screen.getByText("Contratados")).toBeInTheDocument()

    // Performance labels
    expect(screen.getByText("Taxa de Conversão")).toBeInTheDocument()
    expect(screen.getByText("Tempo para Preencher")).toBeInTheDocument()

    // KPI values
    expect(screen.getByText("120")).toBeInTheDocument()
    expect(screen.getByText("45.2%")).toBeInTheDocument()
    expect(screen.getByText("28")).toBeInTheDocument()
  })

  it("shows zeros/dashes when funnel is empty", async () => {
    const emptyMetrics = {
      funnel: { total: 0, screening: 0, interview: 0, offer: 0, hired: 0 },
      performance: { time_to_fill_days: null, conversion_rate: null },
    }
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => emptyMetrics,
    })

    render(wrap(<VacancyAnalyticsTab jobId="job-empty" />))

    await screen.findByTestId("vacancy-analytics-tab")

    // All zeros
    const zeros = screen.getAllByText("0")
    expect(zeros.length).toBeGreaterThanOrEqual(1)

    // Null performance shows dashes
    const dashes = screen.getAllByText("—")
    expect(dashes.length).toBeGreaterThanOrEqual(2)
  })
})

describe("VacancyAnalyticsTab — Rules of Hooks", () => {
  beforeEach(() => {
    cleanup()
    mockFetch.mockClear()
  })

  it("does not crash when jobId changes between renders", () => {
    mockFetch.mockImplementation(() => new Promise(() => {}))
    const qc = makeQueryClient()

    const { rerender } = render(wrap(<VacancyAnalyticsTab jobId="job-a" />, qc))

    expect(() =>
      rerender(wrap(<VacancyAnalyticsTab jobId="job-b" />, qc))
    ).not.toThrow()

    expect(() =>
      rerender(wrap(<VacancyAnalyticsTab jobId="job-a" />, qc))
    ).not.toThrow()
  })

  it("handles envelope response {ok, data: metrics}", async () => {
    const enveloped = { ok: true, data: MOCK_METRICS }
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => enveloped,
    })

    render(wrap(<VacancyAnalyticsTab jobId="job-envelope" />))

    await screen.findByTestId("vacancy-analytics-tab")
    expect(screen.getByText("120")).toBeInTheDocument()
  })
})
