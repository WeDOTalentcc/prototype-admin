"use client"

/**
 * VacancyDecisionBar — Phase I.2.
 *
 * Mirror of `PipelineDecisionBar` (`src/components/candidate-preview/
 * PipelineDecisionBar.tsx`). Renders the stage-specific primary action(s) for
 * a vacancy at the TOP of the preview (canonical layout per Paulo, 2026-05-06).
 *
 * Receives the discriminated `VacancyAction` and a single `onAction` dispatch
 * handler. Stage-specific UI variations:
 * - `noop` (encerrada) → nothing renders
 * - `open-status-modal` (ao_vivo) → renders 3 buttons (Pausar/Concluir/Cancelar)
 *   that pre-select the modal mode (Phase I.5)
 * - everything else → single primary button
 *
 * Visual: solid (default variant) buttons, NOT ghost — to differentiate
 * from the icon-only ActionBar above.
 *
 * See `.planning/vacancy-pipeline-plan.md` Phase I.2.d.
 */
import { Button } from "@/components/ui/button"
import { Pause, CheckCircle, XCircle, Copy, RotateCcw } from "lucide-react"
import type { VacancyAction, VacancyStatusModalMode } from "@/components/pages/pipeline-overview-page"

/**
 * Structural type — any object with these 3 fields works. Avoids name
 * collision with the VacancyLite defined locally in vacancy-preview.tsx
 * (same name, different fields). The generic parameter `V` lets callers
 * pass their richer types and TypeScript flows them through onAction.
 */
type VacancyDecisionBarVacancy = {
  id: string
  title: string
  status: string
}

interface VacancyDecisionBarProps<V extends VacancyDecisionBarVacancy = VacancyDecisionBarVacancy> {
  vacancy: V
  action: VacancyAction
  onAction: (action: VacancyAction, vacancy: V) => void
}

export function VacancyDecisionBar<V extends VacancyDecisionBarVacancy>({ vacancy, action, onAction }: VacancyDecisionBarProps<V>) {
  // encerrada -> CTA disabled, render nothing.
  if (action.kind === "noop") {
    return null
  }

  // encerrada (active path) -> Duplicar + Reativar
  if (action.kind === "duplicate") {
    return (
      <div className="flex items-center gap-2 px-3 py-2 border-t border-lia-border-subtle">
        <Button
          size="sm"
          className="h-7 px-3 text-xs flex-1"
          onClick={() => onAction(action, vacancy)}
        >
          <Copy className="w-3 h-3 mr-1.5" />
          {action.label}
        </Button>
        <Button
          variant="outline"
          size="sm"
          className="h-7 px-3 text-xs flex-1"
          onClick={() => onAction({ kind: "reactivate", label: "Reativar vaga" }, vacancy)}
        >
          <RotateCcw className="w-3 h-3 mr-1.5" />
          Reativar
        </Button>
      </div>
    )
  }

  // ao_vivo -> 3 buttons (mode picker for the JobStatusModal mode).
  if (action.kind === "open-status-modal") {
    return (
      <div className="flex items-center gap-2 px-3 py-2 border-t border-lia-border-subtle">
        <span className="text-xs text-lia-text-secondary mr-1">Status da vaga:</span>
        {(["pause", "activate", "cancel"] as VacancyStatusModalMode[]).map((m) => (
          <Button
            key={m}
            variant="outline"
            size="sm"
            className="h-7 px-2.5 text-xs"
            onClick={() => onAction(
              { kind: "open-status-modal", label: action.label, mode: m },
              vacancy,
            )}
          >
            {m === "pause" && (<><Pause className="w-3 h-3 mr-1.5" />Pausar</>)}
            {m === "activate" && (<><CheckCircle className="w-3 h-3 mr-1.5" />Concluir</>)}
            {m === "cancel" && (<><XCircle className="w-3 h-3 mr-1.5" />Cancelar</>)}
          </Button>
        ))}
      </div>
    )
  }

  // All other stages: single primary CTA.
  return (
    <div className="flex items-center gap-2 px-3 py-2 border-t border-lia-border-subtle">
      <Button
        size="sm"
        className="h-7 px-3 text-xs flex-1"
        onClick={() => onAction(action, vacancy)}
      >
        {action.label}
      </Button>
    </div>
  )
}
