/**
 * Recruitment Stages — Backwards-compatible re-export layer
 *
 * All data and logic has been moved to `src/lib/recruitment/`:
 *  - stages-data.ts      — Stage types, RECRUITMENT_STAGES constant
 *  - sub-statuses-data.ts — Sub-status types and data constants
 *  - stage-utils.ts       — Utility functions (getStageByName, etc.)
 *
 * This file re-exports everything so existing imports continue to work.
 * New code should import from `@/lib/recruitment` directly.
 */

export type {
  StageType,
  StatusCategory,
  RecruitmentStage,
  CompanyPipelineStage,
} from './recruitment/stages-data'

export {
  RECRUITMENT_STAGES,
  LIA_ASSISTED_STAGES,
  LIA_ASSISTED_STAGE_NAMES,
  DEFAULT_SLA_DAYS,
} from './recruitment/stages-data'

export type {
  SubStatus,
  CandidateSource,
  RejectionReason,
  OfferDeclineReason,
  StandbyReason,
} from './recruitment/sub-statuses-data'

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
} from './recruitment/sub-statuses-data'

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
} from './recruitment/stage-utils'
