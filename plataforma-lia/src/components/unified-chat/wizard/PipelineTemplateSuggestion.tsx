"use client"

import { useCallback, useState } from "react"
import { Sparkles, Layers, Sparkle } from "lucide-react"
import { toast } from "sonner"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import type { WizardPipelineTemplateSuggestion } from "@/components/unified-chat/wizard/wizard-types"

/**
 * PipelineTemplateSuggestion — card injetado no chat do wizard pela LIA
 * quando o backend (Phase 1.6) detecta department/seniority/job_family e
 * sugere até top-3 templates de pipeline JÁ CRIADOS pelo cliente em
 * Configurações > Recrutamento > Templates de Pipeline.
 *
 * Distinção do `WizardPipelineTemplateCard` (Onda 25 / Onda 28):
 *   - WizardPipelineTemplateCard => 5 PRESETS canonical (technical/executive/
 *     operational/mass_hiring/intern), shipados com a plataforma.
 *   - PipelineTemplateSuggestion => templates CUSTOMIZADOS pelo cliente,
 *     vindos do banco (CompanyPipelineTemplate), ranqueados por match com
 *     a vaga em curso.
 *
 * Design tokens canonical (Design System v4.2.x):
 *   - Header com accent cyan (`text-wedo-cyan`) — LIA "agindo" (memory
 *     `project_white_label_ai_assistant`).
 *   - Botão primário "Aplicar este template" usa variant Ink canonical
 *     (`bg-lia-text-primary`), NUNCA cyan — cyan é exclusivo da
 *     identidade da assistente, não de actions do recrutador.
 *   - Scores formatados como `{percent}% match`.
 */
export interface PipelineTemplateSuggestionProps {
  templates: WizardPipelineTemplateSuggestion[]
  /**
   * vacancy persistida no Rails. Pode ser `null` quando o wizard ainda
   * não criou a vaga no backend (e.g. sugestão emitida em jd_enrichment
   * antes de F8 publish). Nesse caso o card mostra os templates mas
   * desabilita "Aplicar" — o recrutador é orientado a re-aplicar depois
   * que a vaga existir.
   */
  vacancyId: string | null | undefined
  /**
   * Callback após sucesso do POST /apply-pipeline-template. O wizard
   * avança (ou o caller marca o template como aplicado para a vaga).
   */
  onApplied: (templateId: string, source: "wizard_explicit") => void
  /** Callback "Não, vou customizar" — avança wizard sem aplicar. */
  onSkip: () => void
  /** Callback "Ver outros templates" — abre lista/sheet ou navega. */
  onSeeOthers?: () => void
}

export function PipelineTemplateSuggestion({
  templates,
  vacancyId,
  onApplied,
  onSkip,
  onSeeOthers,
}: PipelineTemplateSuggestionProps) {
  const t = useTranslations("wizard.pipelineTemplate")
  const [pendingId, setPendingId] = useState<string | null>(null)

  const handleApply = useCallback(
    async (templateId: string) => {
      if (!vacancyId) {
        toast.error(t("errorNoVacancy"))
        return
      }
      setPendingId(templateId)
      try {
        const response = await fetch(
          `/api/backend-proxy/job-vacancies/${vacancyId}/apply-pipeline-template`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              template_id: templateId,
              source: "wizard_explicit",
            }),
          },
        )
        if (!response.ok) {
          const detail = await response
            .json()
            .catch(() => ({ detail: response.statusText }))
          throw new Error(
            typeof detail?.detail === "string" ? detail.detail : t("errorToast"),
          )
        }
        toast.success(t("appliedToast"))
        onApplied(templateId, "wizard_explicit")
      } catch (err) {
        const message = err instanceof Error ? err.message : t("errorToast")
        toast.error(message)
      } finally {
        setPendingId(null)
      }
    },
    [vacancyId, onApplied, t],
  )

  if (templates.length === 0) return null

  const disabled = !vacancyId
  const top = templates.slice(0, 3)

  return (
    <div
      role="group"
      aria-label={t("suggestionTitle")}
      data-testid="pipeline-template-suggestion-card"
      className="mt-2 rounded-md border border-lia-border-subtle bg-lia-bg-secondary p-3"
    >
      {/* Header — LIA falando, accent cyan apropriado */}
      <div className="flex items-center gap-2">
        <span
          className="flex h-7 w-7 items-center justify-center rounded-md bg-wedo-cyan/15 text-wedo-cyan"
          aria-hidden="true"
        >
          <Sparkles className="h-4 w-4" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-medium uppercase tracking-wide text-wedo-cyan">
            {t("suggestionTitle")}
          </p>
          <p className="text-sm font-semibold text-lia-text-primary">
            {t("suggestionSubtitle")}
          </p>
        </div>
      </div>

      {/* Templates */}
      <div className="mt-3 flex flex-col gap-2">
        {top.map((template) => {
          const isPending = pendingId === template.template_id
          const percent = Math.round(template.score * 100)
          const stagesLabel = t("stagesCount", { count: template.stages_count })
          return (
            <div
              key={template.template_id}
              data-testid={`pipeline-template-option-${template.template_id}`}
              className="rounded-md border border-lia-border-default bg-lia-bg-primary p-2.5"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <h4 className="truncate text-sm font-semibold text-lia-text-primary">
                    {template.name}
                  </h4>
                  {template.description && (
                    <p className="mt-0.5 line-clamp-2 text-[12px] text-lia-text-secondary">
                      {template.description}
                    </p>
                  )}
                  <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                    <span className="inline-flex items-center gap-1 rounded-full bg-lia-bg-tertiary px-2 py-0.5 text-[11px] font-medium text-lia-text-secondary">
                      <Layers className="h-3 w-3" aria-hidden="true" />
                      {stagesLabel}
                    </span>
                    <span className="inline-flex items-center gap-1 rounded-full bg-status-success/10 px-2 py-0.5 text-[11px] font-medium text-status-success">
                      <Sparkle className="h-3 w-3" aria-hidden="true" />
                      {t("matchPercent", { percent })}
                    </span>
                  </div>
                </div>
              </div>
              <button
                type="button"
                disabled={disabled || pendingId !== null}
                onClick={() => handleApply(template.template_id)}
                className={cn(
                  "mt-2 inline-flex w-full items-center justify-center rounded-md bg-lia-text-primary px-3 py-1.5 text-[12px] font-medium text-lia-bg-primary transition-colors",
                  "hover:bg-lia-text-primary/90",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-text-primary focus-visible:ring-offset-1",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                )}
                aria-label={`${t("applyAction")} — ${template.name}`}
                data-testid={`pipeline-template-apply-${template.template_id}`}
              >
                {isPending ? t("applying") : t("applyAction")}
              </button>
            </div>
          )
        })}
      </div>

      {/* Footer actions */}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-lia-border-subtle pt-2">
        {onSeeOthers ? (
          <button
            type="button"
            onClick={onSeeOthers}
            className="text-[12px] font-medium text-lia-text-secondary underline-offset-2 hover:text-lia-text-primary hover:underline"
            data-testid="pipeline-template-see-others"
          >
            {t("viewOthers")}
          </button>
        ) : (
          <span />
        )}
        <button
          type="button"
          onClick={onSkip}
          disabled={pendingId !== null}
          className="text-[12px] font-medium text-lia-text-secondary underline-offset-2 hover:text-lia-text-primary hover:underline disabled:opacity-50"
          data-testid="pipeline-template-skip"
        >
          {t("skipAction")}
        </button>
      </div>
    </div>
  )
}
