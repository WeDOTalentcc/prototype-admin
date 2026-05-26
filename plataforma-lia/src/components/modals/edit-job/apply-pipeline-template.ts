/**
 * Pure helpers for `useEditJob.applyPipelineTemplate` — extracted so the
 * canonical-endpoint logic is testable without rendering the entire hook
 * (whose import graph pulls jsdom + all of lia-api into the vitest worker
 * and OOMs the runner).
 *
 * Sprint Pipeline Templates Gap #4 — producer canonical is
 * `POST /vacancies/{vacancy_id}/apply-pipeline-template`
 * (`PipelineTemplateService.apply_to_vacancy` emits audit log). The hook
 * consumer used to do a state-only apply; this helper now mediates the
 * persisted vs local-only branch.
 */
import type { InterviewStage, PipelineTemplate } from "./edit-job.types"

export function translateTemplateStages(template: PipelineTemplate): InterviewStage[] {
  return template.stages.map((s, idx) => ({
    stageName: s.name,
    order: s.order || idx + 1,
    sla: s.sla_days,
    type:
      s.type === "automatic"
        ? "automated"
        : (s.type as "automated" | "manual" | "hybrid"),
  }))
}

export type ApplyResult =
  | { mode: "persisted"; stages: InterviewStage[]; templateName: string }
  | { mode: "local"; stages: InterviewStage[]; templateName: string }
  | { mode: "error"; message: string }

export interface ApplyContext {
  vacancyId: string | null | undefined
  template: PipelineTemplate | undefined
  fetchImpl?: typeof fetch
}

/**
 * Decides whether to call the canonical endpoint (edit mode) or keep apply
 * state-local (create mode), and returns a discriminated result for the
 * caller to translate into toast + setState.
 */
export async function applyPipelineTemplateCore(
  ctx: ApplyContext,
  templateId: string,
): Promise<ApplyResult> {
  const fetchImpl = ctx.fetchImpl ?? fetch
  if (!ctx.template) {
    return { mode: "error", message: "Template não encontrado" }
  }

  const stages = translateTemplateStages(ctx.template)
  const templateName = ctx.template.name

  if (ctx.vacancyId) {
    // Edit mode — persist via canonical endpoint (audit log emitted)
    try {
      const response = await fetchImpl(
        `/api/backend-proxy/job-vacancies/${ctx.vacancyId}/apply-pipeline-template`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ template_id: templateId, source: "manual_modal" }),
        },
      )
      if (!response.ok) {
        let detail = `HTTP ${response.status}`
        try {
          const body = await response.json()
          detail = body?.detail || body?.message || detail
        } catch {
          /* body not JSON */
        }
        return { mode: "error", message: `Erro ao aplicar template: ${detail}` }
      }
      return { mode: "persisted", stages, templateName }
    } catch (err) {
      const detail = err instanceof Error ? err.message : "network error"
      return { mode: "error", message: `Erro ao aplicar template: ${detail}` }
    }
  }

  // Create mode — state-only; legacy increment-usage fire-and-forget
  fetchImpl(
    `/api/backend-proxy/company/pipeline-templates/${templateId}/increment-usage`,
    { method: "POST" },
  ).catch((err) => {
    console.warn(
      "[applyPipelineTemplateCore] increment-usage fire-and-forget failed",
      err,
    )
  })
  return { mode: "local", stages, templateName }
}
