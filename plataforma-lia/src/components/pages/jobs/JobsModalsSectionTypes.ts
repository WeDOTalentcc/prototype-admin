import React from "react"
import type { Job } from "@/components/jobs"
import type { ScreeningConfig } from "@/hooks/recruitment/useScreeningConfig"

export interface JobsModalsSectionProps {
  allJobs: Job[]
  selectedJobsForBatch: Set<number>

  showReport: boolean
  reportJob: Job | null
  onCloseReport: () => void

  showCompareModal: boolean
  onCloseCompareModal: () => void

  showPublishModal: boolean
  onClosePublishModal: () => void

  showUnpublishModal: boolean
  onCloseUnpublishModal: () => void

  showInsightsModal: boolean
  onCloseInsightsModal: () => void

  showDuplicateModal: boolean
  onCloseDuplicateModal: () => void

  showStatusModal: boolean
  onCloseStatusModal: () => void
  statusModalMode: 'pause' | 'activate'

  showAssignRecruiterModal: boolean
  onCloseAssignRecruiterModal: () => void

  showCreateJobModal: boolean
  onCloseCreateJobModal: () => void

  showScreeningChannelsModal: boolean
  onCloseScreeningChannelsModal: () => void
  showScreeningSettingsModal: boolean
  onCloseScreeningSettingsModal: () => void
  showScreeningSchedulingModal: boolean
  onCloseScreeningSchedulingModal: () => void
  screeningConfig: ScreeningConfig
  updateScreeningConfig: (updates: Partial<ScreeningConfig>) => Promise<boolean>

  showReactivateScreeningDialog: boolean
  reactivateScreeningJobs: Job[]
  reactivateEndDate: string

  showWSITutorialModal: boolean
  onCloseWSITutorialModal: () => void

  companyRecruiters: Array<{
    id: string
    name: string
    email?: string
    avatar?: string
    active_jobs_count?: number
    performance_score?: number
  }>

  activeFilter: string

  onDeselectAll: () => void
  onRefreshJobs: () => void | Promise<void>
  onSetBackendJobs: React.Dispatch<React.SetStateAction<Job[]>>
  onSetSelectedJob: (job: Job | null) => void
  onSetPreviewJob: (job: Job | null) => void
  onSetActiveFilter: (filter: string) => void
  onOpenJobCreationChat: (msg?: string) => void
  onSetPendingNavigateJobId: (id: string | null) => void
  onNavigateToCreatedJob: (jobId: string, jobTitle: string) => void
  onSetReactivateScreeningDialog: (show: boolean) => void
  onSetReactivateScreeningJobs: (jobs: Job[]) => void
  onSetReactivateEndDate: (date: string) => void
  jobs?: Job[]
  onPublish?: (jobIds: string[], channels: string[], options?: Record<string, unknown>) => Promise<void>
  onUnpublish?: (jobIds: string[], options?: Record<string, unknown>) => Promise<void>
  onOpenCommunicationModal?: (jobIds: string[], templateCategory?: string) => void
}
