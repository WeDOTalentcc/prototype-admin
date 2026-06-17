import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor, fireEvent } from "@testing-library/react"
import { WizardSuggestionChips } from "../WizardSuggestionChips"

// Mock fetch para controlar o que o endpoint retorna
const mockFetch = vi.fn()
global.fetch = mockFetch

function suggestionsResponse(entries: Record<string, { value: unknown; source: string; confidence: number; explanation: string }>) {
  return {
    ok: true,
    json: async () => ({
      suggestions: entries,
      fields_with_suggestions: Object.keys(entries),
      fields_without_suggestions: [],
    }),
  }
}

describe("WizardSuggestionChips", () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  it("não renderiza quando title e department estão ausentes", async () => {
    const { container } = render(
      <WizardSuggestionChips data={{}} onUpdate={vi.fn()} />
    )
    // fetch nunca deve ser chamado sem contexto
    expect(mockFetch).not.toHaveBeenCalled()
    expect(container.querySelector("[data-testid='wizard-suggestion-chips']")).toBeNull()
  })

  it("não renderiza quando API retorna sugestões abaixo do threshold de confiança", async () => {
    mockFetch.mockResolvedValueOnce(
      suggestionsResponse({
        seniority: { value: "Pleno", source: "lia_history", confidence: 0.4, explanation: "Baixa confiança" },
      })
    )
    render(
      <WizardSuggestionChips
        data={{ parsed_title: "Desenvolvedor Backend" }}
        onUpdate={vi.fn()}
      />
    )
    await waitFor(() => expect(mockFetch).toHaveBeenCalled())
    expect(screen.queryByTestId("wizard-suggestion-chips")).toBeNull()
  })

  it("não renderiza chip para campo já preenchido", async () => {
    mockFetch.mockResolvedValueOnce(
      suggestionsResponse({
        seniority: { value: "Pleno", source: "lia_history", confidence: 0.85, explanation: "Histórico" },
      })
    )
    render(
      <WizardSuggestionChips
        data={{ parsed_title: "Dev Backend", seniority: "Senior" }}  // seniority já preenchido
        onUpdate={vi.fn()}
      />
    )
    await waitFor(() => expect(mockFetch).toHaveBeenCalled())
    expect(screen.queryByTestId("suggestion-chip-seniority")).toBeNull()
  })

  it("renderiza chip com confiança >= 0.6 para campo vazio", async () => {
    mockFetch.mockResolvedValueOnce(
      suggestionsResponse({
        seniority: { value: "Pleno", source: "lia_history", confidence: 0.85, explanation: "Baseado em 5 vagas similares" },
      })
    )
    render(
      <WizardSuggestionChips
        data={{ parsed_title: "Desenvolvedor Backend" }}
        onUpdate={vi.fn()}
      />
    )
    await waitFor(() => screen.getByTestId("suggestion-chip-seniority"))
    expect(screen.getByTestId("suggestion-chip-seniority")).toBeDefined()
    expect(screen.getByText("Pleno")).toBeDefined()
  })

  it("ao clicar no chip chama onUpdate com o valor e descarta o chip", async () => {
    const onUpdate = vi.fn()
    mockFetch.mockResolvedValueOnce(
      suggestionsResponse({
        work_model: { value: "Remoto", source: "company_settings", confidence: 0.9, explanation: "Padrão da empresa" },
      })
    )
    render(
      <WizardSuggestionChips
        data={{ parsed_title: "Dev Backend" }}
        onUpdate={onUpdate}
      />
    )
    await waitFor(() => screen.getByTestId("suggestion-chip-work_model"))
    fireEvent.click(screen.getByTestId("suggestion-chip-work_model"))

    expect(onUpdate).toHaveBeenCalledWith({ work_model: "Remoto" })
    // após clicar, o chip some
    expect(screen.queryByTestId("suggestion-chip-work_model")).toBeNull()
  })

  it("falha silenciosa quando fetch lança erro (fail-open)", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"))
    const { container } = render(
      <WizardSuggestionChips
        data={{ parsed_title: "Dev Backend" }}
        onUpdate={vi.fn()}
      />
    )
    await waitFor(() => expect(mockFetch).toHaveBeenCalled())
    // sem chips = nada renderizado, sem crash
    expect(container.querySelector("[data-testid='wizard-suggestion-chips']")).toBeNull()
  })

  it("formata faixa salarial como R$ min – R$ max", async () => {
    mockFetch.mockResolvedValueOnce(
      suggestionsResponse({
        salary_range: {
          value: { min: 8000, max: 12000 },
          source: "lia_history",
          confidence: 0.75,
          explanation: "Banda salarial histórica",
        },
      })
    )
    render(
      <WizardSuggestionChips
        data={{ parsed_title: "Dev Backend", department: "Tecnologia" }}
        onUpdate={vi.fn()}
      />
    )
    await waitFor(() => screen.getByTestId("suggestion-chip-salary_range"))
    expect(screen.getByText(/R\$ 8\.000/)).toBeDefined()
    expect(screen.getByText(/R\$ 12\.000/)).toBeDefined()
  })

  it("chama API com title, department e seniority como contexto", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({ suggestions: {} }) })
    render(
      <WizardSuggestionChips
        data={{ parsed_title: "Dev Senior", department: "Tech", seniority: "Senior" }}
        onUpdate={vi.fn()}
      />
    )
    await waitFor(() => expect(mockFetch).toHaveBeenCalled())
    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toContain("/api/v1/wizard/suggestions/all")
    const body = JSON.parse(opts.body)
    expect(body.job_title).toBe("Dev Senior")
    expect(body.department).toBe("Tech")
    expect(body.seniority).toBe("Senior")
  })
})
