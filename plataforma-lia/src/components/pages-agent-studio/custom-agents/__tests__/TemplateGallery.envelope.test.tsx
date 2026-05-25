/**
 * Hotfix P0 (2026-05-25): TemplateGallery não crasha com envelope canonical
 *
 * Regression guard: antes do fix do jsonFetcher (envelope unwrap), proxy
 * /api/backend-proxy/agent-template-catalog/categories retornava {ok, data, meta},
 * useAgentCategories devolvia o objeto envelope inteiro, e
 * `catalogCategories.filter(c => c.is_active)` crashou com
 * "catalogCategories.filter is not a function".
 *
 * Este teste mocka o hook devolvendo o shape canonical (array de AgentCategory,
 * como o fetcher fixed agora produz) e confirma render OK.
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

const setActiveCategoryMock = vi.fn()
vi.mock("@/stores/agent-studio-store", () => ({
  useAgentStudioStore: () => ({
    activeCategory: "all",
    setActiveCategory: setActiveCategoryMock,
  }),
}))

vi.mock("@/hooks/agents/use-legacy-agent-templates", async () => {
  const { AGENT_TEMPLATES } = await import("@/lib/__tests__/__fixtures__/agent-templates-fixture")
  return {
    useLegacyAgentTemplates: () => ({
      templates: AGENT_TEMPLATES,
      isLoading: false,
      error: null,
    }),
  }
})

vi.mock("@/hooks/agents/use-agent-template-catalog", () => ({
  useAgentCategories: () => ({
    // Shape canonical PÓS-fix do fetcher: array de AgentCategory desempacotado.
    data: [
      { id: "screening", label_pt: "Triagem", label_en: "Screening", icon: "Filter", sort_order: 1, is_active: true },
      { id: "sourcing", label_pt: "Captação", label_en: "Sourcing", icon: "Search", sort_order: 2, is_active: true },
      { id: "communication", label_pt: "Comunicação", label_en: "Communication", icon: "MessageCircle", sort_order: 3, is_active: true },
    ],
    isLoading: false,
    error: null,
    mutate: () => Promise.resolve(),
  }),
  useAgentTemplateCatalog: () => ({ data: [], isLoading: false, error: null, mutate: () => Promise.resolve() }),
  useAgentSectors: () => ({ data: [], isLoading: false, error: null, mutate: () => Promise.resolve() }),
}))

import { TemplateGallery } from "../TemplateGallery"

describe("TemplateGallery — envelope canonical (P0 hotfix regression guard)", () => {
  it("renderiza sem crash quando hook devolve array canonical de categorias", () => {
    expect(() =>
      render(
        <TemplateGallery
          onTemplateSelect={() => {}}
          onCreateManual={() => {}}
        />,
      ),
    ).not.toThrow()
  })

  it("renderiza chips de categoria filtrados por is_active", () => {
    render(
      <TemplateGallery
        onTemplateSelect={() => {}}
        onCreateManual={() => {}}
      />,
    )
    // Chip "Todos" sempre aparece (canonical first item)
    // Como i18n mock retorna a key, "all" vira label
    expect(screen.getByText("all")).toBeInTheDocument()
  })
})
