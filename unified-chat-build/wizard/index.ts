/**
 * Wizard WSI — exports for integration with UnifiedChat.
 */

// Hook
export { useWizardFlow } from "./useWizardFlow"
export type { WizardFlowReturn } from "./useWizardFlow"

// Integration
export { useWizardIntegration } from "./useWizardIntegration"

// Components
export { DynamicContextPanel } from "./DynamicContextPanel"
export { WizardProgressBar } from "./WizardProgressBar"
export { ProgressiveDisclosure } from "./ProgressiveDisclosure"
export { FirstUseTooltip } from "./FirstUseTooltips"
export type { TooltipId } from "./FirstUseTooltips"
export { WizardErrorBoundary } from "./WizardErrorBoundary"

// Types
export type {
  WizardStage,
  WizardStagePayload,
  ScreeningMode,
  EnrichedJobDescription,
  ScreeningQuestion,
  CalibrationCandidate,
  IntakeData,
  JdEnrichmentData,
  BigFiveData,
  SalaryData,
  CompetencyData,
  WsiQuestionsData,
  EligibilityData,
  ReviewData,
  PublishData,
  CalibrationData,
  HandoffData,
} from "./wizard-types"

export { STAGE_LABELS, STAGE_ORDER } from "./wizard-types"
