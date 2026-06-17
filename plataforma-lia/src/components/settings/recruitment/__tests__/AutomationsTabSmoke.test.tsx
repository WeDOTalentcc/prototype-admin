import { describe, it, expect, vi, beforeEach } from "vitest"
import { render } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AutomationsTab } from "../automations-tab"

vi.mock("@/utils/license-manager", () => ({
  hasModuleAccess: () => true,
}))
vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "test-company-id" }),
}))
vi.mock("@/lib/api/api-fetch", () => ({
  apiFetch: vi.fn().mockResolvedValue({
    json: () => Promise.resolve({ success: true, data: { automations: [] } }),
    ok: true,
  }),
}))

const MESSAGES = {
  settings: {
    recruitment: {
      automationsTab: {
        upsellTitle: "Automações",
        upsellDesc: "desc",
        configuredWorkflows: "Fluxos Configurados",
        newWorkflow: "Novo Fluxo",
        emptyTitle: "Nenhuma automação configurada ainda",
        emptyDesc: "Crie sua primeira automação para agilizar o processo seletivo",
        createFirst: "Criar primeira automação",
        trigger: "Gatilho: {value}",
        executions: "{count} execuções",
        successPct: "{pct}% sucesso",
        statusActive: "Ativo",
        statusPaused: "Pausado",
        edit: "Editar",
        quickActions: "Ações Rápidas",
        createWorkflow: "Criar Workflow",
        createWorkflowDesc: "Do zero",
        importTemplate: "Importar Modelo",
        importTemplateDesc: "Da biblioteca",
        viewAnalytics: "Ver Análises",
        viewAnalyticsDesc: "Desempenho",
        export: "Exportar",
        pageTitle: "Automação de Fluxos",
        pageSubtitle: "Construtor visual",
        tabOverview: "Visão Geral",
        tabBuilder: "Construtor",
        tabTemplates: "Modelos",
        tabLogs: "Logs",
        builderTitle: "Construtor Visual",
        builderDesc: "Arrastar e soltar",
        templateLibrary: "Biblioteca de Modelos",
        templateLibraryDesc: "Modelos pré-configurados",
        executionLogs: "Logs de Execução",
        executionLogsDesc: "Histórico de execuções",
        summaryActive: "{active} ativo(s) de {total}",
        summaryExecs: "{count} execuções",
        summarySuccess: "{pct}% de sucesso",
      },
    },
  },
}

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>
      <NextIntlClientProvider locale="pt" messages={MESSAGES}>
        {children}
      </NextIntlClientProvider>
    </QueryClientProvider>
  )
  Wrapper.displayName = "TestWrapper"
  return Wrapper
}

describe("AutomationsTab — smoke tests", () => {
  beforeEach(() => { vi.clearAllMocks() })

  it("mounts without throwing", () => {
    expect(() =>
      render(<AutomationsTab onSettingsChange={() => {}} />, { wrapper: makeWrapper() })
    ).not.toThrow()
  })
})
