import { lazy } from "react"

export const LazyBigFiveModal = lazy(() =>
  import("@/components/big-five-modal").then(m => ({ default: m.BigFiveModal }))
)

export const LazyEnglishTestModal = lazy(() =>
  import("./english-test-modal").then(m => ({ default: m.EnglishTestModal }))
)

export const LazyGeneralScoreModal = lazy(() =>
  import("./general-score-modal").then(m => ({ default: m.GeneralScoreModal }))
)

export const LazyCloseVacancyModal = lazy(() =>
  import("./close-vacancy-modal").then(m => ({ default: m.CloseVacancyModal }))
)

export const LazyJobUnpublishModal = lazy(() =>
  import("./job-unpublish-modal").then(m => ({ default: m.JobUnpublishModal }))
)

export const LazyJobStatusModal = lazy(() =>
  import("./job-status-modal").then(m => ({ default: m.JobStatusModal }))
)

export const LazyJobCompareModal = lazy(() =>
  import("./job-compare-modal").then(m => ({ default: m.JobCompareModal }))
)

export const LazyUnifiedCommunicationModal = lazy(() =>
  import("./unified-communication-modal").then(m => ({ default: m.UnifiedCommunicationModal }))
)

export const LazyStageTransitionActionsModal = lazy(() =>
  import("./stage-transition-actions-modal").then(m => ({ default: m.StageTransitionActionsModal }))
)

export const LazyTechnicalTestModal = lazy(() =>
  import("./technical-test-modal").then(m => ({ default: m.TechnicalTestModal }))
)

export const LazyAddCandidatesToVacancyModal = lazy(() =>
  import("./add-candidates-to-vacancy-modal").then(m => ({ default: m.AddCandidatesToVacancyModal }))
)

export const LazyScreeningMediaModal = lazy(() =>
  import("./screening-media-modal").then(m => ({ default: m.ScreeningMediaModal }))
)

export const LazyCandidateDecisionFlowModal = lazy(() =>
  import("@/components/candidate-decision-flow-modal").then(m => ({ default: m.CandidateDecisionFlowModal }))
)

export const LazyBulkActionModal = lazy(() =>
  import("./bulk-action-modal").then(m => ({ default: m.BulkActionModal }))
)

export const LazyNewCandidateUnifiedModal = lazy(() =>
  import("./new-candidate-unified-modal").then(m => ({ default: m.NewCandidateUnifiedModal }))
)

export const LazyCandidateReviewModal = lazy(() =>
  import("@/components/pages/candidate-review-modal").then(m => ({ default: m.CandidateReviewModal }))
)
