/**
 * Wizard WSI — exports for integration with UnifiedChat.
 */

// Hook
export { useWizardFlow } from "./useWizardFlow"
export type { WizardFlowReturn } from "./useWizardFlow"

// Components
export { DynamicContextPanel } from "./DynamicContextPanel"
export { WizardProgressBar } from "./WizardProgressBar"

// Types
export type {
  WizardStage,
  WizardStagePayload,
  ScreeningMode,
  EnrichedJobDescription,
  ScreeningQuestion,
  CalibrationCandidate,
} from "./wizard-types"

export { STAGE_LABELS, STAGE_ORDER } from "./wizard-types"
