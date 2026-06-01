/**
 * HiringPoliciesHub tests — STRUCTURED surface + P3b instructions (2026-06-01)
 *
 * Pins: (1) structured policy block via MinhaEmpresaCard; (2) loading/error/
 * missing-block states; (3) rules-of-hooks rerender; (4) P3b — 11 free-text
 * instruction blocks render and respect RBAC read-only.
 */
import React from "react"
import { describe, test, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

const mockFetch = vi.fn()
global.fetch = mockFetch as unknown as typeof fetch

const mockUseCards = vi.fn()
vi.mock("@/hooks/settings/use-company-settings-cards", () => ({
  useCompanySettingsCards: () => mockUseCards(),
}))

const mockEditMode = vi.fn(() => ({ isEditing: true, canToggle: true, toggleEditMode: vi.fn(), setEditMode: vi.fn() }))
vi.mock("@/hooks/settings/useSettingsEditMode", () => ({ useSettingsEditMode: () => mockEditMode() }))
vi.mock("@/components/settings/SettingsEditModeToggle", () => ({ SettingsEditModeToggle: () => null }))

vi.mock("@/hooks/settings/useSettingsBroadcast", () => ({
  SETTINGS_QUERY_KEYS: { hiringPolicy: () => ["hiring-policy"] },
  dispatchSettingsUpdate: vi.fn(),
}))

vi.mock("@/components/settings/MinhaEmpresaCard", () => ({
  MinhaEmpresaCard: ({ block, isReadOnly }: { block: { key: string; fields: unknown[] }; isReadOnly: boolean }) => (
    <div data-testid="policy-card" data-block={block.key} data-fields={block.fields.length} data-readonly={String(isReadOnly)} />
  ),
}))

import { HiringPoliciesHub } from "../HiringPoliciesHub"

const POLICY_BLOCK = {
  key: "policy", title: "Políticas de Recrutamento", iconName: "FileText",
  fields: [
    { key: "min_interviews_before_offer", label: "Min?", value: 3, type: "number", editable: true, block: "policy" },
    { key: "auto_screening", label: "Auto?", value: true, type: "boolean", editable: true, block: "policy" },
  ],
  status: "partial", progress: { filled: 2, total: 2, missingLabels: [] },
}
const BASIC_BLOCK = { key: "basic", title: "Perfil", iconName: "Building", fields: [], status: "empty", progress: { filled: 0, total: 0, missingLabels: [] } }

function baseReturn(overrides: Record<string, unknown> = {}) {
  return {
    blocks: [POLICY_BLOCK, BASIC_BLOCK], benefits: [], companyId: "co-1",
    loading: false, error: null, recentlyUpdated: new Set<string>(),
    editingField: null, isSavingField: false,
    startEditing: vi.fn(), cancelEditing: vi.fn(), saveField: vi.fn(),
    refreshAll: vi.fn(), watchdogError: null, ...overrides,
  }
}

function renderHub() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(<QueryClientProvider client={qc}><HiringPoliciesHub /></QueryClientProvider>)
}

describe("HiringPoliciesHub (structured + instructions)", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockEditMode.mockReturnValue({ isEditing: true, canToggle: true, toggleEditMode: vi.fn(), setEditMode: vi.fn() })
    mockFetch.mockResolvedValue({ ok: true, status: 200, json: async () => ({ policy_instructions: {} }) })
  })

  test("renders the canonical structured policy block", () => {
    mockUseCards.mockReturnValue(baseReturn())
    renderHub()
    expect(screen.getByText("Políticas de Recrutamento")).toBeTruthy()
    const card = screen.getByTestId("policy-card")
    expect(card.getAttribute("data-block")).toBe("policy")
    expect(card.getAttribute("data-readonly")).toBe("false")
  })

  test("P3b: renders all 11 instruction blocks", async () => {
    mockUseCards.mockReturnValue(baseReturn())
    renderHub()
    await waitFor(() => {
      const KEYS = [
        "screening_criteria", "candidate_feedback_policy", "communication_window",
        "interview_scheduling_policy", "interview_reminder_policy", "no_show_policy",
        "salary_negotiation_policy", "remote_work_policy", "data_retention_candidate_policy",
        "talent_pool_opt_in_policy", "diversity_inclusion_guidelines",
      ]
      for (const k of KEYS) {
        expect(screen.getByTestId(`instruction-block-${k}`), `missing ${k}`).toBeTruthy()
      }
    })
  })

  test("P3b: instruction textareas disabled in read-only mode", async () => {
    mockEditMode.mockReturnValue({ isEditing: false, canToggle: false, toggleEditMode: vi.fn(), setEditMode: vi.fn() })
    mockUseCards.mockReturnValue(baseReturn())
    renderHub()
    await waitFor(() => {
      const ta = screen.getByTestId("instruction-block-no_show_policy").querySelector("textarea")
      expect(ta?.disabled).toBe(true)
    })
  })

  test("shows loading state", () => {
    mockUseCards.mockReturnValue(baseReturn({ loading: true }))
    renderHub()
    expect(screen.getByText(/Carregando políticas/i)).toBeTruthy()
  })

  test("shows error on watchdog error", () => {
    mockUseCards.mockReturnValue(baseReturn({ watchdogError: "Falha de rede" }))
    renderHub()
    expect(screen.getByText(/Falha de rede/i)).toBeTruthy()
  })

  test("shows error when policy block missing", () => {
    mockUseCards.mockReturnValue(baseReturn({ blocks: [BASIC_BLOCK] }))
    renderHub()
    expect(screen.getByText(/Bloco de políticas não encontrado/i)).toBeTruthy()
  })

  test("rules-of-hooks: rerender loading→loaded→loading without throw", () => {
    mockUseCards.mockReturnValue(baseReturn({ loading: true }))
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const { rerender } = render(<QueryClientProvider client={qc}><HiringPoliciesHub /></QueryClientProvider>)
    mockUseCards.mockReturnValue(baseReturn())
    expect(() => rerender(<QueryClientProvider client={qc}><HiringPoliciesHub /></QueryClientProvider>)).not.toThrow()
    mockUseCards.mockReturnValue(baseReturn({ loading: true }))
    expect(() => rerender(<QueryClientProvider client={qc}><HiringPoliciesHub /></QueryClientProvider>)).not.toThrow()
  })
})
