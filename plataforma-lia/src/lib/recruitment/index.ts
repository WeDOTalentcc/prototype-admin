export type {
  StageType,
  StatusCategory,
  RecruitmentStage,
  CompanyPipelineStage,
} from './stages-data'

export {
  RECRUITMENT_STAGES,
  LIA_ASSISTED_STAGES,
  LIA_ASSISTED_STAGE_NAMES,
  DEFAULT_SLA_DAYS,
} from './stages-data'

export type {
  SubStatus,
  CandidateSource,
  RejectionReason,
  OfferDeclineReason,
  StandbyReason,
} from './sub-statuses-data'

export {
  SUB_STATUSES,
  TEST_STATUSES,
  DOCUMENT_STATUSES,
  REJECTION_REASONS,
  OFFER_DECLINE_REASONS,
  CANDIDATE_SOURCES,
  getCandidateSourceById,
  isApplicationSource,
  getRejectionReasonsByCategory,
} from './sub-statuses-data'

export {
  getCompanyPipelineStages,
  getJobPipelineStages,
  getEditableJobStages,
  getStageByName,
  getSubStatusesByStage,
  getSubStatusDisplayName,
  getTestStatusesByType,
  getAllSubStatuses,
  mapLegacyStage,
  getDefaultSubStatus,
  getApprovalSubStatuses,
  getRejectionSubStatuses,
  getWaitingSubStatuses,
} from './stage-utils'

// WT-2022 P0.STAGES - adapter helpers (hook snake_case to legacy camelCase)
export type { HookRecruitmentStage } from "./stages-data"
export {
  normalizeStageFromHook,
  normalizeStagesFromHook,
} from "./stages-data"

// WT-2022 P0.SUB_STATUSES - adapter helpers (hook snake_case to legacy camelCase)
export type { HookSubStatus } from "./sub-statuses-data"
export {
  normalizeSubStatusFromHook,
  normalizeSubStatusesFromHook,
} from "./sub-statuses-data"
