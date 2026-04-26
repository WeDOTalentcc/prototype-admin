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
import {
  STAGE_LABELS,
  STAGE_ORDER,
  type HandoffData,
  type WizardStage,
} from "./wizard-types"

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
 * Final wizard stages that should trigger the closing summary card AND
 * the "all completed" rendering of the plan card. Both `done` and
 * `handoff` are accepted because the backend currently emits `handoff`
 * as the terminal stage, while `done` is reserved for a future explicit
 * completion step (and unit tests dispatch it).
 */
export const WIZARD_CLOSING_STAGES: readonly WizardStage[] = ["handoff", "done"] as const

export function isWizardClosingStage(stage: WizardStage | null): boolean {
  return stage !== null && (WIZARD_CLOSING_STAGES as readonly string[]).includes(stage)
}

/**
 * Map the wizard's `currentStage` onto the 6 visible plan steps.
 *
 *  - `completed`: stage strictly precedes the current stage in `STAGE_ORDER`
 *  - `in_progress`: the current stage itself
 *  - `pending`: any stage after the current one (or all of them if the
 *    current stage is unknown / hasn't reached the visible window yet)
 *
 * Special case — terminal stages (`handoff`, `done`): every visible step
 * is marked `completed` so the chat-feed plan card reflects "concluído"
 * instead of staying frozen on calibration's "in progress" pill (Task #830).
 */
export function buildPlanFlowSteps(currentStage: WizardStage | null): FlowStep[] {
  if (isWizardClosingStage(currentStage)) {
    return PLAN_VISIBLE_STAGES.map((stage) => ({
      id: stage,
      label: STAGE_LABELS[stage],
      status: "completed",
    }))
  }
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
 * User-facing suffix appended to the plan card title once the wizard
 * reaches a terminal stage (Task #830). Kept as a constant so the unit
 * tests, the chat surface, and any future Vue port stay in sync.
 */
export const WIZARD_PLAN_COMPLETED_SUFFIX = "Concluído"
export const WIZARD_PLAN_COMPLETED_TITLE =
  `${WIZARD_PLAN_TITLE} — ${WIZARD_PLAN_COMPLETED_SUFFIX}`

/**
 * Title to render at the top of the plan card given the current stage.
 * Switches to the "concluído" variant on terminal stages so the recruiter
 * sees a clear "this finished" signal instead of a frozen progress card.
 */
export function planCardTitleForStage(currentStage: WizardStage | null): string {
  return isWizardClosingStage(currentStage)
    ? WIZARD_PLAN_COMPLETED_TITLE
    : WIZARD_PLAN_TITLE
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

// ---------------------------------------------------------------------------
// Closing card — "Vaga publicada" injected into the feed at done/handoff
// ---------------------------------------------------------------------------

/**
 * Stable id for the non-persisted closing card so re-emits of the
 * same final stage update the existing card in place instead of stacking.
 */
export const WIZARD_PUBLISHED_MESSAGE_ID = "lia-wizard-published-card"
export const WIZARD_PUBLISHED_TITLE = "Vaga publicada"

/**
 * Plain data the chat-feed closing card consumes. Keeping it as a small
 * record (no React imports) makes the helper trivial to unit-test and
 * port to Vue/Vuetify later.
 */
export interface WizardPublishedJobCardData {
  jobId: number | null
  title: string | null
  url: string | null
  shareLink: string | null
}

/**
 * Build the closing-card data from a wizard stage payload's `data` field.
 * Returns `null` when the stage isn't a closing stage so the chat surface
 * can decide whether to inject the card.
 *
 * The card is intentionally lenient: it renders even when only one of
 * (title, jobId, url) is present — the wizard is "done" the moment the
 * backend says so, even if the publish step couldn't fetch every detail.
 */
export function buildPublishedJobCard(
  stage: WizardStage | null,
  data: Record<string, unknown> | null | undefined,
): WizardPublishedJobCardData | null {
  if (!isWizardClosingStage(stage)) return null
  const d = (data ?? {}) as Partial<HandoffData> & Record<string, unknown>
  const jobId = typeof d.job_id === "number" ? d.job_id : null
  const title = typeof d.job_title === "string" && d.job_title.trim() !== ""
    ? d.job_title
    : null
  const handoffUrl = typeof d.handoff_url === "string" && d.handoff_url.trim() !== ""
    ? d.handoff_url
    : null
  const url = handoffUrl ?? (jobId !== null ? `/jobs/${jobId}` : null)
  const shareLink = typeof d.share_link === "string" && d.share_link.trim() !== ""
    ? d.share_link
    : null
  return { jobId, title, url, shareLink }
}

/**
 * Cheap structural equality so the closing card doesn't churn when the
 * wizard re-emits the same `handoff` payload (e.g. resume after refresh).
 */
export function publishedJobCardsEqual(
  a: WizardPublishedJobCardData | null,
  b: WizardPublishedJobCardData | null,
): boolean {
  if (a === b) return true
  if (a === null || b === null) return false
  return (
    a.jobId === b.jobId &&
    a.title === b.title &&
    a.url === b.url &&
    a.shareLink === b.shareLink
  )
}
