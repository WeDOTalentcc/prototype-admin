"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { ShieldAlert, X } from "lucide-react"
import { STAGE_LABELS, STAGE_ORDER, type WizardStage } from "./wizard-types"
import { PLAN_VISIBLE_STAGES } from "./wizard-plan-card"
import type { DegradedStageEntry } from "./useWizardFlow"

interface Props {
  currentStage: WizardStage | null
  completeness: number
  stageHistory: WizardStage[]
  /**
   * Task #1112 — stages que rodaram em modo degradado (fallback
   * determinístico no backend). Renderiza um chip "IA degradada" sobre
   * o ponto da etapa correspondente. `null`/ausente = nenhum aviso.
   */
  degradedStages?: Partial<Record<WizardStage, DegradedStageEntry>>
  /**
   * Compact one-line layout used by the floating chat bubble where the
   * standard 6-dot row eats too much vertical space. Renders as
   * "Etapa X de Y · Nome" with the same progress bar.
   */
  compact?: boolean
  /**
   * Task #1128 — optional callback for the "Cancelar wizard" button.
   * When provided, renders a small dismissive button on the right side
   * of the bar that asks the parent to abort the current wizard run
   * (which in `UnifiedChat` translates to DELETE on the wizard session
   * + local `wizard.reset()` + switch back to general chat). When
   * undefined the button is hidden so existing callers that don't want
   * a cancel affordance keep their current layout.
   */
  onCancelWizard?: () => void
}

const DEGRADED_REASON_COPY: Record<string, string> = {
  timeout: "tempo esgotado do provedor de IA",
  provider_error: "erro/cota do provedor de IA",
  exception: "falha inesperada na geração automática",
}

function buildDegradedTooltip(
  stage: WizardStage,
  marker: DegradedStageEntry,
): string {
  const label = STAGE_LABELS[stage] ?? stage
  const reasonCopy =
    typeof marker === "string" ? DEGRADED_REASON_COPY[marker] : null
  const detail = reasonCopy
    ? ` (${reasonCopy})`
    : typeof marker === "string"
      ? ` (${marker})`
      : ""
  return `IA degradada na etapa "${label}"${detail} — revise a sugestão antes de aprovar.`
}

/**
 * WizardProgressBar — compact step indicator for the wizard.
 *
 * Audit 2026-06-05 (#5): a barra agora reflete a ETAPA do fluxo
 * (Etapa X de Y → largura = X/Y), NÃO a completude da ficha. Antes usava
 * `completeness` (% de campos preenchidos), o que mostrava ~50% mesmo já na
 * etapa de finalização (confunde o recrutador). O contador de etapas usa o
 * mesmo plano visível do plan-card (`PLAN_VISIBLE_STAGES` — single source of
 * truth). Design: wedo-cyan accent, lia-border-subtle, Open Sans.
 */
export function WizardProgressBar({ currentStage, completeness, stageHistory, degradedStages, compact = false, onCancelWizard }: Props) {
  if (!currentStage) return null

  const currentIdx = STAGE_ORDER.indexOf(currentStage)
  const degraded = degradedStages ?? {}
  // ALL degraded stages, including ones the dot row hides (e.g. `salary`,
  // `bigfive`). Recruiter precisa ver mesmo quando o backend dropou um
  // benchmark de salário em fallback determinístico.
  const allDegradedStages = (Object.keys(degraded) as WizardStage[]).filter(
    (s) => Boolean(degraded[s]),
  )
  const totalDegradedCount = allDegradedStages.length
  // Subset that lands on the visible dot row — usado só para renderizar
  // os chips ShieldAlert sobre os pontos. Stages hidden ainda contam para
  // o summary/banner via `hiddenDegradedStages`.
  const visibleDegradedStages = allDegradedStages.filter((s) =>
    PLAN_VISIBLE_STAGES.includes(s),
  )
  const hiddenDegradedStages = allDegradedStages.filter(
    (s) => !PLAN_VISIBLE_STAGES.includes(s),
  )

  // ── Progresso por ETAPA (audit 2026-06-05 #5) ───────────────────────────
  // Posição do recrutador dentro do plano VISÍVEL (mesmo contador do plan
  // card). Stages "ocultos" do backend (salary/bigfive/handoff) colapsam na
  // etapa visível mais recente já iniciada — assim a finalização cai em N/N
  // (≈100%), não em meio da barra.
  const visibleStepIdx = (() => {
    const direct = PLAN_VISIBLE_STAGES.indexOf(currentStage)
    if (direct >= 0) return direct
    let last = -1
    for (let i = 0; i < PLAN_VISIBLE_STAGES.length; i++) {
      if (STAGE_ORDER.indexOf(PLAN_VISIBLE_STAGES[i]) <= currentIdx) last = i
    }
    return Math.max(last, 0)
  })()
  const stepTotal = PLAN_VISIBLE_STAGES.length
  const stepNumber = visibleStepIdx + 1
  const stepLabel = STAGE_LABELS[currentStage]
  const stepSummary = `Etapa ${stepNumber} de ${stepTotal} · ${stepLabel}`
  const stepProgressPct = Math.round((stepNumber / stepTotal) * 100)

  if (compact) {
    const compactDegradedTitle =
      totalDegradedCount > 0
        ? `${totalDegradedCount} etapa${totalDegradedCount === 1 ? "" : "s"} em modo degradado: ${allDegradedStages
            .map((s) => STAGE_LABELS[s] ?? s)
            .join(", ")} — revise antes de aprovar.`
        : undefined
    return (
      <div
        className="px-3 py-2 bg-lia-bg-primary"
        aria-label={`Wizard de criação de vaga: ${stepSummary}`}
        data-degraded-count={totalDegradedCount}
        data-step-number={stepNumber}
        data-step-total={stepTotal}
      >
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <span className="text-[11px] font-medium text-lia-text-secondary truncate">
            {stepSummary}
          </span>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {totalDegradedCount > 0 && (
              <span
                role="status"
                data-testid="wizard-progress-degraded-count"
                title={compactDegradedTitle}
                aria-label={compactDegradedTitle}
                className="inline-flex items-center gap-0.5 rounded-full bg-status-error/10 px-1.5 py-0.5 text-[10px] font-medium text-status-error"
              >
                <ShieldAlert className="w-2.5 h-2.5" aria-hidden="true" />
                {totalDegradedCount}
              </span>
            )}
            <span className="text-[11px] text-lia-text-tertiary tabular-nums">
              {stepNumber}/{stepTotal}
            </span>
            {onCancelWizard && (
              <button
                type="button"
                onClick={onCancelWizard}
                data-testid="wizard-cancel-button-compact"
                title="Cancelar wizard"
                aria-label="Cancelar wizard"
                className="inline-flex items-center justify-center w-4 h-4 rounded-full text-lia-text-tertiary hover:text-status-error hover:bg-status-error/10 transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-status-error"
              >
                <X className="w-2.5 h-2.5" aria-hidden="true" />
              </button>
            )}
          </div>
        </div>
        <div className="h-1 rounded-full bg-lia-bg-secondary overflow-hidden">
          <div
            className="h-full rounded-full bg-wedo-cyan transition-[width] duration-500 ease-out motion-reduce:transition-none"
            style={{ width: `${stepProgressPct}%` }}
          />
        </div>
      </div>
    )
  }

  return (
    <div
      className="px-4 py-2.5 bg-lia-bg-primary"
      data-degraded-count={totalDegradedCount}
      data-step-number={stepNumber}
      data-step-total={stepTotal}
    >
      {/* Cabeçalho da etapa (audit #5): "Etapa X de Y · Nome" + Cancelar. */}
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <span className="text-[11px] font-medium text-lia-text-secondary truncate">
          {stepSummary}
        </span>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-[11px] text-lia-text-tertiary tabular-nums">
            {stepNumber}/{stepTotal}
          </span>
          {onCancelWizard && (
            <button
              type="button"
              onClick={onCancelWizard}
              data-testid="wizard-cancel-button"
              className="inline-flex items-center gap-1 text-[11px] text-lia-text-tertiary hover:text-status-error transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-status-error rounded px-1 py-0.5"
            >
              <X className="w-3 h-3" aria-hidden="true" />
              Cancelar wizard
            </button>
          )}
        </div>
      </div>

      {/* Progress bar — largura por ETAPA (não por completude da ficha). */}
      <div className="h-1 rounded-full bg-lia-bg-secondary mb-2.5 overflow-hidden">
        <div
          className="h-full rounded-full bg-wedo-cyan transition-[width] duration-500 ease-out motion-reduce:transition-none"
          style={{ width: `${stepProgressPct}%` }}
        />
      </div>

      {totalDegradedCount > 0 && (
        <div
          role="status"
          data-testid="wizard-progress-degraded-summary"
          data-visible-count={visibleDegradedStages.length}
          data-hidden-count={hiddenDegradedStages.length}
          className="mt-2 rounded-md border border-status-error/30 bg-status-error/5 px-2 py-1 text-[11px] text-status-error"
        >
          <div className="flex items-center gap-1.5">
            <ShieldAlert className="w-3 h-3 flex-shrink-0" aria-hidden="true" />
            <span className="leading-snug">
              {totalDegradedCount === 1
                ? "1 etapa rodou em modo degradado — revise antes de aprovar."
                : `${totalDegradedCount} etapas rodaram em modo degradado — revise antes de aprovar.`}
            </span>
          </div>
          {/* Lista as etapas — inclui as ocultas dos pontos (ex.: salário,
              Big Five) para que o recrutador NÃO aprove um benchmark de
              salário fallback achando que veio do LLM, mesmo que essa
              etapa não apareça no row de pontos. */}
          <ul className="mt-1 ml-5 list-disc space-y-0.5">
            {allDegradedStages.map((s) => {
              const marker = degraded[s] as DegradedStageEntry
              const tooltip = buildDegradedTooltip(s, marker)
              return (
                <li
                  key={s}
                  data-testid={`wizard-progress-degraded-list-${s}`}
                  data-stage={s}
                  title={tooltip}
                  aria-label={tooltip}
                  className="leading-snug"
                >
                  {STAGE_LABELS[s] ?? s}
                  {typeof marker === "string" &&
                    DEGRADED_REASON_COPY[marker] && (
                      <span className="text-status-error/80">
                        {" "}
                        ({DEGRADED_REASON_COPY[marker]})
                      </span>
                    )}
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}
