"use client"

import { useState, useEffect, useMemo, useCallback, useRef } from "react"
import { toast } from "sonner"
import { useCommunicationTemplates } from "@/hooks/use-communication-templates"
import { replaceTemplateVariables } from "./job-status-utils"
import { useJobUIStore } from "@/stores/job-ui-store"
import type {
  PauseData,
  ActivateData,
  JobItem,
  CandidateItem,
  FlowStep,
  NotificationChannel,
  RecruiterChannel,
} from "./types"
import { PAUSE_TEMPLATE_SITUATIONS } from "./types"

interface UseJobStatusModalParams {
  isOpen: boolean
  onClose: () => void
  jobs: JobItem[]
  candidates: CandidateItem[]
  mode: 'pause' | 'activate'
  onPause?: (data: PauseData) => Promise<void>
  onActivate?: (data: ActivateData) => Promise<void>
  onStatusChange?: (jobIds: string[], newStatus: string, options: {
    reason?: string
    notifyRecruiters?: boolean
    notifyCandidates?: boolean
    resumeScreening?: boolean
    republish?: boolean
    updateDeadlines?: boolean
  }) => void
  onNavigateToJobWithCommunication?: (jobId: string, params: {
    template: string
    candidateIds: string[]
    channel: 'email' | 'whatsapp' | 'both'
  }) => void
}

export function useJobStatusModal({
  isOpen,
  onClose,
  jobs,
  candidates,
  mode,
  onPause,
  onActivate,
  onStatusChange,
  onNavigateToJobWithCommunication,
}: UseJobStatusModalParams) {
  const [currentStep, setCurrentStep] = useState<FlowStep>('options')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [pauseReason, setPauseReason] = useState("")
  const [customReason, setCustomReason] = useState("")
  const [cancelScreenings, setCancelScreenings] = useState(true)
  const [cancelInterviews, setCancelInterviews] = useState(true)
  const [cancelTests, setCancelTests] = useState(true)
  const [notifyApplicants, setNotifyApplicants] = useState(false)
  const [notificationChannel, setNotificationChannel] = useState<NotificationChannel>('email')
  const [selectedTemplateId, setSelectedTemplateId] = useState('')
  const [notificationSubject, setNotificationSubject] = useState('')
  const [notificationMessage, setNotificationMessage] = useState('')
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<Set<string>>(new Set())
  const [notifyRecruiters, setNotifyRecruiters] = useState(true)
  const [recruiterChannel, setRecruiterChannel] = useState<RecruiterChannel>('email')
  const [resumeScreening, setResumeScreening] = useState(true)
  const [republish, setRepublish] = useState(true)
  const [updateDeadlines, setUpdateDeadlines] = useState(false)
  const [loadingCandidates, setLoadingCandidates] = useState(false)
  const [fetchedCandidates, setFetchedCandidates] = useState<CandidateItem[]>([])

  const { templates, loading: templatesLoading } = useCommunicationTemplates()

  const isPauseMode = mode === 'pause'
  const jobIds = useMemo(() => jobs.map(j => j.id), [jobs])

  const allCandidates = useMemo(() => {
    return candidates.length > 0 ? candidates : fetchedCandidates
  }, [candidates, fetchedCandidates])

  const jobCandidates = useMemo(() => {
    return allCandidates.filter(c => jobIds.includes(c.jobId))
  }, [allCandidates, jobIds])

  const candidatesInProposal = useMemo(() => {
    return jobCandidates.filter(c =>
      c.stage.toLowerCase() === 'proposta' ||
      c.stage.toLowerCase() === 'offer' ||
      c.stage.toLowerCase() === 'proposal' ||
      c.stage.toLowerCase() === 'offer_made' ||
      c.stage.toLowerCase() === 'offer_accepted'
    )
  }, [jobCandidates])

  const hasProposalBlock = candidatesInProposal.length > 0

  const totalInterviews = useMemo(() => {
    return jobs.reduce((sum, job) => sum + (job.interviews_scheduled || 0), 0)
  }, [jobs])

  const totalScreenings = useMemo(() => {
    return jobs.reduce((sum, job) => sum + (job.screening_count || 0), 0)
  }, [jobs])

  const totalTests = useMemo(() => {
    return jobs.reduce((sum, job) => sum + (job.tests_scheduled || 0), 0)
  }, [jobs])

  const availableTemplates = useMemo(() => {
    return templates.filter(t =>
      PAUSE_TEMPLATE_SITUATIONS.includes(t.situation as typeof PAUSE_TEMPLATE_SITUATIONS[number]) &&
      (notificationChannel === 'both' || t.channel === notificationChannel) &&
      t.isActive
    )
  }, [templates, notificationChannel])

  useEffect(() => {
    if (isOpen) {
      setCurrentStep('options')
      setPauseReason('')
      setCustomReason('')
      setCancelScreenings(true)
      setCancelInterviews(true)
      setCancelTests(true)
      setNotifyApplicants(false)
      setNotificationChannel('email')
      setSelectedTemplateId('')
      setNotificationSubject('')
      setNotificationMessage('')
      setSelectedCandidateIds(new Set(jobCandidates.map(c => c.id)))
      setNotifyRecruiters(true)
      setRecruiterChannel('email')
      setResumeScreening(true)
      setRepublish(true)
      setUpdateDeadlines(false)
    }
  }, [isOpen, jobCandidates])

  const hasFetchedRef = useRef(false)

  useEffect(() => {
    const fetchCandidatesForJobs = async () => {
      const shouldSkip = !isOpen || jobs.length === 0 || candidates.length > 0 || hasFetchedRef.current || !isPauseMode
      if (shouldSkip) return

      hasFetchedRef.current = true
      setLoadingCandidates(true)
      try {
        const allFetched: CandidateItem[] = []

        for (const job of jobs) {
          try {
            const response = await fetch(`/api/backend-proxy/candidates?job_id=${job.id}&limit=200`)
            if (response.ok) {
              const data = await response.json()
              const candidatesData = data.candidates || data.items || data || []

              if (Array.isArray(candidatesData)) {
                allFetched.push(...candidatesData.map((c: Record<string, unknown>) => ({
                  id: c.id || c.candidate_id,
                  name: c.name || c.full_name || 'Candidato',
                  email: c.email,
                  phone: c.phone || c.whatsapp,
                  stage: c.stage || c.pipeline_stage || c.current_stage || 'Triagem',
                  jobId: job.id
                } as CandidateItem)))
              }
            }
          } catch (err) {
          }
        }

        setFetchedCandidates(allFetched)
        setSelectedCandidateIds(new Set(allFetched.map(c => c.id)))
      } catch (error) {
      } finally {
        setLoadingCandidates(false)
      }
    }

    fetchCandidatesForJobs()
  }, [isOpen, jobs.length, candidates.length, isPauseMode])

  useEffect(() => {
    if (!isOpen) {
      hasFetchedRef.current = false
    }
  }, [isOpen])

  useEffect(() => {
    if (availableTemplates.length > 0 && !selectedTemplateId) {
      const defaultTemplate = availableTemplates.find(t => t.situation === 'vaga_fechada') || availableTemplates[0]
      setSelectedTemplateId(defaultTemplate.id)
      setNotificationSubject(defaultTemplate.subject || '')
      setNotificationMessage(replaceTemplateVariables(defaultTemplate.body, jobs[0]?.title || ''))
    }
  }, [availableTemplates, selectedTemplateId, jobs])

  const handleTemplateChange = useCallback((templateId: string) => {
    setSelectedTemplateId(templateId)
    const template = templates.find(t => t.id === templateId)
    if (template) {
      setNotificationSubject(template.subject || '')
      setNotificationMessage(replaceTemplateVariables(template.body, jobs[0]?.title || ''))
    }
  }, [templates, jobs])

  const getSuccessMessage = useCallback(() => {
    if (isPauseMode) {
      const parts = ['Vaga(s) pausada(s) com sucesso']
      if (cancelInterviews && totalInterviews > 0) parts.push(`${totalInterviews} entrevistas desmarcadas`)
      if (cancelScreenings && totalScreenings > 0) parts.push(`${totalScreenings} triagens canceladas`)
      if (notifyApplicants) parts.push(`${selectedCandidateIds.size} candidato(s) notificado(s)`)
      if (notifyRecruiters) parts.push('recrutadores notificados')
      return parts.join('. ') + '.'
    } else {
      return `${jobs.length} vaga(s) ativada(s) com sucesso.`
    }
  }, [isPauseMode, cancelInterviews, totalInterviews, cancelScreenings, totalScreenings, notifyApplicants, selectedCandidateIds.size, notifyRecruiters, jobs.length])

  const handleProceed = useCallback(() => {
    if (hasProposalBlock && isPauseMode) {
      toast.error(`${candidatesInProposal.length} candidato(s) em etapa de Proposta devem ser finalizados antes de continuar.`)
      return
    }

    if (isPauseMode && notifyApplicants && onNavigateToJobWithCommunication) {
      handleSubmitAndNavigate()
    } else if (isPauseMode && notifyApplicants) {
      setCurrentStep('communication')
    } else {
      setCurrentStep('confirmation')
    }
  }, [hasProposalBlock, isPauseMode, candidatesInProposal.length, notifyApplicants, onNavigateToJobWithCommunication])

  const handleCommunicationProceed = useCallback(() => {
    setCurrentStep('confirmation')
  }, [])

  const handleSubmitAndNavigate = async () => {
    if (isSubmitting) return
    setIsSubmitting(true)

    try {
      if (isPauseMode && onPause) {
        const data: PauseData = {
          jobIds,
          pauseReason: pauseReason === 'other' ? customReason : pauseReason,
          notifyApplicants: false,
          cancelScheduledInterviews: cancelInterviews,
          cancelScheduledScreenings: cancelScreenings,
          cancelScheduledTests: cancelTests,
          sendRecruiterSummary: notifyRecruiters,
          recruiterNotificationChannel: recruiterChannel,
        }
        await onPause(data)
      }

      toast.success('Vaga pausada. Abrindo modal de comunicação...')

      const eligibleCandidates = jobCandidates.filter(c => !candidatesInProposal.find(p => p.id === c.id))

      if (jobs.length > 0 && onNavigateToJobWithCommunication) {
        const pendingAction = {
          jobId: jobs[0].id,
          template: 'vaga_fechada',
          candidateIds: eligibleCandidates.map(c => c.id),
          channel: 'email' as const
        }
        useJobUIStore.getState().setPendingCommunicationAction(pendingAction)

        onClose()
        onNavigateToJobWithCommunication(jobs[0].id, pendingAction)
      } else {
        onClose()
      }
    } catch (error) {
      toast.error('Erro ao processar. Tente novamente.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSubmit = async () => {
    if (isSubmitting) return
    setIsSubmitting(true)

    try {
      if (isPauseMode) {
        if (onPause) {
          const data: PauseData = {
            jobIds,
            pauseReason: pauseReason === 'other' ? customReason : pauseReason,
            notifyApplicants,
            notificationChannel: notifyApplicants ? notificationChannel : undefined,
            notificationMessage: notifyApplicants ? notificationMessage : undefined,
            notificationSubject: notifyApplicants && notificationChannel !== 'whatsapp' ? notificationSubject : undefined,
            candidateIds: notifyApplicants ? Array.from(selectedCandidateIds) : undefined,
            cancelScheduledInterviews: cancelInterviews,
            cancelScheduledScreenings: cancelScreenings,
            cancelScheduledTests: cancelTests,
            sendRecruiterSummary: notifyRecruiters,
            recruiterNotificationChannel: recruiterChannel,
          }
          await onPause(data)
        } else if (onStatusChange) {
          onStatusChange(jobIds, 'Paralisada', {
            reason: pauseReason === 'other' ? customReason : pauseReason,
            notifyRecruiters,
            notifyCandidates: notifyApplicants,
          })
        }
        setCurrentStep('complete')
      } else {
        if (onActivate) {
          const data: ActivateData = {
            jobIds,
            resumeScreening,
            republish,
            updateDeadlines,
            notifyRecruiters,
            notifyCandidates: notifyApplicants,
          }
          await onActivate(data)
        } else if (onStatusChange) {
          onStatusChange(jobIds, 'Ativa', {
            resumeScreening,
            republish,
            updateDeadlines,
            notifyRecruiters,
            notifyCandidates: notifyApplicants,
          })
        }
        toast.success(getSuccessMessage())
        onClose()
      }
    } catch (error) {
      toast.error('Erro ao processar. Tente novamente.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = useCallback(() => {
    onClose()
  }, [onClose])

  return {
    currentStep, setCurrentStep, isSubmitting, isPauseMode, jobIds,
    pauseReason, setPauseReason, customReason, setCustomReason,
    cancelScreenings, setCancelScreenings, cancelInterviews, setCancelInterviews,
    cancelTests, setCancelTests,
    notifyApplicants, setNotifyApplicants, notificationChannel, setNotificationChannel,
    selectedTemplateId, notificationSubject, setNotificationSubject,
    notificationMessage, setNotificationMessage, selectedCandidateIds,
    notifyRecruiters, setNotifyRecruiters, recruiterChannel, setRecruiterChannel,
    resumeScreening, setResumeScreening, republish, setRepublish,
    updateDeadlines, setUpdateDeadlines,
    jobCandidates, candidatesInProposal, hasProposalBlock,
    totalInterviews, totalScreenings, totalTests,
    availableTemplates, templatesLoading, handleTemplateChange,
    getSuccessMessage, handleProceed, handleCommunicationProceed, handleSubmit, handleClose,
  }
}
