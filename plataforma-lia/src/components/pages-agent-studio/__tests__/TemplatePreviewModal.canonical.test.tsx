/**
 * TemplateClonePanel — P1-1 canonical Dialog conversion sentinel (2026-05-26).
 *
 * Garante que o preview de templates renderiza como Dialog central
 * canonical (role=dialog) e NÃO mais como Sheet lateral. Cobre
 * elevation tonal (border-medium + shadow-lia-lg + rounded-xl).
 */

import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

import { TemplateClonePanel } from "../template-clone/TemplateClonePanel"
import type { AgentTemplate } from "../custom-agents/types"

const TPL: AgentTemplate = {
  id: "tpl-x",
  name: "Triagem Volume",
  description: "Processa alto volume",
  category: "screening",
  domain: "screening",
  icon: "Bot",
  system_prompt: "Você é um agente de triagem.",
  allowed_tools: ["search_candidates"],
  context_level: "standard",
  max_steps: 8,
  temperature: 0.3,
  enable_memory: true,
  excluded_tools: [],
}

describe("TemplateClonePanel — P1-1 canonical Dialog (central)", () => {
  it("renderiza como role=dialog (Radix Dialog, não Sheet)", () => {
    render(
      <TemplateClonePanel
        template={TPL}
        open
        onClose={vi.fn()}
        onClone={vi.fn()}
      />
    )
    const dialog = screen.getByRole("dialog")
    expect(dialog).toBeTruthy()
    // Sheet lateral teria data-side=right; Dialog canonical não.
    expect(dialog.getAttribute("data-side")).toBeNull()
  })

  it("preview content renderizado (system_prompt + tools + persona + config)", () => {
    render(
      <TemplateClonePanel
        template={TPL}
        open
        onClose={vi.fn()}
        onClone={vi.fn()}
      />
    )
    expect(screen.getByTestId("template-clone-section-prompt")).toBeTruthy()
    expect(screen.getByTestId("template-clone-section-tools")).toBeTruthy()
    expect(screen.getByTestId("template-clone-section-persona")).toBeTruthy()
    expect(screen.getByTestId("template-clone-section-config")).toBeTruthy()
    expect(screen.getByTestId("template-clone-system-prompt").textContent).toContain(
      "agente de triagem"
    )
  })

  it("botão 'Clonar e customizar' presente e dispara onClone", () => {
    const onClone = vi.fn()
    render(
      <TemplateClonePanel
        template={TPL}
        open
        onClose={vi.fn()}
        onClone={onClone}
      />
    )
    const cta = screen.getByTestId("template-clone-confirm")
    expect(cta).toBeTruthy()
    fireEvent.click(cta)
    expect(onClone).toHaveBeenCalledWith(TPL)
  })

  it("DialogContent tem elevation tonal canonical (border-medium + shadow-lia-lg + rounded-xl)", () => {
    render(
      <TemplateClonePanel
        template={TPL}
        open
        onClose={vi.fn()}
        onClone={vi.fn()}
      />
    )
    const panel = screen.getByTestId("template-clone-panel")
    const cls = panel.className
    expect(cls).toContain("border-lia-border-medium")
    expect(cls).toContain("shadow-lia-lg")
    expect(cls).toContain("rounded-xl")
  })
})
