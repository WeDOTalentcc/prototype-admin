/**
 * Sprint visual 2026-05-26 — TemplateCard rich layout canonical.
 *
 * 3 métricas (Ferramentas / Passos máx / Contexto) + alert sutil
 * "Personalize antes de ativar" + 3 botões hierarchy (Usar template Ink +
 * Customizar outline + Preview ghost).
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { TemplateCard } from "../TemplateCard"
import type { AgentTemplate } from "../types"

vi.mock("next-intl", () => ({
  useTranslations: (ns?: string) => (key: string, vars?: Record<string, unknown>) => {
    if (vars && "count" in vars) return `${vars.count} tools`
    // Echo namespaced key suffix for readability assertions
    return ns ? `${ns}.${key}` : key
  },
}))

const baseTemplate: AgentTemplate = {
  id: "tpl-rich-1",
  name: "Recrutador Rich",
  description: "Template com layout rico Sprint visual",
  category: "screening" as AgentTemplate["category"],
  domain: "tech",
  icon: "Bot",
  system_prompt: "...",
  allowed_tools: ["search", "screen", "rank"],
  context_level: "standard",
  max_steps: 12,
  temperature: 0.7,
  enable_memory: false,
  excluded_tools: [],
  tags: ["popular"],
}

describe("TemplateCard — Sprint visual rich layout", () => {
  it("renderiza 3 métricas: Ferramentas count, Passos máx, Contexto label", () => {
    render(<TemplateCard template={baseTemplate} onSelect={vi.fn()} />)
    const metrics = screen.getByTestId(`template-card-metrics-${baseTemplate.id}`)
    expect(metrics).toBeTruthy()
    // Ferramentas: allowed_tools.length = 3
    expect(metrics.textContent).toContain("3")
    // Passos max: 12
    expect(metrics.textContent).toContain("12")
    // Contexto: "standard" label key resolvido pelo mock
    expect(metrics.textContent?.toLowerCase()).toContain("standard")
  })

  it("renderiza alert sutil 'Personalize antes de ativar'", () => {
    const { container } = render(
      <TemplateCard template={baseTemplate} onSelect={vi.fn()} />,
    )
    const note = container.querySelector('[role="note"]')
    expect(note).toBeTruthy()
    expect(note?.textContent?.toLowerCase()).toContain("personalize")
  })

  it("renderiza 3 botões com data-testid únicos (use + customize + preview)", () => {
    render(<TemplateCard template={baseTemplate} onSelect={vi.fn()} />)
    expect(screen.getByTestId(`template-card-use-${baseTemplate.id}`)).toBeTruthy()
    expect(screen.getByTestId(`template-card-customize-${baseTemplate.id}`)).toBeTruthy()
    expect(screen.getByTestId(`template-card-preview-${baseTemplate.id}`)).toBeTruthy()
  })

  it("badge Popular renderiza quando tag presente (wedo-purple, NÃO wedo-cyan)", () => {
    const { container } = render(
      <TemplateCard template={baseTemplate} onSelect={vi.fn()} />,
    )
    const html = container.innerHTML
    expect(html).toContain("wedo-purple")
    expect(html).not.toContain("bg-wedo-cyan")
  })

  it("onSelect chamado quando 'Usar template' clicado; onCustomize/onPreview opcionais usam onSelect como fallback", () => {
    const onSelect = vi.fn()
    render(<TemplateCard template={baseTemplate} onSelect={onSelect} />)
    fireEvent.click(screen.getByTestId(`template-card-use-${baseTemplate.id}`))
    expect(onSelect).toHaveBeenCalledTimes(1)
    expect(onSelect).toHaveBeenCalledWith(baseTemplate)

    // Customize sem prop -> usa onSelect fallback
    fireEvent.click(screen.getByTestId(`template-card-customize-${baseTemplate.id}`))
    expect(onSelect).toHaveBeenCalledTimes(2)

    // Preview sem prop -> usa onSelect fallback
    fireEvent.click(screen.getByTestId(`template-card-preview-${baseTemplate.id}`))
    expect(onSelect).toHaveBeenCalledTimes(3)
  })

  it("onCustomize / onPreview dedicados chamados quando providos", () => {
    const onSelect = vi.fn()
    const onCustomize = vi.fn()
    const onPreview = vi.fn()
    render(
      <TemplateCard
        template={baseTemplate}
        onSelect={onSelect}
        onCustomize={onCustomize}
        onPreview={onPreview}
      />,
    )
    fireEvent.click(screen.getByTestId(`template-card-customize-${baseTemplate.id}`))
    fireEvent.click(screen.getByTestId(`template-card-preview-${baseTemplate.id}`))
    expect(onCustomize).toHaveBeenCalledTimes(1)
    expect(onPreview).toHaveBeenCalledTimes(1)
    expect(onSelect).toHaveBeenCalledTimes(0)
  })

  it("NÃO usa text-wedo-cyan no markup (white-label Studio)", () => {
    const { container } = render(
      <TemplateCard template={baseTemplate} onSelect={vi.fn()} />,
    )
    expect(container.innerHTML).not.toContain("text-wedo-cyan")
    expect(container.innerHTML).not.toContain("bg-wedo-cyan")
  })
})
