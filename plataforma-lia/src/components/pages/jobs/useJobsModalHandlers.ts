"use client"

import { useCallback } from "react"
import { useRouter } from "next/navigation"
import { liaApi } from "@/services/lia-api"
import { toast } from "sonner"
import { useJobUIStore } from "@/stores/job-ui-store"
import { navigateToJobDetail } from "@/lib/navigation/job-navigation"
import type { JobsModalsSectionProps } from "./JobsModalsSectionTypes"
import type { UnpublishData } from "@/components/modals/job-unpublish-modal"

interface PublishHandlersDeps {
  allJobs: JobsModalsSectionProps['allJobs']
  selectedJobsForBatch: JobsModalsSectionProps['selectedJobsForBatch']
  companyRecruiters: JobsModalsSectionProps['companyRecruiters']
  onDeselectAll: JobsModalsSectionProps['onDeselectAll']
  onRefreshJobs: JobsModalsSectionProps['onRefreshJobs']
  onSetSelectedJob: JobsModalsSectionProps['onSetSelectedJob']
  onClosePublishModal: JobsModalsSectionProps['onClosePublishModal']
  onCloseUnpublishModal: JobsModalsSectionProps['onCloseUnpublishModal']
  onCloseDuplicateModal: JobsModalsSectionProps['onCloseDuplicateModal']
}

export function useJobsModalHandlers(props: JobsModalsSectionProps) {
  const router = useRouter()
  const {
    allJobs,
    selectedJobsForBatch,
    companyRecruiters,
    onDeselectAll,
    onRefreshJobs,
    onSetSelectedJob,
    onClosePublishModal,
    onCloseUnpublishModal,
    onCloseDuplicateModal,
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

  const handlePublishCommunication = useCallback((jobIds: string[], _templateCategory?: string) => {
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
        // Routed through canonical helper (post-mortem 2026-04-29):
        // /jobs/<id> page does not exist anymore. The `?action=sourcing`
        // query param is preserved for when the canonical route is restored
        // — passing it as a hint via the toast description for now.
        navigateToJobDetail(router, String(newJobId), undefined)
      }
    } catch (error) {
      toast.error('Erro ao duplicar vaga. Tente novamente.')
    }
  }, [allJobs, selectedJobsForBatch, companyRecruiters, router, onCloseDuplicateModal, onDeselectAll, onRefreshJobs])

  return {
    handlePublish,
    handlePublishUnpublish,
    handlePublishCommunication,
    handleFullUnpublish,
    handleUnpublishNavigate,
    handleInsightsSendEmail,
    handleDuplicate,
  }
}
