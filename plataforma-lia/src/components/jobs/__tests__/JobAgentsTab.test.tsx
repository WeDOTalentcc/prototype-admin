/**
 * Onda 3 F8 (2026-05-28) — JobAgentsTab canonical tests.
 *
 * Cobertura:
 *   1. Empty state quando deployments=[].
 *   2. Renderiza cards quando há deployments.
 *   3. Botão pause chama PATCH com is_active=false.
 *   4. Detach confirma + invoca DELETE.
 *   5. CTA "Acoplar agente" abre modal.
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import { JobAgentsTab } from "../JobAgentsTab"

const messages = {
  jobs: {
    agents: {
      header: "Agentes acoplados a esta vaga",
      subheader: "Sub",
      loading: "Carregando agentes acoplados...",
      loadError: "Erro",
      emptyTitle: "Nenhum agente acoplado ainda",
      empty: "Acople um agente para automatizar tarefas desta vaga.",
      fallbackAgentName: "Agente",
      lastRun: "Última execução",
      neverRun: "Ainda não executou",
      processed: "{count} processados",
      detachConfirm: "Tem certeza?",
      attachSuccess: "ok",
      status: { active: "Ativo", paused: "Pausado" },
      cta: { attach: "Acoplar agente" },
      action: {
        pause: "Pausar",
        resume: "Ativar",
        detach: "Desacoplar",
        viewReasoning: "Ver raciocínio",
      },
      triggerMode: {
        on_create: "Quando criada",
        on_schedule: "Sob agendamento",
        manual: "Manualmente",
        on_apply: "Quando aplicar",
      },
      attachModal: {
        title: "Acoplar agente a esta vaga",
        jobLabel: "Vaga",
        cancel: "Cancelar",
        submit: "Acoplar",
        loadingAgents: "Carregando...",
        fields: {
          agent: "Agente",
          agentPlaceholder: "Selecione",
          trigger: "Trigger",
          schedule: "Agendamento",
          activateNow: "Ativar",
        },
        errors: {
          agentRequired: "...",
          agentsLoadFailed: "...",
          generic: "...",
        },
      },
    },
  },
}

beforeEach(() => {
  cleanup()
  vi.restoreAllMocks()
  Object.defineProperty(window, "localStorage", {
    value: {
      getItem: vi.fn(() => "token"),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    },
    configurable: true,
  })
})

function renderTab(jobAgentsResponse: unknown) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  global.fetch = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
    if (url.includes("/jobs/") && url.endsWith("/agents") && (!init?.method || init.method === "GET")) {
      return Promise.resolve({
        ok: true, status: 200,
        json: () => Promise.resolve(jobAgentsResponse),
      })
    }
    if (url.includes("/company-ai-persona")) {
      return Promise.resolve({
        ok: true, status: 200, json: () => Promise.resolve({ name: "LIA", tone: "professional" }),
      })
    }
    return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) })
  }) as unknown as typeof fetch

  return render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="pt-BR" messages={messages as any}>
        <JobAgentsTab jobId="job-1" jobTitle="Dev Sr" />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  )
}

describe("JobAgentsTab", () => {
  it("empty state quando deployments=[]", async () => {
    renderTab({ deployments: [], total: 0 })
    await waitFor(() => {
      expect(screen.getByTestId("job-agents-empty")).toBeInTheDocument()
    })
  })

  it("renderiza cards quando há deployments", async () => {
    renderTab({
      deployments: [
        {
          id: "d1",
          agent_id: "a1",
          company_id: "c1",
          target_type: "job",
          target_id: "job-1",
          target_name: null,
          trigger_mode: "on_schedule",
          schedule_cron: "0 9 * * *",
          is_active: true,
          config_overrides: {},
          execution_count: 3,
          candidates_processed: 5,
          last_execution_at: "2026-05-27T10:00:00Z",
          created_by: "u1",
          created_at: null,
          updated_at: null,
          agent_name: "Sourcing Bot",
          agent_category: null,
          agent_status: "active",
          agent_domain: null,
        },
      ],
      total: 1,
    })
    await waitFor(() => {
      expect(screen.getByTestId("job-agent-card-d1")).toBeInTheDocument()
      expect(screen.getByText("Sourcing Bot")).toBeInTheDocument()
    })
  })

  it("CTA 'Acoplar agente' abre modal", async () => {
    renderTab({ deployments: [], total: 0 })
    await waitFor(() => screen.getByTestId("attach-agent-cta"))
    fireEvent.click(screen.getByTestId("attach-agent-cta"))
    await waitFor(() => {
      expect(screen.getByTestId("assign-agent-to-job-modal")).toBeInTheDocument()
    })
  })

  it("botão pause chama PATCH com is_active=false", async () => {
    renderTab({
      deployments: [
        {
          id: "d1",
          agent_id: "a1",
          company_id: "c",
          target_type: "job",
          target_id: "job-1",
          target_name: null,
          trigger_mode: "manual",
          schedule_cron: null,
          is_active: true,
          config_overrides: {},
          execution_count: 0,
          candidates_processed: 0,
          last_execution_at: null,
          created_by: "u",
          created_at: null,
          updated_at: null,
          agent_name: "Bot",
          agent_category: null,
          agent_status: "active",
          agent_domain: null,
        },
      ],
      total: 1,
    })
    await waitFor(() => screen.getByTestId("toggle-pause-d1"))
    fireEvent.click(screen.getByTestId("toggle-pause-d1"))
    await waitFor(() => {
      const calls = (global.fetch as ReturnType<typeof vi.fn>).mock.calls
      const patch = calls.find(
        ([url, init]) =>
          typeof url === "string" &&
          url.includes("/agent-deployments/d1") &&
          (init as RequestInit | undefined)?.method === "PATCH",
      )
      expect(patch).toBeTruthy()
      const body = JSON.parse((patch![1] as RequestInit).body as string)
      expect(body).toEqual({ is_active: false })
    })
  })

  it("detach confirma + invoca DELETE", async () => {
    const originalConfirm = window.confirm
    window.confirm = vi.fn(() => true)
    renderTab({
      deployments: [
        {
          id: "d1",
          agent_id: "a1",
          company_id: "c",
          target_type: "job",
          target_id: "job-1",
          target_name: null,
          trigger_mode: "manual",
          schedule_cron: null,
          is_active: true,
          config_overrides: {},
          execution_count: 0,
          candidates_processed: 0,
          last_execution_at: null,
          created_by: "u",
          created_at: null,
          updated_at: null,
          agent_name: "Bot",
          agent_category: null,
          agent_status: "active",
          agent_domain: null,
        },
      ],
      total: 1,
    })
    await waitFor(() => screen.getByTestId("detach-d1"))
    fireEvent.click(screen.getByTestId("detach-d1"))
    await waitFor(() => {
      const calls = (global.fetch as ReturnType<typeof vi.fn>).mock.calls
      const del = calls.find(
        ([url, init]) =>
          typeof url === "string" &&
          url.includes("/jobs/job-1/agents/d1") &&
          (init as RequestInit | undefined)?.method === "DELETE",
      )
      expect(del).toBeTruthy()
    })
    window.confirm = originalConfirm
  })
})
