/**
 * P5 (Paulo 2026-05-30) — galeria de templates em 2 colunas (era 3).
 * Os cards ricos (descrição + capacidades + conversa) respiram melhor em 2 col.
 */
import { describe, expect, it, vi } from "vitest"
import { render } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useLocale: () => "pt",
  useTranslations: () => (key: string) => key,
}))

vi.mock("@/stores/agent-studio-store", () => ({
  useAgentStudioStore: () => ({
    activeCategory: "all",
    setActiveCategory: vi.fn(),
  }),
}))

vi.mock("@/hooks/agents/use-legacy-agent-templates", async () => {
  const { AGENT_TEMPLATES } = await import(
    "@/lib/__tests__/__fixtures__/agent-templates-fixture"
  )
  return {
    useLegacyAgentTemplates: () => ({
      templates: AGENT_TEMPLATES,
      isLoading: false,
      error: null,
    }),
  }
})

vi.mock("@/hooks/agents/use-agent-template-catalog", () => ({
  useAgentCategories: () => ({ data: [], isLoading: false, error: null, mutate: () => Promise.resolve() }),
  useAgentTemplateCatalog: () => ({ data: [], isLoading: false, error: null, mutate: () => Promise.resolve() }),
  useAgentSectors: () => ({ data: [], isLoading: false, error: null, mutate: () => Promise.resolve() }),
}))

import { TemplateGallery } from "../TemplateGallery"

describe("TemplateGallery — P5 grid 2 colunas", () => {
  it("usa lg:grid-cols-2 e não lg:grid-cols-3", () => {
    const { container } = render(
      <TemplateGallery onTemplateSelect={() => {}} />,
    )
    const grid = container.querySelector(".grid.grid-cols-1")
    expect(grid).toBeTruthy()
    const cls = grid?.className ?? ""
    expect(cls).toContain("lg:grid-cols-2")
    expect(cls).not.toContain("lg:grid-cols-3")
  })
})
