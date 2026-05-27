/**
 * Studio Restructure Fase 1 — TDD Red pin para estado-alvo pós-refactor.
 *
 * Estado-alvo (substitui T2 consolidation prévio):
 *   - Top-level: exatamente 2 tabs — Meus Agentes (default) + Gêmeos Digitais
 *   - SEM sub-tabs (MySubTab eliminado)
 *   - Marketplace NÃO é tab — vira CTA secundário "Explorar Marketplace"
 *     no header right, com href="/agents/marketplace"
 *   - CTA primário "+ Criar Agente" permanece no header right
 *
 * Mistura source-grep (assertions de eliminação) + render mock (assertions de UI).
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
  default: () => <div data-testid="stub-multi-strategy">multi-strategy</div>,
}))
vi.mock("../MarketplaceTab", () => ({
  __esModule: true,
  default: () => <div data-testid="stub-marketplace">marketplace</div>,
}))
vi.mock("../CustomAgentsTab", () => ({
  __esModule: true,
  default: () => <div data-testid="stub-custom-agents">custom-agents</div>,
}))
vi.mock("../DigitalTwinComponents", () => ({
  __esModule: true,
  TwinsList: () => <div data-testid="stub-twins-list">twins</div>,
  EvaluateWithTwinModal: () => null,
  CreateDigitalTwinModal: () => null,
}))
vi.mock("../custom-agents", () => ({
  __esModule: true,
  TemplateGallery: () => <div data-testid="stub-template-gallery">templates</div>,
  AgentCard: () => null,
  AgentCardSkeleton: () => null,
  AgentDetailsPanel: () => null,
  DeployDialog: () => null,
  AIAgentBuilder: () => <div data-testid="stub-conv-creator" />,
  TestDebugPanel: () => null,
  ApprovalsList: () => null,
}))
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
  useAgentStudioStore: () => ({ selectTemplate: vi.fn(), reset: vi.fn() }),
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

describe("Studio Restructure Fase 1 — source-grep eliminations", () => {
  it("AgentStudioPage NÃO declara o type MySubTab", () => {
    expect(STUDIO_SRC).not.toMatch(/type\s+MySubTab\b/)
  })

  it("AgentStudioPage NÃO importa MarketplaceTab", () => {
    expect(STUDIO_SRC).not.toMatch(
      /import\s+MarketplaceTab\s+from\s+["']@\/components\/pages-agent-studio\/MarketplaceTab["']/
    )
  })

  it("AgentStudioPage NÃO usa useState<MySubTab>", () => {
    expect(STUDIO_SRC).not.toMatch(/useState<MySubTab>/)
    expect(STUDIO_SRC).not.toMatch(/\bmySubTab\b/)
  })

  it("AgentStudioPage NÃO renderiza <MarketplaceTab /> como tab content", () => {
    expect(STUDIO_SRC).not.toMatch(/<MarketplaceTab\s*\/>/)
  })

  it("AgentStudioPage NÃO tem branch activeTab === 'marketplace'", () => {
    expect(STUDIO_SRC).not.toMatch(/activeTab\s*===\s*["']marketplace["']/)
  })
})

describe("Studio Restructure Fase 1 — top-level tabs render", () => {
  it("renderiza exatamente 2 tabs top-level: Meus Agentes + Gêmeos Digitais", async () => {
    render(<AgentStudioPage />)
    await waitFor(() => {
      const tablists = screen.getAllByRole("tablist", { name: /tabs/i })
      expect(tablists.length).toBeGreaterThanOrEqual(1)
      const top = tablists[0]
      const directTabs = top.querySelectorAll(":scope > button[role='tab']")
      expect(directTabs.length).toBe(2)
      const labels = Array.from(directTabs).map((b) => b.textContent ?? "")
      expect(labels.join("|")).toContain("studio.tabs.myAgents")
      expect(labels.join("|")).toContain("studio.tabs.digitalTwins")
      expect(labels.join("|")).not.toContain("studio.tabs.marketplace")
    })
  })

  it("default top tab = Meus Agentes", async () => {
    render(<AgentStudioPage />)
    await waitFor(() => {
      const t = screen.getByRole("tab", { name: /studio\.tabs\.myAgents/i })
      expect(t.getAttribute("aria-selected")).toBe("true")
    })
  })

  it("NÃO renderiza sub-tab 'Agentes de Captação'", async () => {
    render(<AgentStudioPage />)
    await waitFor(() => {
      expect(screen.queryByText(/studio\.tabs\.sourcingAgents/i)).toBeNull()
      expect(screen.queryByText(/Agentes de Captação/i)).toBeNull()
    })
  })

  it("NÃO renderiza sub-tab 'Agentes Personalizados'", async () => {
    render(<AgentStudioPage />)
    await waitFor(() => {
      expect(screen.queryByText(/studio\.tabs\.customAgents/i)).toBeNull()
      expect(screen.queryByText(/Agentes Personalizados/i)).toBeNull()
    })
  })

  it("aba 'Gêmeos Digitais' alterna conteúdo para TwinsList", async () => {
    render(<AgentStudioPage />)
    const gemeosTab = await screen.findByRole("tab", {
      name: /studio\.tabs\.digitalTwins/i,
    })
    await act(async () => {
      fireEvent.click(gemeosTab)
    })
    expect(screen.getByTestId("stub-twins-list")).toBeTruthy()
  })
})

describe("Studio Restructure Fase 1 — header CTAs", () => {
  it("renderiza CTA primário '+ Criar Agente'", async () => {
    render(<AgentStudioPage />)
    await waitFor(() => {
      // Match botão pelo texto canonical ou key i18n
      const el =
        screen.queryByText(/\+\s*Criar Agente/i) ||
        screen.queryByText(/studio\.cta\.createAgent/i)
      expect(el).not.toBeNull()
    })
  })

  it("renderiza CTA secundário 'Explorar Marketplace' como link com href /agents/marketplace", async () => {
    render(<AgentStudioPage />)
    await waitFor(() => {
      const el =
        (screen.queryByText(/Explorar Marketplace/i) as HTMLElement | null) ||
        (screen.queryByText(/studio\.cta\.exploreMarketplace/i) as HTMLElement | null)
      expect(el).not.toBeNull()
      // Sobe pra ancora mais próxima.
      const anchor = el?.closest("a")
      expect(anchor).not.toBeNull()
      expect(anchor?.getAttribute("href")).toBe("/agents/marketplace")
    })
  })
})
