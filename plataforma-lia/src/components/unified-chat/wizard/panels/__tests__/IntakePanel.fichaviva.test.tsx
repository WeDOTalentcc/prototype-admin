import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { IntakePanel } from "../IntakePanel"

/**
 * Fase 5a — IntakePanel como "ficha viva".
 *
 * Zona bloqueante (título/senioridade/modelo/modo) + zona enriquecedora
 * (depto/localização/contrato/salário) + chips de competências editáveis
 * (lendo suggestions_data.competencies da Fase 3, ou confirmed_* quando presente).
 * Edição é local via onUpdate (write-back real ao backend é 5b).
 *
 * Disciplina: Rules-of-Hooks (rerender data null→cheio→null sem throw).
 */

const SUGGESTIONS = {
  technical: [
    { skill: "Python", contexto: "core" },
    { skill: "PostgreSQL", contexto: "db" },
  ],
  behavioral: [
    { competencia: "Comunicação", contexto: "squad", trait_big_five: "extraversion" },
  ],
}

function fullData(overrides: Record<string, unknown> = {}) {
  return {
    raw_input: "Engenheiro de Software Sênior remoto",
    parsed_title: "Engenheiro de Software",
    parsed_seniority: "senior",
    parsed_model: "remoto",
    parsed_department: "Tecnologia",
    parsed_location: "São Paulo",
    parsed_employment_type: "CLT",
    screening_mode: "compact",
    suggestions_data: { competencies: SUGGESTIONS },
    ...overrides,
  }
}

describe("IntakePanel ficha viva — Rules of Hooks", () => {
  it("rerender data vazio → cheio → vazio sem throw", () => {
    const { rerender } = render(<IntakePanel data={{}} />)
    expect(() => {
      rerender(<IntakePanel data={fullData()} />)
      rerender(<IntakePanel data={{}} />)
    }).not.toThrow()
  })
})

describe("IntakePanel ficha viva — zonas", () => {
  it("zona bloqueante mostra título/senioridade/modelo/modo", () => {
    render(<IntakePanel data={fullData()} />)
    const zone = screen.getByTestId("intake-blocking-zone")
    expect(zone).toBeInTheDocument()
    expect(zone).toHaveTextContent(/Engenheiro de Software/)
    expect(zone).toHaveTextContent(/senior/i)
    expect(zone).toHaveTextContent(/remoto/i)
    // modo compact → rótulo legível
    expect(zone).toHaveTextContent(/Compacto/i)
  })

  it("zona enriquecedora mostra depto/localização/contrato", () => {
    render(<IntakePanel data={fullData()} />)
    const zone = screen.getByTestId("intake-enriching-zone")
    expect(zone).toHaveTextContent(/Tecnologia/)
    expect(zone).toHaveTextContent(/São Paulo/)
    expect(zone).toHaveTextContent(/CLT/)
  })

  it("campo bloqueante ausente aparece como pendente (não some)", () => {
    render(<IntakePanel data={fullData({ screening_mode: undefined })} />)
    const zone = screen.getByTestId("intake-blocking-zone")
    // ainda lista "Modo de triagem" como pendente
    expect(zone).toHaveTextContent(/Modo de triagem/i)
  })
})

describe("IntakePanel ficha viva — competências", () => {
  it("renderiza chips técnicas e comportamentais das sugestões", () => {
    render(<IntakePanel data={fullData()} />)
    const block = screen.getByTestId("intake-competencies")
    expect(block).toHaveTextContent("Python")
    expect(block).toHaveTextContent("PostgreSQL")
    expect(block).toHaveTextContent("Comunicação")
  })

  it("prefere confirmed_* sobre suggestions quando presente", () => {
    render(<IntakePanel data={fullData({
      confirmed_technical_competencies: [{ skill: "Rust", contexto: "x" }],
      confirmed_behavioral_competencies: [{ competencia: "Liderança", contexto: "x", trait_big_five: "extraversion" }],
    })} />)
    const block = screen.getByTestId("intake-competencies")
    expect(block).toHaveTextContent("Rust")
    expect(block).toHaveTextContent("Liderança")
    expect(block).not.toHaveTextContent("Python")
  })

  it("remover um chip técnico chama onUpdate com a lista reduzida", () => {
    const onUpdate = vi.fn()
    render(<IntakePanel data={fullData()} onUpdate={onUpdate} />)
    // botão de remover da primeira técnica (Python)
    fireEvent.click(screen.getByTestId("remove-technical-0"))
    expect(onUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        confirmed_technical_competencies: [{ skill: "PostgreSQL", contexto: "db" }],
      }),
    )
  })

  it("adicionar uma técnica chama onUpdate com a lista incrementada", () => {
    const onUpdate = vi.fn()
    render(<IntakePanel data={fullData()} onUpdate={onUpdate} />)
    const input = screen.getByTestId("add-technical-input") as HTMLInputElement
    fireEvent.change(input, { target: { value: "Docker" } })
    fireEvent.keyDown(input, { key: "Enter" })
    expect(onUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        confirmed_technical_competencies: expect.arrayContaining([
          { skill: "Python", contexto: "core" },
          { skill: "PostgreSQL", contexto: "db" },
          expect.objectContaining({ skill: "Docker" }),
        ]),
      }),
    )
  })
})

describe("IntakePanel ficha viva — comportamento existente preservado", () => {
  it("editar raw_input ainda chama onUpdate", () => {
    const onUpdate = vi.fn()
    render(<IntakePanel data={fullData()} onUpdate={onUpdate} />)
    fireEvent.click(screen.getByLabelText(/Editar descri/i))
    const ta = screen.getByLabelText(/Editar descri.+da vaga/i) as HTMLTextAreaElement
    fireEvent.change(ta, { target: { value: "Texto novo" } })
    fireEvent.click(screen.getByText(/Salvar/i))
    expect(onUpdate).toHaveBeenCalledWith(expect.objectContaining({ raw_input: "Texto novo" }))
  })
})
