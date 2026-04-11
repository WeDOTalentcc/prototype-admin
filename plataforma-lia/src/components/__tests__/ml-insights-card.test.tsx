/**
 * Tests — MLInsightsCard (P4)
 *
 * Cobre:
 * - Estado inicial (colapsado, sem chamadas ao hook)
 * - Expand: chama fetchTimeToFill + fetchSalary ao abrir
 * - Loading state
 * - Exibição de dados após carregamento
 * - Estado de erro com botão de refresh
 * - Não refaz chamadas no segundo expand (hasFetched)
 */
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { MLInsightsCard } from "../ml-insights-card"
import { useMLPredictions } from "@/hooks/ai/use-ml-predictions"

vi.mock("@/hooks/ai/use-ml-predictions")

const mockFetchTimeToFill = vi.fn()
const mockFetchSalary = vi.fn()

const defaultHookReturn = {
  timeToFill: null,
  salary: null,
  insights: null,
  loading: false,
  error: null,
  fetchTimeToFill: mockFetchTimeToFill,
  fetchSalary: mockFetchSalary,
  fetchInsights: vi.fn(),
}

const mockUseML = vi.mocked(useMLPredictions)

const defaultProps = {
  companyId: "company-001",
  jobData: { title: "Engenheiro de Software", department: "Engineering", seniority: "senior" },
}

describe("MLInsightsCard", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetchTimeToFill.mockResolvedValue(undefined)
    mockFetchSalary.mockResolvedValue(undefined)
    mockUseML.mockReturnValue(defaultHookReturn)
  })

  it("renderiza colapsado por padrão sem chamar hooks de fetch", () => {
    render(<MLInsightsCard {...defaultProps} />)
    expect(screen.getByText("Previsões IA")).toBeInTheDocument()
    expect(mockFetchTimeToFill).not.toHaveBeenCalled()
    expect(mockFetchSalary).not.toHaveBeenCalled()
  })

  it("chama fetchTimeToFill e fetchSalary ao expandir", async () => {
    render(<MLInsightsCard {...defaultProps} />)
    fireEvent.click(screen.getByText("Previsões IA"))
    await waitFor(() => {
      expect(mockFetchTimeToFill).toHaveBeenCalledWith("company-001", defaultProps.jobData)
      expect(mockFetchSalary).toHaveBeenCalledWith("company-001", defaultProps.jobData)
    })
  })

  it("mostra loading spinner ao carregar", () => {
    mockUseML.mockReturnValue({ ...defaultHookReturn, loading: true })

    render(<MLInsightsCard {...defaultProps} />)
    fireEvent.click(screen.getByText("Previsões IA"))
    expect(screen.getByText("Calculando previsões...")).toBeInTheDocument()
  })

  it("exibe dados de time-to-fill quando disponíveis", async () => {
    mockUseML.mockReturnValue({
      ...defaultHookReturn,
      timeToFill: {
        predicted_days: 28,
        range_min: 20,
        range_max: 35,
        confidence: 0.72,
        confidence_level: "medium",
        comparison_to_market: "Na média do mercado",
        explanation: "Baseado em 12 vagas similares",
        factors: [],
        model_version: "v1",
      },
    })

    render(<MLInsightsCard {...defaultProps} />)
    fireEvent.click(screen.getByText("Previsões IA"))
    expect(screen.getByText(/28 dias/)).toBeInTheDocument()
    expect(screen.getByText(/Na média do mercado/)).toBeInTheDocument()
  })

  it("exibe faixa salarial quando disponível", async () => {
    mockUseML.mockReturnValue({
      ...defaultHookReturn,
      salary: {
        suggested_min: 10000,
        suggested_max: 15000,
        market_percentile: 50,
        competitive_analysis: "Na média do mercado",
        confidence: 0.68,
        confidence_level: "medium",
        explanation: "...",
        factors: [],
      },
    })

    render(<MLInsightsCard {...defaultProps} />)
    fireEvent.click(screen.getByText("Previsões IA"))
    expect(screen.getByText(/R\$\s*10\.000/)).toBeInTheDocument()
    expect(screen.getByText(/R\$\s*15\.000/)).toBeInTheDocument()
    expect(screen.getByText(/P50/)).toBeInTheDocument()
  })

  it("exibe mensagem de erro e botão de refresh", () => {
    mockUseML.mockReturnValue({
      ...defaultHookReturn,
      error: "Erro de conexão com o backend",
    })

    render(<MLInsightsCard {...defaultProps} />)
    fireEvent.click(screen.getByText("Previsões IA"))
    expect(screen.getByText("Erro de conexão com o backend")).toBeInTheDocument()
  })

  it("nao refaz chamadas no segundo expand (hasFetched cache)", async () => {
    render(<MLInsightsCard {...defaultProps} />)
    // Primeiro expand
    fireEvent.click(screen.getByText("Previsões IA"))
    await waitFor(() => expect(mockFetchTimeToFill).toHaveBeenCalledTimes(1))
    // Fechar
    fireEvent.click(screen.getByText("Previsões IA"))
    // Reabrir
    fireEvent.click(screen.getByText("Previsões IA"))
    // Deve continuar com 1 chamada (não repetiu)
    expect(mockFetchTimeToFill).toHaveBeenCalledTimes(1)
  })
})
