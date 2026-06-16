/**
 * Sprint 7B-2 — PoolAgentsTab UI sentinels
 *
 * Cobre:
 * - Empty state quando 0 assignments
 * - Render multi-category (3 assignments diferentes)
 * - Filter chip por categoria filtra a lista
 * - Dispatch on-demand happy path (chama useDispatchAgent)
 * - Pause via useUpdateAssignment
 * - Remove com confirm chama useUnassignAgent
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import type { PoolAgentAssignment } from "@/types/pool-agent-assignment"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

const mockData: { assignments: PoolAgentAssignment[]; isLoading: boolean; error: string | null } = {
  assignments: [],
  isLoading: false,
  error: null,
}
const dispatchTrigger = vi.fn().mockResolvedValue({ status: "queued", assignment_id: "x" })
const updateTrigger = vi.fn().mockResolvedValue({})
const unassignTrigger = vi.fn().mockResolvedValue(undefined)
const mutateSpy = vi.fn().mockResolvedValue(undefined)

vi.mock("@/hooks/talent-pools/use-pool-agents", () => ({
  usePoolAgents: () => ({
    data: mockData.assignments,
    isLoading: mockData.isLoading,
    error: mockData.error,
    mutate: mutateSpy,
  }),
  useDispatchAgent: () => dispatchTrigger,
  useUpdateAssignment: () => updateTrigger,
  useUnassignAgent: () => unassignTrigger,
}))

// Force user confirm dialog to true
beforeEach(() => {
  vi.spyOn(window, "confirm").mockReturnValue(true)
  mockData.assignments = []
  mockData.isLoading = false
  mockData.error = null
  dispatchTrigger.mockClear()
  updateTrigger.mockClear()
  unassignTrigger.mockClear()
})

function makeAssignment(overrides: Partial<PoolAgentAssignment> = {}): PoolAgentAssignment {
  return {
    id: "a-" + Math.random().toString(36).slice(2),
    talent_pool_id: "pool-1",
    custom_agent_id: "agent-1",
    custom_agent_name: "Sourcing Bot",
    custom_agent_category: "sourcing",
    status: "active",
    schedule_type: "on_demand",
    schedule_config: {},
    config_overrides: {},
    last_run_at: null,
    last_run_status: null,
    runtime_metrics: {},
    created_at: "2026-05-25T00:00:00Z",
    updated_at: "2026-05-25T00:00:00Z",
    created_by: "user-1",
    ...overrides,
  }
}

// Import AFTER mocks
import { PoolAgentsTab } from "../PoolAgentsTab"

describe("PoolAgentsTab — Sprint 7B-2", () => {
  it("renderiza empty state quando 0 assignments", () => {
    mockData.assignments = []
    render(<PoolAgentsTab poolId="pool-1" />)
    expect(screen.getByTestId("pool-agents-empty")).toBeInTheDocument()
  })

  it("renderiza múltiplas categorias", () => {
    mockData.assignments = [
      makeAssignment({ id: "a1", custom_agent_name: "SourcerX", custom_agent_category: "sourcing" }),
      makeAssignment({ id: "a2", custom_agent_name: "ScreenerY", custom_agent_category: "screening" }),
      makeAssignment({ id: "a3", custom_agent_name: "CommZ", custom_agent_category: "communication" }),
    ]
    render(<PoolAgentsTab poolId="pool-1" />)
    expect(screen.getByText("SourcerX")).toBeInTheDocument()
    expect(screen.getByText("ScreenerY")).toBeInTheDocument()
    expect(screen.getByText("CommZ")).toBeInTheDocument()
  })

  it("filter chip por categoria filtra a lista", () => {
    mockData.assignments = [
      makeAssignment({ id: "a1", custom_agent_name: "SourcerX", custom_agent_category: "sourcing" }),
      makeAssignment({ id: "a2", custom_agent_name: "ScreenerY", custom_agent_category: "screening" }),
    ]
    render(<PoolAgentsTab poolId="pool-1" />)
    const chip = screen.getByTestId("filter-chip-sourcing")
    fireEvent.click(chip)
    expect(screen.getByText("SourcerX")).toBeInTheDocument()
    expect(screen.queryByText("ScreenerY")).not.toBeInTheDocument()
  })

  it("dispatch on-demand chama useDispatchAgent", async () => {
    mockData.assignments = [makeAssignment({ id: "a1" })]
    render(<PoolAgentsTab poolId="pool-1" />)
    const btn = screen.getByTestId("assignment-run-a1")
    fireEvent.click(btn)
    await waitFor(() => expect(dispatchTrigger).toHaveBeenCalledWith("a1"))
  })

  it("toggle pause chama useUpdateAssignment", async () => {
    mockData.assignments = [makeAssignment({ id: "a1", status: "active" })]
    render(<PoolAgentsTab poolId="pool-1" />)
    const btn = screen.getByTestId("assignment-toggle-status-a1")
    fireEvent.click(btn)
    await waitFor(() =>
      expect(updateTrigger).toHaveBeenCalledWith("a1", { status: "paused" }),
    )
  })

  it("remove com confirm chama useUnassignAgent", async () => {
    mockData.assignments = [makeAssignment({ id: "a1" })]
    render(<PoolAgentsTab poolId="pool-1" />)
    const btn = screen.getByTestId("assignment-remove-a1")
    fireEvent.click(btn)
    await waitFor(() => expect(unassignTrigger).toHaveBeenCalledWith("a1"))
  })
})
