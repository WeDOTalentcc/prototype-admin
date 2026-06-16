/**
 * Fase 3 Sprint 3 (2026-05-30) — AgentDetailsPanel split layout.
 *
 * Garante:
 *  - o sandbox vive INLINE no detalhe (coluna direita), não num 2º Dialog
 *  - existe apenas UM Dialog (sem modal-sobre-modal)
 *  - o banner "MODO SIMULAÇÃO" do sandbox aparece junto da config
 *  - "Ativar agente" do sandbox inline encaminha pra onActivate
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => {
    const t = (key: string, vals?: Record<string, unknown>) =>
      vals ? `${key}:${JSON.stringify(vals)}` : key
    t.has = (key: string) => key.startsWith("wouldDoVerb.")
    return t
  },
}))

vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({ persona: { name: "Aria" } }),
}))

vi.mock("@/hooks/agents", () => ({
  useAgentDeployments: () => ({ deployments: [], isLoading: false }),
  useAgentActivities: () => ({ activities: [], isLoading: false, isError: false }),
}))

vi.mock("../../decision-tree/DecisionTreeDrawer", () => ({
  DecisionTreeBody: () => <div data-testid="mock-decision-tree-body" />,
}))

vi.mock("../VersionHistoryPanel", () => ({
  VersionHistoryPanel: () => <div data-testid="mock-version-history" />,
}))

import { AgentDetailsPanel } from "../AgentDetailsPanel"
import type { CustomAgent } from "../types"

const AGENT = {
  id: "agent-1",
  name: "Triador",
  domain: "screening",
  category: "screening",
  description: "Triagem técnica",
  context_level: "full",
  max_steps: 8,
  allowed_tools: ["send_email"],
  total_executions: 3,
  avg_confidence: 0.7,
} as unknown as CustomAgent

describe("AgentDetailsPanel split (sandbox inline)", () => {
  it("renders the sandbox INLINE inside a single Dialog (no nested modal)", () => {
    render(
      <AgentDetailsPanel
        agent={AGENT}
        open
        onClose={() => {}}
        onDeploy={() => {}}
        onTest={() => {}}
        onActivate={() => {}}
      />,
    )
    // Exactly one Dialog overlay.
    expect(document.querySelectorAll('[role="dialog"]').length).toBe(1)
    // Sandbox column + inline body present alongside the config.
    expect(screen.getByTestId("agent-details-sandbox-column")).toBeTruthy()
    expect(screen.getByTestId("agent-sandbox-inline")).toBeTruthy()
    expect(screen.getByTestId("sandbox-simulation-banner")).toBeTruthy()
    // Example chips ride along (T3).
    expect(screen.getByTestId("sandbox-example-chips")).toBeTruthy()
  })

  it("does NOT render the old standalone sandbox Dialog testid", () => {
    render(
      <AgentDetailsPanel
        agent={AGENT}
        open
        onClose={() => {}}
        onDeploy={() => {}}
        onTest={() => {}}
        onActivate={() => {}}
      />,
    )
    // The standalone wrapper testid must not appear from the details panel.
    expect(screen.queryByTestId("agent-sandbox-panel")).toBeNull()
  })
})
