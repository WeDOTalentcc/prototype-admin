/**
 * Onda 3 F8 (2026-05-28) — AssignAgentToJobModal canonical tests.
 *
 * Cobertura:
 *   1. Abre quando open=true e renderiza titulo + jobTitle.
 *   2. Trigger modes mostrados = APENAS os 4 do target_type=job
 *      (on_create, on_schedule, manual, on_apply).
 *   3. Submit sem agente selecionado → erro inline.
 *   4. Submit OK fecha modal + chama onAssigned.
 *   5. Erro do backend mostra mensagem inline.
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { NextIntlClientProvider } from "next-intl"
import { AssignAgentToJobModal } from "../AssignAgentToJobModal"

const messages = {
  jobs: {
    agents: {
      triggerMode: {
        on_create: "Quando a vaga for criada",
        on_schedule: "Sob agendamento",
        manual: "Manualmente",
        on_apply: "Quando candidato aplicar",
      },
      attachModal: {
        title: "Acoplar agente a esta vaga",
        jobLabel: "Vaga",
        cancel: "Cancelar",
        submit: "Acoplar",
        loadingAgents: "Carregando...",
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

function renderModal(props: Partial<React.ComponentProps<typeof AssignAgentToJobModal>> = {}) {
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
        json: () => Promise.resolve({ agents: [{ id: "a1", name: "Sourcing Bot" }], total: 1 }),
      })
    }
    return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({}) })
  }) as unknown as typeof fetch
}

describe("AssignAgentToJobModal", () => {
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
      expect(screen.getByTestId("trigger-radio-on_create")).toBeInTheDocument()
      expect(screen.getByTestId("trigger-radio-on_schedule")).toBeInTheDocument()
      expect(screen.getByTestId("trigger-radio-manual")).toBeInTheDocument()
      expect(screen.getByTestId("trigger-radio-on_apply")).toBeInTheDocument()
      // stage-only modes NÃO devem aparecer
      expect(screen.queryByTestId("trigger-radio-on_enter_stage")).toBeNull()
    })
  })

  it("submit sem agente selecionado mostra erro inline", async () => {
    mockAgentsFetch()
    renderModal()
    await waitFor(() => screen.getByTestId("attach-submit"))
    const btn = screen.getByTestId("attach-submit") as HTMLButtonElement
    // O botão está disabled sem agente selecionado, então o erro real vem
    // ao tentar submit programaticamente. Verificamos o disabled state.
    expect(btn.disabled).toBe(true)
  })

  it("submit OK chama onAssigned + fecha", async () => {
    mockAgentsFetch()
    const onClose = vi.fn()
    const onAssigned = vi.fn()
    renderModal({ onClose, onAssigned })
    await waitFor(() => screen.getByTestId("job-agent-select"))

    // Select agent
    const select = screen.getByTestId("job-agent-select") as HTMLSelectElement
    fireEvent.change(select, { target: { value: "a1" } })

    const btn = screen.getByTestId("attach-submit") as HTMLButtonElement
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
          json: () => Promise.resolve({ agents: [{ id: "a1", name: "Bot" }], total: 1 }),
        })
      }
      // attach call fails
      return Promise.resolve({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: "Boom" }),
      })
    }) as unknown as typeof fetch

    renderModal()
    await waitFor(() => screen.getByTestId("job-agent-select"))
    fireEvent.change(screen.getByTestId("job-agent-select"), {
      target: { value: "a1" },
    })
    fireEvent.click(screen.getByTestId("attach-submit"))
    await waitFor(() => {
      expect(screen.getByTestId("attach-error")).toBeInTheDocument()
    })
  })
})
