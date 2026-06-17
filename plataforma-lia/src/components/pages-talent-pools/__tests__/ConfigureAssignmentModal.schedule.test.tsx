/**
 * Sprint 7C Part 3 — ConfigureAssignmentModal schedule wiring tests
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

function makeAssignment(overrides: Partial<PoolAgentAssignment> = {}): PoolAgentAssignment {
  return {
    id: "a-1",
    talent_pool_id: "pool-1",
    custom_agent_id: "ca-1",
    custom_agent_name: "Sourcer X",
    custom_agent_category: "sourcing",
    status: "active",
    schedule_type: "on_demand",
    schedule_config: {},
    config_overrides: {},
    last_run_at: null,
    last_run_status: null,
    runtime_metrics: {},
    created_at: "2026-05-26T00:00:00Z",
    updated_at: "2026-05-26T00:00:00Z",
    created_by: "u-1",
    ...overrides,
  }
}

import { ConfigureAssignmentModal } from "../ConfigureAssignmentModal"

describe("ConfigureAssignmentModal — schedule Sprint 7C Part 3", () => {
  it("renderiza CronScheduleBuilder quando schedule_type=cron", () => {
    render(
      <ConfigureAssignmentModal
        assignment={makeAssignment({
          schedule_type: "cron",
          schedule_config: { cron_expression: "0 9 * * *" },
        })}
        poolId="pool-1"
        open
        onClose={() => {}}
        onSaved={() => {}}
      />,
    )
    expect(screen.getByTestId("cron-schedule-builder")).toBeInTheDocument()
    expect(screen.queryByTestId("event-trigger-picker")).not.toBeInTheDocument()
  })

  it("renderiza EventTriggerPicker quando schedule_type=event_driven", () => {
    render(
      <ConfigureAssignmentModal
        assignment={makeAssignment({
          schedule_type: "event_driven",
          schedule_config: { event_triggers: ["candidate_added_to_pool"] },
        })}
        poolId="pool-1"
        open
        onClose={() => {}}
        onSaved={() => {}}
      />,
    )
    expect(screen.getByTestId("event-trigger-picker")).toBeInTheDocument()
    expect(screen.queryByTestId("cron-schedule-builder")).not.toBeInTheDocument()
  })

  it("submit canonical inclui schedule_type + schedule_config", async () => {
    render(
      <ConfigureAssignmentModal
        assignment={makeAssignment({
          schedule_type: "cron",
          schedule_config: { cron_expression: "0 9 * * *" },
        })}
        poolId="pool-1"
        open
        onClose={() => {}}
        onSaved={() => {}}
      />,
    )
    fireEvent.click(screen.getByTestId("config-submit"))
    await waitFor(() =>
      expect(updateTrigger).toHaveBeenCalledWith(
        "a-1",
        expect.objectContaining({
          schedule_type: "cron",
          schedule_config: expect.objectContaining({
            cron_expression: expect.stringMatching(/\* \* \*/),
          }),
        }),
      ),
    )
  })
})
