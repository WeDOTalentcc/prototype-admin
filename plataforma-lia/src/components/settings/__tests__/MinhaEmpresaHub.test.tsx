/**
 * Smoke tests — MinhaEmpresaHub (Sprint 1 Hardening 2026-05-26)
 *
 * Detecta regressão de rules-of-hooks: early returns ANTES de hooks
 * crasham a UI quando activeSubsection muda entre renders.
 * Padrão idêntico ao bug BulkImportModal de 2026-05-04.
 */
import React from "react"
import { describe, test, expect, vi, beforeEach } from "vitest"
import { render, act } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import { MinhaEmpresaHub } from "../MinhaEmpresaHub"

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock("@/hooks/settings/use-company-settings-cards", () => ({
  useCompanySettingsCards: () => ({
    blocks: [],
    benefits: [],
    companyId: "test-company-123",
    loading: false,
    error: null,
    successMessage: null,
    overallProgress: 50,
    expandedBlocks: new Set<string>(),
    recentlyUpdated: new Set<string>(),
    editingField: null,
    isSavingField: false,
    toggleBlock: vi.fn(),
    startEditing: vi.fn(),
    cancelEditing: vi.fn(),
    saveField: vi.fn(),
    refreshAll: vi.fn(),
  }),
}))

vi.mock("@/hooks/settings/use-settings-conversational", () => ({
  useSettingsConversational: () => ({
    triggerAction: vi.fn(),
    triggerPrefillSection: vi.fn(),
  }),
}))

vi.mock("@/contexts/lia-float-context", () => ({
  useLiaChatContext: () => ({
    setChatMessages: vi.fn(),
  }),
}))

vi.mock("@/components/settings/LearningLoopsPanel", () => ({
  LearningLoopsPanel: () => <div data-testid="learning-loops-panel">LearningLoops</div>,
}))

vi.mock("@/components/settings/LiaFieldsConfigPanel", () => ({
  LiaFieldsConfigPanel: () => <div data-testid="lia-fields-panel">LiaFields</div>,
}))

vi.mock("@/components/settings/AnalyzeWebsiteModal", () => ({
  AnalyzeWebsiteModal: () => null,
}))

vi.mock("@/components/settings/CultureApprovalBanner", () => ({
  // Fase 5.1 (outra sessao) trouxe React Query; mock evita 'No QueryClient'
  CultureApprovalBanner: () => null,
}))

vi.mock("@/components/settings/SettingsEditModeToggle", () => ({
  SettingsEditModeToggle: () => <div data-testid="settings-edit-mode-toggle-mock" />,
}))

// Sprint B.7 (2026-05-26): Hub agora chama useSettingsEditMode → useAuth.
// Mockar hook canonical para isolar smoke test de provider deps.
vi.mock("@/hooks/settings/useSettingsEditMode", () => ({
  useSettingsEditMode: () => ({
    isEditing: true,
    canToggle: true,
    toggleEditMode: vi.fn(),
    setEditMode: vi.fn(),
  }),
}))

// Sprint B.7 (2026-05-26): captura prop `isReadOnly` para validar wiring.
const cardPropsCaptured: Array<{ isReadOnly?: boolean }> = []
vi.mock("@/components/settings/MinhaEmpresaCard", () => ({
  MinhaEmpresaCard: (props: { isReadOnly?: boolean }) => {
    cardPropsCaptured.push({ isReadOnly: props.isReadOnly })
    return <div data-testid="minha-empresa-card">Card</div>
  },
}))

vi.mock("@/components/unified-chat/website-proposal-injector", () => ({
  buildWebsiteProposalMessage: vi.fn(() => ({ role: "assistant", content: "test" })),
}))

// ── Messages ─────────────────────────────────────────────────────────────────
const MESSAGES = {
  settings: {
    minhaEmpresa: {
      title: "Minha Empresa",
      description: "Configure os dados da empresa",
      loading: "Carregando...",
      loadingCompanyData: "Carregando dados...",
      analyzeWebsite: "Analisar site",
      analyzeWebsiteTitle: "Analisar nosso site",
      refreshData: "Atualizar",
      configuredSuffix: "{progress}% configurado",
      profileCompletePending: "{progress}% — {count} campo(s) pendente(s)",
      sectionsToReview: "{count} seção(ões)",
      almostComplete: "Quase completo",
      askLiaShort: "Pedir à LIA",
      askLiaToFillTitle: "Pedir à LIA para preencher {section}",
    },
  },
}

function wrap(activeSubsection?: string) {
  return (
    <NextIntlClientProvider locale="pt-BR" messages={MESSAGES}>
      <MinhaEmpresaHub activeSubsection={activeSubsection} />
    </NextIntlClientProvider>
  )
}

// ── Testes ───────────────────────────────────────────────────────────────────
describe("MinhaEmpresaHub — smoke rerender (rules-of-hooks)", () => {
  beforeEach(() => { vi.clearAllMocks() })

  test("mount sem activeSubsection não lança", () => {
    expect(() => render(wrap(undefined))).not.toThrow()
  })

  test("mount com activeSubsection='learning-loops' não lança", () => {
    expect(() => render(wrap("learning-loops"))).not.toThrow()
  })

  test("rerender '' → 'learning-loops' → 'instrucoes-lia' não lança (detecta rules-of-hooks regression)", () => {
    const { rerender } = render(wrap(undefined))

    expect(() => act(() => { rerender(wrap("learning-loops")) })).not.toThrow()
    expect(() => act(() => { rerender(wrap("instrucoes-lia")) })).not.toThrow()
    expect(() => act(() => { rerender(wrap(undefined)) })).not.toThrow()
  })
})
