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
}

/**
 * WizardProgressBar — compact step indicator for the wizard.
 * Shows the same 6 visible stages the chat-feed plan card uses
 * (single source of truth: `PLAN_VISIBLE_STAGES` in `wizard-plan-card`).
 * Design: wedo-cyan accent, lia-border-subtle, Open Sans.
 */
export function WizardProgressBar({ currentStage, completeness, stageHistory }: Props) {
  if (!currentStage) return null

  const currentIdx = STAGE_ORDER.indexOf(currentStage)

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
