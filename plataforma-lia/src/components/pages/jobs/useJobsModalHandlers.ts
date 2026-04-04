"use client"

import { useCallback } from "react"
import { useRouter } from "next/navigation"
import { liaApi } from "@/services/lia-api"
import { toast } from "sonner"
import { useJobUIStore } from "@/stores/job-ui-store"
import type { JobsModalsSectionProps } from "./JobsModalsSectionTypes"
import type { UnpublishData } from "@/components/modals/job-unpublish-modal"

export function useJobsModalHandlers(props: JobsModalsSectionProps) {
  const router = useRouter()
  const {
    allJobs,
    selectedJobsForBatch,
    companyRecruiters,
    activeFilter,
    onDeselectAll,
    onRefreshJobs,
    onSetBackendJobs,
    onSetSelectedJob,
    onSetPreviewJob,
    onSetEditingJob,
    onSetActiveFilter,
    onOpenJobCreationChat,
    onSetPendingNavigateJobId,
    onSetReactivateScreeningDialog,
    onSetReactivateScreeningJobs,
    onSetReactivateEndDate,
    onClosePublishModal,
    onCloseUnpublishModal,
    onCloseDuplicateModal,
    onCloseStatusModal,
    onCloseAssignRecruiterModal,
    onCloseCreateJobModal,
    onCloseEditJobModal,
    reactivateScreeningJobs,
    reactivateEndDate,
  } = props

  const handlePublish = useCallback(async (jobIds: string[], channels: string[], _options: Record<string, unknown>) => {
    try {
      const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))

      for (const job of selectedJobs) {
        if (!job.backendId) continue

        await liaApi.updateJobVacancy(job.backendId, {
          status: 'Ativa',
          published_website: channels.includes('portal')
        })

        if (channels.includes('linkedin')) {
          try {
            const linkedInResult = await liaApi.publishToLinkedIn(job.backendId)
            if (linkedInResult.mock) {
              toast.info(`LinkedIn: ${linkedInResult.message}`)
            }
          } catch (err) {
          }
        }

        if (channels.includes('indeed')) {
          try {
            const indeedResult = await liaApi.publishToIndeed(job.backendId)
            if (indeedResult.note) {
              toast.info(`Indeed: ${indeedResult.note}`)
            }
          } catch (err) {
          }
        }
      }

      toast.success(`${jobIds.length} vaga(s) publicada(s) em ${channels.length} canal(is)`)
      onClosePublishModal()
      onDeselectAll()
      onRefreshJobs()
    } catch (error) {
      toast.error('Erro ao publicar vagas. Tente novamente.')
    }
  }, [allJobs, selectedJobsForBatch, onClosePublishModal, onDeselectAll, onRefreshJobs])

  const handlePublishUnpublish = useCallback(async (jobIds: string[], options: Record<string, unknown>) => {
    try {
      const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))

      for (const job of selectedJobs) {
        if (!job.backendId) continue

        if (job.publishedLinkedIn) {
          try {
            await liaApi.unpublishFromPlatform(job.backendId, 'linkedin')
          } catch (err) {
          }
        }

        if (job.publishedIndeed) {
          try {
            await liaApi.unpublishFromPlatform(job.backendId, 'indeed')
          } catch (err) {
          }
        }

        if ((options as Record<string, unknown>)?.freezeJob) {
          try {
            await liaApi.updateJobVacancy(job.backendId, {
              status: 'Paralisada'
            })
          } catch (err) {
          }
        }
      }

      toast.success(`${jobIds.length} vaga(s) despublicada(s)`)
      onClosePublishModal()
      onDeselectAll()
      onRefreshJobs()
    } catch (error) {
      toast.error('Erro ao despublicar vagas. Tente novamente.')
    }
  }, [allJobs, selectedJobsForBatch, onClosePublishModal, onDeselectAll, onRefreshJobs])

  const handlePublishCommunication = useCallback((jobIds: string[], _templateCategory: string) => {
    const selectedJobsList = allJobs.filter(job => jobIds.includes(String(job.id)))
    const jobTitles = selectedJobsList.map(j => j.title).join(', ')
    toast.info(
      `Para notificar candidatos das vagas "${jobTitles}", acesse a página do Kanban de cada vaga e use o menu de comunicação.`,
      { duration: 8000 }
    )
  }, [allJobs])

  const handleFullUnpublish = useCallback(async (data: UnpublishData) => {
    try {
      const response = await fetch('/api/backend-proxy/job-boards/unpublish-complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_ids: data.jobIds,
          freeze_job: data.freezeJob,
          freeze_reason: data.freezeReason,
          freeze_start_date: data.freezeStartDate,
          unfreeze_date: data.unfreezeDate,
          notify_applicants: data.notifyApplicants,
          notification_channel: data.notificationChannel,
          notification_message: data.notificationMessage,
          notification_subject: data.notificationSubject,
          candidate_ids: data.candidateIds,
          cancel_scheduled_interviews: data.cancelScheduledInterviews,
          cancel_scheduled_screenings: data.cancelScheduledScreenings,
          send_recruiter_summary: data.sendRecruiterSummary
        })
      })

      if (!response.ok) {
        throw new Error('Failed to unpublish')
      }

      const result = await response.json()

      if (result.frozen_jobs?.length > 0) {
        toast.success(`${result.frozen_jobs.length} vaga(s) congelada(s) com sucesso`)
      } else if (result.unpublished_jobs?.length > 0) {
        toast.success(`${result.unpublished_jobs.length} vaga(s) despublicada(s)`)
      }

      onDeselectAll()
      onRefreshJobs()
    } catch (error) {
      throw error
    }
  }, [onDeselectAll, onRefreshJobs])

  const handleUnpublishNavigate = useCallback((jobId: string, params: { template: string; candidateIds: string[]; channel: string }) => {
    const job = allJobs.find(j => String(j.id) === jobId)
    if (job) {
      onSetSelectedJob(job)
      onCloseUnpublishModal()

      useJobUIStore.getState().setPendingCommunicationAction({
        template: params.template,
        candidateIds: params.candidateIds,
        channel: params.channel as 'email' | 'whatsapp',
        jobId: jobId
      })
    }
  }, [allJobs, onSetSelectedJob, onCloseUnpublishModal])

  const handleInsightsSendEmail = useCallback((reportData: { jobIds: string[]; reportHtml: string }) => {
    const jobTitles = allJobs
      .filter(job => reportData.jobIds.includes(String(job.id)))
      .map(j => j.title)
      .join(', ')
    const subject = encodeURIComponent(`Relatório de Insights - ${jobTitles}`)
    const body = encodeURIComponent(`Segue relatório de insights das vagas selecionadas.\n\n${reportData.reportHtml.replace(/<[^>]*>/g, '')}`)
    window.open(`mailto:?subject=${subject}&body=${body}`, '_blank')
    toast.success('Abrindo cliente de email...')
  }, [allJobs])

  const handleDuplicate = useCallback(async (options: Record<string, unknown>) => {
    try {
      const selectedJob = allJobs.find(job => selectedJobsForBatch.has(job.id))
      if (!selectedJob?.backendId) {
        toast.error('Vaga não encontrada')
        return
      }

      const includesCandidates = options.candidateOption !== 'none'
      const candidateFilter = options.candidateOption === 'approved' ? 'approved' : (options.candidateOption === 'all' ? 'all' : null)
      const selectedRecruiter = companyRecruiters.find(r => r.id === options.recruiterId)

      const result = await liaApi.duplicateJobVacancy(selectedJob.backendId, {
        copies: 1,
        includeCandiates: includesCandidates,
        candidateFilter: candidateFilter,
        overrides: {
          title: options.newTitle as string,
          recruiter: selectedRecruiter?.name || selectedJob.recruiter,
          recruiter_email: selectedRecruiter?.email || selectedJob.recruiterEmail,
          status: 'Rascunho',
          deadline_shortlist: options.deadlineShortlist as string,
          deadline_screening: options.deadlineScreening as string,
          deadline_closing: options.deadlineClosing as string
        }
      })

      const newJobId = result?.jobs?.[0]?.id
      const candidatesIncluded = result?.total_candidates_cloned || 0

      if (includesCandidates && candidatesIncluded > 0) {
        toast.success(`Vaga "${options.newTitle}" criada com ${candidatesIncluded} candidato(s)!`)
      } else if (options.candidateOption === 'none') {
        toast.success(`Vaga "${options.newTitle}" criada! Inicie a busca de candidatos.`)
      } else {
        toast.success(`Vaga "${options.newTitle}" criada com sucesso!`)
      }

      onCloseDuplicateModal()
      onDeselectAll()
      onRefreshJobs()

      if (options.candidateOption === 'none' && newJobId) {
        router.push(`/jobs/${newJobId}?action=sourcing`)
      }
    } catch (error) {
      toast.error('Erro ao duplicar vaga. Tente novamente.')
    }
  }, [allJobs, selectedJobsForBatch, companyRecruiters, router, onCloseDuplicateModal, onDeselectAll, onRefreshJobs])

  const handlePause = useCallback(async (data: Record<string, unknown>) => {
    try {
      const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
      const updatePromises = selectedJobs.map(job => {
        if (job.backendId) {
          return liaApi.updateJobVacancyStatus(job.backendId, 'Paralisada')
        }
        return Promise.resolve(null)
      })
      await Promise.all(updatePromises)

      if (data.sendRecruiterSummary && data.recruiterNotificationChannel) {
        const channelMap: Record<string, string[]> = {
          'email': ['email'],
          'teams': ['teams'],
          'bell': ['bell'],
          'email_teams': ['email', 'teams'],
          'all': ['email', 'teams', 'bell']
        }
        const channels = channelMap[data.recruiterNotificationChannel as string] || ['bell']

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
            reason: data.pauseReason as string,
            cancelled_screenings: data.cancelScheduledScreenings as boolean,
            cancelled_interviews: data.cancelScheduledInterviews as boolean,
            cancelled_tests: data.cancelScheduledTests as boolean,
            notified_candidates_count: data.notifyApplicants ? (data.candidateIds as string[])?.length || 0 : 0,
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
    } catch (error) {
      throw error
    }
  }, [allJobs, selectedJobsForBatch, onSetBackendJobs, onDeselectAll])

  const handleActivate = useCallback(async (data: Record<string, unknown>) => {
    try {
      const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
      const updatePromises = selectedJobs.map(job => {
        if (job.backendId) {
          return liaApi.updateJobVacancyStatus(job.backendId, 'Ativa')
        }
        return Promise.resolve(null)
      })
      await Promise.all(updatePromises)

      const activateData = data as Record<string, unknown>
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

  const handleAssign = useCallback(async (jobIds: string[], recruiterId: string, options: { notifyRecruiter: boolean; transferCommunications: boolean }) => {
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
    if (activeFilter === 'visao-geral') {
      onSetActiveFilter('todas')
      setTimeout(() => onOpenJobCreationChat(), 100)
    } else {
      onOpenJobCreationChat()
    }
  }, [activeFilter, onCloseCreateJobModal, onSetActiveFilter, onOpenJobCreationChat])

  const handleJobCreated = useCallback((jobId: string) => {
    onCloseCreateJobModal()
    useJobUIStore.getState().setJobCreationMode(jobId)
    onSetPendingNavigateJobId(jobId)
    onRefreshJobs()
  }, [onCloseCreateJobModal, onSetPendingNavigateJobId, onRefreshJobs])

  const handleEditSave = useCallback(async (jobId: string, updates: Record<string, unknown>) => {
    try {
      await liaApi.updateJobVacancy(jobId, updates)
      toast.success('Vaga atualizada com sucesso!')
      onCloseEditJobModal()
      onSetEditingJob(null)
      window.location.reload()
    } catch (error) {
      toast.error('Erro ao atualizar vaga. Tente novamente.')
      throw error
    }
  }, [onCloseEditJobModal, onSetEditingJob])

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
    handlePublish,
    handlePublishUnpublish,
    handlePublishCommunication,
    handleFullUnpublish,
    handleUnpublishNavigate,
    handleInsightsSendEmail,
    handleDuplicate,
    handlePause,
    handleActivate,
    handleStatusNavigate,
    handleAssign,
    handleCreateWithWizard,
    handleJobCreated,
    handleEditSave,
    handleReactivateScreening,
  }
}
