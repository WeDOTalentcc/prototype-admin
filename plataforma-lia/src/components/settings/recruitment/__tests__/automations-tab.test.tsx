/**
 * PR-AUTO — AutomationsTab API wiring tests (TDD red→green)
 *
 * Verifica que AutomationsTab busca automações da API real em vez de
 * usar dados hardcoded. Resolve achado P0 do audit enterprise (2026-04-26):
 * `useState` com 3 workflows falsos de 2024 — dados fantasma exibidos
 * ao recrutador como se fossem reais.
 *
 * Sensor computacional: este teste detecta regressão se alguém
 * reintroduzir dados hardcoded no componente.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

// ── Mocks ────────────────────────────────────────────────────────────────

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn() }),
  usePathname: () => "/configuracoes/recruitment",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "test-company-123", isLoading: false }),
}));

vi.mock("@/utils/license-manager", () => ({
  hasModuleAccess: () => true,
}));

// `automations-tab` chama `apiFetch` (wrapper de `fetch` com `credentials:
// 'include'`). Como o módulo captura `fetch` no escopo da factory durante o
// import, `vi.stubGlobal('fetch', …)` chamado em `beforeEach` não intercepta
// — o componente continua usando o `fetch` original. Mockar `apiFetch`
// diretamente é o vetor canônico, e como `apiFetch` delega para `fetch`,
// preservamos a asserção `expect(fetch).toHaveBeenCalledWith(...)`
// encaminhando os mesmos argumentos para o `fetch` global (que continua sendo
// stubbed por `vi.stubGlobal`).
vi.mock("@/lib/api/api-fetch", () => ({
  apiFetch: (input: RequestInfo | URL, init?: RequestInit) => {
    const f = globalThis.fetch as typeof fetch;
    // Encaminha exatamente os argumentos recebidos (sem `init` quando ausente)
    // para preservar a forma do call signature observado pelo `expect` —
    // `toHaveBeenCalledWith(stringContaining(...))` exige match exato da lista
    // de args, então um `undefined` extra quebraria a asserção.
    return init === undefined ? f(input as RequestInfo) : f(input as RequestInfo, init);
  },
}));

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
    });
  }
  if (typeof window !== "undefined" && !(window as unknown as { ResizeObserver?: unknown }).ResizeObserver) {
    (window as unknown as { ResizeObserver: unknown }).ResizeObserver = class {
      observe() {} unobserve() {} disconnect() {}
    };
  }
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AutomationsTab } from "../automations-tab";

const MESSAGES = {
  settings: {
    recruitment: {
      automationsTab: {
        loadError: "Não foi possível carregar as automações",
        upsellTitle: "Automações Inteligentes",
        upsellDesc: "Automatize etapas do processo seletivo",
        loading: "Carregando automações...",
        activeWorkflows: "Workflows Ativos",
        ofTotalSimple: "de {total} no total",
        executionsToday: "Execuções Hoje",
        totalAccumulated: "total acumulado",
        successRate: "Taxa de Sucesso",
        averageOfAutomations: "média das automações",
        automationsLabel: "Automações",
        configured: "configuradas",
        configuredWorkflows: "Workflows Configurados",
        newWorkflow: "Nova automação",
        emptyTitle: "A LIA pode automatizar tarefas repetitivas pra você",
        emptyExample: "Exemplo: Quando um candidato chega na etapa Entrevista, envie automaticamente o convite pelo WhatsApp.",
        createWithLia: "Criar com a LIA",
        seeExamples: "Ver exemplos",
        emptyDesc: "Crie seu primeiro workflow de automação",
        createFirst: "Criar primeira automação",
        trigger: "Gatilho: {value}",
        executions: "{count} execuções",
        successPct: "{pct}% sucesso",
        statusActive: "Ativo",
        statusPaused: "Pausado",
        edit: "Editar",
        quickActions: "Ações Rápidas",
        createWorkflow: "Criar Workflow",
        createWorkflowDesc: "Crie um novo workflow do zero",
        importTemplate: "Importar Template",
        importTemplateDesc: "Use um template pré-configurado",
        importTemplateDescDetail: "Templates pré-configurados para os casos de uso mais comuns",
        viewAnalytics: "Ver Analytics",
        viewAnalyticsDesc: "Acompanhe o desempenho",
        builderTitle: "Builder de Automações",
        builderDesc: "Crie workflows visuais arrastando componentes",
        templateLibrary: "Biblioteca de Templates",
        templateLibraryDesc: "Templates prontos para usar",
        executionLogs: "Logs de Execução",
        executionLogsDesc: "Histórico de execuções",
        pageTitle: "Automações",
        pageSubtitle: "Deixe a LIA executar tarefas repetitivas do seu processo",
        export: "Exportar",
        tabOverview: "Visão Geral",
        tabBuilder: "Criar",
        tabTemplates: "Exemplos",
        tabLogs: "Histórico",
        trigger_candidate_stage_changed: "Candidato movimentado",
        trigger_interview_scheduled: "Entrevista agendada",
        trigger_offer_sent: "Oferta enviada",
        trigger_candidate_hired: "Candidato contratado",
        trigger_job_opened: "Vaga aberta",
        trigger_cv_uploaded: "CV enviado",
      },
    },
  },
};

function renderWithIntl(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <NextIntlClientProvider locale="pt-BR" messages={MESSAGES}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

// ── API response fixtures ────────────────────────────────────────────────

const MOCK_AUTOMATIONS = [
  {
    id: "auto-001",
    name: "Notificação Automática de Aprovação",
    description: "Envia email quando candidato é aprovado na triagem",
    trigger_type: "candidate_stage_changed",
    action_type: "send_email",
    is_active: true,
    executions_count: 42,
    last_executed_at: "2026-04-20T10:00:00Z",
    success_rate: 99,
  },
  {
    id: "auto-002",
    name: "Lembrete de Entrevista",
    description: "WhatsApp 24h antes da entrevista",
    trigger_type: "interview_scheduled",
    action_type: "send_whatsapp",
    is_active: false,
    executions_count: 0,
    last_executed_at: null,
    success_rate: 100,
  },
];

// ── Tests ────────────────────────────────────────────────────────────────

describe("AutomationsTab — API wiring (PR-AUTO)", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          success: true,
          data: { automations: MOCK_AUTOMATIONS, total: 2 },
        }),
      }),
    );
  });

  it("faz fetch para /api/backend-proxy/automations SEM company_id no URL (REGRA 2 canonical)", async () => {
    // REGRA 2 CLAUDE.md user-global: company_id NUNCA via query/body.
    // Backend extrai do JWT via Depends(require_company_id). Frontend stripped.
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/backend-proxy/automations"),
      );
    });

    const url = (fetch as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
    // Sensor canonical: a URL NÃO pode conter company_id query param.
    expect(url).not.toContain("company_id=");
  });

  it("exibe nome da automação retornada pela API", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await screen.findByText("Notificação Automática de Aprovação");
    expect(
      screen.getByText("Notificação Automática de Aprovação"),
    ).toBeInTheDocument();
  });

  it("NÃO exibe dados hardcoded de 2024 ('Triagem Automática de Candidatos')", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await waitFor(() => {
      expect(
        screen.queryByText("Triagem Automática de Candidatos"),
      ).not.toBeInTheDocument();
    });
  });

  it("mapeia trigger_type para label legível", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await waitFor(() => {
      // candidate_stage_changed → "Candidato movimentado"
      expect(screen.getByText(/Candidato movimentado/i)).toBeInTheDocument();
    });
  });

  it("mapeia is_active=false para status Pausado", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await waitFor(() => {
      expect(screen.getByText("Pausado")).toBeInTheDocument();
    });
  });

  it("exibe estado vazio quando API retorna lista vazia", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ success: true, data: { automations: [], total: 0 } }),
      }),
    );
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await waitFor(() => {
      expect(
        screen.getByText(/a lia pode automatizar/i),
      ).toBeInTheDocument();
    });
  });

  it("exibe estado de erro quando fetch falha", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network error")));
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await waitFor(() => {
      expect(
        screen.getByText(/não foi possível carregar/i),
      ).toBeInTheDocument();
    });
  });
});
