/**
 * Sprint 7B-2 — ConfigureAssignmentModal UI sentinels
 *
 * Cobre:
 * - Render do form de config
 * - Toggle status active↔paused dispara update
 * - Submit dispara PATCH com config_overrides
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import type { PoolAgentAssignment } from "@/types/pool-agent-assignment"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

const updateTrigger = vi.fn().mockResolvedValue({})

vi.mock("@/hooks/talent-pools/use-pool-agents", () => ({
  useUpdateAssignment: () => updateTrigger,
}))

beforeEach(() => {
  updateTrigger.mockClear()
})

function makeAssignment(): PoolAgentAssignment {
  return {
    id: "a-1",
    talent_pool_id: "pool-1",
    custom_agent_id: "ca-1",
    custom_agent_name: "Sourcer X",
    custom_agent_category: "sourcing",
    status: "active",
    schedule_type: "on_demand",
    schedule_config: {},
    config_overrides: { foo: "bar" },
    last_run_at: null,
    last_run_status: null,
    runtime_metrics: {},
    created_at: "2026-05-25T00:00:00Z",
    updated_at: "2026-05-25T00:00:00Z",
    created_by: "u-1",
  }
}

import { ConfigureAssignmentModal } from "../ConfigureAssignmentModal"

describe("ConfigureAssignmentModal — Sprint 7B-2", () => {
  it("renderiza form de config com nome do agent", () => {
    render(
      <ConfigureAssignmentModal
        assignment={makeAssignment()}
        poolId="pool-1"
        open
        onClose={() => {}}
        onSaved={() => {}}
      />,
    )
    expect(screen.getByText(/Sourcer X/)).toBeInTheDocument()
    expect(screen.getByTestId("config-overrides-editor")).toBeInTheDocument()
  })

  it("toggle status active→paused dispara update", async () => {
    render(
      <ConfigureAssignmentModal
        assignment={makeAssignment()}
        poolId="pool-1"
        open
        onClose={() => {}}
        onSaved={() => {}}
      />,
    )
    fireEvent.click(screen.getByTestId("config-status-toggle"))
    await waitFor(() =>
      expect(updateTrigger).toHaveBeenCalledWith(
        "a-1",
        expect.objectContaining({ status: "paused" }),
      ),
    )
  })

  it("submit dispara PATCH com config_overrides JSON válido", async () => {
    render(
      <ConfigureAssignmentModal
        assignment={makeAssignment()}
        poolId="pool-1"
        open
        onClose={() => {}}
        onSaved={() => {}}
      />,
    )
    const textarea = screen.getByTestId("config-overrides-editor") as HTMLTextAreaElement
    fireEvent.change(textarea, { target: { value: '{"new_key":"new_value"}' } })
    fireEvent.click(screen.getByTestId("config-submit"))
    await waitFor(() =>
      expect(updateTrigger).toHaveBeenCalledWith(
        "a-1",
        expect.objectContaining({
          config_overrides: { new_key: "new_value" },
        }),
      ),
    )
  })
})
