/**
 * Tests for MarketplaceTab two-section split + first_party badge
 * and CustomAgentsTab first_party filter.
 * vitest + react-testing-library
 */
import React from "react"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"

// ---- minimal next-intl mock ----
vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, _params?: Record<string, unknown>) => key,
}))

// ---- minimal next/navigation mock ----
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
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
vi.mock("@/components/ui/dialog", () => ({
  Dialog: () => null,
  DialogContent: () => null,
  DialogHeader: () => null,
  DialogTitle: () => null,
  DialogDescription: () => null,
  DialogFooter: () => null,
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
function makeListing(overrides: Record<string, unknown>) {
  return {
    id: overrides.id || "list-1",
    agent_id: overrides.agent_id || "agent-1",
    title: overrides.title || "Test Agent",
    short_description: "desc",
    category: "general",
    tags: [],
    status: "active",
    credits_per_execution: 0,
    is_free: true,
    install_count: 5,
    avg_rating: 0,
    total_ratings: 0,
    agent_name: null,
    agent_role: null,
    agent_domain: null,
    published_at: null,
    ...overrides,
  }
}

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

// ---- BrowseMarketplace tests (via MarketplaceTab) ----
// We import BrowseMarketplace indirectly by testing the "browse" tab content.
// Since tabs mock renders all tab contents, we can assert on rendered content.

describe("BrowseMarketplace splits listings into agent and template sections", () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it("renders separate sections for agents and templates", async () => {
    const mockListings = [
      makeListing({ id: "a1", title: "Sourcing Agent", listing_type: "agent", agent_type: "custom" }),
      makeListing({ id: "t1", title: "Onboarding Template", listing_type: "template" }),
    ]

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ listings: mockListings, total: 2 }),
    } as Response)

    const { default: MarketplaceTab } = await import(
      "@/components/pages-agent-studio/MarketplaceTab"
    )
    render(<MarketplaceTab />)

    await waitFor(() => {
      expect(screen.getByText("sectionAgents")).toBeInTheDocument()
      expect(screen.getByText("sectionTemplates")).toBeInTheDocument()
    })

    expect(screen.getByText("Sourcing Agent")).toBeInTheDocument()
    expect(screen.getByText("Onboarding Template")).toBeInTheDocument()
  })
})

describe("First-party agent shows Oficial WeDo badge", () => {
  it("renders Oficial WeDo badge for first_party agent_type", async () => {
    const mockListings = [
      makeListing({
        id: "fp-1",
        title: "WeDo Sourcer",
        listing_type: "agent",
        agent_type: "first_party",
      }),
    ]

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ listings: mockListings, total: 1 }),
    } as Response)

    vi.resetModules()
    const { default: MarketplaceTab } = await import(
      "@/components/pages-agent-studio/MarketplaceTab"
    )
    render(<MarketplaceTab />)

    await waitFor(() => {
      expect(screen.getByText("Oficial WeDo")).toBeInTheDocument()
    })
  })

  it("does NOT render Oficial WeDo badge for custom agent_type", async () => {
    const mockListings = [
      makeListing({
        id: "c-1",
        title: "Custom Agent",
        listing_type: "agent",
        agent_type: "custom",
      }),
    ]

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ listings: mockListings, total: 1 }),
    } as Response)

    vi.resetModules()
    const { default: MarketplaceTab } = await import(
      "@/components/pages-agent-studio/MarketplaceTab"
    )
    render(<MarketplaceTab />)

    await waitFor(() => {
      expect(screen.queryByText("Oficial WeDo")).not.toBeInTheDocument()
    })
  })
})

describe("Template shows useTemplate button, not install button", () => {
  it("template listing shows useTemplate key, not install key", async () => {
    const mockListings = [
      makeListing({ id: "t-1", title: "Pipeline Template", listing_type: "template" }),
      makeListing({ id: "a-1", title: "Agent One", listing_type: "agent" }),
    ]

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ listings: mockListings, total: 2 }),
    } as Response)

    vi.resetModules()
    const { default: MarketplaceTab } = await import(
      "@/components/pages-agent-studio/MarketplaceTab"
    )
    render(<MarketplaceTab />)

    await waitFor(() => {
      expect(screen.getByText("useTemplate")).toBeInTheDocument()
    })

    // install button exists for agent, not template — install key appears once (for agent)
    const installButtons = screen.getAllByText("install")
    expect(installButtons).toHaveLength(1)
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
