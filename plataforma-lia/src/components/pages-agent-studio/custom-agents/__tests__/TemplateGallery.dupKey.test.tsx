/**
 * Regression test 2026-05-26 — duplicate key 'all' bug.
 *
 * Bug history: backend migration 199 seedou categoria "all" + frontend hardcoded
 * "Todos" como primeiro chip = React renderou 2 chips com key="all" + console
 * warning "Encountered two children with the same key, 'all'".
 *
 * Fix: migration 206 removeu "all" do backend; frontend mantem chip hardcoded.
 *
 * Sensor: assert que apenas UM chip com key/id "all" eh renderizado quando o
 * hook retorna catalogo SEM "all" pseudo-categoria (state pos-migration 206).
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"

// Mock catalog hook — simulates POST-migration-206 backend (no "all" row)
vi.mock("@/hooks/agents/use-agent-template-catalog", () => ({
  useAgentCategories: () => ({
    data: [
      { id: "screening", label_pt: "Triagem", label_en: "Screening", icon: "Search", sort_order: 1, is_active: true },
      { id: "sourcing", label_pt: "Captacao", label_en: "Sourcing", icon: "Users", sort_order: 2, is_active: true },
      { id: "communication", label_pt: "Comunicacao", label_en: "Communication", icon: "MessageSquare", sort_order: 3, is_active: true },
    ],
    isLoading: false,
    error: null,
  }),
}))

vi.mock("@/hooks/agents/use-legacy-agent-templates", () => ({
  useLegacyAgentTemplates: () => ({
    templates: [],
    isLoading: false,
    error: null,
  }),
}))

vi.mock("@/stores/agent-studio-store", () => ({
  useAgentStudioStore: () => ({
    activeCategory: "all",
    setActiveCategory: vi.fn(),
  }),
}))

const messages = {
  agents: {
    customAgents: {
      searchPlaceholder: "Buscar...",
      verticalFilterAriaLabel: "Filtrar verticais",
      verticalAll: "Todos",
      verticalTech: "Tech",
      verticalHealth: "Health",
      verticalEducation: "Education",
      verticalRetail: "Retail",
      verticalGeneric: "Generic",
      empty: "Nenhum template",
      templateCategories: {
        all: "Todos",
        screening: "Triagem",
        sourcing: "Captacao",
        communication: "Comunicacao",
      },
    },
  },
}

import { TemplateGallery } from "../TemplateGallery"

describe("TemplateGallery — duplicate key 'all' regression (2026-05-26)", () => {
  it("renders only ONE chip with id='all' (hardcoded Todos + no backend dup)", () => {
    const warnSpy = vi.spyOn(console, "error").mockImplementation(() => {})

    render(
      <NextIntlClientProvider locale="pt-BR" messages={messages as any}>
        <TemplateGallery onTemplateSelect={vi.fn()} onCreateManual={vi.fn()} />
      </NextIntlClientProvider>,
    )

    // No React "duplicate key" warning fired
    const dupWarnings = warnSpy.mock.calls.filter((args) =>
      args.some((a) => typeof a === "string" && /duplicate.*key|same key/i.test(a)),
    )
    expect(dupWarnings).toHaveLength(0)

    warnSpy.mockRestore()
  })
})
