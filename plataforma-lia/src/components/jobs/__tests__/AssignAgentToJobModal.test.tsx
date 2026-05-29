/**
 * Onda 3 F8 → Onda 4 Agent E (2026-05-29) — AssignAgentToJobModal tests.
 *
 * Apos refactor Rule of Three (Onda 4), este modal e um wrapper thin sobre
 * src/components/shared/agents/AssignAgentModal. Estes tests sao
 * smoke + integration do wrapper:
 *   1. Abre com titulo + jobTitle.
 *   2. Trigger modes mostrados = APENAS os 4 do target_type=job.
 *   3. Submit OK fecha + chama onAssigned.
 *   4. Erro do backend mostra mensagem inline.
 *
 * Tests profundos do comportamento generico moram em
 * src/components/shared/agents/__tests__/AssignAgentModal.test.tsx.
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import { AssignAgentToJobModal } from "../AssignAgentToJobModal"

const messages = {
  agents: {
    assignModal: {
      title: {
        job: "Acoplar agente a esta vaga",
        talent_pool: "Adicionar agente ao pool",
        pipeline_stage: "Adicionar agente a esta etapa",
        candidate_list: "Adicionar agente a esta lista",
      },
      submit: {
        job: "Acoplar",
        talent_pool: "Atribuir",
        pipeline_stage: "Adicionar",
        candidate_list: "Adicionar",
      },
      cancel: "Cancelar",
      loadingAgents: "Carregando...",
      jobLabel: "Vaga",
      poolLabel: "Pool",
      stageLabel: "Etapa",
      listLabel: "Lista",
      fields: {
        agent: "Agente",
        agentPlaceholder: "Selecione um agente",
        trigger: "Quando rodar",
        schedule: "Agendamento",
        activateNow: "Ativar imediatamente",
      },
      errors: {
        agentRequired: "Selecione um agente para continuar.",
        agentsLoadFailed: "Erro ao carregar agentes",
        generic: "Falha ao acoplar agente.",
      },
    },
  },
  jobs: {
    agents: {
      triggerMode: {
        on_create: "Quando a vaga for criada",
        on_schedule: "Sob agendamento",
        manual: "Manualmente",
        on_apply: "Quando candidato aplicar",
      },
    },
  },
  pipeline: {
    stage: {
      triggerMode: {
        on_enter_stage: "Entrar nesta etapa",
        on_exit_stage: "Sair desta etapa",
        on_stuck_in_stage: "Ficar travado nesta etapa",
        on_stage_change: "Houver qualquer mudança",
      },
    },
  },
}

beforeEach(() => {
  cleanup()
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

function renderModal(
  props: Partial<React.ComponentProps<typeof AssignAgentToJobModal>> = {},
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="pt-BR" messages={messages as any}>
        <AssignAgentToJobModal
          jobId="job-1"
          jobTitle="Dev Sênior"
          open={true}
          onClose={vi.fn()}
          {...props}
        />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  )
}

function mockAgentsFetch() {
  global.fetch = vi.fn().mockImplementation((url: string) => {
    if (url.includes("/custom-agents")) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            agents: [{ id: "a1", name: "Sourcing Bot" }],
            total: 1,
          }),
      })
    }
    return Promise.resolve({
      ok: true,
      status: 201,
      json: () => Promise.resolve({}),
    })
  }) as unknown as typeof fetch
}

describe("AssignAgentToJobModal (wrapper) — Onda 4 Agent E", () => {
  it("abre com titulo + jobTitle", async () => {
    mockAgentsFetch()
    renderModal()
    await waitFor(() => {
      expect(screen.getByText("Acoplar agente a esta vaga")).toBeInTheDocument()
      expect(screen.getByText("Dev Sênior")).toBeInTheDocument()
    })
  })

  it("mostra APENAS os 4 trigger modes do target_type=job", async () => {
    mockAgentsFetch()
    renderModal()
    await waitFor(() => {
      expect(
        screen.getByTestId("assign-agent-to-job-trigger-radio-on_create"),
      ).toBeInTheDocument()
      expect(
        screen.getByTestId("assign-agent-to-job-trigger-radio-on_schedule"),
      ).toBeInTheDocument()
      expect(
        screen.getByTestId("assign-agent-to-job-trigger-radio-manual"),
      ).toBeInTheDocument()
      expect(
        screen.getByTestId("assign-agent-to-job-trigger-radio-on_apply"),
      ).toBeInTheDocument()
      // stage-only modes NAO aparecem
      expect(
        screen.queryByTestId("assign-agent-to-job-trigger-radio-on_enter_stage"),
      ).toBeNull()
    })
  })

  it("submit button disabled sem agente selecionado", async () => {
    mockAgentsFetch()
    renderModal()
    await waitFor(() => screen.getByTestId("assign-agent-to-job-submit"))
    const btn = screen.getByTestId("assign-agent-to-job-submit") as HTMLButtonElement
    expect(btn.disabled).toBe(true)
  })

  it("submit OK chama onAssigned + fecha", async () => {
    mockAgentsFetch()
    const onClose = vi.fn()
    const onAssigned = vi.fn()
    renderModal({ onClose, onAssigned })
    await waitFor(() => screen.getByTestId("assign-agent-to-job-agent-select"))

    fireEvent.change(
      screen.getByTestId("assign-agent-to-job-agent-select"),
      { target: { value: "a1" } },
    )

    const btn = screen.getByTestId("assign-agent-to-job-submit") as HTMLButtonElement
    expect(btn.disabled).toBe(false)
    fireEvent.click(btn)
    await waitFor(() => {
      expect(onAssigned).toHaveBeenCalled()
      expect(onClose).toHaveBeenCalled()
    })
  })

  it("erro do backend mostra mensagem inline", async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/custom-agents") && !url.includes("agents/")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve({
              agents: [{ id: "a1", name: "Bot" }],
              total: 1,
            }),
        })
      }
      return Promise.resolve({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: "Boom" }),
      })
    }) as unknown as typeof fetch

    renderModal()
    await waitFor(() => screen.getByTestId("assign-agent-to-job-agent-select"))
    fireEvent.change(
      screen.getByTestId("assign-agent-to-job-agent-select"),
      { target: { value: "a1" } },
    )
    fireEvent.click(screen.getByTestId("assign-agent-to-job-submit"))
    await waitFor(() => {
      expect(screen.getByTestId("assign-agent-to-job-error")).toBeInTheDocument()
    })
  })
})
