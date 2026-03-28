/**
 * Expanded Chat Configuration Module
 * 
 * Re-exports all configuration from wizard-config.ts
 */

export {
  type WizardStage,
  type WizardPhase,
  type WizardPhaseConfig,
  type WizardStageConfig,
  type StageTransitionConfig,
  type StageCriticalFields,
  type ExtendedWizardStageConfig,
  WIZARD_PHASES,
  WIZARD_STAGES,
  FRONTEND_TO_BACKEND_STAGE,
  BACKEND_TO_FRONTEND_STAGE,
  getBackendStageNumber,
  getFrontendStageFromBackend,
  getStageTransitionMessage,
  getMissingCriticalFields,
  generateMissingFieldsMessage,
  PRE_WIZARD_MESSAGE,
  DRAFT_DETECTED_MESSAGE,
  INITIAL_JOB_CREATION_MESSAGE,
  FROM_SCRATCH_ORIENTATION_MESSAGE,
  INITIAL_GENERAL_MESSAGE,
} from './wizard-config'
