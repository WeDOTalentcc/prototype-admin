"use client"

import React from "react"
import { useRouter } from "next/navigation"
import { liaApi } from "@/services/lia-api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
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
import type { UnpublishData } from "@/components/modals/job-unpublish-modal"
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
const EditJobModal = dynamic(() => import("@/components/modals/edit-job-modal").then(m => ({ default: m.EditJobModal })), {
  ssr: false,
  loading: () => null,
})
import { CreateJobModal } from "@/components/modals/create-job-modal"
import { ScreeningChannelsModal, ScreeningSettingsModal, ScreeningSchedulingModal } from "@/components/screening-config"
import { WSITutorialModal } from "@/components/pages/jobs/WSITutorialModal"
import { toast } from "sonner"
import type { Job } from "@/components/jobs"
import type { ScreeningConfig } from "@/hooks/useScreeningConfig"

interface JobsModalsSectionProps {
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

  showEditJobModal: boolean
  onCloseEditJobModal: () => void
  editingJob: Job | null

  showScreeningChannelsModal: boolean
  onCloseScreeningChannelsModal: () => void
  showScreeningSettingsModal: boolean
  onCloseScreeningSettingsModal: () => void
  showScreeningSchedulingModal: boolean
  onCloseScreeningSchedulingModal: () => void
  screeningConfig: ScreeningConfig
  updateScreeningConfig: (updates: Partial<ScreeningConfig>) => void

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
  onRefreshJobs: () => void
  onSetBackendJobs: React.Dispatch<React.SetStateAction<Job[]>>
  onSetSelectedJob: (job: Job | null) => void
  onSetPreviewJob: (job: Job | null) => void
  onSetEditingJob: (job: Job | null) => void
  onSetActiveFilter: (filter: string) => void
  onOpenJobCreationChat: (msg?: string) => void
  onSetPendingNavigateJobId: (id: string | null) => void
  onSetReactivateScreeningDialog: (show: boolean) => void
  onSetReactivateScreeningJobs: (jobs: Job[]) => void
  onSetReactivateEndDate: (date: string) => void
}

export function JobsModalsSection(props: JobsModalsSectionProps) {
  const router = useRouter()
  const {
    allJobs,
    selectedJobsForBatch,
    showReport,
    reportJob,
    onCloseReport,
    showCompareModal,
    onCloseCompareModal,
    showPublishModal,
    onClosePublishModal,
    showUnpublishModal,
    onCloseUnpublishModal,
    showInsightsModal,
    onCloseInsightsModal,
    showDuplicateModal,
    onCloseDuplicateModal,
    showStatusModal,
    onCloseStatusModal,
    statusModalMode,
    showAssignRecruiterModal,
    onCloseAssignRecruiterModal,
    showCreateJobModal,
    onCloseCreateJobModal,
    showEditJobModal,
    onCloseEditJobModal,
    editingJob,
    showScreeningChannelsModal,
    onCloseScreeningChannelsModal,
    showScreeningSettingsModal,
    onCloseScreeningSettingsModal,
    showScreeningSchedulingModal,
    onCloseScreeningSchedulingModal,
    screeningConfig,
    updateScreeningConfig,
    showReactivateScreeningDialog,
    reactivateScreeningJobs,
    reactivateEndDate,
    showWSITutorialModal,
    onCloseWSITutorialModal,
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
  } = props

  return (
    <>
      {showReport && reportJob && (
        <JobReportModal
          job={reportJob}
          isOpen={showReport}
          onClose={onCloseReport}
        />
      )}

      <JobCompareModal
        isOpen={showCompareModal}
        onClose={onCloseCompareModal}
        jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
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
        }))}
      />

      <JobPublishModal
        isOpen={showPublishModal}
        onClose={onClosePublishModal}
        jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
          id: String(job.id),
          code: job.jobId,
          title: job.title,
          status: job.status,
          is_published: job.status === 'Ativa',
          published_channels: []
        }))}
        onPublish={async (jobIds, channels, options) => {
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
        }}
        onUnpublish={async (jobIds, options) => {
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
              
              if (options?.freezeJob) {
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
        }}
        onOpenCommunicationModal={(jobIds, templateCategory) => {
          const selectedJobsList = allJobs.filter(job => jobIds.includes(String(job.id)))
          const jobTitles = selectedJobsList.map(j => j.title).join(', ')
          toast.info(
            `Para notificar candidatos das vagas "${jobTitles}", acesse a página do Kanban de cada vaga e use o menu de comunicação.`,
            { duration: 8000 }
          )
        }}
      />

      <JobUnpublishModal
        isOpen={showUnpublishModal}
        onClose={onCloseUnpublishModal}
        jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id) && job.is_published).map(job => ({
          id: String(job.id),
          code: job.jobId,
          title: job.title,
          status: job.status,
          is_published: job.is_published,
          published_channels: job.published_channels
        }))}
        candidates={[]}
        onUnpublish={async (data: UnpublishData) => {
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
        }}
        onComplete={() => {
          onRefreshJobs()
        }}
        onNavigateToJobWithCommunication={(jobId, params) => {
          const job = allJobs.find(j => String(j.id) === jobId)
          if (job) {
            const queryParams = new URLSearchParams({
              action: 'notify',
              template: params.template,
              channel: params.channel,
              candidates: params.candidateIds.join(',')
            }).toString()
            
            onSetSelectedJob(job)
            onCloseUnpublishModal()
            
            localStorage.setItem('pendingCommunicationAction', JSON.stringify({
              template: params.template,
              candidateIds: params.candidateIds,
              channel: params.channel,
              jobId: jobId
            }))
          }
        }}
      />

      <JobInsightsModal
        isOpen={showInsightsModal}
        onClose={onCloseInsightsModal}
        onSendEmail={(reportData) => {
          const jobTitles = allJobs
            .filter(job => reportData.jobIds.includes(String(job.id)))
            .map(j => j.title)
            .join(', ')
          const subject = encodeURIComponent(`Relatório de Insights - ${jobTitles}`)
          const body = encodeURIComponent(`Segue relatório de insights das vagas selecionadas.\n\n${reportData.reportHtml.replace(/<[^>]*>/g, '')}`)
          window.open(`mailto:?subject=${subject}&body=${body}`, '_blank')
          toast.success('Abrindo cliente de email...')
        }}
        jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
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
          const selectedJob = allJobs.find(job => selectedJobsForBatch.has(job.id))
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
        onDuplicate={async (options) => {
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
                title: options.newTitle,
                recruiter: selectedRecruiter?.name || selectedJob.recruiter,
                recruiter_email: selectedRecruiter?.email || selectedJob.recruiterEmail,
                status: 'Rascunho',
                deadline_shortlist: options.deadlineShortlist,
                deadline_screening: options.deadlineScreening,
                deadline_closing: options.deadlineClosing
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
        }}
      />

      <JobStatusModal
        isOpen={showStatusModal}
        onClose={onCloseStatusModal}
        jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
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
        onPause={async (data) => {
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
              const channels = channelMap[data.recruiterNotificationChannel] || ['bell']
              
              const recruiterIds = [...new Set(selectedJobs
                .map(j => j.recruiter?.id || j.recruiterId)
                .filter(Boolean) as string[])]
              
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
          } catch (error) {
            throw error
          }
        }}
        onActivate={async (data) => {
          try {
            const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
            const updatePromises = selectedJobs.map(job => {
              if (job.backendId) {
                return liaApi.updateJobVacancyStatus(job.backendId, 'Ativa')
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
              const channels = channelMap[data.recruiterNotificationChannel] || ['bell']
              
              const recruiterIds = [...new Set(selectedJobs
                .map(j => j.recruiter?.id || j.recruiterId)
                .filter(Boolean) as string[])]
              
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
        }}
        onNavigateToJobWithCommunication={(jobId, params) => {
          onCloseStatusModal()
          const job = allJobs.find(j => String(j.id) === jobId)
          if (job) {
            onSetSelectedJob(job)
            onSetPreviewJob(job)
            
            localStorage.setItem('pendingCommunicationAction', JSON.stringify({
              template: params.template,
              candidateIds: params.candidateIds,
              channel: params.channel,
              jobId: jobId,
              action: 'pause_notification'
            }))
            
            toast.success('Vaga pausada. O modal de comunicação será aberto para notificar candidatos.')
          }
        }}
      />

      <JobAssignRecruiterModal
        isOpen={showAssignRecruiterModal}
        onClose={onCloseAssignRecruiterModal}
        jobs={allJobs.filter(job => selectedJobsForBatch.has(job.id)).map(job => ({
          id: String(job.id),
          code: job.jobId,
          title: job.title,
          recruiter: job.recruiter
        }))}
        recruiters={companyRecruiters}
        onAssign={async (jobIds, recruiterId, options) => {
          try {
            const selectedJobs = allJobs.filter(job => selectedJobsForBatch.has(job.id))
            const recruiter = companyRecruiters.find(r => r.id === recruiterId)
            
            if (!recruiter) {
              toast.error('Recrutador não encontrado')
              return
            }
            
            const previousRecruiters = [...new Set(selectedJobs
              .map(j => j.recruiter?.id || j.recruiterId)
              .filter(Boolean) as string[])]
            
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
                ? { ...job, recruiter: recruiter.name, recruiterEmail: recruiter.email } 
                : job
            ))
            
            toast.success(`Recrutador atribuído a ${jobIds.length} vaga(s)`)
            onCloseAssignRecruiterModal()
            onDeselectAll()
          } catch (error) {
            toast.error('Erro ao atribuir recrutador. Tente novamente.')
          }
        }}
      />

      <CreateJobModal
        isOpen={showCreateJobModal}
        onClose={onCloseCreateJobModal}
        onCreateWithWizard={() => {
          onCloseCreateJobModal()
          if (activeFilter === 'visao-geral') {
            onSetActiveFilter('todas')
            setTimeout(() => onOpenJobCreationChat(), 100)
          } else {
            onOpenJobCreationChat()
          }
        }}
        onJobCreated={(jobId) => {
          onCloseCreateJobModal()
          localStorage.setItem("jobCreationMode", jobId)
          onSetPendingNavigateJobId(jobId)
          onRefreshJobs()
        }}
      />

      <EditJobModal
        isOpen={showEditJobModal}
        onClose={() => {
          onCloseEditJobModal()
          onSetEditingJob(null)
        }}
        job={editingJob}
        onSave={async (jobId, updates) => {
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
        }}
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

      {showReactivateScreeningDialog && reactivateScreeningJobs.length > 0 && (
        <Dialog open={showReactivateScreeningDialog} onOpenChange={(open) => !open && onSetReactivateScreeningDialog(false)}>
          <DialogContent className="max-w-sm rounded-md bg-white border border-lia-border-subtle dark:bg-lia-bg-primary dark:border-lia-border-subtle">
            <DialogHeader className="pb-3 border-b border-lia-border-subtle dark:border-lia-border-subtle">
              <DialogTitle className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary font-['Open_Sans',sans-serif]">
                Reativar Triagem?
              </DialogTitle>
            </DialogHeader>
            <div className="py-4 space-y-3">
              <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                {reactivateScreeningJobs.length === 1 
                  ? `A vaga "${reactivateScreeningJobs[0]?.title}" tinha a triagem ativa antes de ser pausada. Deseja reativar a triagem?`
                  : `${reactivateScreeningJobs.length} vagas tinham triagem ativa antes de serem pausadas. Deseja reativá-las?`
                }
              </p>
              <div className="space-y-2">
                <Label className="text-xs font-medium text-lia-text-secondary dark:text-lia-text-tertiary">
                  Nova data de término (opcional)
                </Label>
                <Input
                  type="date"
                  value={reactivateEndDate}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => onSetReactivateEndDate(e.target.value)}
                  className="h-8 text-xs border-lia-border-subtle dark:border-lia-border-default dark:bg-lia-bg-elevated"
                />
              </div>
            </div>
            <DialogFooter className="gap-2 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
              <Button
                variant="outline"
                onClick={() => { onSetReactivateScreeningDialog(false); onSetReactivateScreeningJobs([]); onSetReactivateEndDate('') }}
                className="h-8 px-4 text-xs border-lia-border-default dark:border-lia-border-default"
              >
                Não, manter pausada
              </Button>
              <Button
                onClick={async () => {
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
                }}
                className="h-8 px-4 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200"
              >
                Sim, reativar triagem
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      <WSITutorialModal open={showWSITutorialModal} onClose={onCloseWSITutorialModal} />
    </>
  )
}
