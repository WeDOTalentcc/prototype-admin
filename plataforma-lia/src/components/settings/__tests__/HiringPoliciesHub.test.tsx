/**
 * HiringPoliciesHub tests — gates-only surface (V2.2, 2026-06-01).
 * A seção de instruções saiu para LIA & Personalização (PolicyInstructionsGroup).
 * Aqui o hub renderiza apenas o bloco estruturado de gates via MinhaEmpresaCard.
 */
import React from "react"
import { describe, test, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"

const mockUseCards = vi.fn()
vi.mock("@/hooks/settings/use-company-settings-cards", () => ({
  useCompanySettingsCards: () => mockUseCards(),
}))
const mockEditMode = vi.fn(() => ({ isEditing: true, canToggle: true, toggleEditMode: vi.fn(), setEditMode: vi.fn() }))
vi.mock("@/hooks/settings/useSettingsEditMode", () => ({ useSettingsEditMode: () => mockEditMode() }))
vi.mock("@/components/settings/SettingsEditModeToggle", () => ({ SettingsEditModeToggle: () => null }))
vi.mock("@/components/settings/MinhaEmpresaCard", () => ({
  MinhaEmpresaCard: ({ block, isReadOnly }: { block: { key: string; fields: unknown[] }; isReadOnly: boolean }) => (
    <div data-testid="policy-card" data-block={block.key} data-readonly={String(isReadOnly)} />
  ),
}))

import { HiringPoliciesHub } from "../HiringPoliciesHub"

const POLICY_BLOCK = { key: "policy", title: "Políticas de Recrutamento", iconName: "FileText", fields: [{ key: "x", label: "X", value: 1, type: "number", editable: true, block: "policy" }], status: "partial", progress: { filled: 1, total: 1, missingLabels: [] } }
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

describe("HiringPoliciesHub (gates-only)", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockEditMode.mockReturnValue({ isEditing: true, canToggle: true, toggleEditMode: vi.fn(), setEditMode: vi.fn() })
  })

  test("renders only the structured policy block", () => {
    mockUseCards.mockReturnValue(baseReturn())
    render(<HiringPoliciesHub />)
    expect(screen.getByText("Políticas de Recrutamento")).toBeTruthy()
    expect(screen.getAllByTestId("policy-card")).toHaveLength(1)
    expect(screen.getByTestId("policy-card").getAttribute("data-readonly")).toBe("false")
  })

  test("does NOT render the instructions section (moved to LIA)", () => {
    mockUseCards.mockReturnValue(baseReturn())
    render(<HiringPoliciesHub />)
    expect(screen.queryByText(/Instruções para a LIA/i)).toBeNull()
    expect(screen.queryByTestId("instruction-block-no_show_policy")).toBeNull()
  })

  test("respects RBAC read-only", () => {
    mockEditMode.mockReturnValue({ isEditing: false, canToggle: false, toggleEditMode: vi.fn(), setEditMode: vi.fn() })
    mockUseCards.mockReturnValue(baseReturn())
    render(<HiringPoliciesHub />)
    expect(screen.getByTestId("policy-card").getAttribute("data-readonly")).toBe("true")
  })

  test("loading + watchdog + missing-block states", () => {
    mockUseCards.mockReturnValue(baseReturn({ loading: true }))
    const { rerender } = render(<HiringPoliciesHub />)
    expect(screen.getByText(/Carregando políticas/i)).toBeTruthy()
    mockUseCards.mockReturnValue(baseReturn({ watchdogError: "Falha" }))
    rerender(<HiringPoliciesHub />)
    expect(screen.getByText(/Falha/i)).toBeTruthy()
    mockUseCards.mockReturnValue(baseReturn({ blocks: [BASIC_BLOCK] }))
    rerender(<HiringPoliciesHub />)
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
