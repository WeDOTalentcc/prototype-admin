"use client"

/**
 * Inline "Plano de trabalho" card rendered above the message feed in the
 * expanded chat modal (`expanded-chat-modal.tsx`).
 *
 * Kept as its own thin component so:
 *  - The render condition + title source live in ONE place, in lockstep with
 *    `wizard-plan-card.ts` helpers (Tasks #830 + #835 — the card stays
 *    visible at terminal stages and surfaces the "Concluído" title there).
 *  - It's trivially testable in jsdom without dragging in the rest of the
 *    expanded chat's giant hook graph.
 *  - The Vue/Vuetify port (see `wizard-plan-card.ts` header) gets an obvious
 *    1:1 component to swap.
 *
 * The chat-feed surface in `UnifiedChat.tsx` does NOT use this component:
 * it injects the plan card as a synthetic assistant message handled by
 * `UnifiedMessageList`. The two paths intentionally share the same helpers
 * (`buildPlanFlowSteps`, `planCardTitleForStage`) so they can never drift.
 */
import * as React from "react"
import FlowStepMessage from "@/components/workflow-rail/FlowStepMessage"
import {
  buildPlanFlowSteps,
  planCardTitleForStage,
} from "./wizard-plan-card"
import { type WizardStage } from "./wizard-types"

export interface WizardPlanFeedCardProps {
  currentStage: WizardStage | null
}

export function WizardPlanFeedCard({ currentStage }: WizardPlanFeedCardProps) {
  // The card is gated on "wizard ever started" — i.e. any non-null stage,
  // including terminal `done`/`handoff`. Hiding it at terminal stages was
  // the exact regression Task #835 fixes for the expanded chat surface.
  if (currentStage === null) return null
  const steps = buildPlanFlowSteps(currentStage)
  if (steps.length === 0) return null
  const title = planCardTitleForStage(currentStage)
  return (
    <div
      data-testid="wizard-plan-card"
      className="mb-4 rounded-md border border-lia-border-subtle bg-lia-bg-secondary px-4 py-3"
    >
      <p className="text-sm font-semibold text-lia-text-primary mb-2">
        {title}
      </p>
      <FlowStepMessage steps={steps} compact />
    </div>
  )
}
