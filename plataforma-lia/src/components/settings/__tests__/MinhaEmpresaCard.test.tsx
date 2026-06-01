/**
 * Tests — MinhaEmpresaCard isReadOnly behavior (Sprint B.7 2026-05-26).
 *
 * Audit ref: ~/Documents/wedotalent_audit_2026-05-26/P2-2_ONBOARDING_CONVERSACIONAL_ADR.md Sprint B.7
 *
 * Garante que prop `isReadOnly` (drilled de useSettingsEditMode("minha-empresa") no Hub)
 * esconde edit buttons + força display mode + mostra hint. Default (omitido) = comportamento
 * legacy (edit buttons visíveis, inline editor renderiza quando editingField match).
 */
import React from "react"
import { describe, test, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import { MinhaEmpresaCard } from "../MinhaEmpresaCard"
import type { CardBlock } from "@/hooks/settings/use-company-settings-cards"
import { Building } from "lucide-react"

// ── Mocks ────────────────────────────────────────────────────────────────────
// Children não relevantes para o teste — stub minimal.
vi.mock("@/components/settings/benefits/BenefitsListSection", () => ({
  BenefitsListSection: () => <div data-testid="benefits-list-stub" />,
}))
vi.mock("@/components/settings/WorkforceHubContent", () => ({
  WorkforceHubContent: () => <div data-testid="workforce-stub" />,
}))
vi.mock("@/components/settings/SectionUploadDropZone", () => ({
  SectionUploadDropZone: () => <div data-testid="upload-zone-stub" />,
}))
vi.mock("@/components/settings/LogoUploadField", () => ({
  LogoUploadField: () => <div data-testid="logo-upload-stub" />,
}))

// ── Messages ────────────────────────────────────────────────────────────────
const MESSAGES = {
  settings: {
    minhaEmpresaCard: {
      statusConfigured: "Configurado",
      statusPartial: "Parcial",
      statusPending: "Pendente",
      valueNotDefined: "Não definido",
      valueYes: "Sim",
      valueNo: "Não",
      valueNone: "Nenhum",
      fieldsFilled: "{filled} de {total} preenchidos",
      missingFieldsTitle: "Campos pendentes ({count})",
      uploadHint: "Upload pode preencher.",
      editFieldAria: "Editar {label}",
      readOnlyHint: "Modo visualização ativo. Clique em \"Modo edição\" no header pra ajustar.",
      invalidNumber: "Número inválido",
      timeRangeFormat: "Use HH:MM - HH:MM",
      blockUpload: {
        cultureLabel: "Cultura & EVP",
        cultureHint: "",
        techLabel: "Tech",
        techHint: "",
        benefitsLabel: "Benefícios",
        benefitsHint: "",
        policyLabel: "Políticas",
        policyHint: "",
        workforceLabel: "Workforce",
        workforceHint: "",
        documentsLabel: "Remuneração",
        documentsHint: "",
      },
    },
  },
}

// ── Fixtures ────────────────────────────────────────────────────────────────
const block: CardBlock = {
  key: "basic",
  title: "Dados Básicos",
  subtitle: undefined,
  iconName: "Building",
  status: "configured",
  progress: { filled: 3, total: 3, missingLabels: [] },
  fields: [
    {
      key: "name",
      label: "Nome",
      value: "Acme Inc",
      editable: true,
      type: "text",
      block: "basic",
    },
    {
      key: "industry",
      label: "Setor",
      value: "Tech",
      editable: true,
      type: "text",
      block: "basic",
    },
  ],
} as unknown as CardBlock

const standardProps = {
  block,
  IconComp: Building,
  isExpanded: true,
  recentlyUpdated: new Set<string>(),
  editingField: null,
  isSavingField: false,
  benefits: [],
  companyId: "test-company-123",
  onBenefitsChanged: vi.fn(),
  onLogoUploaded: vi.fn(),
  onToggle: vi.fn(),
  onStartEditing: vi.fn(),
  onCancelEditing: vi.fn(),
  onSaveField: vi.fn(),
}

function wrap(extra: Partial<typeof standardProps> & { isReadOnly?: boolean } = {}) {
  return (
    <NextIntlClientProvider locale="pt-BR" messages={MESSAGES}>
      <MinhaEmpresaCard {...standardProps} {...extra} />
    </NextIntlClientProvider>
  )
}

// ── Testes ──────────────────────────────────────────────────────────────────
describe("MinhaEmpresaCard — read-only mode (Sprint B.7)", () => {
  test("default (isReadOnly omitido): edit buttons renderizam para fields editáveis", () => {
    render(wrap())
    // Há 2 fields editáveis no fixture → 2 botões "Editar X"
    const editButtons = screen.getAllByLabelText(/^Editar /)
    expect(editButtons).toHaveLength(2)
  })

  test("default: hint readonly NÃO aparece quando isReadOnly não é passado", () => {
    render(wrap())
    expect(screen.queryByTestId("readonly-hint-basic")).not.toBeInTheDocument()
  })

  test("isReadOnly=true: nenhum edit button (pencil) renderiza", () => {
    render(wrap({ isReadOnly: true }))
    expect(screen.queryAllByLabelText(/^Editar /)).toHaveLength(0)
  })

  test("isReadOnly=true: hint visual aparece dentro do bloco expandido", () => {
    render(wrap({ isReadOnly: true }))
    const hint = screen.getByTestId("readonly-hint-basic")
    expect(hint).toBeInTheDocument()
    expect(hint.textContent).toMatch(/Modo visualização/)
  })

  test("isReadOnly=true: inline editor NÃO ativa mesmo quando editingField match", () => {
    render(
      wrap({
        isReadOnly: true,
        editingField: { block: "basic", field: "name" },
      }),
    )
    // Inline editor renderiza um <input> autofocus. Em readonly não pode aparecer.
    expect(screen.queryByDisplayValue("Acme Inc")).not.toBeInTheDocument()
    // Valor é exibido como texto, não como input.
    expect(screen.getByText("Acme Inc")).toBeInTheDocument()
  })

  test("isReadOnly=false explícito: comportamento equivalente ao default", () => {
    render(wrap({ isReadOnly: false }))
    expect(screen.getAllByLabelText(/^Editar /)).toHaveLength(2)
    expect(screen.queryByTestId("readonly-hint-basic")).not.toBeInTheDocument()
  })
})
