/**
 * Job Readiness Hub API client (Task #429).
 *
 * Talks to /api/v1/job-readiness/* on the LIA backend. Every call is
 * scoped server-side by the caller's company_id (no tenant on the wire).
 */
import { BACKEND_URL, getAuthHeaders, HttpError } from "./base"

export type ReadinessStage =
  | "importada"
  | "sem_jd"
  | "jd_rascunho"
  | "jd_enriquecido"
  | "perguntas_triagem"
  | "pronta_disparo"
  | "em_triagem"

export type AudiencePolicy = "new_only" | "imported_untriaged" | "manual_selection"

export interface ReadinessStageCount {
  stage: ReadinessStage
  label: string
  count: number
  requires_human: boolean
}

export interface ReadinessOverview {
  total: number
  by_stage: ReadinessStageCount[]
  action_required: number
  queued_actions: number
  last_event_at: string | null
}

export interface ReadinessJobCard {
  id: string
  title: string
  job_id: string | null
  department: string | null
  source_system: string | null
  status: string | null
  readiness_stage: ReadinessStage
  readiness_label: string
  readiness_blockers: string[]
  requires_human: boolean
  next_action: string | null
  last_event_at: string | null
}

export interface ReadinessBoard {
  total: number
  items: ReadinessJobCard[]
}

export interface ReadinessTimelineEvent {
  id: string
  at: string
  actor: string
  action: string
  field: string | null
  summary: string
  old_value: unknown
  new_value: unknown
}

export interface ReadinessJobDetail extends ReadinessJobCard {
  description: string | null
  enriched_jd: Record<string, unknown> | null
  behavioral_competencies: unknown[]
  screening_questions: unknown[]
  assigned_audience_policy: AudiencePolicy | null
  timeline: ReadinessTimelineEvent[]
}

export interface RunBatchSummary {
  enqueued: string[]
  skipped_human_required: string[]
  errors: { job_id: string; error: string }[]
  total: number
}

async function _json<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: { ...getAuthHeaders(), ...(init.headers || {}) },
  })
  if (!res.ok) {
    const text = await res.text().catch(() => "")
    throw new HttpError(res.status, `readiness ${path} ${res.status}: ${text || res.statusText}`)
  }
  return res.json() as Promise<T>
}

export function getReadinessOverview() {
  return _json<ReadinessOverview>("/job-readiness/overview")
}

export function getReadinessBoard(opts: { stage?: ReadinessStage; search?: string; skip?: number; limit?: number } = {}) {
  const params = new URLSearchParams()
  if (opts.stage) params.set("stage", opts.stage)
  if (opts.search) params.set("search", opts.search)
  if (opts.skip !== undefined) params.set("skip", String(opts.skip))
  if (opts.limit !== undefined) params.set("limit", String(opts.limit))
  const qs = params.toString() ? `?${params}` : ""
  return _json<ReadinessBoard>(`/job-readiness/board${qs}`)
}

export function getReadinessJob(id: string) {
  return _json<ReadinessJobDetail>(`/job-readiness/job/${id}`)
}

export function runReadinessAll() {
  return _json<RunBatchSummary>("/job-readiness/run-all", { method: "POST" })
}

export function runReadinessBatch(jobIds: string[]) {
  return _json<RunBatchSummary>("/job-readiness/run-batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_ids: jobIds }),
  })
}

export function approveReadinessStage(id: string) {
  return _json<ReadinessJobDetail>(`/job-readiness/job/${id}/approve-stage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  })
}

export function rejectReadinessStage(id: string, reason?: string) {
  return _json<ReadinessJobDetail>(`/job-readiness/job/${id}/reject-stage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason: reason || "" }),
  })
}

export function dispatchReadinessScreening(id: string, audiencePolicy: AudiencePolicy) {
  return _json<ReadinessJobDetail>(`/job-readiness/job/${id}/dispatch-screening`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ audience_policy: audiencePolicy }),
  })
}

export const READINESS_STAGES_ORDER: ReadinessStage[] = [
  "importada",
  "sem_jd",
  "jd_rascunho",
  "jd_enriquecido",
  "perguntas_triagem",
  "pronta_disparo",
  "em_triagem",
]
