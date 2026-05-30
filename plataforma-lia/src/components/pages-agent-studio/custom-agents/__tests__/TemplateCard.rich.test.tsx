/**
 * Redesign 2026-05-30 — TemplateCard didático (crítica do recrutador).
 *
 * Descrição herói (sem truncação) + capacidades de alto nível em PT
 * (summarizeCapabilities) + metadado discreto traduzido (Análise · etapas) +
 * nota sutil "Ajuste ao seu processo antes de ativar" + 3 botões
 * ("Usar agora" primary / "Ajustar antes" secondary / "Ver detalhes" ghost).
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { TemplateCard } from "../TemplateCard"
import type { AgentTemplate } from "../types"

vi.mock("next-intl", () => ({
  useTranslations: (ns?: string) => (key: string, vars?: Record<string, unknown>) => {
    // Resolve a string de etapas com o count interpolado.
    if (key === "stepsValue" && vars && "count" in vars) {
      return `Processa até ${vars.count} etapas`
    }
    // Echo namespaced key suffix for readability assertions.
    return ns ? `${ns}.${key}` : key
  },
}))

const baseTemplate: AgentTemplate = {
  id: "tpl-rich-1",
  name: "Recrutador Rich",
  description: "Template com layout rico que explica o que o agente faz para o recrutador",
  category: "screening" as AgentTemplate["category"],
  domain: "tech",
  icon: "Bot",
  system_prompt: "...",
  allowed_tools: ["search_candidates", "get_candidate_details", "create_note"],
  context_level: "standard",
  max_steps: 12,
  temperature: 0.7,
  enable_memory: false,
  excluded_tools: [],
  tags: ["popular"],
}

describe("TemplateCard — redesign recrutador-friendly", () => {
  it("renderiza descrição completa (herói, sem line-clamp)", () => {
    render(<TemplateCard template={baseTemplate} onSelect={vi.fn()} />)
    expect(screen.getByText(baseTemplate.description)).toBeTruthy()
  })

  it("renderiza capacidades de alto nível em PT (não nomes técnicos de tools)", () => {
    const { container } = render(
      <TemplateCard template={baseTemplate} onSelect={vi.fn()} />,
    )
    const html = container.innerHTML
    // Capacidades narrativas em PT presentes.
    expect(html).toContain("Encontra os candidatos certos para a vaga")
    expect(html).toContain("Analisa perfis com base nos seus critérios")
    // Nomes técnicos crus NÃO aparecem.
    expect(html).not.toContain("search_candidates")
    expect(html).not.toContain("get_candidate_details")
    expect(html).not.toContain("create_note")
  })

  it("renderiza metadado discreto traduzido (Análise + etapas com count)", () => {
    const { container } = render(
      <TemplateCard template={baseTemplate} onSelect={vi.fn()} />,
    )
    const html = container.innerHTML
    // depthEyebrow + depthValue.standard via mock echo.
    expect(html).toContain("depthEyebrow")
    expect(html).toContain("depthValue.standard")
    // stepsValue resolvido com count=12.
    expect(html).toContain("Processa até 12 etapas")
  })

  it("renderiza nota sutil de personalização", () => {
    const { container } = render(
      <TemplateCard template={baseTemplate} onSelect={vi.fn()} />,
    )
    expect(container.innerHTML).toContain("alert.personalize")
  })

  it("renderiza 3 botões com data-testid únicos (use + customize + preview)", () => {
    render(<TemplateCard template={baseTemplate} onSelect={vi.fn()} />)
    expect(screen.getByTestId(`template-card-use-${baseTemplate.id}`)).toBeTruthy()
    expect(screen.getByTestId(`template-card-customize-${baseTemplate.id}`)).toBeTruthy()
    expect(screen.getByTestId(`template-card-preview-${baseTemplate.id}`)).toBeTruthy()
  })

  it("badge Popular renderiza wedo-purple (NÃO wedo-cyan)", () => {
    const { container } = render(
      <TemplateCard template={baseTemplate} onSelect={vi.fn()} />,
    )
    const html = container.innerHTML
    expect(html).toContain("wedo-purple")
    expect(html).not.toContain("bg-wedo-cyan")
  })

  it("onSelect chamado em 'Usar agora'; customize/preview usam onSelect como fallback", () => {
    const onSelect = vi.fn()
    render(<TemplateCard template={baseTemplate} onSelect={onSelect} />)
    fireEvent.click(screen.getByTestId(`template-card-use-${baseTemplate.id}`))
    expect(onSelect).toHaveBeenCalledTimes(1)
    expect(onSelect).toHaveBeenCalledWith(baseTemplate)

    fireEvent.click(screen.getByTestId(`template-card-customize-${baseTemplate.id}`))
    expect(onSelect).toHaveBeenCalledTimes(2)

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

  it("NÃO usa wedo-cyan no markup (white-label Studio + LIA Cyan Exclusivity)", () => {
    const { container } = render(
      <TemplateCard template={baseTemplate} onSelect={vi.fn()} />,
    )
    expect(container.innerHTML).not.toContain("text-wedo-cyan")
    expect(container.innerHTML).not.toContain("bg-wedo-cyan")
  })
})
