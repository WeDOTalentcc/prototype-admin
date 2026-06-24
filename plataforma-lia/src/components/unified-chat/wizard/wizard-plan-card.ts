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
import type { FlowStep } from "@/components/unified-chat/FlowStepMessage"
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
  "intake",
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
  jobId: number | string | null
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
  // Accept both number (current Rails int IDs) and string (UUIDs/slugs)
  // so a backend ID-format change can't silently strip the ID from the
  // closing card. Empty strings still collapse to null.
  let jobId: number | string | null = null
  if (typeof d.job_id === "number") {
    jobId = d.job_id
  } else if (typeof d.job_id === "string" && d.job_id.trim() !== "") {
    jobId = d.job_id
  }
  const title = typeof d.job_title === "string" && d.job_title.trim() !== ""
    ? d.job_title
    : null
  const handoffUrl = typeof d.handoff_url === "string" && d.handoff_url.trim() !== ""
    ? d.handoff_url
    : null
  // Canonical-fix (post-mortem 2026-04-29): the previous fallback
  // `/jobs/${jobId}` was synthesizing URLs for a route that no longer
  // exists in the Next.js app, leading to 404s on every wizard
  // "Open job page" click. The producer (backend handoff_node in
  // app/domains/job_creation/graph.py) now returns null until product
  // decides the canonical route. Frontend trusts the producer.
  const url = handoffUrl
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

// ---------------------------------------------------------------------------
// Pipeline template selection card (Onda 28 — E.8)
// ---------------------------------------------------------------------------

/**
 * Stable id for the non-persisted pipeline-template selection card so
 * re-emissions of the same `suggestions_data.pipeline_template` block
 * update the existing card in place instead of stacking duplicates in
 * the chat feed.
 */
export const WIZARD_TEMPLATE_MESSAGE_ID = "lia-wizard-template-card"
export const WIZARD_TEMPLATE_TITLE = "Escolha o pipeline desta vaga"

/**
 * Canonical ids for the 5 backend-supported pipeline templates. Mirrors
 * the `suggested_type` enum emitted by `stage_basic_info.py` (Onda 25)
 * so the highlight + click payload stay in sync without a runtime guard.
 */
export type PipelineTemplateType =
  | "technical"
  | "executive"
  | "operational"
  | "mass_hiring"
  | "intern"

export interface PipelineTemplateOption {
  id: PipelineTemplateType
  /** Recruiter-facing short name (PT-BR, used in the chat reply). */
  name: string
  /** One-line summary surfaced as the button's secondary copy. */
  description: string
  /** Pipeline stages displayed as a small chevron-separated list. */
  stages: readonly string[]
}

/**
 * Static catalog of the 5 pipeline templates rendered in the card.
 * Descriptions stay short so the card never overflows the chat column.
 */
export const PIPELINE_TEMPLATES: readonly PipelineTemplateOption[] = [
  {
    id: "technical",
    name: "Técnico",
    description: "Vagas de engenharia, dados e produto.",
    stages: ["Triagem", "Desafio Técnico", "Entrevista Cultural", "Proposta"],
  },
  {
    id: "executive",
    name: "Executivo",
    description: "Liderança sênior, diretoria e C-level.",
    stages: ["Triagem", "Hiring Manager", "C-level", "Negociação"],
  },
  {
    id: "operational",
    name: "Operacional",
    description: "Volume médio com decisão rápida.",
    stages: ["Triagem rápida", "Entrevista", "Proposta"],
  },
  {
    id: "mass_hiring",
    name: "Mass Hiring",
    description: "Alto volume com triagem WSI em batch.",
    stages: ["Triagem WSI", "Validação", "Proposta em batch"],
  },
  {
    id: "intern",
    name: "Estágio",
    description: "Estagiários e trainees, foco acadêmico.",
    stages: ["Avaliação acadêmica", "Entrevista comportamental", "Proposta"],
  },
] as const

/**
 * Plain data the chat-feed pipeline-template card consumes. Mirrors the
 * shape of `suggestions_data.pipeline_template` emitted by the backend —
 * we keep the templates list flexible (string[] of ids) so a future
 * backend tweak that hides one option doesn't require a frontend bump.
 */
export interface PipelineTemplateCardData {
  /** Backend's recommendation, used to highlight the matching option. */
  suggestedType: PipelineTemplateType | null
  /** Allowed template ids — when null, all 5 from the catalog are shown. */
  allowedTypes: PipelineTemplateType[] | null
}

const VALID_TEMPLATE_IDS = new Set<string>(PIPELINE_TEMPLATES.map((t) => t.id))

function coerceTemplateType(value: unknown): PipelineTemplateType | null {
  return typeof value === "string" && VALID_TEMPLATE_IDS.has(value)
    ? (value as PipelineTemplateType)
    : null
}

/**
 * Build the template-card data from a wizard stage payload's `data`
 * field. Returns `null` when the backend hasn't surfaced a template
 * suggestion yet so the chat surface can skip injection.
 *
 * Accepts both shapes the backend may emit:
 *   - `data.suggestions_data.pipeline_template = { suggested_type, templates }`
 *     (Onda 25 canonical path)
 *   - `data.pipeline_template = { ... }` (legacy fallback while the
 *     backend stabilises the wrapper key — drops with no behaviour change)
 */
export function buildPipelineTemplateCard(
  data: Record<string, unknown> | null | undefined,
): PipelineTemplateCardData | null {
  if (!data) return null
  const wrapper =
    (data.suggestions_data as Record<string, unknown> | undefined) ?? data
  const block = wrapper?.pipeline_template as
    | Record<string, unknown>
    | undefined
  if (!block || typeof block !== "object") return null
  const suggestedType = coerceTemplateType(block.suggested_type)
  const rawTemplates = block.templates
  let allowedTypes: PipelineTemplateType[] | null = null
  if (Array.isArray(rawTemplates)) {
    const filtered = rawTemplates
      .map((t) => {
        if (typeof t === "string") return coerceTemplateType(t)
        if (t && typeof t === "object") {
          return coerceTemplateType((t as Record<string, unknown>).id)
        }
        return null
      })
      .filter((t): t is PipelineTemplateType => t !== null)
    allowedTypes = filtered.length > 0 ? filtered : null
  }
  // No usable signal at all — skip injection.
  if (suggestedType === null && allowedTypes === null) return null
  return { suggestedType, allowedTypes }
}

/**
 * Cheap structural equality so the template card doesn't churn when the
 * wizard re-emits the same suggestion (e.g. recruiter sends another
 * message before picking a template).
 */
export function pipelineTemplateCardsEqual(
  a: PipelineTemplateCardData | null,
  b: PipelineTemplateCardData | null,
): boolean {
  if (a === b) return true
  if (a === null || b === null) return false
  if (a.suggestedType !== b.suggestedType) return false
  const aList = a.allowedTypes
  const bList = b.allowedTypes
  if (aList === bList) return true
  if (aList === null || bList === null) return false
  if (aList.length !== bList.length) return false
  for (let i = 0; i < aList.length; i++) {
    if (aList[i] !== bList[i]) return false
  }
  return true
}
