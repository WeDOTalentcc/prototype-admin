/**
 * T5b UX Transformação 5 — TemplateGallery vertical filter sentinels
 *
 * Cobre:
 * - Renderiza 6 vertical filter chips (All, Tech, Health, Education, Retail, Generic)
 * - Filtro "Tech" mostra apenas templates com vertical="tech"
 * - Filtro "Health" mostra apenas templates com vertical="health"
 * - Filtro "Generic" mostra apenas templates sem vertical (null)
 * - Filtro "All" mostra todos os templates
 * - WCAG 2.2 AA: chips têm aria-pressed + role group + aria-label
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { fireEvent, render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useLocale: () => "pt",
  useTranslations: () => (key: string) => key,
}))

// Mock the agent-studio-store
const setActiveCategoryMock = vi.fn()
vi.mock("@/stores/agent-studio-store", () => ({
  useAgentStudioStore: () => ({
    activeCategory: "all",
    setActiveCategory: setActiveCategoryMock,
  }),
}))

// Sprint 3 Parte 2: mock catalog hooks so render uses fixture (sem fetch real).
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
    data: [
      { id: "screening", label_pt: "Triagem", label_en: "Screening", icon: "Filter", sort_order: 1, is_active: true },
      { id: "sourcing", label_pt: "Captação", label_en: "Sourcing", icon: "Search", sort_order: 2, is_active: true },
      { id: "communication", label_pt: "Comunicação", label_en: "Communication", icon: "MessageCircle", sort_order: 3, is_active: true },
      { id: "analytics", label_pt: "Análise", label_en: "Analytics", icon: "BarChart3", sort_order: 4, is_active: true },
      { id: "job_management", label_pt: "Vagas", label_en: "Jobs", icon: "Briefcase", sort_order: 5, is_active: true },
      { id: "automation", label_pt: "Automação", label_en: "Automation", icon: "Zap", sort_order: 6, is_active: true },
    ],
    isLoading: false,
    error: null,
    mutate: () => Promise.resolve(),
  }),
  useAgentTemplateCatalog: () => ({ data: [], isLoading: false, error: null, mutate: () => Promise.resolve() }),
  useAgentSectors: () => ({ data: [], isLoading: false, error: null, mutate: () => Promise.resolve() }),
}))

import { TemplateGallery } from "../TemplateGallery"
import { AGENT_TEMPLATES } from "@/lib/__tests__/__fixtures__/agent-templates-fixture"

function renderGallery() {
  return render(
    <TemplateGallery
      onTemplateSelect={() => {}}
      onCreateManual={() => {}}
    />,
  )
}

describe("TemplateGallery — vertical filter (T5b UX Transformação 5)", () => {
  beforeEach(() => {
    setActiveCategoryMock.mockClear()
  })

  it("renderiza 6 chips de filtro vertical (All + 4 verticals + Generic)", () => {
    renderGallery()
    expect(screen.getByTestId("vertical-filter-all")).toBeInTheDocument()
    expect(screen.getByTestId("vertical-filter-tech")).toBeInTheDocument()
    expect(screen.getByTestId("vertical-filter-health")).toBeInTheDocument()
    expect(screen.getByTestId("vertical-filter-education")).toBeInTheDocument()
    expect(screen.getByTestId("vertical-filter-retail")).toBeInTheDocument()
    expect(screen.getByTestId("vertical-filter-generic")).toBeInTheDocument()
  })

  it("WCAG 2.2 AA: container vertical filter tem role=group + aria-label", () => {
    renderGallery()
    const container = screen.getByTestId("template-vertical-filter")
    expect(container.getAttribute("role")).toBe("group")
    expect(container.getAttribute("aria-label")).toBeTruthy()
  })

  it("WCAG 2.2 AA: chips usam aria-pressed para estado ativo", () => {
    renderGallery()
    const allBtn = screen.getByTestId("vertical-filter-all")
    // Default = "all" ativo
    expect(allBtn.getAttribute("aria-pressed")).toBe("true")

    const techBtn = screen.getByTestId("vertical-filter-tech")
    expect(techBtn.getAttribute("aria-pressed")).toBe("false")
  })

  it("Filtro 'Tech' mostra apenas templates com vertical=tech", () => {
    renderGallery()
    fireEvent.click(screen.getByTestId("vertical-filter-tech"))
    // Tech templates: tpl-triagem-tech (Triagem Tech)
    expect(screen.getByText("Triagem Tech")).toBeInTheDocument()
    // Generic templates should NOT appear
    expect(screen.queryByText("Sourcing Passivo")).not.toBeInTheDocument()
    expect(screen.queryByText("Talent Pool Curator")).not.toBeInTheDocument()
  })

  it("Filtro 'Health' mostra apenas templates com vertical=health", () => {
    renderGallery()
    fireEvent.click(screen.getByTestId("vertical-filter-health"))
    // Health templates: tpl-onboarding-prep (Onboarding Prep)
    expect(screen.getByText("Onboarding Prep")).toBeInTheDocument()
    expect(screen.queryByText("Triagem Tech")).not.toBeInTheDocument()
  })

  it("Filtro 'Education' mostra apenas templates com vertical=education", () => {
    renderGallery()
    fireEvent.click(screen.getByTestId("vertical-filter-education"))
    // Education templates: tpl-compliance-check (Compliance Check)
    expect(screen.getByText("Compliance Check")).toBeInTheDocument()
    expect(screen.queryByText("Triagem Tech")).not.toBeInTheDocument()
  })

  it("Filtro 'Retail' mostra apenas templates com vertical=retail", () => {
    renderGallery()
    fireEvent.click(screen.getByTestId("vertical-filter-retail"))
    // Retail templates: tpl-triagem-volume (Triagem Volume)
    expect(screen.getByText("Triagem Volume")).toBeInTheDocument()
    expect(screen.queryByText("Triagem Tech")).not.toBeInTheDocument()
  })

  it("Filtro 'Generic' mostra apenas templates SEM vertical (null)", () => {
    renderGallery()
    fireEvent.click(screen.getByTestId("vertical-filter-generic"))
    // Generic templates (sem vertical industry)
    expect(screen.getByText("Sourcing Passivo")).toBeInTheDocument()
    expect(screen.getByText("Talent Pool Curator")).toBeInTheDocument()
    // Specialized templates should NOT appear
    expect(screen.queryByText("Triagem Tech")).not.toBeInTheDocument()
    expect(screen.queryByText("Onboarding Prep")).not.toBeInTheDocument()
  })

  it("Filtro 'Todos' (default) mostra todos os templates", () => {
    renderGallery()
    // Already on "all" by default
    const allTemplates = AGENT_TEMPLATES.length
    expect(allTemplates).toBeGreaterThan(10)
    // Both specialized and generic should be visible
    expect(screen.getByText("Triagem Tech")).toBeInTheDocument()
    expect(screen.getByText("Sourcing Passivo")).toBeInTheDocument()
  })
})
