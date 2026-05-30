/**
 * P1 (Paulo 2026-05-30) — "Usar agora" vs "Ajustar antes" são DISTINTOS.
 *
 *  - "Usar agora"  → cria o agente direto (POST /custom-agents), sem wizard.
 *  - "Ajustar antes" → abre o wizard pré-populado (nenhum POST de criação).
 *
 * Sentinel contra regressão para o bug original (ambos caíam no wizard).
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, vars?: Record<string, unknown>) => {
    if (vars && "name" in vars) return `${key} (${vars.name})`
    if (vars && "count" in vars) return `${key} (${vars.count})`
    return key
  },
  useLocale: () => "pt",
}))

const TEMPLATE = {
  id: "tpl-triagem-tech",
  slug: "tpl-triagem-tech",
  name: "Triagem Tech",
  description: "Triagem técnica automatizada",
  category: "screening",
  domain: "screening",
  system_prompt: "Você é um agente de triagem",
  allowed_tools: ["search_candidates", "get_candidate_details"],
  context_level: "standard",
  max_steps: 8,
  temperature: 0.5,
  tags: [],
}

let wizardOpened = false
vi.mock("../create-agent-wizard", () => ({
  __esModule: true,
  CreateAgentWizard: ({ open }: { open: boolean }) => {
    if (open) wizardOpened = true
    return open ? <div data-testid="wizard-open" /> : null
  },
  inferGoalFromTemplate: () => "triagem_inicial",
}))

vi.mock("../DigitalTwinComponents", () => ({
  __esModule: true,
  TwinsList: () => null,
  CreateDigitalTwinModal: () => null,
}))
vi.mock("../control-room", () => ({ __esModule: true, StudioControlRoom: () => null }))
vi.mock("../template-clone", () => ({ __esModule: true, TemplateClonePanel: () => null }))
vi.mock("../StudioTour", () => ({ __esModule: true, StudioTour: () => null }))
vi.mock("../QuotaMeter", () => ({ __esModule: true, QuotaMeter: () => null }))
vi.mock("../custom-agents", async () => {
  // TemplateGallery real (precisamos do card real com os botões Usar/Ajustar).
  const real = await vi.importActual<typeof import("../custom-agents/TemplateGallery")>(
    "../custom-agents/TemplateGallery",
  )
  return {
    __esModule: true,
    TemplateGallery: real.TemplateGallery,
    AgentCard: () => null,
    AgentCardSkeleton: () => null,
    AgentDetailsPanel: () => null,
    DeployDialog: () => null,
    AIAgentBuilder: () => null,
    TestDebugPanel: () => null,
    ApprovalsList: () => null,
  }
})

vi.mock("@/hooks/agents", () => ({
  __esModule: true,
  useCustomAgents: () => ({ agents: [], mutate: vi.fn() }),
  usePendingApprovals: () => ({ approvals: [], total: 0, isLoading: false, isError: false, mutate: vi.fn() }),
}))
vi.mock("@/stores/agent-studio-store", () => ({
  __esModule: true,
  useAgentStudioStore: () => ({
    selectTemplate: vi.fn(),
    reset: vi.fn(),
    activeCategory: "all",
    setActiveCategory: vi.fn(),
  }),
}))
vi.mock("@/hooks/agents/use-legacy-agent-templates", () => ({
  useLegacyAgentTemplates: () => ({ templates: [TEMPLATE], isLoading: false, error: null }),
}))
vi.mock("@/hooks/agents/use-agent-template-catalog", () => ({
  useAgentCategories: () => ({ data: [], isLoading: false, error: null, mutate: () => Promise.resolve() }),
}))
vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({ persona: { name: "LIA" } }),
}))
vi.mock("@/lib/toast", () => ({
  toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
}))

const fetchMock = vi.fn()

import AgentStudioPage from "../AgentStudioPage"

beforeEach(() => {
  wizardOpened = false
  fetchMock.mockReset()
  fetchMock.mockImplementation((url: string) => {
    if (typeof url === "string" && url.includes("/custom-agents") && !url.includes("?")) {
      return Promise.resolve({ ok: true, json: async () => ({ id: "new-agent-1" }) })
    }
    return Promise.resolve({ ok: true, json: async () => ({ agents: [] }) })
  })
  vi.stubGlobal("fetch", fetchMock)
  window.history.replaceState({}, "", "/estudio-agentes")
})
afterEach(() => {
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

describe("AgentStudioPage — P1 'Usar agora' vs 'Ajustar antes'", () => {
  it("'Usar agora' dispara POST de criação direta (sem abrir o wizard)", async () => {
    await act(async () => {
      render(<AgentStudioPage />)
    })
    const useBtn = await screen.findByTestId(`template-card-use-${TEMPLATE.id}`)
    await act(async () => {
      fireEvent.click(useBtn)
    })
    await waitFor(() => {
      const createCall = fetchMock.mock.calls.find(
        ([u, opts]: any) =>
          typeof u === "string" &&
          u.includes("/custom-agents") &&
          !u.includes("?") &&
          opts?.method === "POST",
      )
      expect(createCall).toBeTruthy()
    })
    // Não abriu o wizard nesse caminho.
    expect(wizardOpened).toBe(false)
    expect(screen.queryByTestId("wizard-open")).toBeNull()
  })

  it("'Ajustar antes' abre o wizard (nenhum POST de criação direta)", async () => {
    await act(async () => {
      render(<AgentStudioPage />)
    })
    const customizeBtn = await screen.findByTestId(`template-card-customize-${TEMPLATE.id}`)
    await act(async () => {
      fireEvent.click(customizeBtn)
    })
    await waitFor(() => {
      expect(wizardOpened).toBe(true)
    })
    const createCall = fetchMock.mock.calls.find(
      ([u, opts]: any) =>
        typeof u === "string" &&
        u.includes("/custom-agents") &&
        !u.includes("?") &&
        opts?.method === "POST",
    )
    expect(createCall).toBeUndefined()
  })
})
