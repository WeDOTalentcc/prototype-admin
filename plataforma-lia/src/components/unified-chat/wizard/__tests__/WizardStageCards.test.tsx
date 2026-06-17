// @vitest-environment jsdom
/**
 * Sensor TDD — WizardStageCards (WizardWsiCard + WizardJdCard)
 * Spec: F2/F4 — cards renderizam do payload de forma determinística.
 * NUNCA dependem de texto livre do LLM — apenas de campos estruturados.
 *
 * framer-motion é mockado porque não está instalado no ambiente de testes.
 */
import React from "react"
import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"

// Mock framer-motion — não instalado no ambiente de testes.
vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_target: object, tag: string) =>
        ({ children, ...props }: React.HTMLAttributes<HTMLElement> & { children?: React.ReactNode }) =>
          React.createElement(tag, props, children),
    },
  ),
  AnimatePresence: ({ children }: { children?: React.ReactNode }) =>
    React.createElement(React.Fragment, null, children),
}))

import { WizardWsiCard } from "../WizardWsiCard"
import { WizardJdCard } from "../WizardJdCard"

// ── WizardWsiCard ──────────────────────────────────────────────────────────────

describe("WizardWsiCard — payload determinístico", () => {
  function makeQuestions(n: number, needsReview = false) {
    return Array.from({ length: n }, (_, i) => ({
      text: "Pergunta de triagem número " + String(i + 1),
      block: i % 2 === 0 ? "technical" : "behavioral",
      needs_manual_review: needsReview && i === 0,
    }))
  }

  it("renderiza as primeiras 3 perguntas visíveis sem expandir", () => {
    const questions = makeQuestions(4)
    render(<WizardWsiCard data={{ questions }} />)
    expect(screen.getByText(/4 perguntas de triagem/i)).toBeInTheDocument()
    expect(screen.getByText("Pergunta de triagem número 1")).toBeInTheDocument()
    expect(screen.getByText("Pergunta de triagem número 2")).toBeInTheDocument()
    expect(screen.getByText("Pergunta de triagem número 3")).toBeInTheDocument()
  })

  it("expande para mostrar perguntas extras ao clicar no header", () => {
    const questions = makeQuestions(5)
    render(<WizardWsiCard data={{ questions }} />)
    const header = screen.getByRole("button", { name: /5 perguntas de triagem/i })
    fireEvent.click(header)
    expect(screen.getByText("Pergunta de triagem número 5")).toBeInTheDocument()
  })

  it("exibe badge 'revisar' quando needs_manual_review=true em alguma pergunta", () => {
    const questions = makeQuestions(3, true)
    render(<WizardWsiCard data={{ questions }} />)
    expect(screen.getByText(/1 revisar/i)).toBeInTheDocument()
  })

  it("não exibe badge revisar quando nenhuma pergunta precisa de revisão", () => {
    const questions = makeQuestions(3, false)
    render(<WizardWsiCard data={{ questions }} />)
    expect(screen.queryByText(/revisar/i)).not.toBeInTheDocument()
  })

  it("retorna null quando questions está vazio (sem crash)", () => {
    const { container } = render(<WizardWsiCard data={{ questions: [] }} />)
    expect(container.firstChild).toBeNull()
  })

  it("smoke: rerender mount/unmount sem throw (Rules of Hooks)", () => {
    const questions = makeQuestions(4)
    const { rerender, unmount } = render(<WizardWsiCard data={{ questions }} />)
    rerender(<WizardWsiCard data={{ questions: makeQuestions(2) }} />)
    unmount()
  })
})

// ── WizardJdCard ───────────────────────────────────────────────────────────────

describe("WizardJdCard — payload determinístico", () => {
  const baseEnriched = {
    titulo_padronizado: "Engenheiro de Software Sênior",
    senioridade_confirmada: "Sênior",
    about_role: "Você vai trabalhar com sistemas distribuídos de alta escala.",
    responsabilidades: ["Desenvolver APIs REST", "Revisar PRs"],
    skills_obrigatorias: [{ skill: "Python" }, { skill: "FastAPI" }],
  }

  it("renderiza título do jd_enriched.titulo_padronizado no header", () => {
    render(
      <WizardJdCard data={{ jd_enriched: baseEnriched, quality_score: 85 }} />,
    )
    expect(screen.getByText("Engenheiro de Software Sênior")).toBeInTheDocument()
  })

  it("renderiza o score quality_score no header", () => {
    render(
      <WizardJdCard data={{ jd_enriched: baseEnriched, quality_score: 85 }} />,
    )
    expect(screen.getByText(/85\/100/)).toBeInTheDocument()
  })

  it("expande ao clicar no botão header (accordion)", () => {
    render(
      <WizardJdCard data={{ jd_enriched: baseEnriched, quality_score: 75 }} />,
    )
    const toggle = screen.getByRole("button", { expanded: false })
    fireEvent.click(toggle)
    expect(screen.getByText(/sistemas distribuídos/i)).toBeInTheDocument()
  })

  it("retorna null quando jd_enriched está ausente (sem crash)", () => {
    const { container } = render(<WizardJdCard data={{}} />)
    expect(container.firstChild).toBeNull()
  })

  it("chama onOpenPanel ao clicar em 'Abrir no painel' (após expand)", () => {
    const onOpenPanel = vi.fn()
    render(
      <WizardJdCard
        data={{ jd_enriched: baseEnriched, quality_score: 60 }}
        onOpenPanel={onOpenPanel}
      />,
    )
    const toggle = screen.getByRole("button", { expanded: false })
    fireEvent.click(toggle)
    fireEvent.click(screen.getByText(/abrir no painel/i))
    expect(onOpenPanel).toHaveBeenCalledTimes(1)
  })

  it("smoke: rerender mount/unmount sem throw (Rules of Hooks)", () => {
    const { rerender, unmount } = render(
      <WizardJdCard data={{ jd_enriched: baseEnriched, quality_score: 70 }} />,
    )
    rerender(
      <WizardJdCard data={{ jd_enriched: baseEnriched, quality_score: 90 }} />,
    )
    unmount()
  })
})
