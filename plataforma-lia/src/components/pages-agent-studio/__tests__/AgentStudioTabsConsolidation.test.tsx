/**
 * UX_AUDIT_ESTUDIO_AGENTES_2026-05-21 — Transformação T2.
 *
 * Garante o contrato canonical pós-consolidação 5 tabs -> 3 tabs:
 *   - Top-level: Meus Agentes | Marketplace | Busca de Talentos
 *   - Sub-tabs em "Meus Agentes": Captação | Personalizados | Gêmeos Digitais
 *   - Default top tab = Meus Agentes; default sub-tab = Personalizados (per audit)
 *   - URL backward-compat: ?tab=<id-antigo> mapeia para o novo agrupamento
 *     (captacao/agents -> Meus Agentes > Captacao; custom/personalizados -> Meus
 *     Agentes > Personalizados; twins/gemeos -> Meus Agentes > Gemeos;
 *     marketplace -> Marketplace; search/busca -> Busca de Talentos).
 *
 * Mantemos os componentes filhos (CaptacaoSection-like content, CustomAgentsTab,
 * MarketplaceTab, TwinsList, MultiStrategySearchPanel) PRESERVADOS — esse teste
 * mocka apenas para isolar a logica de tabs/URL, sem rerender pesado.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, vars?: Record<string, unknown>) => {
    if (vars && "count" in vars) return `${key} (${vars.count})`
    if (vars && "name" in vars) return `${key} (${vars.name})`
    return key
  },
}))

// Stubs leves para componentes pesados — focamos no contrato de tabs/URL.
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
  ConversationalCreator: () => <div data-testid="stub-conv-creator" />,
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

// Stub fetch para evitar warnings de rede.
const fetchMock = vi.fn().mockResolvedValue({
  ok: true,
  json: async () => ({ agents: [] }),
})

import AgentStudioPage from "../AgentStudioPage"

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock)
  // limpa URL entre testes.
  window.history.replaceState({}, "", "/estudio-agentes")
})
afterEach(() => {
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

function setUrl(qs: string) {
  window.history.replaceState({}, "", `/estudio-agentes${qs}`)
}

describe("Agent Studio — T2 consolidation (5 tabs -> 3 tabs)", () => {
  it("renderiza exatamente 2 main tabs top-level (Sprint 4 v3: talentSearch movido pra TalentPoolPage)", async () => {
    render(<AgentStudioPage />)
    await waitFor(() => {
      // Tab navigation usa role="tablist" via PageTabNavigation. Dois tablists
      // aparecem quando "Meus Agentes" esta ativo (top-level + sub-tabs).
      // Sprint 4 v3 (2026-05-25): tab "Busca de Talentos" migrou pra sub-tab
      // "Captação" do TalentPoolPage. Studio agora tem 2 main tabs.
      const tablists = screen.getAllByRole("tablist", { name: /tabs/i })
      expect(tablists.length).toBeGreaterThanOrEqual(1)
      const top = tablists[0]
      const directTabs = top.querySelectorAll(":scope > button[role='tab']")
      expect(directTabs.length).toBe(2)
      const labels = Array.from(directTabs).map((b) => b.textContent ?? "")
      expect(labels.join("|")).toContain("studio.tabs.myAgents")
      expect(labels.join("|")).toContain("studio.tabs.marketplace")
      expect(labels.join("|")).not.toContain("studio.tabs.talentSearch")
    })
  })

  it("default top tab = Meus Agentes", async () => {
    render(<AgentStudioPage />)
    await waitFor(() => {
      const myAgentsTab = screen.getByRole("tab", { name: /studio\.tabs\.myAgents/i })
      expect(myAgentsTab.getAttribute("aria-selected")).toBe("true")
    })
  })

  it("Meus Agentes mostra 3 sub-tabs: Captacao, Personalizados, Gemeos", async () => {
    render(<AgentStudioPage />)
    await waitFor(() => {
      expect(screen.getByRole("tab", { name: /studio\.tabs\.sourcingAgents/i })).toBeTruthy()
      expect(screen.getByRole("tab", { name: /studio\.tabs\.customAgents/i })).toBeTruthy()
      expect(screen.getByRole("tab", { name: /studio\.tabs\.digitalTwins/i })).toBeTruthy()
    })
  })

  it("default sub-tab dentro de Meus Agentes = Personalizados", async () => {
    render(<AgentStudioPage />)
    await waitFor(() => {
      const customTab = screen.getByRole("tab", { name: /studio\.tabs\.customAgents/i })
      expect(customTab.getAttribute("aria-selected")).toBe("true")
    })
    // Conteudo: stub-template-gallery (renderizado apenas em personalizados).
    expect(screen.getByTestId("stub-template-gallery")).toBeTruthy()
  })

  it("clicar em Marketplace alterna pra MarketplaceTab", async () => {
    render(<AgentStudioPage />)
    const mkTab = await screen.findByRole("tab", { name: /studio\.tabs\.marketplace/i })
    await act(async () => {
      fireEvent.click(mkTab)
    })
    expect(screen.getByTestId("stub-marketplace")).toBeTruthy()
  })

  it("clicar em sub-tab Gemeos alterna o conteudo para TwinsList", async () => {
    render(<AgentStudioPage />)
    const gemeosTab = await screen.findByRole("tab", { name: /studio\.tabs\.digitalTwins/i })
    await act(async () => {
      fireEvent.click(gemeosTab)
    })
    expect(screen.getByTestId("stub-twins-list")).toBeTruthy()
  })

  // URL backward compat ---------------------------------------------------

  it("URL ?tab=captacao redireciona para Meus Agentes > sub Captacao", async () => {
    setUrl("?tab=captacao")
    render(<AgentStudioPage />)
    await waitFor(() => {
      const captacaoTab = screen.getByRole("tab", { name: /studio\.tabs\.sourcingAgents/i })
      expect(captacaoTab.getAttribute("aria-selected")).toBe("true")
    })
    expect(new URL(window.location.href).searchParams.get("tab")).toBe("my-agents")
    expect(new URL(window.location.href).searchParams.get("subTab")).toBe("captacao")
  })

  it("URL ?tab=custom (legacy) redireciona para Meus Agentes > Personalizados", async () => {
    setUrl("?tab=custom")
    render(<AgentStudioPage />)
    await waitFor(() => {
      const customTab = screen.getByRole("tab", { name: /studio\.tabs\.customAgents/i })
      expect(customTab.getAttribute("aria-selected")).toBe("true")
    })
    expect(new URL(window.location.href).searchParams.get("tab")).toBe("my-agents")
    expect(new URL(window.location.href).searchParams.get("subTab")).toBe("personalizados")
  })

  it("URL ?tab=twins (legacy) redireciona para Meus Agentes > Gemeos", async () => {
    setUrl("?tab=twins")
    render(<AgentStudioPage />)
    await waitFor(() => {
      const gemeosTab = screen.getByRole("tab", { name: /studio\.tabs\.digitalTwins/i })
      expect(gemeosTab.getAttribute("aria-selected")).toBe("true")
    })
    expect(new URL(window.location.href).searchParams.get("tab")).toBe("my-agents")
    expect(new URL(window.location.href).searchParams.get("subTab")).toBe("gemeos")
  })

  it("URL ?tab=marketplace mantem Marketplace ativo", async () => {
    setUrl("?tab=marketplace")
    render(<AgentStudioPage />)
    await waitFor(() => {
      const mkTab = screen.getByRole("tab", { name: /studio\.tabs\.marketplace/i })
      expect(mkTab.getAttribute("aria-selected")).toBe("true")
    })
    expect(screen.getByTestId("stub-marketplace")).toBeTruthy()
  })

  it("URL ?tab=search (legacy de Sprint 4 v3) cai no default myAgents — tab removida", async () => {
    // Sprint 4 v3 (2026-05-25): tab 'search' migrou pra TalentPoolPage sub-tab Captação.
    // URL legacy ?tab=search nao tem mais correspondencia no Studio — cai no default.
    setUrl("?tab=search")
    render(<AgentStudioPage />)
    await waitFor(() => {
      const myAgentsTab = screen.getByRole("tab", { name: /studio\.tabs\.myAgents/i })
      expect(myAgentsTab.getAttribute("aria-selected")).toBe("true")
    })
  })

  it("URL ?tab=busca (legacy de Sprint 4 v3) cai no default myAgents — tab removida", async () => {
    setUrl("?tab=busca")
    render(<AgentStudioPage />)
    await waitFor(() => {
      const myAgentsTab = screen.getByRole("tab", { name: /studio\.tabs\.myAgents/i })
      expect(myAgentsTab.getAttribute("aria-selected")).toBe("true")
    })
  })

  it("URL desconhecida (?tab=foo) NAO redireciona — mantem default Meus Agentes", async () => {
    setUrl("?tab=foo")
    render(<AgentStudioPage />)
    await waitFor(() => {
      const myAgentsTab = screen.getByRole("tab", { name: /studio\.tabs\.myAgents/i })
      expect(myAgentsTab.getAttribute("aria-selected")).toBe("true")
    })
    // URL nao foi reescrita (foo nao tem mapping).
    expect(new URL(window.location.href).searchParams.get("tab")).toBe("foo")
  })
})
