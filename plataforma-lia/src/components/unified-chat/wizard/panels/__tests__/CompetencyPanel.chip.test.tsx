import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"
import { CompetencyPanel } from "../CompetencyPanel"

/**
 * Tarefa 2 — CompetencyPanel usa o Chip canônico (alinhado à ficha viva 5a).
 * Smoke: renderiza skills + rerender vazio→cheio→vazio sem throw (Rules-of-Hooks).
 */
const DATA = {
  seniority: "senior",
  seniority_display: "Sênior",
  screening_mode: "compact",
  distribution: { technical: 5, behavioral: 2 },
  competency_tree: [
    { skill: "Python", block: "technical" },
    { skill: "SQL", block: "technical" },
    { skill: "Comunicação", block: "behavioral", trait: "extraversion" },
  ],
}

describe("CompetencyPanel — Chip canônico", () => {
  it("renderiza skills técnicas e comportamentais", () => {
    render(<CompetencyPanel data={DATA} />)
    expect(screen.getByText("Python")).toBeInTheDocument()
    expect(screen.getByText("SQL")).toBeInTheDocument()
    expect(screen.getByText("Comunicação")).toBeInTheDocument()
    expect(screen.getByText("extraversion")).toBeInTheDocument()
  })

  it("rerender vazio→cheio→vazio sem throw", () => {
    const { rerender } = render(<CompetencyPanel data={{}} />)
    expect(() => {
      rerender(<CompetencyPanel data={DATA} />)
      rerender(<CompetencyPanel data={{}} />)
    }).not.toThrow()
  })
})
