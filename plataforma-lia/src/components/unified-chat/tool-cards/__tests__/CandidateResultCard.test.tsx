import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import React from "react"
import { CandidateResultCard, type CandidateSummary } from "../CandidateResultCard"
import { ToolSurfaceContext } from "@/contexts/ToolSurfaceContext"

const MOCK_CANDIDATES: CandidateSummary[] = [
  { id: "1", name: "Ana Lima", currentTitle: "Eng. Frontend", matchScore: 87 },
  { id: "2", name: "Carlos Silva", currentTitle: "Dev React", matchScore: 72 },
  { id: "3", name: "Maria Costa", currentTitle: "UX Designer", matchScore: 65 },
  { id: "4", name: "João Santos", currentTitle: "Backend Dev", matchScore: 58 },
]

describe("CandidateResultCard — inline mode (default)", () => {
  it("mostra contagem total de candidatos", () => {
    render(
      <CandidateResultCard candidates={MOCK_CANDIDATES} totalCount={12} />
    )
    expect(screen.getByText(/12 candidatos/i)).toBeInTheDocument()
  })

  it("mostra apenas os 3 primeiros candidatos no inline", () => {
    render(
      <CandidateResultCard candidates={MOCK_CANDIDATES} totalCount={12} />
    )
    expect(screen.getByText("Ana Lima")).toBeInTheDocument()
    expect(screen.getByText("Carlos Silva")).toBeInTheDocument()
    expect(screen.getByText("Maria Costa")).toBeInTheDocument()
    expect(screen.queryByText("João Santos")).not.toBeInTheDocument()
  })

  it("renderiza botão \"Ver todos\" quando onOpenPanel é fornecido", () => {
    const onOpenPanel = vi.fn()
    render(
      <CandidateResultCard candidates={MOCK_CANDIDATES} totalCount={12} onOpenPanel={onOpenPanel} />
    )
    const btn = screen.getByRole("button", { name: /ver/i })
    expect(btn).toBeInTheDocument()
  })

  it("não renderiza botão \"Ver todos\" quando onOpenPanel está ausente", () => {
    render(
      <CandidateResultCard candidates={MOCK_CANDIDATES} totalCount={12} />
    )
    expect(screen.queryByRole("button", { name: /ver/i })).not.toBeInTheDocument()
  })
})

describe("CandidateResultCard — panel mode", () => {
  const PanelWrapper = ({ children }: { children: React.ReactNode }) => (
    <ToolSurfaceContext.Provider value="panel">{children}</ToolSurfaceContext.Provider>
  )

  it("mostra todos os candidatos no panel mode", () => {
    render(
      <CandidateResultCard candidates={MOCK_CANDIDATES} totalCount={4} />,
      { wrapper: PanelWrapper }
    )
    expect(screen.getByText("Ana Lima")).toBeInTheDocument()
    expect(screen.getByText("João Santos")).toBeInTheDocument()
  })

  it("não renderiza botão \"Ver todos\" no panel mode", () => {
    const onOpenPanel = vi.fn()
    render(
      <CandidateResultCard candidates={MOCK_CANDIDATES} totalCount={4} onOpenPanel={onOpenPanel} />,
      { wrapper: PanelWrapper }
    )
    expect(screen.queryByRole("button", { name: /ver/i })).not.toBeInTheDocument()
  })
})
