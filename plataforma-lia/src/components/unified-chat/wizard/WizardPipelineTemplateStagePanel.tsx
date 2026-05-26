"use client"

import { useCallback, useState } from "react"
import { Sparkles, Layers, Sparkle, Building2, ChevronRight } from "lucide-react"
import { toast } from "sonner"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import type { WizardPipelineTemplateSuggestion } from "@/components/unified-chat/wizard/wizard-types"

/**
 * WizardPipelineTemplateStagePanel — painel da STAGE FORMAL `pipeline_template`
 * (Sprint Pipeline Templates Opção B, 2026-05-26, Paulo aprovou).
 *
 * Diferente de `PipelineTemplateSuggestion` (card passivo Gap #6):
 *   - este painel é a UI da STAGE oficial: o recrutador DEVE decidir entre
 *     aplicar um template sugerido OU usar o "Padrão da Empresa" canonical.
 *   - mostra `defaultPipelineStagesCount` para que o recrutador saiba o que
 *     "Padrão da Empresa" significa antes de decidir.
 *   - o botão "Padrão da Empresa" é a action canonical primária (Ink),
 *     porque pipeline default É decisão legítima — não é "fallback".
 *   - "Aplicar este template" é action secundária por template.
 *
 * Design tokens canonical (Design System v4.2.x):
 *   - Header com accent cyan (`text-wedo-cyan`) — LIA "agindo".
 *   - Botão PRIMARY canonical (`bg-lia-text-primary`) reservado para
 *     "Usar Padrão da Empresa" (CTA principal do stage).
 *   - Botões "Aplicar este template" usam o mesmo estilo Ink mas em
 *     escala secundária por card.
 */
export interface WizardPipelineTemplateStagePanelProps {
  templates: WizardPipelineTemplateSuggestion[]
  /** Template recomendado pelo backend (destacado visualmente). */
  suggestedTemplateId: string | null
  /** Contagem de etapas do pipeline DEFAULT da empresa (mostrado no CTA skip). */
  defaultPipelineStagesCount: number
  /** Backend controla se skip é permitido (sempre `true` no padrão Opção B). */
  allowSkip: boolean
  /**
   * Callback quando o recrutador aplica um template específico. Resolve
   * quando o backend confirmar; o caller decide UX de erro.
   */
  onApply: (templateId: string) => Promise<void>
  /** Callback "Usar Padrão da Empresa" (skip canonical). */
  onSkip: () => Promise<void>
  /** Callback "Ver todos os templates" (navega a Configurações). */
  onSeeOthers?: () => void
}

export function WizardPipelineTemplateStagePanel({
  templates,
  suggestedTemplateId,
  defaultPipelineStagesCount,
  allowSkip,
  onApply,
  onSkip,
  onSeeOthers,
}: WizardPipelineTemplateStagePanelProps) {
  const t = useTranslations("wizard.pipelineTemplateStage")
  const [pendingId, setPendingId] = useState<string | null>(null)
  const [skipPending, setSkipPending] = useState(false)

  const handleApply = useCallback(
    async (templateId: string) => {
      setPendingId(templateId)
      try {
        await onApply(templateId)
        toast.success(t("appliedSuccessToast"))
      } catch (err) {
        const message = err instanceof Error ? err.message : "error"
        toast.error(t("applyErrorToast", { error: message }))
      } finally {
        setPendingId(null)
      }
    },
    [onApply, t],
  )

  const handleSkip = useCallback(async () => {
    setSkipPending(true)
    try {
      await onSkip()
      toast.success(t("skippedSuccessToast"))
    } catch (err) {
      const message = err instanceof Error ? err.message : "error"
      toast.error(t("applyErrorToast", { error: message }))
    } finally {
      setSkipPending(false)
    }
  }, [onSkip, t])

  const top = templates.slice(0, 3)
  const anyPending = pendingId !== null || skipPending

  return (
    <div
      role="group"
      aria-label={t("title")}
      data-testid="wizard-pipeline-template-stage-panel"
      className="mt-2 rounded-md border border-lia-border-default bg-lia-bg-secondary p-3"
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
            {t("title")}
          </p>
          <p className="text-sm font-semibold text-lia-text-primary">
            {t("subtitle")}
          </p>
        </div>
      </div>

      {/* Templates list */}
      {top.length > 0 && (
        <div className="mt-3 flex flex-col gap-2">
          {top.map((template) => {
            const isPending = pendingId === template.template_id
            const isSuggested = suggestedTemplateId === template.template_id
            const percent = Math.round(template.score * 100)
            const stagesLabel = t("stagesCount", { count: template.stages_count })
            return (
              <div
                key={template.template_id}
                data-testid={`wizard-pipeline-template-stage-option-${template.template_id}`}
                className={cn(
                  "rounded-md border bg-lia-bg-primary p-2.5",
                  isSuggested
                    ? "border-wedo-cyan/40 ring-1 ring-wedo-cyan/30"
                    : "border-lia-border-default",
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="truncate text-sm font-semibold text-lia-text-primary">
                        {template.name}
                      </h4>
                      {isSuggested && (
                        <span
                          data-testid={`wizard-pipeline-template-stage-suggested-${template.template_id}`}
                          className="inline-flex items-center rounded-full bg-wedo-cyan/15 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-wedo-cyan"
                        >
                          {t("suggestedBadge")}
                        </span>
                      )}
                    </div>
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
                  disabled={anyPending}
                  onClick={() => handleApply(template.template_id)}
                  className={cn(
                    "mt-2 inline-flex w-full items-center justify-center rounded-md border border-lia-border-default bg-lia-bg-primary px-3 py-1.5 text-[12px] font-medium text-lia-text-primary transition-colors",
                    "hover:bg-lia-bg-tertiary",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-text-primary focus-visible:ring-offset-1",
                    "disabled:cursor-not-allowed disabled:opacity-50",
                  )}
                  aria-label={`${t("applyTemplate")} — ${template.name}`}
                  data-testid={`wizard-pipeline-template-stage-apply-${template.template_id}`}
                >
                  {isPending ? t("applying") : t("applyTemplate")}
                </button>
              </div>
            )
          })}
        </div>
      )}

      {/* PRIMARY CTA canonical — "Usar Padrão da Empresa".
          Pipeline default da empresa é decisão legítima, não fallback.
          Aparece SEMPRE que allowSkip=true (Opção B default). */}
      {allowSkip && (
        <div className="mt-3 border-t border-lia-border-subtle pt-3">
          <button
            type="button"
            onClick={handleSkip}
            disabled={anyPending}
            data-testid="wizard-pipeline-template-stage-use-default"
            className={cn(
              "inline-flex w-full items-center justify-center gap-2 rounded-md bg-lia-text-primary px-3 py-2 text-sm font-medium text-lia-bg-primary transition-colors",
              "hover:bg-lia-text-primary/90",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-text-primary focus-visible:ring-offset-1",
              "disabled:cursor-not-allowed disabled:opacity-50",
            )}
          >
            <Building2 className="h-4 w-4" aria-hidden="true" />
            {skipPending ? t("applying") : t("useDefaultPipeline")}
          </button>
          <p className="mt-1 text-center text-[11px] text-lia-text-secondary">
            {t("defaultPipelineInfo", { count: defaultPipelineStagesCount })}
          </p>
        </div>
      )}

      {/* Footer — link "Ver todos os templates" (navigate to Configurações) */}
      {onSeeOthers && (
        <div className="mt-2 flex justify-center">
          <button
            type="button"
            onClick={onSeeOthers}
            className="inline-flex items-center gap-1 text-[12px] font-medium text-lia-text-secondary underline-offset-2 hover:text-lia-text-primary hover:underline"
            data-testid="wizard-pipeline-template-stage-see-others"
          >
            {t("viewAllTemplates")}
            <ChevronRight className="h-3 w-3" aria-hidden="true" />
          </button>
        </div>
      )}
    </div>
  )
}
