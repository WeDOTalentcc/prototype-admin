/**
 * MarketplaceTab — redesign 2026-06-09
 * BrowseMarketplace now uses:
 *   Section 1: first-party agents from custom-agents?agent_type=first_party
 *   Section 2: templates from useLegacyAgentTemplates hook
 *
 * vitest + react-testing-library
 */
import React from "react"
import { render, screen, waitFor, fireEvent } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"

// ---- minimal next-intl mock ----
vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, _params?: Record<string, unknown>) => key,
}))

// ---- next/navigation mock ----
const mockRouterPush = vi.fn()
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockRouterPush }),
  useSearchParams: () => ({ get: () => null }),
  usePathname: () => "/",
}))

// ---- toast mock ----
vi.mock("@/lib/toast", () => ({
  toast: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
}))

// ---- useAiPersona mock ----
vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({ persona: { name: "LIA" } }),
}))

// ---- useLegacyAgentTemplates mock ----
const mockTemplates = [
  {
    id: "tpl-triagem",
    name: "Triagem Técnica",
    description: "Template para triagem de candidatos técnicos",
    category: "screening",
    domain: "talent",
    icon: "Bot",
    system_prompt: "...",
    allowed_tools: ["list_candidates"],
    context_level: "standard" as const,
    max_steps: 8,
    temperature: 0.7,
    enable_memory: true,
    excluded_tools: [],
    tags: ["triagem"],
  },
  {
    id: "tpl-sourcing",
    name: "Captação Proativa",
    description: "Template para captação ativa de talentos",
    category: "sourcing",
    domain: "talent",
    icon: "Search",
    system_prompt: "...",
    allowed_tools: ["search_candidates"],
    context_level: "standard" as const,
    max_steps: 10,
    temperature: 0.5,
    enable_memory: false,
    excluded_tools: [],
    tags: ["sourcing"],
  },
]

vi.mock("@/hooks/agents/use-legacy-agent-templates", () => ({
  useLegacyAgentTemplates: () => ({
    templates: mockTemplates,
    isLoading: false,
    error: null,
  }),
}))

// ---- TemplateCard mock — renders template name + "Usar agora" button ----
vi.mock("@/components/pages-agent-studio/custom-agents/TemplateCard", () => ({
  TemplateCard: ({ template, onSelect }: { template: { id: string; name: string }; onSelect: (t: unknown) => void }) => (
    <div data-testid={`template-card-${template.id}`}>
      <span>{template.name}</span>
      <button onClick={() => onSelect(template)}>Usar agora</button>
    </div>
  ),
}))

// ---- StudioEmptyState mock ----
vi.mock("@/components/pages-agent-studio/StudioEmptyState", () => ({
  StudioEmptyState: () => <div data-testid="studio-empty-state">empty</div>,
}))

// ---- shared component mocks ----
vi.mock("@/components/agent-studio/confirm-alert-dialog", () => ({
  ConfirmAlertDialog: () => null,
}))
vi.mock("@/components/pages-agent-studio/TabSectionHeader", () => ({
  TabSectionHeader: ({ title }: { title: string }) => <div>{title}</div>,
}))
vi.mock("@/components/ui/tabs", () => ({
  Tabs: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TabsList: ({ children }: { children: React.ReactNode }) => <div role="tablist">{children}</div>,
  TabsTrigger: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <button role="tab" data-value={value}>{children}</button>
  ),
  TabsContent: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <div data-testid={`tab-content-${value}`}>{children}</div>
  ),
}))
vi.mock("@/components/ui/button", () => ({
  Button: ({ children, onClick, disabled, ...rest }: React.ButtonHTMLAttributes<HTMLButtonElement> & { children: React.ReactNode }) => (
    <button onClick={onClick} disabled={disabled} {...rest}>{children}</button>
  ),
}))
vi.mock("@/lib/utils", () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(" "),
}))
vi.mock("@/lib/agents/tool-capabilities", () => ({
  TOOL_GROUP: {},
  CAPABILITY_GROUP_ORDER: [],
}))
vi.mock("@/lib/agent-studio/status-config", () => ({
  getCustomAgentStatusConfig: () => ({ bg: "", text: "", dot: "" }),
}))

// ---- helpers ----
function makeCustomAgent(overrides: Record<string, unknown>) {
  return {
    id: "agent-1",
    name: "My Agent",
    role: "Recruiter",
    description: null,
    system_prompt: "",
    allowed_tools: [],
    domain: "talent",
    icon: "🤖",
    status: "active",
    version: 1,
    total_executions: 0,
    avg_confidence: 0,
    is_marketplace_published: false,
    created_at: null,
    updated_at: null,
    ...overrides,
  }
}

// ====================================================================
// Tests for new BrowseMarketplace (Section 1: first-party, Section 2: templates)
// ====================================================================

describe("BrowseMarketplace — Section 1: Agentes WeDo (first-party agents)", () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it("fetches from custom-agents?agent_type=first_party and renders agents in section", async () => {
    const firstPartyAgents = [
      { id: "fp-1", name: "TalentIntelAgent", description: "Agente de inteligência de talentos", icon: "🧠", domain: "talent", role: "Talent Intel", status: "active", agent_type: "first_party" },
      { id: "fp-2", name: "InterviewAnalysisAgent", description: "Análise de entrevistas", icon: "🎙️", domain: "talent", role: "Interview", status: "active", agent_type: "first_party" },
    ]

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ agents: firstPartyAgents }),
    } as Response)

    const { default: MarketplaceTab } = await import(
      "@/components/pages-agent-studio/MarketplaceTab"
    )
    render(<MarketplaceTab />)

    await waitFor(() => {
      expect(screen.getByText("TalentIntelAgent")).toBeInTheDocument()
      expect(screen.getByText("InterviewAnalysisAgent")).toBeInTheDocument()
    })

    // Verify the fetch URL included the correct query params
    const fetchCalls = (global.fetch as ReturnType<typeof vi.fn>).mock.calls
    const agentsFetch = fetchCalls.find(([url]: [string]) =>
      url.includes("custom-agents") && url.includes("agent_type=first_party")
    )
    expect(agentsFetch).toBeDefined()
  })

  it("renders sectionAgents title for first-party section", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ agents: [] }),
    } as Response)

    vi.resetModules()
    const { default: MarketplaceTab } = await import(
      "@/components/pages-agent-studio/MarketplaceTab"
    )
    render(<MarketplaceTab />)

    await waitFor(() => {
      expect(screen.getByText("sectionAgents")).toBeInTheDocument()
    })
  })

  it("renders Oficial WeDo badge for each first-party agent", async () => {
    const firstPartyAgents = [
      { id: "fp-1", name: "WeDo Agent", description: "desc", icon: "🤖", domain: "talent", role: "R", status: "active", agent_type: "first_party" },
    ]

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ agents: firstPartyAgents }),
    } as Response)

    vi.resetModules()
    const { default: MarketplaceTab } = await import(
      "@/components/pages-agent-studio/MarketplaceTab"
    )
    render(<MarketplaceTab />)

    await waitFor(() => {
      expect(screen.getByTestId("official-wedo-badge")).toBeInTheDocument()
      expect(screen.getByText("Oficial WeDo")).toBeInTheDocument()
    })
  })

  it("shows activate button and switches to active chip after successful activation", async () => {
    const firstPartyAgents = [
      { id: "fp-1", name: "WeDo Agent", description: "desc", icon: "🤖", domain: "talent", role: "R", status: "active", agent_type: "first_party" },
    ]

    // Mock fetch to handle all calls: custom-agents, agent-marketplace/install,
    // agent-marketplace/installations, agent-marketplace/billing, etc.
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("custom-agents")) {
        return Promise.resolve({ ok: true, json: async () => ({ agents: firstPartyAgents }) } as Response)
      }
      if (url.includes("agent-marketplace/install")) {
        return Promise.resolve({ ok: true, json: async () => ({ success: true }) } as Response)
      }
      // All other fetches (billing, installations, etc.)
      return Promise.resolve({ ok: true, json: async () => ({}) } as Response)
    })

    vi.resetModules()
    const { default: MarketplaceTab } = await import(
      "@/components/pages-agent-studio/MarketplaceTab"
    )
    render(<MarketplaceTab />)

    await waitFor(() => {
      expect(screen.getByTestId("activate-btn-fp-1")).toBeInTheDocument()
    })

    fireEvent.click(screen.getByTestId("activate-btn-fp-1"))

    await waitFor(() => {
      expect(screen.getByTestId("agent-active-chip")).toBeInTheDocument()
    })
  })
})

describe("BrowseMarketplace — Section 2: Templates (useLegacyAgentTemplates)", () => {
  it("renders sectionTemplates title for templates section", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ agents: [] }),
    } as Response)

    vi.resetModules()
    const { default: MarketplaceTab } = await import(
      "@/components/pages-agent-studio/MarketplaceTab"
    )
    render(<MarketplaceTab />)

    await waitFor(() => {
      expect(screen.getByText("sectionTemplates")).toBeInTheDocument()
    })
  })

  it("renders templates from useLegacyAgentTemplates hook via TemplateCard", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ agents: [] }),
    } as Response)

    vi.resetModules()
    const { default: MarketplaceTab } = await import(
      "@/components/pages-agent-studio/MarketplaceTab"
    )
    render(<MarketplaceTab />)

    await waitFor(() => {
      expect(screen.getByTestId("template-card-tpl-triagem")).toBeInTheDocument()
      expect(screen.getByTestId("template-card-tpl-sourcing")).toBeInTheDocument()
      expect(screen.getByText("Triagem Técnica")).toBeInTheDocument()
      expect(screen.getByText("Captação Proativa")).toBeInTheDocument()
    })
  })
})

describe("CustomAgentsTab filters out first_party agents", () => {
  it("excludes first_party agents from the list", async () => {
    const mockAgents = [
      makeCustomAgent({ id: "fp-1", name: "Official Agent", agent_type: "first_party" }),
      makeCustomAgent({ id: "c-1", name: "My Custom Agent", agent_type: "custom" }),
    ]

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ agents: mockAgents, total: 2 }),
    } as Response)

    vi.resetModules()
    const { default: CustomAgentsTab } = await import(
      "@/components/pages-agent-studio/CustomAgentsTab"
    )
    render(<CustomAgentsTab />)

    await waitFor(() => {
      expect(screen.getByText("My Custom Agent")).toBeInTheDocument()
    })

    expect(screen.queryByText("Official Agent")).not.toBeInTheDocument()
  })

  it("shows empty state when all agents are first_party", async () => {
    const mockAgents = [
      makeCustomAgent({ id: "fp-1", name: "Official A", agent_type: "first_party" }),
      makeCustomAgent({ id: "fp-2", name: "Official B", agent_type: "first_party" }),
    ]

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ agents: mockAgents, total: 2 }),
    } as Response)

    vi.resetModules()
    const { default: CustomAgentsTab } = await import(
      "@/components/pages-agent-studio/CustomAgentsTab"
    )
    render(<CustomAgentsTab />)

    await waitFor(() => {
      expect(screen.getByTestId("studio-empty-state")).toBeInTheDocument()
    })

    expect(screen.queryByText("Official A")).not.toBeInTheDocument()
  })
})
