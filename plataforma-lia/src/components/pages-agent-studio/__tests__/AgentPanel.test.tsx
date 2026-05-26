/**
 * Sprint visual 2026-05-25 — AgentPanel canonical tests.
 *
 * Componente extraído de AgentsTab.tsx:181-251 inline → consumindo
 * <StudioCardShell> canonical (Paulo Opção A).
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { AgentPanel, type SourcingAgent, type TimelineEvent } from "../AgentPanel"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

const baseAgent: SourcingAgent = {
  id: "agent-1",
  agent_name: "Captação Eng",
  status: "active",
  calibration_v: 3,
  search_strategy: {
    required_skills: ["Python"],
    exclusions: ["Java"],
    seniority: "Pleno",
    location: "Remoto",
  },
  preferences: {},
  profiles_viewed: 42,
  profiles_approved: 10,
  profiles_rejected: 5,
  created_at: "2026-05-25T00:00:00Z",
}

describe("AgentPanel — Sprint visual canonical", () => {
  it("renderiza nome do agente + versão + status badge", () => {
    render(
      <AgentPanel
        agent={baseAgent}
        timeline={[]}
        onToggle={vi.fn()}
        onRecalibrate={vi.fn()}
      />,
    )
    expect(screen.getByText("Captação Eng")).toBeTruthy()
    expect(screen.getByText("v3")).toBeTruthy()
    expect(screen.getByText("statusActive")).toBeTruthy()
  })

  it("renderiza metrics canonical (viewed / approved / rejected)", () => {
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

  it("status paused exibe ícone Play (resume) + onToggle handler chamado", () => {
    const onToggle = vi.fn()
    render(
      <AgentPanel
        agent={{ ...baseAgent, status: "paused" }}
        timeline={[]}
        onToggle={onToggle}
        onRecalibrate={vi.fn()}
      />,
    )
    // Botão pause/resume é o primeiro com title="resume" (paused → resume key)
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
    // Não deve haver classes Tailwind hardcoded
    expect(html).not.toContain("bg-green-50")
    expect(html).not.toContain("bg-red-50")
    expect(html).not.toContain("bg-blue-50")
    // bg-lia-bg-tertiary é canonical (badgeStyles.default) — não checar inline.
    // O fix do Sprint visual foi remover hardcodes Tailwind brutos (bg-green-50/red-50/blue-50)
    // + chip seniority migrado pra wedo-purple. Verifica seniority purple:
    expect(html).toContain("bg-wedo-purple/10")
  })

  it("renderiza timeline body quando timeline.length > 0", () => {
    const timeline: TimelineEvent[] = [
      {
        id: "t1",
        icon: "👍",
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
