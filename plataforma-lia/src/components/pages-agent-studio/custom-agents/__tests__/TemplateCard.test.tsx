/**
 * Sprint visual 2026-05-25 — TemplateCard refactor canonical tests.
 *
 * Sprint visual fixes:
 *  - Badge "Popular": cyan → wedo-purple (insight-purple #9860D1)
 *  - Consume <StudioCardShell> canonical
 *  - asButton (entire card clickable) com aria-label
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { TemplateCard } from "../TemplateCard"
import type { AgentTemplate } from "../types"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, vars?: Record<string, unknown>) => {
    if (vars && "count" in vars) return `${vars.count} tools`
    return key
  },
}))

const baseTemplate: AgentTemplate = {
  id: "tpl-1",
  name: "Recrutador Tech",
  description: "Template otimizado para vagas de engenharia",
  category: "recruiter" as AgentTemplate["category"],
  domain: "tech",
  icon: "Bot",
  system_prompt: "...",
  allowed_tools: ["search", "screen"],
  context_level: "basic" as AgentTemplate["context_level"],
  max_steps: 10,
  temperature: 0.7,
  enable_memory: false,
  excluded_tools: [],
  tags: ["popular"],
}

describe("TemplateCard — Sprint visual canonical refactor", () => {
  it("renderiza nome + descrição + meta categoria + count tools", () => {
    render(<TemplateCard template={baseTemplate} onSelect={vi.fn()} />)
    expect(screen.getByText("Recrutador Tech")).toBeTruthy()
    expect(screen.getByText("Template otimizado para vagas de engenharia")).toBeTruthy()
    expect(screen.getByText("2 tools")).toBeTruthy()
  })

  it("badge Popular usa wedo-purple (insight-purple), NÃO wedo-cyan", () => {
    const { container } = render(
      <TemplateCard template={baseTemplate} onSelect={vi.fn()} />,
    )
    const html = container.innerHTML
    // Insight purple #9860D1 mapeado para wedo-purple no Tailwind
    expect(html).toContain("wedo-purple")
    // White-label: NÃO usa cyan no Studio
    expect(html).not.toContain("badgeStyles.cyan")
    expect(html).not.toContain("bg-wedo-cyan/10")
  })

  it("onSelect chamado quando card clicado (asButton)", () => {
    const onSelect = vi.fn()
    render(<TemplateCard template={baseTemplate} onSelect={onSelect} />)
    const btn = screen.getByRole("button", { name: "Recrutador Tech" })
    fireEvent.click(btn)
    expect(onSelect).toHaveBeenCalledWith(baseTemplate)
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
