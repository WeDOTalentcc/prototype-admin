import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { EligibilityResultsSection } from "../eligibility-results-section"
import type { EligibilityResultItem } from "../eligibility-results-section"

const approvedResults: EligibilityResultItem[] = [
  {
    id: "q1",
    question: "Você possui CNH categoria B válida?",
    answer: "Sim, possuo CNH B.",
    passed: true,
    is_eliminatory: true,
  },
  {
    id: "q2",
    question: "Você tem disponibilidade para início imediato?",
    answer: "Sim, posso iniciar em até 10 dias.",
    passed: true,
    is_eliminatory: true,
  },
]

const eliminatedResults: EligibilityResultItem[] = [
  {
    id: "q1",
    question: "Você possui CNH categoria B válida?",
    answer: "Sim, possuo CNH B.",
    passed: true,
    is_eliminatory: true,
  },
  {
    id: "q2",
    question: "Você possui inglês fluente para reuniões internacionais?",
    answer: "Tenho inglês intermediário.",
    passed: false,
    is_eliminatory: true,
    reconsideration: '1ª tentativa: "Tenho inglês básico" → Reconsiderou antes da resposta final.',
  },
]

describe("EligibilityResultsSection", () => {
  it("não renderiza quando não há resultados — verificação de contrato (caller)", () => {
    const { container } = render(<EligibilityResultsSection results={[]} />)
    expect(container.firstChild).toBeNull()
    expect(screen.queryByText("Pré-triagem — Elegibilidade")).not.toBeInTheDocument()
  })

  it("candidato aprovado: exibe header com status positivo e todas as perguntas atendidas", () => {
    render(<EligibilityResultsSection results={approvedResults} />)

    expect(screen.getByText("Pré-triagem — Elegibilidade")).toBeInTheDocument()
    expect(screen.getByText(/Todas as 2 perguntas atendidas/)).toBeInTheDocument()
  })

  it("candidato aprovado: expande e exibe perguntas e respostas ao clicar no header", async () => {
    const user = userEvent.setup()
    render(<EligibilityResultsSection results={approvedResults} />)

    const btn = screen.getByRole("button", { name: /Pré-triagem/i })
    await user.click(btn)

    expect(screen.getByText("Você possui CNH categoria B válida?")).toBeInTheDocument()
    expect(screen.getByText("Sim, possuo CNH B.")).toBeInTheDocument()
    expect(screen.getAllByText(/Atendido/)).toHaveLength(2)
  })

  it("candidato eliminado: exibe header com status negativo, seção expandida por padrão", () => {
    render(<EligibilityResultsSection results={eliminatedResults} />)

    expect(screen.getByText(/Eliminado|eliminado/i)).toBeInTheDocument()

    expect(screen.getByText("Você possui inglês fluente para reuniões internacionais?")).toBeInTheDocument()
    expect(screen.getByText(/Não atendido/)).toBeInTheDocument()
  })

  it("candidato eliminado: exibe nota de reconsideração quando presente", () => {
    render(<EligibilityResultsSection results={eliminatedResults} />)

    expect(
      screen.getByText(/1ª tentativa/),
    ).toBeInTheDocument()
  })

  it("candidato eliminado: exibe badge 'Atendido' para perguntas que passaram e 'Não atendido' para a que falhou", () => {
    render(<EligibilityResultsSection results={eliminatedResults} />)

    const passed = screen.getAllByText(/Atendido/)
    const failed = screen.getAllByText(/Não atendido/)
    expect(passed.length).toBeGreaterThanOrEqual(1)
    expect(failed.length).toBe(1)
  })

  it("sem perguntas: seção não exibe o título de elegibilidade (proteção de ruído)", () => {
    render(<EligibilityResultsSection results={[]} />)
    expect(screen.queryByText("Pré-triagem — Elegibilidade")).not.toBeInTheDocument()
  })
})
