/**
 * PR-AUTO — AutomationsTab API wiring tests (TDD red→green)
 *
 * Sprint A.5+A.6 (2026-05-26): Builder wiring
 * Sprint D.1+D.4 (2026-05-26): Item actions wiring (toggle, test, duplicate, delete)
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

// ── Mocks ────────────────────────────────────────────────────────────────

// Sprint D.3: useSearchParams mockable per-test (deep-link ?view=builder)
const mockSearchParamsState = { current: new URLSearchParams() };

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn() }),
  usePathname: () => "/configuracoes/recruitment",
  useSearchParams: () => mockSearchParamsState.current,
}));

vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "test-company-123", isLoading: false }),
}));

vi.mock("@/utils/license-manager", () => ({
  hasModuleAccess: () => true,
}));

vi.mock("@/lib/api/api-fetch", () => ({
  apiFetch: (input: RequestInfo | URL, init?: RequestInit) => {
    const f = globalThis.fetch as typeof fetch;
    return init === undefined ? f(input as RequestInfo) : f(input as RequestInfo, init);
  },
}));

// Sprint A.5+D.1+D.4: mocks de mutations canonical.
const mockCreateMutateAsync = vi.fn().mockResolvedValue({ id: "new-auto-id" });
const mockCreateMutate = vi.fn();
const mockUpdateMutateAsync = vi.fn().mockResolvedValue({ id: "existing-id" });
const mockToggleMutate = vi.fn();
const mockTestMutateAsync = vi.fn().mockResolvedValue({ success: true });
const mockDeleteMutate = vi.fn();

// Sprint A.7: useTriggerTypes/useActionTypes wiring. Default = backend canonical
// shape success. Tests podem reatribuir esses objetos via beforeEach pra simular
// loading/error states. (vi.mock factory roda no hoisting — variables aqui são
// closure-captured pelo mock factory.)
const mockTriggerTypesState: { data: unknown; error: unknown; isLoading: boolean } = {
  data: {
    success: true,
    data: {
      trigger_types: [
        { value: "candidate_stage_changed", name: "Candidato mudou de etapa", description: "..." },
        { value: "interview_scheduled", name: "Entrevista agendada", description: "..." },
      ],
    },
  },
  error: null,
  isLoading: false,
};

const mockActionTypesState: { data: unknown; error: unknown; isLoading: boolean } = {
  data: {
    success: true,
    data: {
      action_types: [
        { value: "send_email", name: "Enviar e-mail", description: "...", config_fields: [] },
        { value: "send_whatsapp", name: "Enviar WhatsApp", description: "...", config_fields: [] },
      ],
    },
  },
  error: null,
  isLoading: false,
};

// Sprint A.8: useOperators/useConditionFields wiring mock state.
const mockOperatorsState: { data: unknown; error: unknown; isLoading: boolean } = {
  data: {
    success: true,
    data: {
      operators: [
        { value: "eq", name: "for igual a", label_pt: "for igual a", label_en: "equals" },
        { value: "gt", name: "for maior que", label_pt: "for maior que", label_en: "greater than" },
      ],
    },
  },
  error: null,
  isLoading: false,
};

const mockConditionFieldsState: { data: unknown; error: unknown; isLoading: boolean } = {
  data: {
    success: true,
    data: {
      condition_fields: [
        { value: "candidate.wsi_score", name: "score WSI", type: "number", category: "candidate" },
        { value: "candidate.years_experience", name: "anos de experiência", type: "number", category: "candidate" },
      ],
    },
  },
  error: null,
  isLoading: false,
};


vi.mock("@/hooks/automations/useAutomationMutations", () => ({
  useCreateAutomation: () => ({
    mutateAsync: mockCreateMutateAsync,
    mutate: mockCreateMutate,
    isPending: false,
  }),
  useUpdateAutomation: () => ({
    mutateAsync: mockUpdateMutateAsync,
    isPending: false,
  }),
  useToggleAutomationActive: () => ({
    mutate: mockToggleMutate,
    isPending: false,
  }),
  useTestAutomation: () => ({
    mutateAsync: mockTestMutateAsync,
    isPending: false,
  }),
  useDeleteAutomation: () => ({
    mutate: mockDeleteMutate,
    isPending: false,
  }),
  useTriggerTypes: () => mockTriggerTypesState,
  useActionTypes: () => mockActionTypesState,
  useOperators: () => mockOperatorsState,
  useConditionFields: () => mockConditionFieldsState,
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
        moreActions: "Mais ações",
        actionTest: "Testar",
        actionDuplicate: "Duplicar",
        actionDelete: "Excluir",
        pauseAutomation: "Pausar automação",
        activateAutomation: "Ativar automação",
        testOk: "Teste OK: {name}",
        testFailed: "Teste falhou: {name}",
        duplicateSuffix: "{name} (cópia)",
        deleteConfirm: 'Excluir automação "{name}"?',
        quickActions: "Ações Rápidas",
        createWorkflow: "Criar Workflow",
        createWorkflowDesc: "Crie um novo workflow do zero",
        importTemplate: "Importar Template",
        importTemplateDesc: "Use um template pré-configurado",
        importTemplateDescDetail: "Templates pré-configurados para os casos de uso mais comuns",
        viewAnalytics: "Ver Analytics",
        viewAnalyticsDesc: "Acompanhe o desempenho",
        builderTitle: "Builder de Automações",
        builderTitleNew: "Nova automação",
        builderTitleEdit: "Editar automação",
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
        summaryActive: "{active} de {total} ativas",
        summaryExecs: "{count} execuções",
        summarySuccess: "{pct}% sucesso",
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
    trigger_data: { stage: "approved" },
    action_type: "send_email",
    action_data: { template_id: "approval" },
    conditions: [],
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
    trigger_data: {},
    action_type: "send_whatsapp",
    action_data: {},
    conditions: [],
    is_active: false,
    executions_count: 0,
    last_executed_at: null,
    success_rate: 100,
  },
];

const EMPTY_API_RESPONSE = {
  ok: true,
  json: async () => ({ success: true, data: { automations: [], total: 0 } }),
};

const POPULATED_API_RESPONSE = {
  ok: true,
  json: async () => ({
    success: true,
    data: { automations: MOCK_AUTOMATIONS, total: 2 },
  }),
};

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
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/backend-proxy/automations"),
      );
    });

    const url = (fetch as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
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

// ── Sprint A.5+A.6: Builder wiring ──────────────────────────────────────

describe("AutomationsTab — Builder wiring (Sprint A.5+A.6)", () => {
  beforeEach(() => {
    mockCreateMutateAsync.mockClear();
    mockUpdateMutateAsync.mockClear();
    mockCreateMutate.mockClear();
  });

  it("clicar 'Nova automação' no header abre tab Criar com SentenceBuilder", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(EMPTY_API_RESPONSE));
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    await screen.findByText(/a lia pode automatizar/i);

    const buttons = screen.getAllByRole("button", { name: /nova automação/i });
    fireEvent.click(buttons[0]);

    await waitFor(() => {
      const matches = screen.getAllByText(/nova automação/i);
      expect(matches.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("empty state 'Criar com a LIA' abre tab Criar (mesmo flow que header)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(EMPTY_API_RESPONSE));
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    await screen.findByText(/a lia pode automatizar/i);

    const createWithLiaBtn = screen.getByRole("button", { name: /criar com a lia/i });
    fireEvent.click(createWithLiaBtn);

    await waitFor(() => {
      const matches = screen.getAllByText(/nova automação/i);
      expect(matches.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("empty state 'Ver exemplos' navega para tab Exemplos (templates)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(EMPTY_API_RESPONSE));
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    await screen.findByText(/a lia pode automatizar/i);

    fireEvent.click(screen.getByRole("button", { name: /ver exemplos/i }));

    await waitFor(() => {
      expect(screen.getByText(/biblioteca de templates/i)).toBeInTheDocument();
    });
  });

  it("clicar Edit pencil em workflow existente abre builder com state populado", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(POPULATED_API_RESPONSE));
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    await screen.findByText("Notificação Automática de Aprovação");

    const editButtons = screen.getAllByRole("button", { name: /^editar$/i });
    expect(editButtons.length).toBeGreaterThan(0);
    fireEvent.click(editButtons[0]);

    await waitFor(() => {
      expect(screen.getByText(/editar automação/i)).toBeInTheDocument();
    });
  });

  it("trocar pra tab Visão Geral via tab strip volta pra lista", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(EMPTY_API_RESPONSE));
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    await screen.findByText(/a lia pode automatizar/i);

    fireEvent.click(screen.getByRole("button", { name: /criar com a lia/i }));

    await waitFor(() => {
      const matches = screen.getAllByText(/nova automação/i);
      expect(matches.length).toBeGreaterThanOrEqual(2);
    });

    fireEvent.click(screen.getByRole("button", { name: /visão geral/i }));

    await waitFor(() => {
      expect(screen.getByText(/a lia pode automatizar/i)).toBeInTheDocument();
    });
  });

  it("não chama useCreateAutomation antes do user clicar Salvar", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(EMPTY_API_RESPONSE));
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    await screen.findByText(/a lia pode automatizar/i);

    fireEvent.click(screen.getByRole("button", { name: /criar com a lia/i }));

    await waitFor(() => {
      const matches = screen.getAllByText(/nova automação/i);
      expect(matches.length).toBeGreaterThanOrEqual(2);
    });

    expect(mockCreateMutateAsync).not.toHaveBeenCalled();
    expect(mockUpdateMutateAsync).not.toHaveBeenCalled();
  });
});

// ── Sprint D.1+D.4: Item actions wiring ─────────────────────────────────

describe("AutomationsTab — Item actions wiring (Sprint D.1+D.4)", () => {
  beforeEach(() => {
    mockToggleMutate.mockClear();
    mockTestMutateAsync.mockClear();
    mockCreateMutate.mockClear();
    mockDeleteMutate.mockClear();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(POPULATED_API_RESPONSE));
  });

  it("D.1: clicar chip status 'Ativo' chama useToggleAutomationActive com isActive=false", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await screen.findByText("Notificação Automática de Aprovação");

    const toggleBtn = screen.getByTestId("workflow-toggle-auto-001");
    fireEvent.click(toggleBtn);

    expect(mockToggleMutate).toHaveBeenCalledWith({
      id: "auto-001",
      isActive: false,
    });
  });

  it("D.1: clicar chip status 'Pausado' chama toggle com isActive=true", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await screen.findByText("Lembrete de Entrevista");

    const toggleBtn = screen.getByTestId("workflow-toggle-auto-002");
    fireEvent.click(toggleBtn);

    expect(mockToggleMutate).toHaveBeenCalledWith({
      id: "auto-002",
      isActive: true,
    });
  });

  it("D.4: clicar MoreHorizontal abre popover com Testar/Duplicar/Excluir", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await screen.findByText("Notificação Automática de Aprovação");

    const moreBtn = screen.getByTestId("workflow-more-auto-001");
    fireEvent.click(moreBtn);

    await waitFor(() => {
      expect(screen.getByTestId("workflow-action-test-auto-001")).toBeInTheDocument();
      expect(screen.getByTestId("workflow-action-duplicate-auto-001")).toBeInTheDocument();
      expect(screen.getByTestId("workflow-action-delete-auto-001")).toBeInTheDocument();
    });
  });

  it("D.4: clicar 'Testar' chama useTestAutomation com {id, dryRunPayload:{}}", async () => {
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});

    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await screen.findByText("Notificação Automática de Aprovação");

    fireEvent.click(screen.getByTestId("workflow-more-auto-001"));
    await waitFor(() => {
      expect(screen.getByTestId("workflow-action-test-auto-001")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("workflow-action-test-auto-001"));

    await waitFor(() => {
      expect(mockTestMutateAsync).toHaveBeenCalledWith({
        id: "auto-001",
        dryRunPayload: {},
      });
    });
    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalled();
    });
    alertSpy.mockRestore();
  });

  it("D.4: clicar 'Duplicar' chama useCreateAutomation com clone do workflow", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await screen.findByText("Notificação Automática de Aprovação");

    fireEvent.click(screen.getByTestId("workflow-more-auto-001"));
    await waitFor(() => {
      expect(screen.getByTestId("workflow-action-duplicate-auto-001")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("workflow-action-duplicate-auto-001"));

    expect(mockCreateMutate).toHaveBeenCalledTimes(1);
    const payload = mockCreateMutate.mock.calls[0][0];
    expect(payload.trigger_type).toBe("candidate_stage_changed");
    expect(payload.action_type).toBe("send_email");
    expect(payload.name).toContain("cópia");
  });

  it("D.4: clicar 'Excluir' + confirm chama useDeleteAutomation com id", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);

    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await screen.findByText("Notificação Automática de Aprovação");

    fireEvent.click(screen.getByTestId("workflow-more-auto-001"));
    await waitFor(() => {
      expect(screen.getByTestId("workflow-action-delete-auto-001")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("workflow-action-delete-auto-001"));

    expect(confirmSpy).toHaveBeenCalled();
    expect(mockDeleteMutate).toHaveBeenCalledWith("auto-001");

    confirmSpy.mockRestore();
  });

  it("D.4: cancelar confirm dialog NÃO chama deleteMutation", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);

    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await screen.findByText("Notificação Automática de Aprovação");

    fireEvent.click(screen.getByTestId("workflow-more-auto-001"));
    await waitFor(() => {
      expect(screen.getByTestId("workflow-action-delete-auto-001")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("workflow-action-delete-auto-001"));

    expect(confirmSpy).toHaveBeenCalled();
    expect(mockDeleteMutate).not.toHaveBeenCalled();

    confirmSpy.mockRestore();
  });
});

// ── Sprint A.7: real types wiring (useTriggerTypes / useActionTypes) ─────

describe("AutomationsTab — Catalog wiring (Sprint A.7)", () => {
  beforeEach(() => {
    // reset to canonical success state by default
    mockTriggerTypesState.data = {
      success: true,
      data: {
        trigger_types: [
          { value: "candidate_stage_changed", name: "Candidato mudou de etapa", description: "..." },
          { value: "interview_scheduled", name: "Entrevista agendada", description: "..." },
        ],
      },
    };
    mockTriggerTypesState.error = null;
    mockTriggerTypesState.isLoading = false;
    mockActionTypesState.data = {
      success: true,
      data: {
        action_types: [
          { value: "send_email", name: "Enviar e-mail", description: "...", config_fields: [] },
          { value: "send_whatsapp", name: "Enviar WhatsApp", description: "...", config_fields: [] },
        ],
      },
    };
    mockActionTypesState.error = null;
    mockActionTypesState.isLoading = false;
    mockCreateMutateAsync.mockClear();
    mockUpdateMutateAsync.mockClear();
  });

  it("renderiza builder sem crash quando triggers/actions vêm do backend canonical", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(EMPTY_API_RESPONSE));
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    await screen.findByText(/a lia pode automatizar/i);
    fireEvent.click(screen.getByRole("button", { name: /criar com a lia/i }));

    await waitFor(() => {
      // SentenceBuilder renderiza — section title visível 2x (header CTA + body)
      const headers = screen.getAllByText(/nova automação/i);
      expect(headers.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("usa mock fallback quando useTriggerTypes retorna error (REGRA 4 explicit warn)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(EMPTY_API_RESPONSE));
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

    mockTriggerTypesState.data = undefined;
    mockTriggerTypesState.error = new Error("backend down");

    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await screen.findByText(/a lia pode automatizar/i);
    fireEvent.click(screen.getByRole("button", { name: /criar com a lia/i }));

    await waitFor(() => {
      const headers = screen.getAllByText(/nova automação/i);
      expect(headers.length).toBeGreaterThanOrEqual(2);
    });

    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining("useTriggerTypes error"),
      expect.any(Error),
    );

    warnSpy.mockRestore();
  });

  it("usa mock fallback quando backend retorna array vazio (loading-equivalent)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(EMPTY_API_RESPONSE));

    mockTriggerTypesState.data = { success: true, data: { trigger_types: [] } };
    mockActionTypesState.data = { success: true, data: { action_types: [] } };

    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await screen.findByText(/a lia pode automatizar/i);
    fireEvent.click(screen.getByRole("button", { name: /criar com a lia/i }));

    await waitFor(() => {
      const headers = screen.getAllByText(/nova automação/i);
      expect(headers.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("não crasha quando backend retorna shape inesperado (defesa adapter)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(EMPTY_API_RESPONSE));

    mockTriggerTypesState.data = { unexpected: "garbage" };
    mockActionTypesState.data = null;

    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);
    await screen.findByText(/a lia pode automatizar/i);
    fireEvent.click(screen.getByRole("button", { name: /criar com a lia/i }));

    await waitFor(() => {
      const headers = screen.getAllByText(/nova automação/i);
      expect(headers.length).toBeGreaterThanOrEqual(2);
    });
  });
});

describe("AutomationsTab — Sprint D.3 LIA chat bridge hydration", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    mockSearchParamsState.current = new URLSearchParams();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ success: true, data: { automations: [], total: 0 } }),
      }),
    );
  });

  it("hidrata builder a partir de sessionStorage payload (vindo do chat LIA)", async () => {
    const payload = {
      trigger: { type: "candidate_applied", params: {} },
      conditions: [],
      actions: [{ type: "send_whatsapp", params: { template_id: "interview_invite" } }],
      name: "Convite WhatsApp ao se candidatar",
    };
    window.sessionStorage.setItem(
      "lia-pending-automation-state",
      JSON.stringify(payload),
    );

    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    // Builder abre — title de edição/criação aparece
    await waitFor(() => {
      const headers = screen.getAllByText(/nova automação/i);
      expect(headers.length).toBeGreaterThanOrEqual(1);
    });

    // sessionStorage é limpo após hidratação (one-shot consume)
    expect(
      window.sessionStorage.getItem("lia-pending-automation-state"),
    ).toBeNull();
  });

  it("abre builder em modo novo quando URL tem ?view=builder (deep-link)", async () => {
    mockSearchParamsState.current = new URLSearchParams("view=builder");

    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    await waitFor(() => {
      const headers = screen.getAllByText(/nova automação/i);
      expect(headers.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("não abre builder sem payload nem deep-link (modo overview default)", async () => {
    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    // Overview state: empty state aparece (sem builder header de edição)
    await screen.findByText(/a lia pode automatizar/i);
  });

  it("gracefully handles sessionStorage JSON inválido (REGRA 4 anti-silent)", async () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    window.sessionStorage.setItem(
      "lia-pending-automation-state",
      "{not-valid-json",
    );

    renderWithIntl(<AutomationsTab onSettingsChange={() => {}} />);

    // Não crasha — log warn + fallback pra overview
    await screen.findByText(/a lia pode automatizar/i);
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining("[AutomationsTab]"),
      expect.anything(),
    );

    warnSpy.mockRestore();
  });
});
