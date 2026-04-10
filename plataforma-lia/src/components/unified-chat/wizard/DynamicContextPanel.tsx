"use client"

import React from "react"
import { X } from "lucide-react"
import type { WizardStage } from "./wizard-types"
import { STAGE_LABELS } from "./wizard-types"
import { JdEnrichmentPanel } from "./panels/JdEnrichmentPanel"
import { CompetencyPanel } from "./panels/CompetencyPanel"
import { WsiQuestionsPanel } from "./panels/WsiQuestionsPanel"
import { SalaryPanel } from "./panels/SalaryPanel"
import { EligibilityPanel } from "./panels/EligibilityPanel"
import { ReviewPanel } from "./panels/ReviewPanel"
import { PublishPanel } from "./panels/PublishPanel"
import { CalibrationPanel } from "./panels/CalibrationPanel"
import { HandoffPanel } from "./panels/HandoffPanel"

interface Props {
  stage: WizardStage | null
  data: Record<string, unknown>
  requiresApproval: boolean
  onApprove?: () => void
  onReject?: () => void
  onClose?: () => void
  onUpdate?: (updates: Record<string, unknown>) => void
}

/**
 * DynamicContextPanel — routes to the correct wizard panel based on stage.
 *
 * Renders in the 340px split-view column of UnifiedChat.
 * Design: lia-bg-primary, lia-border-subtle, Open Sans.
 */
export function DynamicContextPanel({
  stage,
  data,
  requiresApproval,
  onApprove,
  onReject,
  onClose,
  onUpdate,
}: Props) {
  if (!stage) return null

  return (
    <div className="flex flex-col h-full bg-lia-bg-primary">
      {/* Panel header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-lia-border-subtle flex-shrink-0">
        <h3 className="text-sm font-semibold text-lia-text-primary font-['Open_Sans',sans-serif]">
          {STAGE_LABELS[stage] || stage}
        </h3>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Panel content — scrollable */}
      <div className="flex-1 overflow-y-auto">
        {renderPanel(stage, data, requiresApproval, onApprove, onReject, onUpdate)}
      </div>
    </div>
  )
}

function renderPanel(
  stage: WizardStage,
  data: Record<string, unknown>,
  requiresApproval: boolean,
  onApprove?: () => void,
  onReject?: () => void,
  onUpdate?: (updates: Record<string, unknown>) => void,
) {
  switch (stage) {
    case "jd_enrichment":
      return (
        <JdEnrichmentPanel
          data={data}
          requiresApproval={requiresApproval}
          onApprove={onApprove}
          onReject={onReject}
        />
      )
    case "salary":
      return <SalaryPanel data={data} onUpdate={onUpdate} />
    case "competency":
      return <CompetencyPanel data={data} onUpdate={onUpdate} />
    case "wsi_questions":
      return (
        <WsiQuestionsPanel
          data={data}
          requiresApproval={requiresApproval}
          onApprove={onApprove}
          onReject={onReject}
        />
      )
    case "eligibility":
      return <EligibilityPanel data={data} onUpdate={onUpdate} />
    case "review":
      return <ReviewPanel data={data} />
    case "publish":
      return <PublishPanel data={data} onUpdate={onUpdate} />
    case "calibration":
      return (
        <CalibrationPanel
          data={data}
          onApprove={onApprove}
          onReject={onReject}
        />
      )
    case "handoff":
      return <HandoffPanel data={data} />
    default:
      return (
        <div className="p-4 text-sm text-lia-text-secondary font-['Open_Sans',sans-serif]">
          Processando {STAGE_LABELS[stage] || stage}...
        </div>
      )
  }
}
