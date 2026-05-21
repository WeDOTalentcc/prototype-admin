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

import { AlertRuleTemplatesManager } from "../AlertRuleTemplatesManager"
import type { AlertRuleTemplate } from "@/hooks/communication/use-alert-rule-templates"

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
    render(
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
    render(
      <AlertRuleTemplatesManager isAdmin={true} currentUserId="user-self" />,
    )
    expect(screen.getByText("Alerta minha")).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: /Master canonical/i }))

    expect(screen.getByText("Candidato criado")).toBeInTheDocument()
    expect(screen.queryByText("Alerta minha")).not.toBeInTheDocument()
    expect(screen.queryByText("Alerta alheia")).not.toBeInTheDocument()
  })

  test("startCreate: clicar 'Nova regra' abre form de criação", () => {
    render(
      <AlertRuleTemplatesManager isAdmin={true} currentUserId="user-self" />,
    )
    expect(screen.queryByText("Criar alert rule")).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: /Nova regra/i }))

    expect(screen.getByText("Criar alert rule")).toBeInTheDocument()
  })

  test("permission gate: isAdmin=false + currentUserId=null esconde edit/delete em customs alheios", () => {
    render(
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
