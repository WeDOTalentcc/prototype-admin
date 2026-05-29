/**
 * Onda 3 F8 → Onda 4 Agent E (2026-05-29) — StageAgentTriggerModal tests.
 *
 * Apos refactor Rule of Three (Onda 4), este modal e wrapper thin sobre
 * src/components/shared/agents/AssignAgentModal. Smoke + integration:
 *   1. Trigger modes mostrados = APENAS os 4 do target_type=pipeline_stage.
 *   2. Submit OK fecha modal.
 *   3. Submit sem agente: botao disabled.
 *   4. Erro do backend mostra mensagem inline.
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import { StageAgentTriggerModal } from "../StageAgentTriggerModal"

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
      loadingAgents: "Carregando agentes...",
      jobLabel: "Vaga",
      poolLabel: "Pool",
      stageLabel: "Etapa",
      listLabel: "Lista",
      fields: {
        agent: "Agente",
        agentPlaceholder: "Selecione um agente",
        trigger: "Disparar quando candidato",
        schedule: "Agendamento",
        activateNow: "Ativar imediatamente",
      },
      errors: {
        agentRequired: "Selecione um agente.",
        agentsLoadFailed: "Erro",
        generic: "Falha.",
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
  props: Partial<React.ComponentProps<typeof StageAgentTriggerModal>> = {},
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="pt-BR" messages={messages as any}>
        <StageAgentTriggerModal
          stageId="stage-1"
          stageName="Triagem Inicial"
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
    if (url.includes("/custom-agents") && !url.includes("deployments")) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            agents: [{ id: "a1", name: "Triagem Bot" }],
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

describe("StageAgentTriggerModal (wrapper) — Onda 4 Agent E", () => {
  it("mostra APENAS os 4 trigger modes do target_type=pipeline_stage", async () => {
    mockAgentsFetch()
    renderModal()
    await waitFor(() => {
      expect(
        screen.getByTestId("stage-agent-trigger-trigger-radio-on_enter_stage"),
      ).toBeInTheDocument()
      expect(
        screen.getByTestId("stage-agent-trigger-trigger-radio-on_exit_stage"),
      ).toBeInTheDocument()
      expect(
        screen.getByTestId("stage-agent-trigger-trigger-radio-on_stuck_in_stage"),
      ).toBeInTheDocument()
      expect(
        screen.getByTestId("stage-agent-trigger-trigger-radio-on_stage_change"),
      ).toBeInTheDocument()
      expect(
        screen.queryByTestId("stage-agent-trigger-trigger-radio-on_create"),
      ).toBeNull()
      expect(
        screen.queryByTestId("stage-agent-trigger-trigger-radio-on_apply"),
      ).toBeNull()
    })
  })

  it("submit sem agente: botao disabled", async () => {
    mockAgentsFetch()
    renderModal()
    await waitFor(() => screen.getByTestId("stage-agent-trigger-submit"))
    const btn = screen.getByTestId("stage-agent-trigger-submit") as HTMLButtonElement
    expect(btn.disabled).toBe(true)
  })

  it("submit OK chama onAssigned + fecha", async () => {
    mockAgentsFetch()
    const onClose = vi.fn()
    const onAssigned = vi.fn()
    renderModal({ onClose, onAssigned })
    await waitFor(() => screen.getByTestId("stage-agent-trigger-agent-select"))

    fireEvent.change(
      screen.getByTestId("stage-agent-trigger-agent-select"),
      { target: { value: "a1" } },
    )

    fireEvent.click(screen.getByTestId("stage-agent-trigger-submit"))

    await waitFor(() => {
      expect(onAssigned).toHaveBeenCalled()
      expect(onClose).toHaveBeenCalled()
    })
  })

  it("erro do backend mostra mensagem inline", async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/custom-agents") && !url.includes("deployments")) {
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
        json: () => Promise.resolve({ detail: "Stage error" }),
      })
    }) as unknown as typeof fetch

    renderModal()
    await waitFor(() => screen.getByTestId("stage-agent-trigger-agent-select"))
    fireEvent.change(
      screen.getByTestId("stage-agent-trigger-agent-select"),
      { target: { value: "a1" } },
    )
    fireEvent.click(screen.getByTestId("stage-agent-trigger-submit"))
    await waitFor(() => {
      expect(screen.getByTestId("stage-agent-trigger-error")).toBeInTheDocument()
    })
  })
})
