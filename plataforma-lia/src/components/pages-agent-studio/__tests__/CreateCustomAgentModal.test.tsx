/**
 * Sprint 4 Fase 3 (Studio Experience) — config humana `/edit`.
 *
 * Contexto: a tela de criar/editar agente custom (`CreateCustomAgentModal`)
 * expunha jargão de developer (system_prompt mono, allowed_tools como string
 * vírgula-separada, temperature numérica, max_steps, domain crus). Esta sprint
 * reescreve para um recrutador: checkboxes PT, "estilo de resposta" segmented,
 * disclosure "Configuração avançada".
 *
 * Coverage:
 *  - Ferramentas como checkboxes (não input vírgula-separado); marcar inclui o
 *    slug canonical no allowed_tools do submit.
 *  - "Estilo de resposta" segmented (Consistente/Equilibrado/Criativo) →
 *    temperature 0.2/0.5/0.8 no submit. O número nunca aparece na UI.
 *  - "Configuração avançada" recolhida por default (domain + max_steps tucked).
 *  - Edit: temperature existente deriva o preset; allowed_tools existentes vêm
 *    pré-marcados.
 *  - Contrato backend preservado (slug array + número exato no body do fetch).
 *  - i18n canonical contract: zero MISSING_MESSAGE com messages/pt-BR.json real.
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import ptBRMessages from "../../../../messages/pt-BR.json"
import { CreateCustomAgentModal } from "../CustomAgentsTab"

vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({
    persona: { name: "Aurora", tone: "profissional" },
    isLoading: false,
    isSaving: false,
    error: null,
    validationErrors: [],
    reload: vi.fn(),
    update: vi.fn(),
  }),
}))

const AVAILABLE_TOOLS = [
  "search_candidates",
  "get_candidate_details",
  "move_candidate",
  "send_email",
  "get_pipeline_summary",
]

function mockFetch(saveBodyRef: { current: unknown }) {
  return vi.fn(async (url: string, init?: RequestInit) => {
    if (typeof url === "string" && url.includes("available-tools")) {
      return {
        ok: true,
        json: async () => ({ tools: AVAILABLE_TOOLS }),
      } as Response
    }
    if (typeof url === "string" && url.includes("job-vacancies")) {
      return {
        ok: true,
        json: async () => ({ jobs: [{ id: "job-1", title: "Vaga Engenheiro" }, { id: "job-2", title: "Vaga Designer" }] }),
      } as Response
    }
    if (typeof url === "string" && url.includes("talent-pools")) {
      return {
        ok: true,
        json: async () => ({ pools: [{ id: "pool-1", name: "Banco Tech" }] }),
      } as Response
    }
    // save (POST/PATCH custom-agents)
    saveBodyRef.current = init?.body ? JSON.parse(init.body as string) : null
    return { ok: true, json: async () => ({ id: "new-agent" }) } as Response
  })
}

function renderModal(agent: Parameters<typeof CreateCustomAgentModal>[0]["agent"]) {
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={ptBRMessages as Record<string, unknown>}>
      <CreateCustomAgentModal agent={agent} onClose={vi.fn()} onSaved={vi.fn()} />
    </NextIntlClientProvider>,
  )
}

describe("CreateCustomAgentModal — config humana (Sprint 4)", () => {
  let saveBodyRef: { current: unknown }

  beforeEach(() => {
    saveBodyRef = { current: null }
    vi.stubGlobal("fetch", mockFetch(saveBodyRef))
  })

  it("renders tools as checkboxes, not a comma-separated text input", async () => {
    renderModal(null)
    await waitFor(() => {
      expect(
        screen.getByRole("checkbox", { name: ptBRMessages.agents.customAgents.tools.search_candidates }),
      ).toBeTruthy()
    })
    // The old comma-separated placeholder must be gone.
    expect(screen.queryByPlaceholderText(/search_candidates, list_jobs/)).toBeNull()
  })

  it("checking a tool adds its canonical slug to allowed_tools on submit", async () => {
    renderModal(null)
    await waitFor(() => screen.getByRole("checkbox", { name: ptBRMessages.agents.customAgents.tools.search_candidates }))

    fireEvent.change(screen.getByLabelText(ptBRMessages.agents.customAgents.name), { target: { value: "Triagem Tech" } })
    fireEvent.change(screen.getByLabelText(ptBRMessages.agents.customAgents.role), { target: { value: "Analista" } })
    fireEvent.change(screen.getByLabelText(ptBRMessages.agents.customAgents.instructionsLabel), { target: { value: "Avalie candidatos." } })

    fireEvent.click(screen.getByRole("checkbox", { name: ptBRMessages.agents.customAgents.tools.search_candidates }))
    fireEvent.click(screen.getByRole("checkbox", { name: ptBRMessages.agents.customAgents.tools.send_email }))

    fireEvent.click(screen.getByRole("button", { name: ptBRMessages.agents.customAgents.createAgent }))

    await waitFor(() => expect(saveBodyRef.current).toBeTruthy())
    const body = saveBodyRef.current as { allowed_tools: string[] }
    expect(body.allowed_tools).toContain("search_candidates")
    expect(body.allowed_tools).toContain("send_email")
    expect(body.allowed_tools).not.toContain("move_candidate")
  })

  it("'Mais criativo' style maps to temperature 0.8 on submit", async () => {
    renderModal(null)
    await waitFor(() => screen.getByRole("checkbox", { name: ptBRMessages.agents.customAgents.tools.search_candidates }))

    fireEvent.change(screen.getByLabelText(ptBRMessages.agents.customAgents.name), { target: { value: "Sourcing" } })
    fireEvent.change(screen.getByLabelText(ptBRMessages.agents.customAgents.role), { target: { value: "Sourcer" } })
    fireEvent.change(screen.getByLabelText(ptBRMessages.agents.customAgents.instructionsLabel), { target: { value: "Busque talentos." } })

    fireEvent.click(screen.getByRole("radio", { name: ptBRMessages.agents.customAgents.styleCreative }))
    fireEvent.click(screen.getByRole("button", { name: ptBRMessages.agents.customAgents.createAgent }))

    await waitFor(() => expect(saveBodyRef.current).toBeTruthy())
    expect((saveBodyRef.current as { temperature: number }).temperature).toBe(0.8)
  })

  it("default style is balanced → temperature 0.5; no raw number shown", async () => {
    renderModal(null)
    await waitFor(() => screen.getByRole("checkbox", { name: ptBRMessages.agents.customAgents.tools.search_candidates }))

    // No number input for temperature anywhere.
    const spinbuttons = screen.queryAllByRole("spinbutton")
    // max_steps (advanced) is a number input but lives inside collapsed <details>.
    // Temperature must NOT be a number input.
    spinbuttons.forEach(el => {
      expect(el.getAttribute("max")).not.toBe("2")
    })

    fireEvent.change(screen.getByLabelText(ptBRMessages.agents.customAgents.name), { target: { value: "A" } })
    fireEvent.change(screen.getByLabelText(ptBRMessages.agents.customAgents.role), { target: { value: "B" } })
    fireEvent.change(screen.getByLabelText(ptBRMessages.agents.customAgents.instructionsLabel), { target: { value: "C." } })
    fireEvent.click(screen.getByRole("button", { name: ptBRMessages.agents.customAgents.createAgent }))

    await waitFor(() => expect(saveBodyRef.current).toBeTruthy())
    expect((saveBodyRef.current as { temperature: number }).temperature).toBe(0.5)
  })

  it("'Configuração avançada' is collapsed by default", async () => {
    renderModal(null)
    await waitFor(() => screen.getByRole("checkbox", { name: ptBRMessages.agents.customAgents.tools.search_candidates }))
    // Radix Dialog renders into a portal, so query the whole document.
    const details = document.querySelector("details")
    expect(details).toBeTruthy()
    expect((details as HTMLDetailsElement).open).toBe(false)
    // The advanced summary is present and collapsed.
    expect(screen.getByText(ptBRMessages.agents.customAgents.advancedConfig)).toBeTruthy()
  })

  it("editing derives the style from existing temperature and pre-checks tools", async () => {
    renderModal({
      id: "a1",
      name: "Existente",
      role: "Role",
      description: null,
      system_prompt: "Prompt existente",
      allowed_tools: ["search_candidates", "get_candidate_details"],
      domain: "screening",
      icon: "bot",
      status: "active",
      version: 1,
      total_executions: 0,
      avg_confidence: 0,
      is_marketplace_published: false,
      created_at: null,
      updated_at: null,
      max_steps: 8,
      temperature: 0.2,
    })
    await waitFor(() =>
      expect(
        (screen.getByRole("checkbox", { name: ptBRMessages.agents.customAgents.tools.search_candidates }) as HTMLInputElement).checked,
      ).toBe(true),
    )
    // 0.2 → "consistent" preset selected.
    expect(
      screen.getByRole("radio", { name: ptBRMessages.agents.customAgents.styleConsistent }).getAttribute("aria-checked"),
    ).toBe("true")
  })

  it("editing a sourcing agent with config.job_id pre-selects the linked job", async () => {
    renderModal({
      id: "a1",
      name: "Sourcing",
      role: "Sourcer",
      description: null,
      system_prompt: "Busque talentos.",
      allowed_tools: [],
      domain: "sourcing",
      icon: "bot",
      status: "active",
      version: 1,
      total_executions: 0,
      avg_confidence: 0,
      is_marketplace_published: false,
      created_at: null,
      updated_at: null,
      max_steps: 8,
      temperature: 0.5,
      config: { job_id: "job-1" },
    })
    // The linked job appears as an option and its select is pre-selected.
    const opt = await screen.findByRole("option", { name: "Vaga Engenheiro" })
    const select = opt.closest("select") as HTMLSelectElement
    expect(select.value).toBe("job-1")
  })

  it("selecting a job link includes config.job_id in the save payload", async () => {
    renderModal(null)
    await waitFor(() => screen.getByRole("checkbox", { name: ptBRMessages.agents.customAgents.tools.search_candidates }))

    fireEvent.change(screen.getByLabelText(ptBRMessages.agents.customAgents.name), { target: { value: "Sourcing" } })
    fireEvent.change(screen.getByLabelText(ptBRMessages.agents.customAgents.role), { target: { value: "Sourcer" } })
    fireEvent.change(screen.getByLabelText(ptBRMessages.agents.customAgents.instructionsLabel), { target: { value: "Busque." } })

    // Switch link type to "Vaga" and pick a job from the dropdown.
    fireEvent.click(screen.getByRole("button", { name: ptBRMessages.agents.studio.modal.job }))
    const opt = await screen.findByRole("option", { name: "Vaga Engenheiro" })
    const select = opt.closest("select") as HTMLSelectElement
    fireEvent.change(select, { target: { value: "job-1" } })

    fireEvent.click(screen.getByRole("button", { name: ptBRMessages.agents.customAgents.createAgent }))
    await waitFor(() => expect(saveBodyRef.current).toBeTruthy())
    const body = saveBodyRef.current as { config: { job_id: string | null; talent_pool_id: string | null } }
    expect(body.config.job_id).toBe("job-1")
    expect(body.config.talent_pool_id).toBeNull()
  })

  it("i18n canonical contract: no MISSING_MESSAGE with real pt-BR messages", async () => {
    const errors: { code?: string; message: string }[] = []
    render(
      <NextIntlClientProvider
        locale="pt-BR"
        messages={ptBRMessages as Record<string, unknown>}
        onError={(err) => errors.push({ code: (err as { code?: string }).code, message: String(err) })}
      >
        <CreateCustomAgentModal agent={null} onClose={vi.fn()} onSaved={vi.fn()} />
      </NextIntlClientProvider>,
    )
    await waitFor(() => screen.getByRole("checkbox", { name: ptBRMessages.agents.customAgents.tools.search_candidates }))
    expect(errors.filter(e => e.message.includes("MISSING_MESSAGE"))).toEqual([])
  })
})
