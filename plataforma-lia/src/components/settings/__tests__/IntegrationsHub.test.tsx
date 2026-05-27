/**
 * Smoke tests — IntegrationsHub
 *
 * Escopo mínimo: verificar que o componente monta e não lança para as
 * variações de activeSubsection esperadas. Não testa internals de cada
 * integração (esses ficam em testes dedicados por widget).
 *
 * Harness: todos os fetches + hooks de dados são mockados.
 * Pattern: alinhado com MinhaEmpresaHub.test.tsx.
 */
import React from "react"
import { render } from "@testing-library/react"
import { describe, it, vi, beforeAll } from "vitest"

// ── shims jsdom ────────────────────────────────────────────────────────────
beforeAll(() => {
  if (typeof window !== "undefined" && !window.matchMedia) {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: (query: string) => ({
        matches: false, media: query, onchange: null,
        addEventListener: () => {}, removeEventListener: () => {},
        addListener: () => {}, removeListener: () => {},
        dispatchEvent: () => false,
      }),
    })
  }
})

// ── mocks ──────────────────────────────────────────────────────────────────
vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

vi.mock("@/hooks/company/use-current-company", () => ({
  useCurrentCompany: () => ({ companyId: "test-co", tenantId: "test-co" }),
}))

// Mock the canonical server-data hook (Task 3.3 extraction)
vi.mock("@/hooks/integrations/use-integrations-data", () => ({
  useIntegrationsData: () => ({
    enrichedIntegrations: [],
    catalogLoading: false,
    googleStatus: "idle",
    microsoftStatus: "not_configured",
    teamsStatus: "not_configured",
    llmConfig: null,
    refetchLlmConfig: vi.fn(),
  }),
}))

vi.mock("@/lib/api/api-fetch", () => ({
  apiFetch: vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) }),
}))

// Stub sub-components that would trigger heavy rendering / more fetches
vi.mock("@/components/settings/integrations/IntegrationCard", () => ({
  IntegrationCard: () => <div data-testid="integration-card-stub" />,
}))

vi.mock("@/components/settings/integrations/IntegrationDetailModal", () => ({
  IntegrationDetailModal: () => <div data-testid="integration-modal-stub" />,
}))

vi.mock("@/components/settings/integrations/IntegrationGrid", () => ({
  IntegrationGrid: () => <div data-testid="integration-grid-stub" />,
}))

// integration-data is a pure constants file — import as-is (no mock needed)

import { IntegrationsHub } from "@/components/settings/IntegrationsHub"

describe("IntegrationsHub — smoke rerender (rules-of-hooks + mount)", () => {
  it("monta sem activeSubsection sem lançar", () => {
    const { unmount } = render(<IntegrationsHub activeSubsection="" />)
    unmount()
  })

  it("monta com activeSubsection=i-models\ sem lançar", () => {
    const { unmount } = render(<IntegrationsHub activeSubsection="ai-models" />)
    unmount()
  })

  it("rerenderiza entre subsections sem lançar (detecta rules-of-hooks regression)", () => {
    const { rerender, unmount } = render(<IntegrationsHub activeSubsection="" />)
    rerender(<IntegrationsHub activeSubsection="ats" />)
    rerender(<IntegrationsHub activeSubsection="calendar" />)
    rerender(<IntegrationsHub activeSubsection="" />)
    unmount()
  })
})
