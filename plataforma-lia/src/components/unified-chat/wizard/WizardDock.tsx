"use client"

import { Maximize2 } from "lucide-react"
import type { ReactNode } from "react"

interface WizardDockProps {
  stage: string
  stageLabel: string
  requiresApproval: boolean
  onExpand: () => void
  /** WizardProgressBar compacto — projetado aqui quando o painel está docked */
  progressBar: ReactNode
  /** Painel real renderizado em escala (thumbnail vivo) — pointer-events none */
  thumbnail: ReactNode
}

/**
 * Manus F1 — card minimizado do painel do wizard, acima do input.
 * Padrão FloatingToolPreview (Suna): affordance viva + maximizar.
 * Container clicável é div role=button (NUNCA <button> aninhando interativos).
 */
export function WizardDock({
  stage: _stage,
  stageLabel,
  requiresApproval,
  onExpand,
  progressBar,
  thumbnail,
}: WizardDockProps) {
  return (
    <div
      data-testid="wizard-dock"
      role="button"
      tabIndex={0}
      onClick={onExpand}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          onExpand()
        }
      }}
      aria-label={`Abrir painel: ${stageLabel}`}
      className="mx-3 mb-2 flex items-stretch gap-3 rounded-xl border border-lia-border-subtle bg-lia-bg-primary shadow-md shadow-black/10 p-2 cursor-pointer hover:border-wedo-cyan/50 transition-colors motion-reduce:transition-none"
    >
      <div
        data-testid="wizard-dock-thumbnail"
        aria-hidden="true"
        className="pointer-events-none select-none w-20 h-14 overflow-hidden rounded-md border border-lia-border-subtle bg-lia-bg-secondary flex-shrink-0"
      >
        <div className="origin-top-left scale-[0.18] w-[420px] h-[600px]">{thumbnail}</div>
      </div>
      <div className="flex-1 min-w-0 flex flex-col justify-center gap-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-lia-text-primary truncate">{stageLabel}</span>
          {requiresApproval && (
            <span className="px-1.5 py-0.5 rounded bg-status-warning/10 text-status-warning text-[10px] font-medium whitespace-nowrap">
              1 aprovação pendente
            </span>
          )}
        </div>
        <div className="min-w-0">{progressBar}</div>
      </div>
      <div className="flex items-center pr-1 text-lia-text-disabled">
        <Maximize2 className="w-4 h-4" aria-hidden="true" />
      </div>
    </div>
  )
}
