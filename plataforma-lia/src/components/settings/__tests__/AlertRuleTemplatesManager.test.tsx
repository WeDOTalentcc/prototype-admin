/**
 * Smoke tests — AlertRuleTemplatesManager (P0.G #2)
 *
 * Cobre patterns canonical:
 *  1. render: monta componente, espera lista render com label do alert
 *  2. filter chips: clique em "Master canonical" filtra masters apenas
 *  3. startCreate: clique em "Nova regra" abre form de criação
 *  4. permission gate: isAdmin=false + currentUserId=null esconde edit/delete
 *     em customs alheios (created_by !== currentUserId)
 *
 * Pattern: mock do hook canonical via vi.mock; smoke render apenas.
 */
import React from "react"
import { describe, test, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, within } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"

import { AlertRuleTemplatesManager } from "../AlertRuleTemplatesManager"
import type { AlertRuleTemplate } from "@/hooks/communication/use-alert-rule-templates"

// Mensagens mínimas espelhando `messages/pt-BR.json → settings.catalogs`.
const CATALOG_MESSAGES = {
  settings: {
    catalogs: {
      common: {
        filters: "Filtrar:",
        filterAll: "Todos",
        filterAllFeminine: "Todas",
        filterMaster: "Master canonical",
        filterCustom: "Customs da empresa",
        masterChip: "Master canonical",
        defaultChip: "Default",
        deprecatedChip: "Deprecated",
        tryAgain: "Tentar novamente",
        save: "Salvar",
        cancel: "Cancelar",
        edit: "Editar",
        customize: "Customizar",
        customizeHint: "Customizar (cria cópia)",
        delete: "Excluir",
        deleteAdminOnly: "Excluir (admin only)",
        customizedMasterFlash: "Master \"{label}\" customizado",
        countSummary: "{master} master · {custom} custom · {total} total",
      },
      alert: {
        title: "Gerenciador de Alertas (Notificações)",
        newButton: "Nova regra",
        formTitleCreate: "Criar alert rule",
        formTitleEdit: "Editar alert rule",
        confirmDelete: "Excluir alert \"{label}\"?",
        successCreate: "Alert rule criada",
        successUpdate: "Alert rule atualizada",
        successDelete: "Alert rule excluída",
        failCreate: "Falha ao criar",
        failUpdate: "Falha ao atualizar",
        emptyList: "Nenhuma alert rule nessa categoria.",
        validationLabel: "Label deve ter pelo menos 3 caracteres",
        validationEventType: "Event type deve ser slug (a-z, 0-9, _, ., ex: candidate.applied)",
        validationChannels: "Selecione ao menos 1 canal",
        placeholderLabel: "Label (ex: Candidato aplicou em vaga)",
        placeholderEventType: "Event type (slug: candidate.applied, interview.cancelled)",
        placeholderAudience: "Audience",
        placeholderDelayMinutes: "Delay em minutos (0 = imediato)",
        channelsHeader: "Canais (multi-seleção):",
        labelLgpdCompliant: "Respeita janela LGPD (horario comercial Brasilia)",
        labelLgpdChip: "LGPD janela ✓",
        labelChannels: "Canais:",
        labelDelay: "Delay:",
        labelDelayUnit: "min",
      },
    },
  },
} as const

function renderWithIntl(ui: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={CATALOG_MESSAGES}>
      {ui}
    </NextIntlClientProvider>,
  )
}

const masterTemplate: AlertRuleTemplate = {
  id: "master-1",
  company_id: null,
  is_master_template: true,
  parent_template_id: null,
  data: {
    event_type: "candidate.created",
    label: "Candidato criado",
    description: "Notifica recrutador quando candidato chega",
    audience: "recruiter",
    channels: ["email", "in_app"],
    delay_minutes: 0,
    schedule_lgpd_compliant: true,
  },
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  created_by: null,
  deleted_at: null,
}

const customOwnTemplate: AlertRuleTemplate = {
  id: "custom-own-1",
  company_id: "company-uuid",
  is_master_template: false,
  parent_template_id: null,
  data: {
    event_type: "candidate.shortlisted",
    label: "Alerta minha",
    audience: "recruiter",
    channels: ["email"],
    delay_minutes: 5,
    schedule_lgpd_compliant: false,
  },
  created_at: "2026-01-02T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
  created_by: "user-self",
  deleted_at: null,
}

const customForeignTemplate: AlertRuleTemplate = {
  id: "custom-foreign-1",
  company_id: "company-uuid",
  is_master_template: false,
  parent_template_id: null,
  data: {
    event_type: "candidate.hired",
    label: "Alerta alheia",
    audience: "admin",
    channels: ["teams"],
    delay_minutes: 0,
    schedule_lgpd_compliant: true,
  },
  created_at: "2026-01-03T00:00:00Z",
  updated_at: "2026-01-03T00:00:00Z",
  created_by: "user-other",
  deleted_at: null,
}

const hookReturnValue = {
  templates: [masterTemplate, customOwnTemplate, customForeignTemplate],
  masterCount: 1,
  customCount: 2,
  total: 3,
  isLoading: false,
  error: null,
  refetch: vi.fn(),
  createCustom: vi.fn(),
  updateTemplate: vi.fn(),
  deleteTemplate: vi.fn(),
  customizeMaster: vi.fn(),
}

vi.mock("@/hooks/communication/use-alert-rule-templates", async () => {
  const actual = await vi.importActual<
    typeof import("@/hooks/communication/use-alert-rule-templates")
  >("@/hooks/communication/use-alert-rule-templates")
  return {
    ...actual,
    useAlertRuleTemplates: vi.fn(() => hookReturnValue),
  }
})

describe("AlertRuleTemplatesManager — smoke (P0.G #2)", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test("renders Manager card title + lista de alert rules", () => {
    renderWithIntl(
      <AlertRuleTemplatesManager isAdmin={true} currentUserId="user-self" />,
    )
    expect(
      screen.getByText("Gerenciador de Alertas (Notificações)"),
    ).toBeInTheDocument()
    expect(screen.getByText("Candidato criado")).toBeInTheDocument()
    expect(screen.getByText("Alerta minha")).toBeInTheDocument()
    expect(screen.getByText("Alerta alheia")).toBeInTheDocument()
  })

  test("filter chips: clicar 'Master canonical' filtra só masters", () => {
    renderWithIntl(
      <AlertRuleTemplatesManager isAdmin={true} currentUserId="user-self" />,
    )
    expect(screen.getByText("Alerta minha")).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: /Master canonical/i }))

    expect(screen.getByText("Candidato criado")).toBeInTheDocument()
    expect(screen.queryByText("Alerta minha")).not.toBeInTheDocument()
    expect(screen.queryByText("Alerta alheia")).not.toBeInTheDocument()
  })

  test("startCreate: clicar 'Nova regra' abre form de criação", () => {
    renderWithIntl(
      <AlertRuleTemplatesManager isAdmin={true} currentUserId="user-self" />,
    )
    expect(screen.queryByText("Criar alert rule")).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: /Nova regra/i }))

    expect(screen.getByText("Criar alert rule")).toBeInTheDocument()
  })

  test("permission gate: isAdmin=false + currentUserId=null esconde edit/delete em customs alheios", () => {
    renderWithIntl(
      <AlertRuleTemplatesManager isAdmin={false} currentUserId={null} />,
    )

    // Alerta alheia (created_by = "user-other"): sem edit/delete
    const foreignRow = screen.getByText("Alerta alheia").closest("div.flex.items-start")
    expect(foreignRow).not.toBeNull()
    const foreignButtons = within(foreignRow as HTMLElement).queryAllByRole("button")
    expect(foreignButtons.length).toBe(0)

    // Master: aparece apenas botão "Customizar"
    const masterRow = screen
      .getByText("Candidato criado")
      .closest("div.flex.items-start")
    const masterButtons = within(masterRow as HTMLElement).queryAllByRole("button")
    expect(masterButtons.length).toBe(1)
    expect(masterButtons[0]).toHaveAttribute("title", "Customizar")
  })
})
