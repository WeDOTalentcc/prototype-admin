"use client"

import React, { Suspense, lazy } from "react"

/**
 * LazyPanels — Phase D.2 Performance optimization.
 *
 * Lazy-loads wizard panels to reduce initial bundle size.
 * Only loads a panel when the wizard reaches that stage.
 *
 * NOTE: DynamicContextPanel now handles lazy loading internally.
 * This module is kept for backward compatibility and direct imports.
 */

// Lazy imports for each panel
const IntakePanel = lazy(() =>
  import("./panels/IntakePanel").then((m) => ({ default: m.IntakePanel }))
)
const JdEnrichmentPanel = lazy(() =>
  import("./panels/JdEnrichmentPanel").then((m) => ({ default: m.JdEnrichmentPanel }))
)
const BigFivePanel = lazy(() =>
  import("./panels/BigFivePanel").then((m) => ({ default: m.BigFivePanel }))
)
const CompetencyPanel = lazy(() =>
  import("./panels/CompetencyPanel").then((m) => ({ default: m.CompetencyPanel }))
)
const WsiQuestionsPanel = lazy(() =>
  import("./panels/WsiQuestionsPanel").then((m) => ({ default: m.WsiQuestionsPanel }))
)
const SalaryPanel = lazy(() =>
  import("./panels/SalaryPanel").then((m) => ({ default: m.SalaryPanel }))
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

function PanelLoader() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="w-5 h-5 border-2 border-wedo-cyan border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

export {
  IntakePanel,
  JdEnrichmentPanel,
  BigFivePanel,
  CompetencyPanel,
  WsiQuestionsPanel,
  SalaryPanel,
  EligibilityPanel,
  ReviewPanel,
  PublishPanel,
  CalibrationPanel,
  HandoffPanel,
  DonePanel,
  PanelLoader,
  Suspense,
}
