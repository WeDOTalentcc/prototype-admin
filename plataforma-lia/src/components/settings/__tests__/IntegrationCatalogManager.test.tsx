/**
 * Smoke tests — IntegrationCatalogManager (P0.G #3)
 *
 * Cobre patterns canonical:
 *  1. render: monta componente, espera lista render com label da integration
 *  2. filter chips: clique em "Master canonical" filtra masters apenas
 *  3. startCreate: clique em "Nova integração" abre form de criação
 *  4. permission gate: isAdmin=false + currentUserId=null esconde edit/delete
 *     em customs alheios (created_by !== currentUserId)
 *
 * Pattern: mock do hook canonical via vi.mock; smoke render apenas.
 * Nota: hook retorna `entries` (não `templates`) e métodos `updateEntry`/`deleteEntry`.
 */
import React from "react"
import { describe, test, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, within } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"

import { IntegrationCatalogManager } from "../IntegrationCatalogManager"
import type { IntegrationCatalogEntry } from "@/hooks/integrations/use-integration-catalog"

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
      integration: {
        title: "Gerenciador de Integrações",
        newButton: "Nova integração",
        formTitleCreate: "Criar integration",
        formTitleEdit: "Editar integration",
        confirmDelete: "Excluir integration \"{label}\"?",
        successCreate: "Integration criada",
        successUpdate: "Integration atualizada",
        successDelete: "Integration excluída",
        failCreate: "Falha ao criar",
        failUpdate: "Falha ao atualizar",
        emptyList: "Nenhuma integration nessa categoria.",
        validationLabel: "Label deve ter pelo menos 2 caracteres",
        validationProvider: "Provider deve ser slug (a-z, 0-9, _)",
        validationDescription: "Descrição é obrigatória",
        placeholderLabel: "Label (ex: HubSpot CRM)",
        placeholderProvider: "Provider slug (ex: hubspot)",
        placeholderDescription: "Descrição curta",
        placeholderCategory: "Categoria",
        placeholderStatus: "Status",
        placeholderLogoUrl: "Logo URL (opcional)",
        placeholderFullDescription: "Descrição completa (opcional)",
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

const masterEntry: IntegrationCatalogEntry = {
  id: "master-1",
  company_id: null,
  is_master_template: true,
  parent_template_id: null,
  data: {
    provider: "anthropic",
    label: "Anthropic Claude",
    category: "ai_models",
    description: "LLM provider canonical",
    status: "production",
  },
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  created_by: null,
  deleted_at: null,
}

const customOwnEntry: IntegrationCatalogEntry = {
  id: "custom-own-1",
  company_id: "company-uuid",
  is_master_template: false,
  parent_template_id: null,
  data: {
    provider: "myats",
    label: "Integração minha",
    category: "ats",
    description: "ATS interno",
    status: "production",
  },
  created_at: "2026-01-02T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
  created_by: "user-self",
  deleted_at: null,
}

const customForeignEntry: IntegrationCatalogEntry = {
  id: "custom-foreign-1",
  company_id: "company-uuid",
  is_master_template: false,
  parent_template_id: null,
  data: {
    provider: "foreigncrm",
    label: "Integração alheia",
    category: "crm_hris",
    description: "CRM externo",
    status: "production",
  },
  created_at: "2026-01-03T00:00:00Z",
  updated_at: "2026-01-03T00:00:00Z",
  created_by: "user-other",
  deleted_at: null,
}

const hookReturnValue = {
  entries: [masterEntry, customOwnEntry, customForeignEntry],
  masterCount: 1,
  customCount: 2,
  total: 3,
  isLoading: false,
  error: null,
  refetch: vi.fn(),
  createCustom: vi.fn(),
  updateEntry: vi.fn(),
  deleteEntry: vi.fn(),
  customizeMaster: vi.fn(),
}

vi.mock("@/hooks/integrations/use-integration-catalog", async () => {
  const actual = await vi.importActual<
    typeof import("@/hooks/integrations/use-integration-catalog")
  >("@/hooks/integrations/use-integration-catalog")
  return {
    ...actual,
    useIntegrationCatalog: vi.fn(() => hookReturnValue),
  }
})

describe("IntegrationCatalogManager — smoke (P0.G #3)", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test("renders Manager card title + lista de integrations", () => {
    renderWithIntl(
      <IntegrationCatalogManager isAdmin={true} currentUserId="user-self" />,
    )
    expect(screen.getByText("Gerenciador de Integrações")).toBeInTheDocument()
    expect(screen.getByText("Anthropic Claude")).toBeInTheDocument()
    expect(screen.getByText("Integração minha")).toBeInTheDocument()
    expect(screen.getByText("Integração alheia")).toBeInTheDocument()
  })

  test("filter chips: clicar 'Master canonical' filtra só masters", () => {
    renderWithIntl(
      <IntegrationCatalogManager isAdmin={true} currentUserId="user-self" />,
    )
    expect(screen.getByText("Integração minha")).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: /Master canonical/i }))

    expect(screen.getByText("Anthropic Claude")).toBeInTheDocument()
    expect(screen.queryByText("Integração minha")).not.toBeInTheDocument()
    expect(screen.queryByText("Integração alheia")).not.toBeInTheDocument()
  })

  test("startCreate: clicar 'Nova integração' abre form de criação", () => {
    renderWithIntl(
      <IntegrationCatalogManager isAdmin={true} currentUserId="user-self" />,
    )
    expect(screen.queryByText("Criar integration")).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: /Nova integração/i }))

    expect(screen.getByText("Criar integration")).toBeInTheDocument()
  })

  test("permission gate: isAdmin=false + currentUserId=null esconde edit/delete em customs alheios", () => {
    renderWithIntl(
      <IntegrationCatalogManager isAdmin={false} currentUserId={null} />,
    )

    // Integração alheia (created_by = "user-other"): sem edit/delete
    const foreignRow = screen
      .getByText("Integração alheia")
      .closest("div.flex.items-start")
    expect(foreignRow).not.toBeNull()
    const foreignButtons = within(foreignRow as HTMLElement).queryAllByRole("button")
    expect(foreignButtons.length).toBe(0)

    // Master: aparece apenas botão "Customizar"
    const masterRow = screen
      .getByText("Anthropic Claude")
      .closest("div.flex.items-start")
    const masterButtons = within(masterRow as HTMLElement).queryAllByRole("button")
    expect(masterButtons.length).toBe(1)
    expect(masterButtons[0]).toHaveAttribute("title", "Customizar")
  })
})
