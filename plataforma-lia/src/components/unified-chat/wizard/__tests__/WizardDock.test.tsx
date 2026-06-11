import React from "react"
import { describe, it, expect, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { WizardDock } from "../WizardDock"

const baseProps = {
  stage: "wsi_questions",
  stageLabel: "Perguntas WSI",
  requiresApproval: true,
  onExpand: vi.fn(),
  progressBar: <div data-testid="progress-slot" />,
  thumbnail: <div data-testid="thumb-slot" />,
}

describe("WizardDock — Manus F1", () => {
  it("renderiza label da etapa, slot de progresso e thumbnail inerte", () => {
    render(<WizardDock {...baseProps} />)
    expect(screen.getByText("Perguntas WSI")).toBeInTheDocument()
    expect(screen.getByTestId("progress-slot")).toBeInTheDocument()
    const thumb = screen.getByTestId("wizard-dock-thumbnail")
    expect(thumb).toHaveAttribute("aria-hidden", "true")
  })

  it("badge de pendência quando requiresApproval", () => {
    render(<WizardDock {...baseProps} />)
    expect(screen.getByText(/aprovação pendente/i)).toBeInTheDocument()
  })

  it("clique no card chama onExpand", () => {
    const onExpand = vi.fn()
    render(<WizardDock {...baseProps} onExpand={onExpand} />)
    fireEvent.click(screen.getByTestId("wizard-dock"))
    expect(onExpand).toHaveBeenCalledTimes(1)
  })

  it("smoke rerender mount/unmount sem throw (Rules of Hooks)", () => {
    const { rerender, unmount } = render(<WizardDock {...baseProps} />)
    rerender(<WizardDock {...baseProps} requiresApproval={false} />)
    unmount()
  })
})
