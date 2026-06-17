/**
 * Sensor #5 (audit 2026-06-05): WizardProgressBar reflete a ETAPA do fluxo
 * (Etapa X de Y), nao a completude da ficha. Pina o bug do Paulo: na
 * finalizacao a barra mostrava ~50% (porque usava completeness) -- agora cai em
 * N/N (~100%).
 */
import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import { WizardProgressBar } from "../WizardProgressBar"
import type { WizardStage } from "../wizard-types"

function renderBar(stage: WizardStage, completeness = 0.3, compact = false) {
  return render(
    <WizardProgressBar
      currentStage={stage}
      completeness={completeness}
      stageHistory={[]}
      compact={compact}
    />,
  )
}

describe("WizardProgressBar — progresso por etapa (audit #5)", () => {
  it("finalizacao (handoff) cai em N/N mesmo com completeness baixa", () => {
    const { container } = renderBar("handoff", 0.3)
    const root = container.querySelector("[data-step-number]") as HTMLElement
    expect(root.getAttribute("data-step-number")).toBe(
      root.getAttribute("data-step-total"),
    )
    const bar = container.querySelector(".bg-wedo-cyan") as HTMLElement
    expect(bar.style.width).toBe("100%")
  })

  it("primeira etapa visivel (jd_enrichment) e 1/N", () => {
    const { container } = renderBar("jd_enrichment", 0.9)
    const root = container.querySelector("[data-step-number]") as HTMLElement
    expect(root.getAttribute("data-step-number")).toBe("1")
  })

  it("a largura NAO segue a completeness (segue a etapa)", () => {
    // completeness 0.3 mas etapa final -> barra 100% (nao 30%).
    const { container } = renderBar("handoff", 0.3)
    const bar = container.querySelector(".bg-wedo-cyan") as HTMLElement
    expect(bar.style.width).not.toBe("30%")
  })

  it("mostra o rotulo 'Etapa X de Y' no layout full-page", () => {
    renderBar("wsi_questions", 0.5)
    expect(screen.getByText(/Etapa \d+ de \d+/)).toBeTruthy()
  })

  it("compact tambem e step-based", () => {
    const { container } = renderBar("handoff", 0.3, true)
    const bar = container.querySelector(".bg-wedo-cyan") as HTMLElement
    expect(bar.style.width).toBe("100%")
  })
})
