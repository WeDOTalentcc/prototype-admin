/**
 * Studio Restructure Fase 1 — TDD Red.
 *
 * Pin: TemplateGallery DEVE apresentar labels visíveis "Tipo:" e "Vertical:"
 * antes das pills correspondentes. Hoje as pills aparecem sem label de prefixo.
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
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
  useAgentCategories: () => ({
    data: [
      { id: "screening", label_pt: "Triagem", label_en: "Screening", icon: "Filter", sort_order: 1, is_active: true },
      { id: "sourcing", label_pt: "Captação", label_en: "Sourcing", icon: "Search", sort_order: 2, is_active: true },
    ],
    isLoading: false,
    error: null,
    mutate: () => Promise.resolve(),
  }),
  useAgentTemplateCatalog: () => ({ data: [], isLoading: false, error: null, mutate: () => Promise.resolve() }),
  useAgentSectors: () => ({ data: [], isLoading: false, error: null, mutate: () => Promise.resolve() }),
}))

import { TemplateGallery } from "../TemplateGallery"

function renderGallery() {
  return render(
    <TemplateGallery
      onTemplateSelect={() => {}}
      onCreateManual={() => {}}
    />,
  )
}

describe("TemplateGallery — Studio Restructure Fase 1 labels", () => {
  it("apresenta label visível 'Tipo:' antes das pills de categoria", () => {
    renderGallery()
    const label = screen.getByText(/^Tipo:?$/i)
    expect(label).toBeTruthy()
    // Label vem ANTES das pills de filtro de categoria
    const categoryFilters = screen.queryByTestId("template-category-filter")
      || screen.getAllByRole("button").find((b) => /screening|sourcing|all/i.test(b.getAttribute("data-testid") ?? ""))
    if (categoryFilters) {
      const labelPos = label.compareDocumentPosition(categoryFilters)
      // DOCUMENT_POSITION_FOLLOWING = 0x04
      expect(labelPos & 0x04).toBeTruthy()
    }
  })

  it("apresenta label visível 'Vertical:' antes das pills de vertical", () => {
    renderGallery()
    const label = screen.getByText(/^Vertical:?$/i)
    expect(label).toBeTruthy()
    const verticalContainer = screen.getByTestId("template-vertical-filter")
    const labelPos = label.compareDocumentPosition(verticalContainer)
    expect(labelPos & 0x04).toBeTruthy()
  })
})
