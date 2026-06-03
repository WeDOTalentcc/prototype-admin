import { describe, expect, it } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { WsiQuestionsPanel } from "../WsiQuestionsPanel"
import type { ScreeningQuestion } from "../../wizard-types"

/**
 * Harness fixes — auditoria fluxo de criacao de vagas (2026-06-03).
 *
 * Pina 4 defeitos confirmados no painel WSI:
 *  #7 hydration  dentro de  (WsiQuestionsPanel.tsx:291 envolvia :301).
 *  #4a toggle de aprovacao por pergunta estava MORTO (onToggleApprove nunca
 *      era plugado pelo pai → contador preso em 0/N, "Aprovar todas" travado).
 *  #4b acao "Editar" redundante com "Regenerar" (ambas caiam no mesmo tool).
 *  #4c fonte do texto da pergunta maior que o chat (text-sm 14px vs text-[13px]).
 */

function makeQuestion(i: number, block: "technical" | "behavioral"): ScreeningQuestion {
  return {
    question: `Pergunta ${i + 1} sobre ${block}`,
    ideal_answer: "Resposta ideal de referencia",
    scoring_rubric: {},
    framework: "CBI",
    block,
    skill: "Skill X",
    weight: 1,
    approved: false,
  }
}

function renderPanel(count = 3) {
  const questions: ScreeningQuestion[] = Array.from({ length: count }, (_, i) =>
    makeQuestion(i, i === 0 ? "behavioral" : "technical"),
  )
  return render(
    <WsiQuestionsPanel
      data={{
        questions,
        screening_mode: "compact",
        distribution: null,
        seniority_level: "pleno",
      }}
      requiresApproval={true}
    />,
  )
}

describe("WsiQuestionsPanel — harness fixes (audit 2026-06-03)", () => {
  it("#7 nao renderiza botao aninhado em botao (hydration-safe)", () => {
    const { container } = renderPanel()
    expect(container.querySelectorAll("button button").length).toBe(0)
  })

  it("#4a toggle de aprovacao atualiza o contador X/Y aprovadas", () => {
    renderPanel(3)
    expect(screen.getByText(/0\/3 aprovadas/)).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText(/Aprovar pergunta 1/i))
    expect(screen.getByText(/1\/3 aprovadas/)).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText(/Desaprovar pergunta 1/i))
    expect(screen.getByText(/0\/3 aprovadas/)).toBeInTheDocument()
  })

  it("#4b nao exibe acao 'Editar' (redundante com Regenerar)", () => {
    renderPanel()
    fireEvent.click(screen.getByText(/Pergunta 1 sobre/))
    expect(screen.queryByRole("button", { name: /^Editar/i })).not.toBeInTheDocument()
  })

  it("#4c texto da pergunta usa o mesmo tamanho do chat (text-[13px], nao text-sm)", () => {
    renderPanel()
    const p = screen.getByText(/Pergunta 1 sobre/)
    expect(p.className).toContain("text-[13px]")
    expect(p.className).not.toContain("text-sm")
  })
})

describe("WsiQuestionsPanel — Regenerar/Substituir fundidos (audit 2026-06-03 #4)", () => {
  it("não exibe 'Substituir' (fundido em 'Regenerar')", () => {
    const questions = Array.from({ length: 3 }, (_, i) => ({
      question: `Pergunta ${i + 1}`,
      ideal_answer: "x", scoring_rubric: {}, framework: "CBI" as const,
      block: "technical" as const, skill: "S", weight: 1, approved: false,
    }))
    render(
      <WsiQuestionsPanel
        data={{ questions, screening_mode: "compact", distribution: null, seniority_level: "pleno" }}
        requiresApproval={true}
      />,
    )
    fireEvent.click(screen.getByText(/Pergunta 1/))
    expect(screen.queryByRole("button", { name: /Substituir/i })).not.toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Regenerar/i })).toBeInTheDocument()
  })
})
