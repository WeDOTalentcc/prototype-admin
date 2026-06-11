"use client"

import React, { Suspense, lazy } from "react"
import { Minimize2 } from "lucide-react"
import type { WizardStage } from "./wizard-types"
import { STAGE_LABELS } from "./wizard-types"
import { WizardErrorBoundary } from "./WizardErrorBoundary"

// Lazy-load all panels for code splitting
const IntakePanel = lazy(() =>
  import("./panels/IntakePanel").then((m) => ({ default: m.IntakePanel }))
)
const JdEnrichmentPanel = lazy(() =>
  import("./panels/JdEnrichmentPanel").then((m) => ({ default: m.JdEnrichmentPanel }))
)
const BigFivePanel = lazy(() =>
  import("./panels/BigFivePanel").then((m) => ({ default: m.BigFivePanel }))
)
const SalaryPanel = lazy(() =>
  import("./panels/SalaryPanel").then((m) => ({ default: m.SalaryPanel }))
)
const CompetencyPanel = lazy(() =>
  import("./panels/CompetencyPanel").then((m) => ({ default: m.CompetencyPanel }))
)
const WsiQuestionsPanel = lazy(() =>
  import("./panels/WsiQuestionsPanel").then((m) => ({ default: m.WsiQuestionsPanel }))
)
const EligibilityPanel = lazy(() =>
  import("./panels/EligibilityPanel").then((m) => ({ default: m.EligibilityPanel }))
)
const ReviewPanel = lazy(() =>
  import("./panels/ReviewPanel").then((m) => ({ default: m.ReviewPanel }))
)
const PublishPanel = lazy(() =>
  import("./panels/PublishPanel").then((m) => ({ default: m.PublishPanel }))
)
const CalibrationPanel = lazy(() =>
  import("./panels/CalibrationPanel").then((m) => ({ default: m.CalibrationPanel }))
)
const HandoffPanel = lazy(() =>
  import("./panels/HandoffPanel").then((m) => ({ default: m.HandoffPanel }))
)
const DonePanel = lazy(() =>
  import("./panels/DonePanel").then((m) => ({ default: m.DonePanel }))
)
const SchedulingPanel = lazy(() =>
  import("./panels/SchedulingPanel").then((m) => ({ default: m.SchedulingPanel }))
)

function PanelLoader() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="w-5 h-5 border-2 border-wedo-cyan border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

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
 * Stages with meaningful visual content that warrant splitting the chat view.
 * Stages not listed (intake → eligibility) are conversational — full-width only.
 */
export const SPLIT_STAGES: WizardStage[] = [
  // HITL canonical stages -- todos com case correspondente em renderPanel switch
  // abaixo. Fix C 2026-05-27: expandido de 7 -> 13 stages cobrindo todo o fluxo
  // wizard. pipeline_template e deliberadamente excluido pq tem rendering
  // proprio em UnifiedChat.tsx (via WizardPipelineTemplateStagePanel inline).
  // Sensor canonical em __tests__/DynamicContextPanel.split-stages-canonical.test.ts.
  "intake",
  "jd_enrichment",
  "bigfive",
  "salary",
  "competency",
  "wsi_questions",
  "eligibility",
  "review",
  "publish",
  "calibration",
  "handoff",
  "done",
  "scheduling",
]

/**
 * DynamicContextPanel — routes to the correct wizard panel based on stage.
 *
 * Renders in the split-view column of UnifiedChat (340px sidebar, 420px fullscreen).
 * All panels are lazy-loaded with Suspense for code splitting.
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
      <div className="flex items-center justify-between px-4 py-2.5 flex-shrink-0 border-b border-lia-border-subtle">
        <h3 className="text-sm font-semibold text-lia-text-primary">
          {STAGE_LABELS[stage] || stage}
        </h3>
        {onClose && (
          <button
            onClick={onClose}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-lia-text-disabled hover:text-lia-text-primary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none"
            title="Minimizar painel"
          >
            <Minimize2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Minimizar</span>
          </button>
        )}
      </div>

      {/* Panel content — scrollable, with Suspense + ErrorBoundary.
          Wrapper keyed por stage: re-monta na troca de estágio e toca a
          transição enter (transform+opacity, ease-out ~200ms, motion-reduce
          safe). NÃO anima propriedades de layout. */}
      <div className="flex-1 overflow-y-auto">
        <div
          key={stage}
          data-testid="wizard-stage-body"
          className="h-full animate-in fade-in slide-in-from-right-2 duration-200 ease-out motion-reduce:animate-none"
        >
          <WizardErrorBoundary>
            <Suspense fallback={<PanelLoader />}>
              {renderPanel(stage, data, requiresApproval, onApprove, onReject, onUpdate)}
            </Suspense>
          </WizardErrorBoundary>
        </div>
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
    case "intake":
      return <IntakePanel data={data} onUpdate={onUpdate} />
    case "jd_enrichment":
      return (
        <JdEnrichmentPanel
          data={data}
          requiresApproval={requiresApproval}
          onApprove={onApprove}
          onReject={onReject}
        />
      )
    case "bigfive":
      return <BigFivePanel data={data} />
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
      return <ReviewPanel data={data} onUpdate={onUpdate} />
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
    case "done":
      return <DonePanel data={data} />
    case "scheduling":
      return <SchedulingPanel data={data} onApprove={onApprove} />
    default:
      return (
        <div className="p-4 text-sm text-lia-text-secondary">
          Processando {STAGE_LABELS[stage] || stage}...
        </div>
      )
  }
}
