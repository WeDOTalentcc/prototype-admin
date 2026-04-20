/**
 * workflowRailAnalytics — lightweight client-side tracking for the WorkflowRail.
 *
 * Uses the project's established `window.dispatchEvent(new CustomEvent(...))`
 * pattern as a pub/sub event bus. No backend endpoint is involved; any
 * future analytics integration (PostHog, Mixpanel, etc.) can subscribe to
 * these events without touching the rail.
 *
 * Events emitted:
 *  - "workflowRail:nextStepClicked" — detail: { stageKey, stepId, actionType, path?, handlerId? }
 *  - "workflowRail:panelToggled"   — detail: { open, stageKey, source }
 */

import type { FunnelStageKey, NextStep } from "./workflowRailCatalog"

export const WORKFLOW_RAIL_NEXT_STEP_EVENT = "workflowRail:nextStepClicked"
export const WORKFLOW_RAIL_PANEL_TOGGLE_EVENT = "workflowRail:panelToggled"

export interface WorkflowRailNextStepClickedDetail {
  stageKey: FunnelStageKey
  stepId: string
  actionType: NextStep["actionType"]
  path?: string
  handlerId?: string
  timestamp: string
}

export type PanelToggleSource =
  | "toggle-button"
  | "mobile-close"
  | "outside-click"
  | "escape"
  | "next-step-click"
  | "next-stage-chip"
  | "pending-action"

export interface WorkflowRailPanelToggledDetail {
  open: boolean
  stageKey: FunnelStageKey
  source: PanelToggleSource
  timestamp: string
}

function safeDispatch(event: Event) {
  if (typeof window === "undefined") return
  try {
    window.dispatchEvent(event)
  } catch {
    // Fire-and-forget — analytics must never break the UI.
  }
}

export function trackWorkflowRailNextStepClick(stageKey: FunnelStageKey, step: NextStep) {
  const detail: WorkflowRailNextStepClickedDetail = {
    stageKey,
    stepId: step.id,
    actionType: step.actionType,
    path: step.path,
    handlerId: step.handlerId,
    timestamp: new Date().toISOString(),
  }
  safeDispatch(new CustomEvent(WORKFLOW_RAIL_NEXT_STEP_EVENT, { detail }))
}

export function trackWorkflowRailPanelToggle(
  open: boolean,
  stageKey: FunnelStageKey,
  source: PanelToggleSource,
) {
  const detail: WorkflowRailPanelToggledDetail = {
    open,
    stageKey,
    source,
    timestamp: new Date().toISOString(),
  }
  safeDispatch(new CustomEvent(WORKFLOW_RAIL_PANEL_TOGGLE_EVENT, { detail }))
}
