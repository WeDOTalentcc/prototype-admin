/**
 * Sprint visual 2026-05-25 — TemplateCard refactor canonical tests.
 *
 * Sprint visual 2026-05-26 — promoted to rich layout (3 metrics + alert + 3 buttons).
 * Layout assertions movidos para TemplateCard.rich.test.tsx; este arquivo
 * mantem apenas testes de identidade/branding que continuam validos.
 *
 * Sprint visual fixes:
 *  - Badge "Popular": cyan → wedo-purple (insight-purple #9860D1)
 *  - Consume <StudioCardShell> canonical
 *  - White-label: NUNCA cyan no Studio
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { TemplateCard } from "../TemplateCard"
import type { AgentTemplate } from "../types"

vi.mock("next-intl", () => ({
  useLocale: () => "pt",
  useTranslations: () => (key: string, vars?: Record<string, unknown>) => {
    if (vars && "count" in vars) return `${vars.count} tools`
    return key
  },
}))

const baseTemplate: AgentTemplate = {
  id: "tpl-1",
  name: "Recrutador Tech",
  description: "Template otimizado para vagas de engenharia",
  category: "screening" as AgentTemplate["category"],
  domain: "tech",
  icon: "Bot",
  system_prompt: "...",
  allowed_tools: ["search", "screen"],
  context_level: "standard",
  max_steps: 10,
  temperature: 0.7,
  enable_memory: false,
  excluded_tools: [],
  tags: ["popular"],
}

describe("TemplateCard — Sprint visual identity/branding", () => {
  it("renderiza nome + descrição", () => {
    render(<TemplateCard template={baseTemplate} onSelect={vi.fn()} />)
    expect(screen.getByText("Recrutador Tech")).toBeTruthy()
    expect(screen.getByText("Template otimizado para vagas de engenharia")).toBeTruthy()
  })

  it("badge Popular usa wedo-purple (insight-purple), NÃO wedo-cyan", () => {
    const { container } = render(
      <TemplateCard template={baseTemplate} onSelect={vi.fn()} />,
    )
    const html = container.innerHTML
    expect(html).toContain("wedo-purple")
    expect(html).not.toContain("badgeStyles.cyan")
    expect(html).not.toContain("bg-wedo-cyan/10")
  })

  it("não renderiza badge Popular quando tag ausente", () => {
    const { container } = render(
      <TemplateCard
        template={{ ...baseTemplate, tags: [] }}
        onSelect={vi.fn()}
      />,
    )
    expect(container.innerHTML).not.toContain("popular")
  })
})
