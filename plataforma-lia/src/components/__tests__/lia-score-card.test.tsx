/**
 * Tests — LIAScoreCard (Item E)
 *
 * Cobre:
 * - Renderização do score
 * - aria-label correto com candidateName
 * - Expansão do breakdown ao clicar no botão
 * - Ausência do botão de expansão quando não há breakdown
 * - Referência ao EU AI Act no breakdown expandido
 */
import { describe, it, expect } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { LIAScoreCard } from "../lia-score-card"

describe("LIAScoreCard", () => {
  it("renders score correctly", () => {
    render(<LIAScoreCard score={85} />)
    expect(screen.getByText("85")).toBeDefined()
  })

  it("has correct aria-label", () => {
    render(<LIAScoreCard score={75} candidateName="João Silva" />)
    const region = screen.getByRole("region")
    expect(region.getAttribute("aria-label")).toContain("João Silva")
  })

  it("shows breakdown when expanded", () => {
    render(
      <LIAScoreCard
        score={80}
        breakdown={{ technical: 85, behavioral: 75 }}
      />
    )
    const expandBtn = screen.getByRole("button")
    fireEvent.click(expandBtn)
    expect(screen.getByText("Técnico")).toBeDefined()
    expect(screen.getByText("Comportamental")).toBeDefined()
  })

  it("does not show expand button without breakdown", () => {
    render(<LIAScoreCard score={70} />)
    const buttons = screen.queryAllByRole("button")
    expect(buttons.length).toBe(0)
  })

  it("shows EU AI Act reference in breakdown", () => {
    render(
      <LIAScoreCard score={80} breakdown={{ technical: 85 }} />
    )
    fireEvent.click(screen.getByRole("button"))
    expect(screen.getByText(/EU AI Act/)).toBeDefined()
  })
})
