/**
 * Task #826 — verifies the helpers that drive the non-persisted
 * "Plano de trabalho" assistant card injected into the chat feed.
 *
 * Pure logic, no DOM: the helpers must keep the visible plan steps in
 * lockstep with the canonical `STAGE_ORDER` from `wizard-types.ts`. Any
 * drift would either show a wrong step as active or skip the
 * highlight entirely.
 */
import { describe, it, expect } from "vitest"
import {
  PLAN_VISIBLE_STAGES,
  WIZARD_PLAN_MESSAGE_ID,
  WIZARD_PLAN_TITLE,
  buildPlanFlowSteps,
  planStepsEqual,
} from "../wizard-plan-card"
import { STAGE_LABELS } from "../wizard-types"

describe("buildPlanFlowSteps", () => {
  it("renders all six visible stages as pending when no stage is set", () => {
    const steps = buildPlanFlowSteps(null)
    expect(steps).toHaveLength(6)
    expect(steps.every((s) => s.status === "pending")).toBe(true)
    expect(steps.map((s) => s.id)).toEqual([...PLAN_VISIBLE_STAGES])
  })

  it("uses canonical STAGE_LABELS for every step (no parallel label table)", () => {
    const steps = buildPlanFlowSteps("competency")
    for (const step of steps) {
      expect(step.label).toBe(STAGE_LABELS[step.id as keyof typeof STAGE_LABELS])
    }
  })

  it("marks earlier visible stages completed and later ones pending", () => {
    const steps = buildPlanFlowSteps("wsi_questions")
    const byId = Object.fromEntries(steps.map((s) => [s.id, s.status]))
    expect(byId.jd_enrichment).toBe("completed")
    expect(byId.competency).toBe("completed")
    expect(byId.wsi_questions).toBe("in_progress")
    expect(byId.review).toBe("pending")
    expect(byId.publish).toBe("pending")
    expect(byId.calibration).toBe("pending")
  })

  it("treats hidden stages (intake, bigfive, salary) as 'before any visible step'", () => {
    // Intake precedes jd_enrichment in STAGE_ORDER, so all visible steps are
    // still pending — no false 'completed' marks for hidden stages.
    const steps = buildPlanFlowSteps("intake")
    expect(steps.every((s) => s.status === "pending")).toBe(true)
  })

  it("highlights calibration as the in-progress step at the end of the visible window", () => {
    const steps = buildPlanFlowSteps("calibration")
    const cal = steps.find((s) => s.id === "calibration")
    expect(cal?.status).toBe("in_progress")
    // Every visible stage before calibration should be completed.
    const before = steps.filter((s) => s.id !== "calibration")
    expect(before.every((s) => s.status === "completed")).toBe(true)
  })
})

describe("planStepsEqual", () => {
  it("returns true for two identical plan-step arrays", () => {
    const a = buildPlanFlowSteps("competency")
    const b = buildPlanFlowSteps("competency")
    expect(planStepsEqual(a, b)).toBe(true)
  })

  it("returns false when any step status differs", () => {
    const a = buildPlanFlowSteps("competency")
    const b = buildPlanFlowSteps("wsi_questions")
    expect(planStepsEqual(a, b)).toBe(false)
  })

  it("returns false on length mismatch", () => {
    const a = buildPlanFlowSteps("competency")
    expect(planStepsEqual(a, a.slice(0, 3))).toBe(false)
  })
})

describe("plan-card constants", () => {
  it("exposes a stable virtual-message id so re-renders update in place", () => {
    expect(WIZARD_PLAN_MESSAGE_ID).toBe("lia-wizard-plan-card")
  })

  it("exposes the user-facing title", () => {
    expect(WIZARD_PLAN_TITLE).toBe("Plano de trabalho")
  })

  it("exposes exactly the six visible stages the WizardProgressBar surfaces", () => {
    expect(PLAN_VISIBLE_STAGES).toEqual([
      "jd_enrichment",
      "competency",
      "wsi_questions",
      "review",
      "publish",
      "calibration",
    ])
  })
})
