/**
 * Studio Restructure Fase 1 — TDD Red integration test.
 *
 * Estado-alvo dentro de "Meus Agentes":
 *   - TemplateGallery aparece com labels visíveis "Tipo:" + "Vertical:"
 *   - NÃO existe botão dashed "Criar do zero" inline
 *   - NÃO existe <details> "Formulário Avançado"
 *   - Clicar aba "Gêmeos Digitais" → TwinsList montada
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react"
import { readFileSync } from "node:fs"
import { join } from "node:path"

const STUDIO_PATH = join(__dirname, "..", "AgentStudioPage.tsx")
const STUDIO_SRC = readFileSync(STUDIO_PATH, "utf-8")

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, vars?: Record<string, unknown>) => {
    if (vars && "count" in vars) return `${key} (${vars.count})`
    if (vars && "name" in vars) return `${key} (${vars.name})`
    return key
  },
}))

vi.mock("../MultiStrategySearchPanel", () => ({
  __esModule: true,
  default: () => <div data-testid="stub-multi-strategy" />,
}))
vi.mock("../MarketplaceTab", () => ({
  __esModule: true,
  default: () => <div data-testid="stub-marketplace" />,
}))
vi.mock("../CustomAgentsTab", () => ({
  __esModule: true,
  default: () => <div data-testid="stub-custom-agents" />,
}))
vi.mock("../DigitalTwinComponents", () => ({
  __esModule: true,
  TwinsList: () => <div data-testid="stub-twins-list">twins</div>,
  EvaluateWithTwinModal: () => null,
  CreateDigitalTwinModal: () => null,
}))
// NÃO mocka TemplateGallery — queremos render real pra checar labels Tipo:/Vertical:
vi.mock("../custom-agents/template-preview-modal", () => ({
  __esModule: true,
  TemplatePreviewModal: () => null,
}))
vi.mock("../create-agent-wizard", () => ({
  __esModule: true,
  CreateAgentWizard: () => null,
}))
vi.mock("@/hooks/agents", () => ({
  __esModule: true,
  useCustomAgents: () => ({ agents: [], mutate: vi.fn() }),
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
  useLegacyAgentTemplates: () => ({ templates: [], isLoading: false, error: null }),
}))
vi.mock("@/hooks/agents/use-agent-template-catalog", () => ({
  useAgentCategories: () => ({ data: [], isLoading: false, error: null, mutate: () => Promise.resolve() }),
  useAgentTemplateCatalog: () => ({ data: [], isLoading: false, error: null, mutate: () => Promise.resolve() }),
  useAgentSectors: () => ({ data: [], isLoading: false, error: null, mutate: () => Promise.resolve() }),
}))

const fetchMock = vi.fn().mockResolvedValue({
  ok: true,
  json: async () => ({ agents: [] }),
})

import AgentStudioPage from "../AgentStudioPage"

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock)
  window.history.replaceState({}, "", "/estudio-agentes")
})
afterEach(() => {
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

describe("Studio Restructure Fase 1 — source-grep extras", () => {
  it("AgentStudioPage NÃO contém botão dashed 'Criar do zero' inline", () => {
    expect(STUDIO_SRC).not.toMatch(/Criar do zero/i)
  })

  it("AgentStudioPage NÃO contém <details> 'Formulário Avançado'", () => {
    expect(STUDIO_SRC).not.toMatch(/Formulário Avançado/i)
    expect(STUDIO_SRC).not.toMatch(/<details[\s\S]{0,200}Avançado/i)
  })
})

describe("Studio Restructure Fase 1 — Meus Agentes render", () => {
  it("renderiza TemplateGallery com labels visíveis 'Tipo:' e 'Vertical:'", async () => {
    render(<AgentStudioPage />)
    await waitFor(() => {
      expect(screen.getByText(/^Tipo:?$/i)).toBeTruthy()
      expect(screen.getByText(/^Vertical:?$/i)).toBeTruthy()
    })
  })

  it("NÃO renderiza botão 'Criar do zero' inline", async () => {
    render(<AgentStudioPage />)
    await waitFor(() => {
      expect(screen.queryByText(/Criar do zero/i)).toBeNull()
    })
  })

  it("NÃO renderiza <details> 'Formulário Avançado'", async () => {
    render(<AgentStudioPage />)
    await waitFor(() => {
      expect(screen.queryByText(/Formulário Avançado/i)).toBeNull()
    })
  })

  it("clicar aba 'Gêmeos Digitais' renderiza TwinsList", async () => {
    render(<AgentStudioPage />)
    const tab = await screen.findByRole("tab", {
      name: /studio\.tabs\.digitalTwins/i,
    })
    await act(async () => {
      fireEvent.click(tab)
    })
    expect(screen.getByTestId("stub-twins-list")).toBeTruthy()
  })
})
