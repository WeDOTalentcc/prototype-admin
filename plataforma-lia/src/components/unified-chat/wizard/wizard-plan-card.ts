/**
 * wizard-plan-card — pure helpers that turn the canonical wizard state
 * (`useWizardFlow`) into the data we render as the non-persisted
 * "Plano de trabalho" assistant message in the chat feed.
 *
 * Keeping the logic in a plain module (no React hooks, no DOM) makes it
 * trivial to unit-test and trivial to port to Vue/Vuetify later — the
 * presentation layer just consumes `FlowStep[]`.
 *
 * Single source of truth: the visible-stage subset and labels both come
 * from `wizard-types.ts`. We never duplicate the labels here.
 */
import type { FlowStep } from "@/components/workflow-rail/FlowStepMessage"
import { STAGE_LABELS, STAGE_ORDER, type WizardStage } from "./wizard-types"

/**
 * Stages surfaced in the chat-feed plan card and the top-of-feed
 * `WizardProgressBar`. Hidden stages (`intake`, `bigfive`, `salary`,
 * `eligibility`, `handoff`, `done`) are still tracked by the hook but
 * collapse into the surrounding visible stages for the recruiter.
 *
 * Mirrors `WizardProgressBar.VISIBLE_STAGES`.
 */
export const PLAN_VISIBLE_STAGES: readonly WizardStage[] = [
  "jd_enrichment",
  "competency",
  "wsi_questions",
  "review",
  "publish",
  "calibration",
] as const

export const WIZARD_PLAN_MESSAGE_ID = "lia-wizard-plan-card"
export const WIZARD_PLAN_TITLE = "Plano de trabalho"

/**
 * Map the wizard's `currentStage` onto the 6 visible plan steps.
 *
 *  - `completed`: stage strictly precedes the current stage in `STAGE_ORDER`
 *  - `in_progress`: the current stage itself
 *  - `pending`: any stage after the current one (or all of them if the
 *    current stage is unknown / hasn't reached the visible window yet)
 */
export function buildPlanFlowSteps(currentStage: WizardStage | null): FlowStep[] {
  const currentIdx =
    currentStage !== null ? STAGE_ORDER.indexOf(currentStage) : -1
  return PLAN_VISIBLE_STAGES.map((stage) => {
    const stageIdx = STAGE_ORDER.indexOf(stage)
    let status: FlowStep["status"]
    if (stageIdx < currentIdx) status = "completed"
    else if (stageIdx === currentIdx) status = "in_progress"
    else status = "pending"
    return { id: stage, label: STAGE_LABELS[stage], status }
  })
}

/**
 * Cheap structural comparison so the chat surface can skip a re-render
 * when the wizard re-emits the same stage (e.g. retries) without changing
 * any visible plan step status.
 */
export function planStepsEqual(a: FlowStep[], b: FlowStep[]): boolean {
  if (a.length !== b.length) return false
  for (let i = 0; i < a.length; i++) {
    if (a[i].id !== b[i].id || a[i].status !== b[i].status) return false
  }
  return true
}
