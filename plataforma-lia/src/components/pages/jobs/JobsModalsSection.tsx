"use client"

import React from "react"
import dynamic from "next/dynamic"
const JobReportModal = dynamic(() => import("@/components/job-report-modal").then(m => ({ default: m.JobReportModal })), {
  ssr: false,
  loading: () => null,
})
const JobCompareModal = dynamic(() => import("@/components/modals/job-compare-modal").then(m => ({ default: m.JobCompareModal })), {
  ssr: false,
  loading: () => null,
})
const JobPublishModal = dynamic(() => import("@/components/modals/job-publish-modal").then(m => ({ default: m.JobPublishModal })), {
  ssr: false,
  loading: () => null,
})
const JobUnpublishModal = dynamic(() => import("@/components/modals/job-unpublish-modal").then(m => ({ default: m.JobUnpublishModal })), {
  ssr: false,
  loading: () => null,
})
const JobInsightsModal = dynamic(() => import("@/components/modals/job-insights-modal").then(m => ({ default: m.JobInsightsModal })), {
  ssr: false,
  loading: () => null,
})
const JobDuplicateModal = dynamic(() => import("@/components/modals/job-duplicate-modal").then(m => ({ default: m.JobDuplicateModal })), {
  ssr: false,
  loading: () => null,
})
const JobStatusModal = dynamic(() => import("@/components/modals/job-status-modal").then(m => ({ default: m.JobStatusModal })), {
  ssr: false,
  loading: () => null,
})
const JobAssignRecruiterModal = dynamic(() => import("@/components/modals/job-assign-recruiter-modal").then(m => ({ default: m.JobAssignRecruiterModal })), {
  ssr: false,
  loading: () => null,
})
import { CreateJobModal } from "@/components/modals/create-job-modal"
import { ScreeningChannelsModal, ScreeningSettingsModal, ScreeningSchedulingModal } from "@/components/screening-config"
import { WSITutorialModal } from "@/components/pages/jobs/WSITutorialModal"
import { ReactivateScreeningDialog } from "./ReactivateScreeningDialog"
import { useJobsModalHandlers } from "./useJobsModalHandlers"
import { useJobsStatusHandlers } from "./useJobsStatusHandlers"
import type { JobsModalsSectionProps } from "./JobsModalsSectionTypes"

export function JobsModalsSection(props: JobsModalsSectionProps) {
  const {
    allJobs,
    selectedJobsForBatch,
    showReport, reportJob, onCloseReport,
    showCompareModal, onCloseCompareModal,
    showPublishModal, onClosePublishModal,
    showUnpublishModal, onCloseUnpublishModal,
    showInsightsModal, onCloseInsightsModal,
    showDuplicateModal, onCloseDuplicateModal,
    showStatusModal, onCloseStatusModal, statusModalMode,
    showAssignRecruiterModal, onCloseAssignRecruiterModal,
    showCreateJobModal, onCloseCreateJobModal,
    showScreeningChannelsModal, onCloseScreeningChannelsModal,
    showScreeningSettingsModal, onCloseScreeningSettingsModal,
    showScreeningSchedulingModal, onCloseScreeningSchedulingModal,
    screeningConfig, updateScreeningConfig,
    showReactivateScreeningDialog, reactivateScreeningJobs, reactivateEndDate,
    showWSITutorialModal, onCloseWSITutorialModal,
    companyRecruiters,
    onSetReactivateScreeningDialog,
    onSetReactivateScreeningJobs,
    onSetReactivateEndDate,
  } = props
  useLiaModalTracking('jobs-report', showReport)
  useLiaModalTracking('jobs-compare', showCompareModal)
  useLiaModalTracking('jobs-publish', showPublishModal)
  useLiaModalTracking('jobs-unpublish', showUnpublishModal)
  useLiaModalTracking('jobs-insights', showInsightsModal)
  useLiaModalTracking('jobs-duplicate', showDuplicateModal)
  useLiaModalTracking('jobs-status', showStatusModal)
  useLiaModalTracking('jobs-assign-recruiter', showAssignRecruiterModal)
  useLiaModalTracking('jobs-create', showCreateJobModal)
  useLiaModalTracking('jobs-screening-channels', showScreeningChannelsModal)
  useLiaModalTracking('jobs-screening-settings', showScreeningSettingsModal)
  useLiaModalTracking('jobs-screening-scheduling', showScreeningSchedulingModal)
  useLiaModalTracking('jobs-reactivate-screening', showReactivateScreeningDialog)
  useLiaModalTracking('jobs-wsi-tutorial', showWSITutorialModal)

  const {
    handlePublish, handlePublishUnpublish, handlePublishCommunication,
    handleFullUnpublish, handleUnpublishNavigate,
    handleInsightsSendEmail, handleDuplicate,
  } = useJobsModalHandlers(props)

  const {
    handlePause, handleCancel, handleActivate, handleStatusNavigate,
    handleAssign, handleCreateWithWizard, handleJobCreated,
    handleReactivateScreening,
  } = useJobsStatusHandlers(props)

  const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))

  return (
    <>
      {showReport && reportJob && (
        <JobReportModal
          job={reportJob as any}
          isOpen={showReport}
          onClose={onCloseReport}
        />
      )}

      <JobCompareModal
        isOpen={showCompareModal}
        onClose={onCloseCompareModal}
        jobs={selectedJobs.map((job) => ({
          id: String(job.id),
          code: job.jobId,
          title: job.title,
          department: job.department,
          location: job.location,
          work_model: job.workModel,
          salary_range: undefined,
          status: job.status,
          deadline: job.deadline,
          candidates_count: job.funnel?.total || 0,
          approved_count: job.funnel?.hired || 0,
          screening_count: job.funnel?.screening || 0,
          performance_score: job.funnel?.hired ? Math.round((job.funnel.hired / Math.max(job.funnel.total, 1)) * 100) : 0,
          benefits: job.benefits,
          technical_requirements: job.technicalRequirements,
          behavioral_competencies: job.behavioralCompetencies
        })) as any}
      />

      <JobPublishModal
        isOpen={showPublishModal}
        onClose={onClosePublishModal}
        jobs={selectedJobs.map(job => ({
          id: String(job.id),
          code: job.jobId,
          title: job.title,
          status: job.status,
          is_published: job.status === 'Ativa',
          published_channels: []
        }))}
        onPublish={handlePublish}
        onUnpublish={handlePublishUnpublish}
        onOpenCommunicationModal={handlePublishCommunication}
      />

      <JobUnpublishModal
        isOpen={showUnpublishModal}
        onClose={onCloseUnpublishModal}
        jobs={selectedJobs.filter(job => job.is_published).map(job => ({
          id: String(job.id),
          code: job.jobId,
          title: job.title,
          status: job.status,
          is_published: job.is_published,
          published_channels: job.published_channels
        }))}
        candidates={[]}
        onUnpublish={handleFullUnpublish}
        onComplete={() => { props.onRefreshJobs() }}
        onNavigateToJobWithCommunication={handleUnpublishNavigate}
      />

      <JobInsightsModal
        isOpen={showInsightsModal}
        onClose={onCloseInsightsModal}
        onSendEmail={handleInsightsSendEmail}
        jobs={selectedJobs.map(job => ({
          id: String(job.id),
          code: job.jobId,
          title: job.title,
          status: job.status,
          priority: job.priority,
          deadline: job.deadline,
          candidates_count: job.funnel?.total || 0,
          approved_count: job.funnel?.hired || 0,
          screening_count: job.funnel?.screening || 0,
          rejected_count: 0,
          performance_score: job.funnel?.hired ? Math.round((job.funnel.hired / Math.max(job.funnel.total, 1)) * 100) : 0
        }))}
      />

      <JobDuplicateModal
        isOpen={showDuplicateModal}
        onClose={onCloseDuplicateModal}
        job={(() => {
          const selectedJob = selectedJobs[0]
          return selectedJob ? {
            id: String(selectedJob.id),
            code: selectedJob.jobId,
            title: selectedJob.title,
            department: selectedJob.department,
            location: selectedJob.location,
            recruiter: selectedJob.recruiter,
            recruiter_email: selectedJob.recruiterEmail,
            candidates_count: selectedJob.funnel?.total || 0,
            approved_count: selectedJob.funnel?.hired || 0
          } : null
        })()}
        recruiters={companyRecruiters}
        onDuplicate={handleDuplicate}
      />

      <JobStatusModal
        isOpen={showStatusModal}
        onClose={onCloseStatusModal}
        jobs={selectedJobs.map(job => ({
          id: String(job.id),
          code: job.jobId,
          title: job.title,
          status: job.status,
          candidates_count: job.funnel?.total || 0,
          screening_count: job.funnel?.screening || 0,
          interviews_scheduled: job.funnel?.interview || 0,
          tests_scheduled: 0,
          approved_count: job.funnel?.hired || 0,
          paused_since: job.status === 'Paralisada' ? job.createdAt : undefined
        }))}
        mode={statusModalMode}
        onPause={handlePause}
        onCancel={handleCancel}
        onActivate={handleActivate}
        onNavigateToJobWithCommunication={handleStatusNavigate}
      />

      <JobAssignRecruiterModal
        isOpen={showAssignRecruiterModal}
        onClose={onCloseAssignRecruiterModal}
        jobs={selectedJobs.map(job => ({
          id: String(job.id),
          code: job.jobId,
          title: job.title,
          recruiter: job.recruiter
        }))}
        recruiters={companyRecruiters}
        onAssign={handleAssign}
      />

      <CreateJobModal
        isOpen={showCreateJobModal}
        onClose={onCloseCreateJobModal}
        onCreateWithWizard={handleCreateWithWizard}
        onJobCreated={handleJobCreated}
      />

      <ScreeningChannelsModal
        isOpen={showScreeningChannelsModal}
        onClose={onCloseScreeningChannelsModal}
        config={screeningConfig}
        updateConfig={updateScreeningConfig}
      />

      <ScreeningSettingsModal
        isOpen={showScreeningSettingsModal}
        onClose={onCloseScreeningSettingsModal}
        config={screeningConfig}
        updateConfig={updateScreeningConfig}
      />

      <ScreeningSchedulingModal
        isOpen={showScreeningSchedulingModal}
        onClose={onCloseScreeningSchedulingModal}
        config={screeningConfig}
        updateConfig={updateScreeningConfig}
      />

      <ReactivateScreeningDialog
        open={showReactivateScreeningDialog}
        jobs={reactivateScreeningJobs}
        endDate={reactivateEndDate}
        onEndDateChange={onSetReactivateEndDate}
        onClose={() => { onSetReactivateScreeningDialog(false); onSetReactivateScreeningJobs([]); onSetReactivateEndDate('') }}
        onReactivate={handleReactivateScreening}
      />

      <WSITutorialModal open={showWSITutorialModal} onClose={onCloseWSITutorialModal} />
    </>
  )
}
