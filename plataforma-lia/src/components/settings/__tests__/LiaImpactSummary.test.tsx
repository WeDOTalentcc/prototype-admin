/**
 * Smoke test — LiaImpactSummary (P1-9 audit 2026-05-26).
 * Cobre 3 acceptance criteria:
 *  1. Renderiza testid canonical "lia-impact-summary"
 *  2. Mostra X de 34 quando toggles vazio (default canonical = all ON)
 *  3. Mostra count reduzido quando toggles têm campos false
 */
import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { LiaImpactSummary } from "@/components/settings/LiaImpactSummary"

describe("LiaImpactSummary — P1-9 visualiza qual dado vai pra IA", () => {
  it("renderiza container com testid canonical", () => {
    render(<LiaImpactSummary toggles={{}} />)
    expect(screen.getByTestId("lia-impact-summary")).toBeInTheDocument()
  })

  it("conta TODOS os campos canonical quando toggles vazio (default ON)", () => {
    render(<LiaImpactSummary toggles={{}} />)
    // Esperado: "34 de 34" — total canonical
    expect(screen.getByText(/34 de 34/)).toBeInTheDocument()
    // 100% visível
    expect(screen.getByText(/\(100%\)/)).toBeInTheDocument()
  })

  it("reduz count quando toggles têm campos explicitamente false", () => {
    render(
      <LiaImpactSummary
        toggles={{
          mission: false,
          values: false,
          tech_stack: false,
        }}
      />,
    )
    // 34 - 3 = 31
    expect(screen.getByText(/31 de 34/)).toBeInTheDocument()
  })

  it("mostra exemplos de uso por campo (educacional)", () => {
    render(<LiaImpactSummary toggles={{}} />)
    expect(screen.getByText("tom dos textos de vaga")).toBeInTheDocument()
    expect(screen.getByText("match cultural com candidatos")).toBeInTheDocument()
    expect(screen.getByText("calibração de perguntas técnicas")).toBeInTheDocument()
  })

  it("mostra hint de ajuste quando há campos OFF", () => {
    render(
      <LiaImpactSummary
        toggles={{ mission: false }}
      />,
    )
    expect(screen.getByText(/campo está ocultos? da LIA/i)).toBeInTheDocument()
  })

  it("NÃO mostra hint de ajuste quando todos ON (100%)", () => {
    render(<LiaImpactSummary toggles={{}} />)
    expect(screen.queryByText(/oculto/i)).not.toBeInTheDocument()
  })
})
