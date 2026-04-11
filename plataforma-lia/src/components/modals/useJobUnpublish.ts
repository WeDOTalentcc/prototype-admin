"use client"

import { useState, useEffect, useMemo, useCallback, useRef } from "react"
import { toast } from "sonner"
import { useCommunicationTemplates, type TemplateSituation } from "@/hooks/chat/use-communication-templates"
import { useJobUIStore } from "@/stores/job-ui-store"
import type { JobUnpublishModalProps, UnpublishData } from "./job-unpublish-modal"

export type FlowStep = 'options' | 'communication' | 'confirmation' | 'complete'
export type NotificationChannel = 'email' | 'whatsapp' | 'both'

export const FREEZE_REASONS = [
  { value: 'budget_review', label: 'Revisão orçamentária' },
  { value: 'headcount_freeze', label: 'Congelamento de headcount' },
  { value: 'restructuring', label: 'Reestruturação da área' },
  { value: 'position_redefinition', label: 'Redefinição do perfil' },
  { value: 'internal_transfer', label: 'Possível transferência interna' },
  { value: 'vacation_period', label: 'Período de férias do gestor' },
  { value: 'market_conditions', label: 'Condições de mercado' },
  { value: 'priority_change', label: 'Mudança de prioridade' },
  { value: 'other', label: 'Outro motivo' },
]

const UNPUBLISH_TEMPLATE_SITUATIONS: TemplateSituation[] = ['vaga_fechada', 'feedback_construtivo']

export function replaceTemplateVariables(body: string, vacancyTitle: string): string {
  return body
    .replace(/\{\{candidato_nome\}\}/g, '{{candidato_nome}}')
    .replace(/\{\{vaga\}\}/g, vacancyTitle)
    .replace(/\{\{empresa_nome\}\}/g, 'Nossa Empresa')
    .replace(/\{\{recrutador_nome\}\}/g, 'Equipe de Recrutamento')
}

export function useJobUnpublish({
  isOpen,
  onClose,
  jobs,
  candidates = [],
  onUnpublish,
  onComplete,
  onNavigateToJobWithCommunication
}: JobUnpublishModalProps) {
  const [currentStep, setCurrentStep] = useState<FlowStep>('options')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [freezeJob, setFreezeJob] = useState(false)
  const [freezeReason, setFreezeReason] = useState('')
  const [freezeStartDate, setFreezeStartDate] = useState('')
  const [unfreezeDate, setUnfreezeDate] = useState('')
  const [notifyApplicants, setNotifyApplicants] = useState(false)

  const [notificationChannel, setNotificationChannel] = useState<NotificationChannel>('email')
  const [selectedTemplateId, setSelectedTemplateId] = useState('')
  const [notificationSubject, setNotificationSubject] = useState('')
  const [notificationMessage, setNotificationMessage] = useState('')
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<Set<string>>(new Set())

  const [acknowledgedWarning, setAcknowledgedWarning] = useState(false)
  const [loadingCandidates, setLoadingCandidates] = useState(false)
  const [fetchedCandidates, setFetchedCandidates] = useState<Array<{
    id: string
    name: string
    email?: string
    phone?: string
    stage: string
    jobId: string
  }>>([])

  const { templates, loading: templatesLoading } = useCommunicationTemplates()

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
      c.stage.toLowerCase() === 'proposal'
    )
  }, [jobCandidates])

  const hasProposalBlock = candidatesInProposal.length > 0

  const availableTemplates = useMemo(() => {
    return templates.filter(t =>
      UNPUBLISH_TEMPLATE_SITUATIONS.includes(t.situation as TemplateSituation) &&
      (notificationChannel === 'both' || t.channel === notificationChannel) &&
      t.isActive
    )
  }, [templates, notificationChannel])

  useEffect(() => {
    if (isOpen) {
      setCurrentStep('options')
      setFreezeJob(false)
      setFreezeReason('')
      setFreezeStartDate(new Date().toISOString().split('T')[0])
      setUnfreezeDate('')
      setNotifyApplicants(false)
      setNotificationChannel('email')
      setSelectedTemplateId('')
      setNotificationSubject('')
      setNotificationMessage('')
      setSelectedCandidateIds(new Set(jobCandidates.map(c => c.id)))
      setAcknowledgedWarning(false)
    }
  }, [isOpen, jobCandidates])

  const hasFetchedRef = useRef(false)

  useEffect(() => {
    const fetchCandidatesForJobs = async () => {
      const shouldSkip = !isOpen || jobs.length === 0 || candidates.length > 0 || hasFetchedRef.current
      if (shouldSkip) return

      hasFetchedRef.current = true
      setLoadingCandidates(true)
      try {
        const allFetched: typeof fetchedCandidates = []

        for (const job of jobs) {
          try {
            const response = await fetch(`/api/backend-proxy/candidates?job_id=${job.id}&limit=200`)
            if (response.ok) {
              const data = await response.json()
              const candidatesData = data.candidates || data.items || data || []

              if (Array.isArray(candidatesData)) {
                allFetched.push(...candidatesData.map((c: Record<string, unknown>) => ({
                  id: (c.id || c.candidate_id) as string,
                  name: (c.name || c.full_name || 'Candidato') as string,
                  email: c.email as string | undefined,
                  phone: (c.phone || c.whatsapp) as string | undefined,
                  stage: (c.stage || c.pipeline_stage || c.current_stage || 'Triagem') as string,
                  jobId: job.id
                })))
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
  }, [isOpen, jobs, candidates.length])

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

  const toggleCandidateSelection = (candidateId: string) => {
    const newSelection = new Set(selectedCandidateIds)
    if (newSelection.has(candidateId)) {
      newSelection.delete(candidateId)
    } else {
      newSelection.add(candidateId)
    }
    setSelectedCandidateIds(newSelection)
  }

  const selectAllCandidates = () => {
    setSelectedCandidateIds(new Set(jobCandidates.filter(c => !candidatesInProposal.find(p => p.id === c.id)).map(c => c.id)))
  }

  const deselectAllCandidates = () => {
    setSelectedCandidateIds(new Set())
  }

  const getSuccessMessage = () => {
    const parts = ['Vaga(s) despublicada(s) com sucesso']
    if (freezeJob) parts.push('e status alterado para Paralisada')
    if (notifyApplicants) parts.push(`${selectedCandidateIds.size} candidato(s) notificado(s)`)
    return parts.join('. ') + '.'
  }

  const handleSubmitAndNavigate = async () => {
    if (isSubmitting) return
    setIsSubmitting(true)

    try {
      const data: UnpublishData = {
        jobIds,
        freezeJob,
        freezeReason: freezeJob ? freezeReason : undefined,
        freezeStartDate: freezeJob ? freezeStartDate : undefined,
        unfreezeDate: freezeJob && unfreezeDate ? unfreezeDate : undefined,
        notifyApplicants: false,
        cancelScheduledInterviews: freezeJob,
        cancelScheduledScreenings: freezeJob,
        sendRecruiterSummary: freezeJob,
      }

      await onUnpublish(data)

      toast.success('Vaga despublicada. Abrindo modal de comunicação...')

      const eligibleCandidates = jobCandidates.filter(c => !candidatesInProposal.find(p => p.id === c.id))

      if (jobs.length > 0) {
        const pendingAction = {
          jobId: jobs[0].id,
          template: 'vaga_fechada',
          candidateIds: eligibleCandidates.map(c => c.id),
          channel: 'email' as const
        }
        useJobUIStore.getState().setPendingCommunicationAction(pendingAction)
        onClose()
        if (onNavigateToJobWithCommunication) {
          onNavigateToJobWithCommunication(jobs[0].id, pendingAction)
        }
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
      const data: UnpublishData = {
        jobIds,
        freezeJob,
        freezeReason: freezeJob ? freezeReason : undefined,
        freezeStartDate: freezeJob ? freezeStartDate : undefined,
        unfreezeDate: freezeJob && unfreezeDate ? unfreezeDate : undefined,
        notifyApplicants,
        notificationChannel: notifyApplicants ? notificationChannel : undefined,
        notificationMessage: notifyApplicants ? notificationMessage : undefined,
        notificationSubject: notifyApplicants && notificationChannel !== 'whatsapp' ? notificationSubject : undefined,
        candidateIds: notifyApplicants ? Array.from(selectedCandidateIds) : undefined,
        cancelScheduledInterviews: freezeJob && notifyApplicants,
        cancelScheduledScreenings: freezeJob && notifyApplicants,
        sendRecruiterSummary: freezeJob && notifyApplicants,
      }

      await onUnpublish(data)

      if (freezeJob && notifyApplicants) {
        setCurrentStep('complete')
      } else {
        toast.success(getSuccessMessage())
        onClose()
        onComplete?.()
      }
    } catch (error) {
      toast.error('Erro ao processar. Tente novamente.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleProceed = () => {
    if (hasProposalBlock) {
      toast.error(`${candidatesInProposal.length} candidato(s) em etapa de Proposta devem ser finalizados antes de continuar.`)
      return
    }

    if (notifyApplicants && onNavigateToJobWithCommunication) {
      handleSubmitAndNavigate()
    } else if (notifyApplicants) {
      setCurrentStep('communication')
    } else {
      handleSubmit()
    }
  }

  const handleCommunicationProceed = () => {
    if (freezeJob) {
      setCurrentStep('confirmation')
    } else {
      handleSubmit()
    }
  }

  const handleClose = () => {
    if (currentStep === 'complete') {
      onComplete?.()
    }
    onClose()
  }

  return {
    currentStep, setCurrentStep,
    isSubmitting,
    freezeJob, setFreezeJob,
    freezeReason, setFreezeReason,
    freezeStartDate, setFreezeStartDate,
    unfreezeDate, setUnfreezeDate,
    notifyApplicants, setNotifyApplicants,
    notificationChannel, setNotificationChannel,
    selectedTemplateId,
    notificationSubject, setNotificationSubject,
    notificationMessage, setNotificationMessage,
    selectedCandidateIds,
    acknowledgedWarning, setAcknowledgedWarning,
    loadingCandidates,
    jobCandidates, candidatesInProposal,
    hasProposalBlock,
    availableTemplates,
    handleTemplateChange,
    toggleCandidateSelection,
    selectAllCandidates, deselectAllCandidates,
    handleProceed, handleCommunicationProceed,
    handleSubmit, handleClose,
    jobs,
  }
}

export type UseJobUnpublishReturn = ReturnType<typeof useJobUnpublish>
