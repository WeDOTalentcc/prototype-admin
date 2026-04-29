"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { Check } from "lucide-react"
import { STAGE_LABELS, STAGE_ORDER, type WizardStage } from "./wizard-types"
import { PLAN_VISIBLE_STAGES } from "./wizard-plan-card"

interface Props {
  currentStage: WizardStage | null
  completeness: number
  stageHistory: WizardStage[]
  /**
   * Compact one-line layout used by the floating chat bubble where the
   * standard 6-dot row eats too much vertical space. Renders as
   * "Etapa X de Y · Nome" with the same progress bar.
   */
  compact?: boolean
}

/**
 * WizardProgressBar — compact step indicator for the wizard.
 * Shows the same 6 visible stages the chat-feed plan card uses
 * (single source of truth: `PLAN_VISIBLE_STAGES` in `wizard-plan-card`).
 * Design: wedo-cyan accent, lia-border-subtle, Open Sans.
 */
export function WizardProgressBar({ currentStage, completeness, stageHistory, compact = false }: Props) {
  if (!currentStage) return null

  const currentIdx = STAGE_ORDER.indexOf(currentStage)

  if (compact) {
    // Find the recruiter's position within the *visible* plan so the
    // counter ("Etapa X de Y") matches the dots view above; collapse
    // hidden backend stages into the surrounding visible step.
    const visibleIdx = (() => {
      const direct = PLAN_VISIBLE_STAGES.indexOf(currentStage)
      if (direct >= 0) return direct
      // current stage is hidden — pick the latest visible stage that
      // already started (or 0 if we're still before the first one).
      let last = -1
      for (let i = 0; i < PLAN_VISIBLE_STAGES.length; i++) {
        if (STAGE_ORDER.indexOf(PLAN_VISIBLE_STAGES[i]) <= currentIdx) last = i
      }
      return Math.max(last, 0)
    })()
    const total = PLAN_VISIBLE_STAGES.length
    const stepNumber = visibleIdx + 1
    const label = STAGE_LABELS[currentStage]
    const summary = `Etapa ${stepNumber} de ${total} · ${label}`

    return (
      <div
        className="px-3 py-2 bg-lia-bg-primary"
        aria-label={`Wizard de criação de vaga: ${summary}`}
      >
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <span className="text-[11px] font-medium text-wedo-cyan truncate">
            {summary}
          </span>
          <span className="text-[11px] text-lia-text-tertiary flex-shrink-0 tabular-nums">
            {Math.round(completeness * 100)}%
          </span>
        </div>
        <div className="h-1 rounded-full bg-lia-bg-secondary overflow-hidden">
          <div
            className="h-full rounded-full bg-wedo-cyan transition-all duration-500 ease-out motion-reduce:transition-none"
            style={{ width: `${Math.round(completeness * 100)}%` }}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="px-4 py-2.5 bg-lia-bg-primary">
      {/* Progress bar */}
      <div className="h-1 rounded-full bg-lia-bg-secondary mb-2.5 overflow-hidden">
        <div
          className="h-full rounded-full bg-wedo-cyan transition-all duration-500 ease-out motion-reduce:transition-none"
          style={{ width: `${Math.round(completeness * 100)}%` }}
        />
      </div>

      {/* Stage dots */}
      <div className="flex items-center justify-between">
        {PLAN_VISIBLE_STAGES.map((stage) => {
          const stageIdx = STAGE_ORDER.indexOf(stage)
          const isCompleted = stageIdx < currentIdx
          const isCurrent = stage === currentStage
          const isPending = stageIdx > currentIdx

          return (
            <div key={stage} className="flex flex-col items-center gap-1">
              <div
                className={cn(
                  "w-5 h-5 rounded-full flex items-center justify-center text-[10px] transition-colors",
                  isCompleted && "bg-wedo-cyan text-white",
                  isCurrent && "bg-wedo-cyan/20 border-2 border-wedo-cyan text-wedo-cyan",
                  isPending && "bg-lia-bg-secondary text-lia-text-disabled border border-lia-border-subtle",
                )}
              >
                {isCompleted ? <Check className="w-3 h-3" /> : null}
              </div>
              <span
                className={cn(
                  "text-[10px] leading-tight text-center max-w-[60px]",
                  isCurrent ? "text-wedo-cyan font-medium" : "text-lia-text-tertiary",
                )}
              >
                {STAGE_LABELS[stage]}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
