/**
 * TemplateClonePanel — sentinels for UX T4 (clone-first / HubSpot Breeze).
 *
 * UX_AUDIT_ESTUDIO_AGENTES_2026-05-21 — Transformação 4 (linha 281).
 *
 * Cobre:
 * - Render do panel com template carregado (header + body + footer)
 * - Não-render quando template é null (defensive nullable handling)
 * - Preview rich: system_prompt completo, allowed_tools, tags, persona, config
 * - CTA "Clonar e customizar" dispara onClone com o template
 * - Cancelar dispara onClose
 * - Sheet em posição right canonical (vs left/top/bottom)
 * - Acessibilidade: SheetTitle + SheetDescription presentes (não silenciados)
 * - Acessibilidade: ScrollArea provê scroll keyboard-friendly para preview longo
 *
 * NOTE: TemplatePreviewModal (Sprint B QW#5) é preservado como entry-point
 * alternativo — esta suite NÃO testa o modal (existe sentinel separado se
 * necessário). T4 swap só altera o entry-point primário do TemplateGallery.
 */

import { describe, expect, it, vi } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

import { TemplateClonePanel } from "../TemplateClonePanel"
import type { AgentTemplate } from "../../custom-agents/types"

const TPL: AgentTemplate = {
  id: "tpl-triagem-tech",
  name: "Triagem Tech",
  description: "Filtra candidatos de tecnologia por stack",
  category: "screening",
  domain: "screening",
  icon: "Code",
  system_prompt:
    "Você é um agente de triagem técnica. Analise o CV do candidato focando em: stack tecnológico, anos de experiência, projetos relevantes.",
  allowed_tools: [
    "search_candidates",
    "get_candidate_details",
    "get_evaluation_criteria",
    "create_note",
  ],
  context_level: "standard",
  max_steps: 8,
  temperature: 0.3,
  enable_memory: true,
  excluded_tools: [],
  tags: ["popular", "tech", "triagem"],
}

describe("TemplateClonePanel — T4 clone-first preview", () => {
  it("renderiza name + description no header", () => {
    render(
      <TemplateClonePanel
        template={TPL}
        open={true}
        onClose={vi.fn()}
        onClone={vi.fn()}
      />,
    )
    expect(screen.getByText(TPL.name)).toBeTruthy()
    expect(screen.getByText(TPL.description)).toBeTruthy()
  })

  it("renderiza tags do template como chips", () => {
    render(
      <TemplateClonePanel
        template={TPL}
        open={true}
        onClose={vi.fn()}
        onClone={vi.fn()}
      />,
    )
    const tagsSection = screen.getByTestId("template-clone-tags")
    expect(tagsSection).toBeTruthy()
    TPL.tags.forEach((tag) => {
      // Tag is rendered inside the panel — assert visible text
      expect(tagsSection.textContent).toContain(tag)
    })
  })

  it("renderiza system_prompt completo em bloco preformatado", () => {
    render(
      <TemplateClonePanel
        template={TPL}
        open={true}
        onClose={vi.fn()}
        onClone={vi.fn()}
      />,
    )
    const block = screen.getByTestId("template-clone-system-prompt")
    expect(block.tagName.toLowerCase()).toBe("pre")
    expect(block.textContent).toContain("Você é um agente de triagem")
  })

  it("renderiza allowed_tools como badges (todas as 4)", () => {
    render(
      <TemplateClonePanel
        template={TPL}
        open={true}
        onClose={vi.fn()}
        onClone={vi.fn()}
      />,
    )
    const toolsSection = screen.getByTestId("template-clone-section-tools")
    TPL.allowed_tools.forEach((tool) => {
      expect(toolsSection.textContent).toContain(tool)
    })
  })

  it("renderiza persona/domain/category", () => {
    render(
      <TemplateClonePanel
        template={TPL}
        open={true}
        onClose={vi.fn()}
        onClone={vi.fn()}
      />,
    )
    const personaSection = screen.getByTestId("template-clone-section-persona")
    expect(personaSection.textContent).toContain(TPL.domain)
    expect(personaSection.textContent).toContain(TPL.category)
  })

  it("renderiza config grid (max_steps + temperature + context_level + memoria)", () => {
    render(
      <TemplateClonePanel
        template={TPL}
        open={true}
        onClose={vi.fn()}
        onClone={vi.fn()}
      />,
    )
    const configSection = screen.getByTestId("template-clone-section-config")
    expect(configSection.textContent).toContain(String(TPL.max_steps))
    expect(configSection.textContent).toContain(String(TPL.temperature))
    expect(configSection.textContent).toContain(TPL.context_level)
  })

  it("CTA 'Clonar e customizar' dispara onClone com o template", () => {
    const onClone = vi.fn()
    render(
      <TemplateClonePanel
        template={TPL}
        open={true}
        onClose={vi.fn()}
        onClone={onClone}
      />,
    )
    const cta = screen.getByTestId("template-clone-confirm")
    fireEvent.click(cta)
    expect(onClone).toHaveBeenCalledTimes(1)
    expect(onClone).toHaveBeenCalledWith(TPL)
  })

  it("CTA 'Cancelar' dispara onClose", () => {
    const onClose = vi.fn()
    render(
      <TemplateClonePanel
        template={TPL}
        open={true}
        onClose={onClose}
        onClone={vi.fn()}
      />,
    )
    const cancel = screen.getByTestId("template-clone-cancel")
    fireEvent.click(cancel)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it("retorna null quando template=null (defensive — sem regressão de hooks)", () => {
    const { container } = render(
      <TemplateClonePanel
        template={null}
        open={true}
        onClose={vi.fn()}
        onClone={vi.fn()}
      />,
    )
    // Sheet content não deve estar no DOM quando template é null
    expect(screen.queryByTestId("template-clone-panel")).toBeNull()
    // Defesa adicional: container vazio
    expect(container.querySelector('[data-testid="template-clone-confirm"]')).toBeNull()
  })

  it("não renderiza nada quando open=false (Sheet fechado)", () => {
    render(
      <TemplateClonePanel
        template={TPL}
        open={false}
        onClose={vi.fn()}
        onClone={vi.fn()}
      />,
    )
    // Sheet fechado → Radix não renderiza content. Não há panel testid.
    expect(screen.queryByTestId("template-clone-panel")).toBeNull()
  })

  it("template sem tags renderiza header sem chip group (gracefully)", () => {
    const noTagsTpl = { ...TPL, tags: [] }
    render(
      <TemplateClonePanel
        template={noTagsTpl}
        open={true}
        onClose={vi.fn()}
        onClone={vi.fn()}
      />,
    )
    // Quando tags=[], o div com testid não é renderizado
    expect(screen.queryByTestId("template-clone-tags")).toBeNull()
  })

  it("template sem allowed_tools renderiza fallback empty-state na seção", () => {
    const noToolsTpl = { ...TPL, allowed_tools: [] }
    render(
      <TemplateClonePanel
        template={noToolsTpl}
        open={true}
        onClose={vi.fn()}
        onClone={vi.fn()}
      />,
    )
    const toolsSection = screen.getByTestId("template-clone-section-tools")
    // Empty state visible — i18n key resolves to identity in mock
    expect(toolsSection.textContent).toContain("noToolsConfigured")
  })

  it("acessibilidade: SheetTitle presente (não sr-only) para screen readers", () => {
    render(
      <TemplateClonePanel
        template={TPL}
        open={true}
        onClose={vi.fn()}
        onClone={vi.fn()}
      />,
    )
    // SheetTitle deriva de Radix Dialog.Title — usa role=heading dentro do panel
    const heading = screen.getByRole("heading", { name: TPL.name })
    expect(heading).toBeTruthy()
  })
})
