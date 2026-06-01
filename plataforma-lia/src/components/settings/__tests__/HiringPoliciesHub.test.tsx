/**
 * HiringPoliciesHub tests — STRUCTURED surface (P1 dedup, 2026-06-01)
 *
 * Rewritten from the narrative (18-Textarea) version. The hub is now the
 * canonical structured Políticas surface: it reuses the "policy" block from
 * useCompanySettingsCards + MinhaEmpresaCard (typed editors). These tests pin:
 *  1. Renders the policy block via MinhaEmpresaCard with the right props.
 *  2. Loading / watchdog-error / missing-block states.
 *  3. rules-of-hooks: rerender loading→loaded→loading without throw.
 *
 * MinhaEmpresaCard is mocked — it has its own suite (MinhaEmpresaCard.test.tsx);
 * here we only assert the hub selects the policy block and wires it correctly.
 */
import React from "react"
import { describe, test, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"

const mockUseCards = vi.fn()
vi.mock("@/hooks/settings/use-company-settings-cards", () => ({
  useCompanySettingsCards: () => mockUseCards(),
}))

vi.mock("@/components/settings/MinhaEmpresaCard", () => ({
  MinhaEmpresaCard: ({
    block,
    isReadOnly,
  }: {
    block: { key: string; fields: unknown[] }
    isReadOnly: boolean
  }) => (
    <div
      data-testid="policy-card"
      data-block={block.key}
      data-fields={block.fields.length}
      data-readonly={String(isReadOnly)}
    />
  ),
}))

const mockEditMode = vi.fn(() => ({
  isEditing: true,
  canToggle: true,
  toggleEditMode: vi.fn(),
  setEditMode: vi.fn(),
}))
vi.mock("@/hooks/settings/useSettingsEditMode", () => ({
  useSettingsEditMode: () => mockEditMode(),
}))
vi.mock("@/components/settings/SettingsEditModeToggle", () => ({
  SettingsEditModeToggle: () => null,
}))

import { HiringPoliciesHub } from "../HiringPoliciesHub"

const POLICY_BLOCK = {
  key: "policy",
  title: "Políticas de Recrutamento",
  iconName: "FileText",
  fields: [
    { key: "min_interviews_before_offer", label: "Min entrevistas?", value: 3, type: "number", editable: true, block: "policy" },
    { key: "auto_screening", label: "Triagem automática?", value: true, type: "boolean", editable: true, block: "policy" },
  ],
  status: "partial",
  progress: { filled: 2, total: 2, missingLabels: [] },
}

const BASIC_BLOCK = {
  key: "basic",
  title: "Perfil",
  iconName: "Building",
  fields: [],
  status: "empty",
  progress: { filled: 0, total: 0, missingLabels: [] },
}

function baseReturn(overrides: Record<string, unknown> = {}) {
  return {
    blocks: [POLICY_BLOCK, BASIC_BLOCK],
    benefits: [],
    companyId: "co-1",
    loading: false,
    error: null,
    recentlyUpdated: new Set<string>(),
    editingField: null,
    isSavingField: false,
    startEditing: vi.fn(),
    cancelEditing: vi.fn(),
    saveField: vi.fn(),
    refreshAll: vi.fn(),
    watchdogError: null,
    ...overrides,
  }
}

describe("HiringPoliciesHub (structured)", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test("renders the canonical structured policy block", () => {
    mockUseCards.mockReturnValue(baseReturn())
    render(<HiringPoliciesHub />)
    expect(screen.getByText("Políticas de Recrutamento")).toBeTruthy()
    const card = screen.getByTestId("policy-card")
    expect(card.getAttribute("data-block")).toBe("policy")
    expect(card.getAttribute("data-fields")).toBe("2")
    // Standalone hub is editable (no RBAC gate yet — parity with prior behavior)
    expect(card.getAttribute("data-readonly")).toBe("false")
  })

  test("respects RBAC read-only mode", () => {
    mockEditMode.mockReturnValueOnce({
      isEditing: false,
      canToggle: false,
      toggleEditMode: vi.fn(),
      setEditMode: vi.fn(),
    })
    mockUseCards.mockReturnValue(baseReturn())
    render(<HiringPoliciesHub />)
    expect(screen.getByTestId("policy-card").getAttribute("data-readonly")).toBe("true")
  })

  test("does not render non-policy blocks", () => {
    mockUseCards.mockReturnValue(baseReturn())
    render(<HiringPoliciesHub />)
    expect(screen.getAllByTestId("policy-card")).toHaveLength(1)
  })

  test("shows loading state while fetching", () => {
    mockUseCards.mockReturnValue(baseReturn({ loading: true }))
    render(<HiringPoliciesHub />)
    expect(screen.getByText(/Carregando políticas/i)).toBeTruthy()
  })

  test("shows error state on watchdog error", () => {
    mockUseCards.mockReturnValue(baseReturn({ watchdogError: "Falha de rede" }))
    render(<HiringPoliciesHub />)
    expect(screen.getByText(/Falha de rede/i)).toBeTruthy()
  })

  test("shows error when policy block is missing", () => {
    mockUseCards.mockReturnValue(baseReturn({ blocks: [BASIC_BLOCK] }))
    render(<HiringPoliciesHub />)
    expect(screen.getByText(/Bloco de políticas não encontrado/i)).toBeTruthy()
  })

  test("rules-of-hooks: rerender loading→loaded→loading without throw", () => {
    mockUseCards.mockReturnValue(baseReturn({ loading: true }))
    const { rerender } = render(<HiringPoliciesHub />)
    mockUseCards.mockReturnValue(baseReturn())
    expect(() => rerender(<HiringPoliciesHub />)).not.toThrow()
    mockUseCards.mockReturnValue(baseReturn({ loading: true }))
    expect(() => rerender(<HiringPoliciesHub />)).not.toThrow()
  })
})
