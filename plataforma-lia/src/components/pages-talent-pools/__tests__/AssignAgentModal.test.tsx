/**
 * Sprint 7B-2 -> Onda 4 Agent E (2026-05-29) — wrapper sentinels.
 *
 * O modal Pool agora delega a logica pra
 * src/components/shared/agents/AssignAgentModal (generic). Estes tests
 * sao smoke + integration do wrapper:
 *   - Renderiza com generic + targetType=talent_pool
 *   - Submit traduz trigger_mode -> schedule_type e chama assignAgentToPool
 *   - initialCategory aceito por backward-compat (no-op)
 *
 * Tests profundos do comportamento generico moram em
 * src/components/shared/agents/__tests__/AssignAgentModal.test.tsx.
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

const mockCustomAgents = {
  agents: [
    { id: "ca-1", name: "SourceBot", category: "sourcing", status: "active" },
    { id: "ca-2", name: "ScreenBot", category: "screening", status: "active" },
  ],
  total: 2,
  isLoading: false,
  isError: false,
  mutate: vi.fn(),
}

vi.mock("@/hooks/agents/use-custom-agents", () => ({
  useCustomAgents: () => mockCustomAgents,
}))

const assignAgentToPool = vi.fn().mockResolvedValue({ id: "new-assignment-id" })

vi.mock("@/hooks/talent-pools/use-pool-agents", () => ({
  assignAgentToPool: (poolId: string, payload: unknown) =>
    assignAgentToPool(poolId, payload),
}))

// CronScheduleBuilder usa hooks complexos — mock para nao quebrar render.
vi.mock("@/components/pages-talent-pools/CronScheduleBuilder", () => ({
  CronScheduleBuilder: () => null,
}))

beforeEach(() => {
  assignAgentToPool.mockClear()
})

import { AssignAgentModal } from "../AssignAgentModal"

describe("AssignAgentModal (wrapper Pool) — Onda 4 Agent E", () => {
  it("renderiza o generic com targetType=talent_pool", () => {
    render(
      <AssignAgentModal
        poolId="pool-1"
        open
        onClose={() => {}}
        onAssigned={() => {}}
      />,
    )
    // O generic usa o select dropdown (nao mais cards).
    expect(screen.getByTestId("assign-agent-to-pool-modal")).toBeInTheDocument()
    expect(screen.getByTestId("assign-agent-to-pool-agent-select")).toBeInTheDocument()
  })

  it("lista custom_agents do tenant no select", () => {
    render(
      <AssignAgentModal
        poolId="pool-1"
        open
        onClose={() => {}}
        onAssigned={() => {}}
      />,
    )
    expect(screen.getByText("SourceBot")).toBeInTheDocument()
    expect(screen.getByText("ScreenBot")).toBeInTheDocument()
  })

  it("initialCategory aceito por backward-compat (no-op)", () => {
    // Nao quebra renderizar com initialCategory.
    render(
      <AssignAgentModal
        poolId="pool-1"
        open
        initialCategory="sourcing"
        onClose={() => {}}
        onAssigned={() => {}}
      />,
    )
    // Ambos os agents continuam visiveis — categoria filter foi removido.
    expect(screen.getByText("SourceBot")).toBeInTheDocument()
    expect(screen.getByText("ScreenBot")).toBeInTheDocument()
  })

  it("submit chama assignAgentToPool com payload canonical", async () => {
    render(
      <AssignAgentModal
        poolId="pool-1"
        open
        onClose={() => {}}
        onAssigned={() => {}}
      />,
    )
    // Seleciona agent via select
    fireEvent.change(
      screen.getByTestId("assign-agent-to-pool-agent-select"),
      { target: { value: "ca-1" } },
    )
    // Submit (default trigger_mode = manual -> schedule_type = on_demand)
    fireEvent.click(screen.getByTestId("assign-agent-to-pool-submit"))

    await waitFor(() =>
      expect(assignAgentToPool).toHaveBeenCalledWith(
        "pool-1",
        expect.objectContaining({
          custom_agent_id: "ca-1",
          schedule_type: "on_demand",
        }),
      ),
    )
  })

  it("trigger_mode=on_schedule traduz pra schedule_type=cron + schedule_config", async () => {
    render(
      <AssignAgentModal
        poolId="pool-1"
        open
        onClose={() => {}}
        onAssigned={() => {}}
      />,
    )
    fireEvent.change(
      screen.getByTestId("assign-agent-to-pool-agent-select"),
      { target: { value: "ca-1" } },
    )
    fireEvent.click(
      screen.getByTestId("assign-agent-to-pool-trigger-radio-on_schedule"),
    )
    fireEvent.click(screen.getByTestId("assign-agent-to-pool-submit"))

    await waitFor(() =>
      expect(assignAgentToPool).toHaveBeenCalledWith(
        "pool-1",
        expect.objectContaining({
          custom_agent_id: "ca-1",
          schedule_type: "cron",
          schedule_config: expect.objectContaining({ cron: expect.any(String) }),
        }),
      ),
    )
  })
})
