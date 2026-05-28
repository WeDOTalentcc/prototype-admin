/**
 * Onda 3 F8 (2026-05-28) — StageAgentTriggerModal canonical tests.
 *
 * Cobertura:
 *   1. Trigger modes mostrados = APENAS os 4 do target_type=pipeline_stage
 *      (on_enter_stage, on_exit_stage, on_stuck_in_stage, on_stage_change).
 *   2. Submit OK fecha modal.
 *   3. Submit sem agente: botão disabled.
 *   4. Erro do backend mostra mensagem inline.
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import { StageAgentTriggerModal } from "../StageAgentTriggerModal"

const messages = {
  pipeline: {
    stage: {
      triggerMode: {
        on_enter_stage: "Entrar nesta etapa",
        on_exit_stage: "Sair desta etapa",
        on_stuck_in_stage: "Ficar travado nesta etapa",
        on_stage_change: "Houver qualquer mudança",
      },
      attachModal: {
        title: "Adicionar agente a esta etapa",
        stageLabel: "Etapa",
        cancel: "Cancelar",
        submit: "Adicionar",
        loadingAgents: "Carregando agentes...",
        fields: {
          agent: "Agente",
          agentPlaceholder: "Selecione um agente",
          trigger: "Disparar quando candidato",
          activateNow: "Ativar imediatamente",
        },
        errors: {
          agentRequired: "Selecione um agente.",
          agentsLoadFailed: "Erro",
          generic: "Falha.",
        },
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

function renderModal(props: Partial<React.ComponentProps<typeof StageAgentTriggerModal>> = {}) {
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
        json: () => Promise.resolve({ agents: [{ id: "a1", name: "Triagem Bot" }], total: 1 }),
      })
    }
    return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({}) })
  }) as unknown as typeof fetch
}

describe("StageAgentTriggerModal", () => {
  it("mostra APENAS os 4 trigger modes do target_type=pipeline_stage", async () => {
    mockAgentsFetch()
    renderModal()
    await waitFor(() => {
      expect(screen.getByTestId("stage-trigger-radio-on_enter_stage")).toBeInTheDocument()
      expect(screen.getByTestId("stage-trigger-radio-on_exit_stage")).toBeInTheDocument()
      expect(screen.getByTestId("stage-trigger-radio-on_stuck_in_stage")).toBeInTheDocument()
      expect(screen.getByTestId("stage-trigger-radio-on_stage_change")).toBeInTheDocument()
      expect(screen.queryByTestId("stage-trigger-radio-on_create")).toBeNull()
      expect(screen.queryByTestId("stage-trigger-radio-on_apply")).toBeNull()
    })
  })

  it("submit sem agente: botão disabled", async () => {
    mockAgentsFetch()
    renderModal()
    await waitFor(() => screen.getByTestId("stage-attach-submit"))
    const btn = screen.getByTestId("stage-attach-submit") as HTMLButtonElement
    expect(btn.disabled).toBe(true)
  })

  it("submit OK chama onAssigned + fecha", async () => {
    mockAgentsFetch()
    const onClose = vi.fn()
    const onAssigned = vi.fn()
    renderModal({ onClose, onAssigned })
    await waitFor(() => screen.getByTestId("stage-agent-select"))

    fireEvent.change(screen.getByTestId("stage-agent-select"), {
      target: { value: "a1" },
    })

    fireEvent.click(screen.getByTestId("stage-attach-submit"))

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
          json: () => Promise.resolve({ agents: [{ id: "a1", name: "Bot" }], total: 1 }),
        })
      }
      return Promise.resolve({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: "Stage error" }),
      })
    }) as unknown as typeof fetch

    renderModal()
    await waitFor(() => screen.getByTestId("stage-agent-select"))
    fireEvent.change(screen.getByTestId("stage-agent-select"), {
      target: { value: "a1" },
    })
    fireEvent.click(screen.getByTestId("stage-attach-submit"))
    await waitFor(() => {
      expect(screen.getByTestId("stage-attach-error")).toBeInTheDocument()
    })
  })
})
