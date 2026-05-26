/**
 * Sprint 7B-3b Part 2 v2 (2026-05-26) — AgentPanel canonical CustomAgent tests.
 *
 * Componente migrado de SourcingAgent local type -> CustomAgent canonical
 * (Sprint 7B-1 schema). Field access via adapter helpers (runtime_metrics,
 * config.calibration_v).
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { AgentPanel, type TimelineEvent } from "../AgentPanel"
import type { CustomAgent } from "../custom-agents/types"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

const baseAgent: CustomAgent = {
  id: "agent-1",
  company_id: "comp-1",
  name: "Captacao Eng",
  role: "sourcing_agent",
  description: null,
  system_prompt: "",
  allowed_tools: [],
  domain: "sourcing",
  icon: "Bot",
  status: "active",
  config: { calibration_v: 3 },
  max_steps: 10,
  temperature: 0.7,
  model_override: null,
  enable_memory: false,
  context_level: "standard",
  excluded_tools: [],
  category: "sourcing",
  runtime_metrics: {
    profiles_viewed: 42,
    profiles_approved: 10,
    profiles_rejected: 5,
  },
  search_strategy: {
    required_skills: ["Python"],
    exclusions: ["Java"],
    seniority: "Pleno",
    location: "Remoto",
  },
  outreach_config: null,
  legacy_sourcing_agent_id: null,
  total_executions: 0,
  avg_confidence: 0,
  last_executed_at: null,
  created_at: "2026-05-25T00:00:00Z",
  updated_at: null,
}

describe("AgentPanel — Sprint 7B-3b Part 2 v2 canonical CustomAgent", () => {
  it("renderiza nome do agente (CustomAgent.name) + versao (config.calibration_v) + status badge", () => {
    render(
      <AgentPanel
        agent={baseAgent}
        timeline={[]}
        onToggle={vi.fn()}
        onRecalibrate={vi.fn()}
      />,
    )
    expect(screen.getByText("Captacao Eng")).toBeTruthy()
    expect(screen.getByText("v3")).toBeTruthy()
    expect(screen.getByText("statusActive")).toBeTruthy()
  })

  it("renderiza metrics canonical extraidas de runtime_metrics", () => {
    render(
      <AgentPanel
        agent={baseAgent}
        timeline={[]}
        onToggle={vi.fn()}
        onRecalibrate={vi.fn()}
      />,
    )
    expect(screen.getByText("42")).toBeTruthy()
    expect(screen.getByText("10")).toBeTruthy()
    expect(screen.getByText("5")).toBeTruthy()
  })

  it("runtime_metrics ausente cai pra zero (adapter fail-safe)", () => {
    render(
      <AgentPanel
        agent={{ ...baseAgent, runtime_metrics: undefined }}
        timeline={[]}
        onToggle={vi.fn()}
        onRecalibrate={vi.fn()}
      />,
    )
    // 3 zeros: viewed, approved, rejected
    const zeros = screen.getAllByText("0")
    expect(zeros.length).toBeGreaterThanOrEqual(3)
  })

  it("status paused exibe icone Play (resume) + onToggle handler chamado", () => {
    const onToggle = vi.fn()
    render(
      <AgentPanel
        agent={{ ...baseAgent, status: "paused" }}
        timeline={[]}
        onToggle={onToggle}
        onRecalibrate={vi.fn()}
      />,
    )
    const buttons = screen.getAllByRole("button")
    fireEvent.click(buttons[0])
    expect(onToggle).toHaveBeenCalledOnce()
  })

  it("renderiza chips strategy com tokens DS canonical (sem hardcode bg-green-50/red-50/blue-50)", () => {
    const { container } = render(
      <AgentPanel
        agent={baseAgent}
        timeline={[]}
        onToggle={vi.fn()}
        onRecalibrate={vi.fn()}
      />,
    )
    const html = container.innerHTML
    expect(html).not.toContain("bg-green-50")
    expect(html).not.toContain("bg-red-50")
    expect(html).not.toContain("bg-blue-50")
    expect(html).toContain("bg-wedo-purple/10")
  })

  it("renderiza timeline body quando timeline.length > 0", () => {
    const timeline: TimelineEvent[] = [
      {
        id: "t1",
        icon: "thumbs-up",
        type: "positive",
        reason: "Match perfeito",
        criteria: ["Python", "Remoto"],
        candidate_id: "c1",
        created_at: "2026-05-25T10:00:00Z",
      },
    ]
    render(
      <AgentPanel
        agent={baseAgent}
        timeline={timeline}
        onToggle={vi.fn()}
        onRecalibrate={vi.fn()}
      />,
    )
    expect(screen.getByText("Match perfeito")).toBeTruthy()
    expect(screen.getByText("recentActivity")).toBeTruthy()
  })
})
