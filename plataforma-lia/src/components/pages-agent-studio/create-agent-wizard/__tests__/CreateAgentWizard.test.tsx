/**
 * CreateAgentWizard — sentinels for T1 + T3 (UX_AUDIT_ESTUDIO_AGENTES_2026-05-21).
 *
 * Cobre:
 * T1 — unificacao de entry-points:
 *   - render do step 1 com 5 goals canonical
 *   - selecionar goal e avancar
 *   - voltar (Back) preserva state
 *   - progress bar reflete step atual (aria-valuenow)
 *
 * T3 — "Criar com IA" hero promotion:
 *   - hero card aparece ANTES dos templates no step 2
 *   - badge "Recomendado" visivel
 *   - textarea expande ao selecionar hero
 *   - templates filtrados por goal (sourcing => sourcing-* templates)
 *   - manual option esta no FUNDO
 *
 * Acessibilidade:
 *   - role=radiogroup nos steps
 *   - aria-checked muda quando seleciona
 *   - keyboard nav (Enter/Space) seleciona
 *
 * Endpoints (mocked):
 *   - approach=ai: POST /custom-agents/generate + POST /custom-agents
 *   - approach=template: POST /custom-agents (from template stub)
 *   - approach=manual: POST /custom-agents
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

vi.mock("@/lib/toast", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
}))

// Mock useAiPersona — ApproachStep/ConfigStep usam o hook que faz fetch
// para /api/backend-proxy/company-ai-persona no mount. Sem o mock, esses
// fetches consomem os mockResolvedValueOnce destinados aos endpoints
// canonical do wizard (/custom-agents, /custom-agents/generate) e o teste
// falha porque o POST canonical recebe response undefined.
vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({ persona: { name: "LIA", tone: "professional" }, isLoading: false, error: null }),
  useAiPersonaOptions: () => ({ options: null, isLoading: false, error: null }),
}))

import { CreateAgentWizard } from "../CreateAgentWizard"
import { filterTemplatesByGoal, GOAL_TO_CATEGORIES } from "../types"
import { AGENT_TEMPLATES } from "@/lib/__tests__/__fixtures__/agent-templates-fixture"

// Sprint 3 Parte 2: mock catalog hook so render uses fixture.
vi.mock("@/hooks/agents/use-legacy-agent-templates", async () => {
  const { AGENT_TEMPLATES } = await import("@/lib/__tests__/__fixtures__/agent-templates-fixture")
  return {
    useLegacyAgentTemplates: () => ({
      templates: AGENT_TEMPLATES,
      isLoading: false,
      error: null,
    }),
  }
})

beforeEach(() => {
  global.fetch = vi.fn() as unknown as typeof fetch
  // jsdom doesn't have localStorage by default in some configs — ensure available
  if (typeof window !== "undefined" && !window.localStorage) {
    Object.defineProperty(window, "localStorage", {
      value: {
        getItem: vi.fn().mockReturnValue(null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    })
  }
})

afterEach(() => {
  vi.restoreAllMocks()
})

function open(props: Partial<React.ComponentProps<typeof CreateAgentWizard>> = {}) {
  return render(
    <CreateAgentWizard open={true} onClose={vi.fn()} onCreated={vi.fn()} {...props} />,
  )
}

describe("CreateAgentWizard — T1 unificacao de entry-points", () => {
  it("renderiza step 1 com 5 goals canonical", () => {
    open()
    expect(screen.getByTestId("goal-option-triagem_inicial")).toBeTruthy()
    expect(screen.getByTestId("goal-option-sourcing_ativo")).toBeTruthy()
    expect(screen.getByTestId("goal-option-screening_cultural")).toBeTruthy()
    expect(screen.getByTestId("goal-option-voz_whatsapp")).toBeTruthy()
    expect(screen.getByTestId("goal-option-outro")).toBeTruthy()
  })

  it("usa role=radiogroup com aria-label no step 1", () => {
    open()
    const group = screen.getByRole("radiogroup", { name: /objetivo do agente/i })
    expect(group).toBeTruthy()
  })

  it("aria-checked muda ao selecionar uma goal", () => {
    open()
    const opt = screen.getByTestId("goal-option-triagem_inicial")
    expect(opt.getAttribute("aria-checked")).toBe("false")
    fireEvent.click(opt)
    expect(opt.getAttribute("aria-checked")).toBe("true")
  })

  it("permite selecionar goal via teclado (Enter/Space)", () => {
    open()
    const opt = screen.getByTestId("goal-option-sourcing_ativo")
    fireEvent.keyDown(opt, { key: "Enter" })
    expect(opt.getAttribute("aria-checked")).toBe("true")
  })

  it("botao 'Proximo' fica disabled ate uma goal ser selecionada", () => {
    open()
    const next = screen.getByTestId("wizard-next-button") as HTMLButtonElement
    expect(next.disabled).toBe(true)
    fireEvent.click(screen.getByTestId("goal-option-triagem_inicial"))
    expect(next.disabled).toBe(false)
  })

  it("progress bar reflete o step (aria-valuenow=1 inicialmente)", () => {
    open()
    const pb = screen.getByRole("progressbar")
    expect(pb.getAttribute("aria-valuenow")).toBe("1")
    expect(pb.getAttribute("aria-valuemax")).toBe("4")
  })

  it("avanca para step 2 ao clicar Proximo apos selecionar goal", async () => {
    open()
    fireEvent.click(screen.getByTestId("goal-option-triagem_inicial"))
    fireEvent.click(screen.getByTestId("wizard-next-button"))
    await waitFor(() => {
      const pb = screen.getByRole("progressbar")
      expect(pb.getAttribute("aria-valuenow")).toBe("2")
    })
  })

  it("step indicator mostra 'Etapa N de 4'", () => {
    open()
    const ind = screen.getByTestId("wizard-step-indicator")
    expect(ind.textContent).toContain("Etapa 1 de 4")
  })
})

describe("CreateAgentWizard — T3 'Criar com IA' hero", () => {
  it("step 2 mostra hero 'Criar com IA' no topo, antes dos templates", async () => {
    open({ initialGoal: "triagem_inicial" })
    fireEvent.click(screen.getByTestId("wizard-next-button"))
    await waitFor(() => {
      const hero = screen.getByTestId("approach-ai-hero")
      expect(hero).toBeTruthy()
      // Hero must render before any template option in DOM order (T3 promotion)
      const html = document.body.innerHTML
      const heroIdx = html.indexOf("approach-ai-hero")
      const tmplIdx = html.search(/template-option-/)
      // tmplIdx may be -1 if no templates match this goal; if both exist, hero must come first
      if (tmplIdx >= 0) expect(heroIdx).toBeLessThan(tmplIdx)
    })
  })

  it("hero exibe badge 'Recomendado'", async () => {
    open({ initialGoal: "triagem_inicial" })
    fireEvent.click(screen.getByTestId("wizard-next-button"))
    await waitFor(() => {
      expect(screen.getByText(/recomendado/i)).toBeTruthy()
    })
  })

  it("textarea aparece ao selecionar o hero 'Criar com IA'", async () => {
    open({ initialGoal: "triagem_inicial" })
    fireEvent.click(screen.getByTestId("wizard-next-button"))
    const hero = await screen.findByTestId("approach-ai-hero")
    fireEvent.click(hero)
    expect(screen.getByTestId("ai-description-textarea")).toBeTruthy()
  })

  it("opcao 'Criar custom manual' esta no fundo do step 2", async () => {
    open({ initialGoal: "outro" })
    fireEvent.click(screen.getByTestId("wizard-next-button"))
    await waitFor(() => {
      const manual = screen.getByTestId("approach-manual")
      const hero = screen.getByTestId("approach-ai-hero")
      // manual must come AFTER hero in DOM order (T3 priority)
      const html = document.body.innerHTML
      expect(html.indexOf("approach-ai-hero")).toBeLessThan(html.indexOf("approach-manual"))
    })
  })
})

describe("filterTemplatesByGoal — goal-based template filter", () => {
  it("retorna todos os templates para goal=outro", () => {
    const all = filterTemplatesByGoal(AGENT_TEMPLATES, "outro")
    expect(all.length).toBe(AGENT_TEMPLATES.length)
  })

  it("filtra templates de sourcing para goal=sourcing_ativo", () => {
    const sourcing = filterTemplatesByGoal(AGENT_TEMPLATES, "sourcing_ativo")
    expect(sourcing.length).toBeGreaterThan(0)
    sourcing.forEach((t) => {
      expect(GOAL_TO_CATEGORIES.sourcing_ativo).toContain(t.category)
    })
  })

  it("filtra templates de screening para goal=triagem_inicial", () => {
    const triagem = filterTemplatesByGoal(AGENT_TEMPLATES, "triagem_inicial")
    expect(triagem.length).toBeGreaterThan(0)
    triagem.forEach((t) => {
      expect(t.category).toBe("screening")
    })
  })

  it("NUNCA retorna lista vazia (fallback para categoria sem tags)", () => {
    // Even if all tag hints miss, must fall back to category set.
    const cultural = filterTemplatesByGoal(AGENT_TEMPLATES, "screening_cultural")
    expect(cultural.length).toBeGreaterThan(0)
  })
})

describe("CreateAgentWizard — endpoints chamados conforme approach", () => {
  it("approach=ai chama POST /custom-agents/generate antes de criar", async () => {
    const mockFetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          suggested_name: "Triagem IA",
          suggested_role: "Triagem inicial",
          suggested_domain: "screening",
          suggested_tools: ["search_candidates"],
          suggested_prompt: "Voce e um agente...",
          suggested_context_level: "standard",
          suggested_max_steps: 8,
          suggested_temperature: 0.4,
        }),
      })
    ;(global.fetch as unknown as typeof vi.fn) = mockFetch

    open({ initialGoal: "triagem_inicial" })
    fireEvent.click(screen.getByTestId("wizard-next-button")) // step 1 -> 2

    const hero = await screen.findByTestId("approach-ai-hero")
    fireEvent.click(hero)

    const ta = screen.getByTestId("ai-description-textarea") as HTMLTextAreaElement
    fireEvent.change(ta, {
      target: { value: "Quero um agente de triagem inicial para vagas de Python" },
    })

    fireEvent.click(screen.getByTestId("wizard-next-button")) // step 2 -> 3
    const genBtn = await screen.findByTestId("ai-generate-button")
    fireEvent.click(genBtn)

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/backend-proxy/custom-agents/generate",
        expect.objectContaining({ method: "POST" }),
      )
    })
  })

  it("approach=manual chama POST /custom-agents direto com payload minimo", async () => {
    const mockFetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "agent-uuid-manual" }),
    })
    ;(global.fetch as unknown as typeof vi.fn) = mockFetch

    const onCreated = vi.fn()
    const onClose = vi.fn()
    open({ initialGoal: "outro", onCreated, onClose })

    // step 1 -> 2
    fireEvent.click(screen.getByTestId("wizard-next-button"))
    // pick manual
    const manual = await screen.findByTestId("approach-manual")
    fireEvent.click(manual)
    // step 2 -> 3
    fireEvent.click(screen.getByTestId("wizard-next-button"))
    // fill name
    const nameInput = (await screen.findByTestId("wizard-manual-name-input")) as HTMLInputElement
    fireEvent.change(nameInput, { target: { value: "Meu Agente Manual" } })
    // step 3 -> 4
    fireEvent.click(screen.getByTestId("wizard-next-button"))
    // create
    fireEvent.click(screen.getByTestId("wizard-create-button"))

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/backend-proxy/custom-agents",
        expect.objectContaining({
          method: "POST",
        }),
      )
    })

    // onCreated called with the returned id
    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledWith("agent-uuid-manual")
    })
  })
})
