"use client"

import { useCallback } from "react"
import { liaApi } from "@/services/lia-api"
import { toast } from "sonner"
import { useJobUIStore } from "@/stores/job-ui-store"
import type { JobsModalsSectionProps } from "./JobsModalsSectionTypes"
import type { PauseData, ActivateData, CancelData } from "@/components/modals/job-status/types"

export function useJobsStatusHandlers(props: JobsModalsSectionProps) {
  const {
    allJobs,
    selectedJobsForBatch,
    companyRecruiters,
    reactivateScreeningJobs,
    reactivateEndDate,
    onDeselectAll,
    onRefreshJobs,
    onSetBackendJobs,
    onSetSelectedJob,
    onSetPreviewJob,
    onOpenJobCreationChat,
    onSetPendingNavigateJobId,
    onNavigateToCreatedJob,
    onSetReactivateScreeningDialog,
    onSetReactivateScreeningJobs,
    onSetReactivateEndDate,
    onCloseStatusModal,
    onCloseAssignRecruiterModal,
    onCloseCreateJobModal,
  } = props

  const handlePause = useCallback(async (data: PauseData) => {
    try {
      const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
      const updatePromises = selectedJobs.map(job => {
        if (job.backendId) {
          return liaApi.updateJobVacancyStatus(job.backendId, 'Paralisada', {
            pause_reason: data.pauseReason,
            notify_stages: data.notifyApplicants && data.candidateIds ? ['*'] : undefined,
            notification_channel: data.notificationChannel,
            notification_message: data.notificationMessage,
            notification_subject: data.notificationSubject,
          })
        }
        return Promise.resolve(null)
      })
      const results = await Promise.all(updatePromises)

      if (data.sendRecruiterSummary && data.recruiterNotificationChannel) {
        const channelMap: Record<string, string[]> = {
          'email': ['email'],
          'teams': ['teams'],
          'bell': ['bell'],
          'email_teams': ['email', 'teams'],
          'all': ['email', 'teams', 'bell']
        }
        const channels = channelMap[data.recruiterNotificationChannel] || ['bell']

        const recruiterIds = [...new Set(selectedJobs
          .map(j => j.recruiter)
          .filter(Boolean))]

        if (recruiterIds.length === 0) {
          recruiterIds.push('default_user')
        }

        try {
          await liaApi.sendRecruiterActionNotification({
            recruiter_ids: recruiterIds,
            action: 'pause',
            job_titles: selectedJobs.map(j => j.title),
            job_ids: selectedJobs.map(j => j.backendId || String(j.id)),
            channels,
            reason: data.pauseReason,
            cancelled_screenings: data.cancelScheduledScreenings,
            cancelled_interviews: data.cancelScheduledInterviews,
            cancelled_tests: data.cancelScheduledTests,
            notified_candidates_count: data.notifyApplicants ? data.candidateIds?.length || 0 : 0,
          })
        } catch (notifError) {
        }
      }

      onSetBackendJobs(prev => prev.map(job =>
        selectedJobsForBatch.has(job.id)
          ? { ...job, status: 'Paralisada' as const, screeningStatus: job.screeningStatus === 'active' ? 'paused' as const : job.screeningStatus }
          : job
      ))

      for (const job of selectedJobs) {
        if (job.backendId && (job.screeningStatus === 'active')) {
          try {
            await liaApi.updateScreeningStatus(job.backendId, 'paused', { pause_reason: 'Vaga pausada automaticamente' })
          } catch (err) {
          }
        }
      }
      onDeselectAll()

      const aggregated = { notifications_sent: { success_count: 0, failure_count: 0, details: [] as Array<{ candidate_id: string; success?: boolean; error?: string }> } }
      for (const r of results) {
        if (r?.notifications_sent) {
          aggregated.notifications_sent.success_count += r.notifications_sent.success_count || 0
          aggregated.notifications_sent.failure_count += r.notifications_sent.failure_count || 0
          if (r.notifications_sent.details) {
            aggregated.notifications_sent.details.push(...r.notifications_sent.details)
          }
        }
      }
      return aggregated
    } catch (error) {
      throw error
    }
  }, [allJobs, selectedJobsForBatch, onSetBackendJobs, onDeselectAll])

  const handleCancel = useCallback(async (data: CancelData) => {
    try {
      const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
      const updatePromises = selectedJobs.map(job => {
        if (job.backendId) {
          return liaApi.updateJobVacancyStatus(job.backendId, 'Cancelada', {
            close_reason: data.closeReason || data.cancelReason,
            notify_stages: data.notifyStages,
            notification_channel: data.notificationChannel,
            notification_message: data.notificationMessage,
            notification_subject: data.notificationSubject,
          })
        }
        return Promise.resolve(null)
      })
      const results = await Promise.all(updatePromises)

      if (data.sendRecruiterSummary && data.recruiterNotificationChannel) {
        const channelMap: Record<string, string[]> = {
          'email': ['email'],
          'teams': ['teams'],
          'bell': ['bell'],
          'email_teams': ['email', 'teams'],
          'all': ['email', 'teams', 'bell']
        }
        const channels = channelMap[data.recruiterNotificationChannel] || ['bell']

        const recruiterIds = [...new Set(selectedJobs
          .map(j => j.recruiter)
          .filter(Boolean))]

        if (recruiterIds.length === 0) {
          recruiterIds.push('default_user')
        }

        try {
          await liaApi.sendRecruiterActionNotification({
            recruiter_ids: recruiterIds,
            action: 'cancel',
            job_titles: selectedJobs.map(j => j.title),
            job_ids: selectedJobs.map(j => j.backendId || String(j.id)),
            channels,
            reason: data.cancelReason,
            notified_candidates_count: data.notifyApplicants ? data.candidateIds?.length || 0 : 0,
          })
        } catch (notifError) {
        }
      }

      onSetBackendJobs(prev => prev.map(job =>
        selectedJobsForBatch.has(job.id)
          ? { ...job, status: 'Cancelada' as const }
          : job
      ))

      onDeselectAll()

      const aggregated = { notifications_sent: { success_count: 0, failure_count: 0, details: [] as Array<{ candidate_id: string; success?: boolean; error?: string }> } }
      for (const r of results) {
        if (r?.notifications_sent) {
          aggregated.notifications_sent.success_count += r.notifications_sent.success_count || 0
          aggregated.notifications_sent.failure_count += r.notifications_sent.failure_count || 0
          if (r.notifications_sent.details) {
            aggregated.notifications_sent.details.push(...r.notifications_sent.details)
          }
        }
      }
      return aggregated
    } catch (error) {
      throw error
    }
  }, [allJobs, selectedJobsForBatch, onSetBackendJobs, onDeselectAll])

  const handleActivate = useCallback(async (data: ActivateData) => {
    try {
      const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
      const updatePromises = selectedJobs.map(job => {
        if (job.backendId) {
          return liaApi.updateJobVacancyStatus(job.backendId, 'Ativa')
        }
        return Promise.resolve(null)
      })
      await Promise.all(updatePromises)

      const activateData = data as ActivateData & { sendRecruiterSummary?: boolean; recruiterNotificationChannel?: string }
      if (activateData.sendRecruiterSummary && activateData.recruiterNotificationChannel) {
        const channelMap: Record<string, string[]> = {
          'email': ['email'],
          'teams': ['teams'],
          'bell': ['bell'],
          'email_teams': ['email', 'teams'],
          'all': ['email', 'teams', 'bell']
        }
        const channels = channelMap[String(activateData.recruiterNotificationChannel)] || ['bell']

        const recruiterIds = [...new Set(selectedJobs
          .map(j => j.recruiter)
          .filter(Boolean))]

        if (recruiterIds.length === 0) {
          recruiterIds.push('default_user')
        }

        try {
          await liaApi.sendRecruiterActionNotification({
            recruiter_ids: recruiterIds,
            action: 'activate',
            job_titles: selectedJobs.map(j => j.title),
            job_ids: selectedJobs.map(j => j.backendId || String(j.id)),
            channels,
          })
        } catch (notifError) {
        }
      }

      onSetBackendJobs(prev => prev.map(job =>
        selectedJobsForBatch.has(job.id)
          ? { ...job, status: 'Ativa' as const }
          : job
      ))

      const jobsWithPausedScreening = selectedJobs.filter(j => j.screeningStatus === 'paused' && j.screeningConfig)
      if (jobsWithPausedScreening.length > 0) {
        onSetReactivateScreeningJobs(jobsWithPausedScreening)
        onSetReactivateScreeningDialog(true)
      }
      onDeselectAll()
    } catch (error) {
      throw error
    }
  }, [allJobs, selectedJobsForBatch, onSetBackendJobs, onDeselectAll, onSetReactivateScreeningJobs, onSetReactivateScreeningDialog])

  const handleStatusNavigate = useCallback((jobId: string, params: { template: string; candidateIds: string[]; channel: string }) => {
    onCloseStatusModal()
    const job = allJobs.find(j => String(j.id) === jobId)
    if (job) {
      onSetSelectedJob(job)
      onSetPreviewJob(job)

      useJobUIStore.getState().setPendingCommunicationAction({
        template: params.template,
        candidateIds: params.candidateIds,
        channel: params.channel as 'email' | 'whatsapp',
        jobId: jobId,
        action: 'pause_notification'
      })

      toast.success('Vaga pausada. O modal de comunicação será aberto para notificar candidatos.')
    }
  }, [allJobs, onCloseStatusModal, onSetSelectedJob, onSetPreviewJob])

  const handleAssign = useCallback(async (jobIds: string[], recruiterId: string, options: { notifyRecruiter?: boolean; transferCommunications?: boolean }) => {
    try {
      const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
      const recruiter = companyRecruiters.find(r => r.id === recruiterId)

      if (!recruiter) {
        toast.error('Recrutador não encontrado')
        return
      }

      const previousRecruiters = [...new Set(selectedJobs
        .map(j => j.recruiter)
        .filter(Boolean))]

      const updatePromises = selectedJobs.map(job => {
        if (job.backendId) {
          return liaApi.updateJobVacancy(job.backendId, {
            recruiter: recruiter.name,
            recruiter_email: recruiter.email
          })
        }
        return Promise.resolve(null)
      })
      await Promise.all(updatePromises)

      if (options.notifyRecruiter) {
        try {
          await liaApi.sendRecruiterActionNotification({
            recruiter_ids: [recruiterId],
            action: 'assign',
            job_titles: selectedJobs.map(j => j.title),
            job_ids: selectedJobs.map(j => j.backendId || String(j.id)),
            channels: ['bell', 'email', 'teams'],
          })
        } catch (notifError) {
        }
      }

      if (options.transferCommunications && previousRecruiters.length > 0) {
        try {
          await liaApi.transferCommunications({
            job_ids: selectedJobs.map(j => j.backendId || String(j.id)),
            from_recruiter_ids: previousRecruiters,
            to_recruiter_id: recruiterId
          })
        } catch (transferError) {
          toast.warning('Comunicações não foram transferidas')
        }
      }

      onSetBackendJobs(prev => prev.map(job =>
        selectedJobsForBatch.has(job.id)
          ? { ...job, recruiter: recruiter.name, recruiterEmail: recruiter.email || '' }
          : job
      ))

      toast.success(`Recrutador atribuído a ${jobIds.length} vaga(s)`)
      onCloseAssignRecruiterModal()
      onDeselectAll()
    } catch (error) {
      toast.error('Erro ao atribuir recrutador. Tente novamente.')
    }
  }, [allJobs, selectedJobsForBatch, companyRecruiters, onSetBackendJobs, onCloseAssignRecruiterModal, onDeselectAll])

  const handleCreateWithWizard = useCallback(() => {
    onCloseCreateJobModal()
    onOpenJobCreationChat()
  }, [onCloseCreateJobModal, onOpenJobCreationChat])

  const handleJobCreated = useCallback((jobId: string, jobTitle: string) => {
    onCloseCreateJobModal()
    useJobUIStore.getState().setJobCreationMode(jobId)
    // Set pendingNavigateJobId as fallback so the list-based useEffect can catch it
    // if the router push somehow doesn't happen (e.g., navigation intercepted)
    onSetPendingNavigateJobId(jobId)
    // Primary path: navigate directly to the new job's detail page (deterministic).
    // This MUST happen before kicking off the refresh so a failing list-fetch
    // (e.g. backend bridge returning 500) cannot block navigation (Task #241).
    onNavigateToCreatedJob(jobId, jobTitle)
    // Refresh the jobs list in the background so it stays consistent when user returns.
    // We swallow any rejection here — the navigation already happened and the detail
    // page loads independently of the list.
    try {
      const maybePromise = onRefreshJobs()
      if (maybePromise && typeof maybePromise.catch === 'function') {
        maybePromise.catch((err) => {
          console.warn('[handleJobCreated] background refresh failed (non-blocking):', err)
        })
      }
    } catch (err) {
      console.warn('[handleJobCreated] background refresh threw synchronously:', err)
    }
  }, [onCloseCreateJobModal, onSetPendingNavigateJobId, onRefreshJobs, onNavigateToCreatedJob])

  const handleReactivateScreening = useCallback(async () => {
    for (const job of reactivateScreeningJobs) {
      if (job.backendId) {
        try {
          await liaApi.updateScreeningStatus(job.backendId, 'active', {
            scheduled_end_date: reactivateEndDate || undefined
          })
        } catch (err) {
        }
      }
    }
    onSetBackendJobs(prev => prev.map(j =>
      reactivateScreeningJobs.some((rj) => rj.id === j.id)
        ? { ...j, screeningStatus: 'active' as const }
        : j
    ))
    toast.success(`Triagem reativada para ${reactivateScreeningJobs.length} vaga(s)!`)
    onSetReactivateScreeningDialog(false)
    onSetReactivateScreeningJobs([])
    onSetReactivateEndDate('')
  }, [reactivateScreeningJobs, reactivateEndDate, onSetBackendJobs, onSetReactivateScreeningDialog, onSetReactivateScreeningJobs, onSetReactivateEndDate])

  return {
    handlePause,
    handleCancel,
    handleActivate,
    handleStatusNavigate,
    handleAssign,
    handleCreateWithWizard,
    handleJobCreated,
    handleReactivateScreening,
  }
}
