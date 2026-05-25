/**
 * Sprint 7B-2 — AssignAgentModal UI sentinels
 *
 * Cobre:
 * - Lista custom_agents do tenant
 * - Filter por categoria
 * - Radio schedule_type só on_demand habilitado (cron/event-driven disabled)
 * - Submit dispara useAssignAgent (POST)
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

const assignTrigger = vi.fn().mockResolvedValue({ id: "new-assignment-id" })

vi.mock("@/hooks/talent-pools/use-pool-agents", () => ({
  useAssignAgent: () => assignTrigger,
}))

beforeEach(() => {
  assignTrigger.mockClear()
})

import { AssignAgentModal } from "../AssignAgentModal"

describe("AssignAgentModal — Sprint 7B-2", () => {
  it("lista custom_agents do tenant", () => {
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

  it("filter por categoria filtra a lista", () => {
    render(
      <AssignAgentModal
        poolId="pool-1"
        open
        initialCategory="sourcing"
        onClose={() => {}}
        onAssigned={() => {}}
      />,
    )
    expect(screen.getByText("SourceBot")).toBeInTheDocument()
    expect(screen.queryByText("ScreenBot")).not.toBeInTheDocument()
  })

  it("radio schedule_type — apenas on_demand habilitado", () => {
    render(
      <AssignAgentModal
        poolId="pool-1"
        open
        onClose={() => {}}
        onAssigned={() => {}}
      />,
    )
    const onDemand = screen.getByTestId("schedule-radio-on_demand") as HTMLInputElement
    const cron = screen.getByTestId("schedule-radio-cron") as HTMLInputElement
    const evt = screen.getByTestId("schedule-radio-event_driven") as HTMLInputElement
    expect(onDemand.disabled).toBe(false)
    expect(cron.disabled).toBe(true)
    expect(evt.disabled).toBe(true)
  })

  it("submit dispara useAssignAgent com payload canonical", async () => {
    render(
      <AssignAgentModal
        poolId="pool-1"
        open
        onClose={() => {}}
        onAssigned={() => {}}
      />,
    )
    // Selecionar agent
    fireEvent.click(screen.getByTestId("agent-row-ca-1"))
    // Submit
    fireEvent.click(screen.getByTestId("assign-submit"))
    await waitFor(() =>
      expect(assignTrigger).toHaveBeenCalledWith(
        expect.objectContaining({
          custom_agent_id: "ca-1",
          schedule_type: "on_demand",
        }),
      ),
    )
  })
})
