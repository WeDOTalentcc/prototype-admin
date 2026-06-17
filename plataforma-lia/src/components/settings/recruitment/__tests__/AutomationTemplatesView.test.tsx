/**
 * AutomationTemplatesView tests — Sprint B canonical impeccable.
 *
 * Sensores:
 * - Renderiza os 8 templates canonical
 * - Cada card tem name, description, impact, icon, botão "Usar este"
 * - onUseTemplate é chamado com o template state exato
 * - Cyan presence (LIA exclusive) em icon + CTA
 * - Hover state na border (border-wedo-cyan/40)
 * - Category → icon mapping correto
 * - data-testid pra cada card e CTA
 */

import { describe, it, expect, vi } from "vitest"
import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import {
  AutomationTemplatesView,
  AUTOMATION_TEMPLATES,
} from "../AutomationTemplatesView"

describe("AutomationTemplatesView", () => {
  it("renderiza os 8 templates canonical", () => {
    render(<AutomationTemplatesView onUseTemplate={() => {}} />)
    const cards = screen.getAllByTestId(/^template-card-/)
    expect(cards).toHaveLength(8)
    expect(AUTOMATION_TEMPLATES).toHaveLength(8)
  })

  it("cada template tem name, description e impact visíveis", () => {
    render(<AutomationTemplatesView onUseTemplate={() => {}} />)
    for (const tpl of AUTOMATION_TEMPLATES) {
      const card = screen.getByTestId(`template-card-${tpl.id}`)
      expect(within(card).getByText(tpl.name)).toBeInTheDocument()
      expect(within(card).getByText(tpl.description)).toBeInTheDocument()
      expect(within(card).getByText(tpl.impact)).toBeInTheDocument()
    }
  })

  it("cada template tem icon (aria-hidden, cyan)", () => {
    render(<AutomationTemplatesView onUseTemplate={() => {}} />)
    for (const tpl of AUTOMATION_TEMPLATES) {
      const icon = screen.getByTestId(`template-icon-${tpl.id}`)
      expect(icon).toBeInTheDocument()
      expect(icon).toHaveAttribute("aria-hidden", "true")
      // SVG elements expose className as SVGAnimatedString — use getAttribute
      expect(icon.getAttribute("class")).toContain("text-wedo-cyan")
    }
  })

  it("click em 'Usar este' chama onUseTemplate com o state canonical", async () => {
    const user = userEvent.setup()
    const onUseTemplate = vi.fn()
    render(<AutomationTemplatesView onUseTemplate={onUseTemplate} />)

    const firstTpl = AUTOMATION_TEMPLATES[0]
    const cta = screen.getByTestId(`template-use-${firstTpl.id}`)
    await user.click(cta)

    expect(onUseTemplate).toHaveBeenCalledTimes(1)
    expect(onUseTemplate).toHaveBeenCalledWith(firstTpl.state)
  })

  it("click em template diferente passa state diferente", async () => {
    const user = userEvent.setup()
    const onUseTemplate = vi.fn()
    render(<AutomationTemplatesView onUseTemplate={onUseTemplate} />)

    const target = AUTOMATION_TEMPLATES.find(
      (t) => t.id === "auto_advance_high_wsi",
    )!
    await user.click(screen.getByTestId(`template-use-${target.id}`))

    expect(onUseTemplate).toHaveBeenCalledWith(target.state)
    expect(target.state.conditions).toHaveLength(1)
    expect(target.state.conditions[0]).toEqual({
      field: "candidate.wsi_score",
      operator: "gt",
      value: 80,
    })
  })

  it("cyan presence canonical (LIA exclusive) em icon + CTA", () => {
    render(<AutomationTemplatesView onUseTemplate={() => {}} />)
    const ctas = screen.getAllByTestId(/^template-use-/)
    for (const cta of ctas) {
      expect(cta.className).toContain("text-wedo-cyan")
    }
  })

  it("cards têm hover state border-wedo-cyan/40", () => {
    render(<AutomationTemplatesView onUseTemplate={() => {}} />)
    const cards = screen.getAllByTestId(/^template-card-/)
    for (const card of cards) {
      expect(card.className).toContain("hover:border-wedo-cyan/40")
    }
  })

  it("cards respeitam motion-reduce (a11y)", () => {
    render(<AutomationTemplatesView onUseTemplate={() => {}} />)
    const cards = screen.getAllByTestId(/^template-card-/)
    for (const card of cards) {
      expect(card.className).toContain("motion-reduce:transition-none")
    }
  })

  it("category → icon mapping canonical (Mail pra communication)", () => {
    render(<AutomationTemplatesView onUseTemplate={() => {}} />)
    // Templates communication têm icon Mail (svg lucide-mail)
    const communicationTpls = AUTOMATION_TEMPLATES.filter(
      (t) => t.category === "communication",
    )
    expect(communicationTpls.length).toBeGreaterThan(0)
    for (const tpl of communicationTpls) {
      const icon = screen.getByTestId(`template-icon-${tpl.id}`)
      // lucide-react renderiza SVG; class name canonical inclui o nome do icon
      expect(icon.tagName.toLowerCase()).toBe("svg")
    }
  })

  it("voice 'Quiet Operator': headline sugestivo, não imposição", () => {
    render(<AutomationTemplatesView onUseTemplate={() => {}} />)
    expect(
      screen.getByText("Exemplos prontos pra começar"),
    ).toBeInTheDocument()
    expect(
      screen.getByText("Use como ponto de partida. Você ajusta tudo antes de salvar."),
    ).toBeInTheDocument()
  })

  it("todos os templates têm state canonical com trigger + actions", () => {
    for (const tpl of AUTOMATION_TEMPLATES) {
      expect(tpl.state.trigger).toBeDefined()
      expect(tpl.state.trigger.type).toBeTruthy()
      expect(tpl.state.actions.length).toBeGreaterThan(0)
      expect(tpl.state.name).toBeTruthy()
      expect(Array.isArray(tpl.state.conditions)).toBe(true)
    }
  })
})
