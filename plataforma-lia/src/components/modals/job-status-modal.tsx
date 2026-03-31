// @ts-nocheck
"use client"

import React, { useState, useEffect, useMemo, useCallback, useRef } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import {
  Pause,
  Play,
  Briefcase,
  Users,
  Clock,
  Calendar,
  AlertTriangle,
  CheckCircle,
  Filter,
  Megaphone,
  Mail,
  CalendarOff,
  FileText,
  MessageSquare,
  Send,
  ChevronRight,
  Check,
  X,
  Loader2,
  Activity,
  Bell,
} from "lucide-react"
import { toast } from "sonner"
import { useCommunicationTemplates, type TemplateSituation } from "@/hooks/use-communication-templates"

export interface PauseData {
  jobIds: string[]
  pauseReason?: string
  notifyApplicants: boolean
  notificationChannel?: 'email' | 'whatsapp' | 'both'
  notificationMessage?: string
  notificationSubject?: string
  candidateIds?: string[]
  cancelScheduledInterviews: boolean
  cancelScheduledScreenings: boolean
  cancelScheduledTests: boolean
  sendRecruiterSummary: boolean
  recruiterNotificationChannel?: 'email' | 'teams' | 'bell'
}

export interface ActivateData {
  jobIds: string[]
  resumeScreening: boolean
  republish: boolean
  updateDeadlines: boolean
  notifyRecruiters: boolean
  notifyCandidates: boolean
}

interface JobStatusModalProps {
  isOpen: boolean
  onClose: () => void
  jobs: Array<{
    id: string
    code?: string
    title: string
    status: string
    candidates_count?: number
    screening_count?: number
    interviews_scheduled?: number
    tests_scheduled?: number
    paused_since?: string
    approved_count?: number
  }>
  candidates?: Array<{
    id: string
    name: string
    email?: string
    phone?: string
    stage: string
    jobId: string
  }>
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

type FlowStep = 'options' | 'communication' | 'confirmation' | 'complete'
type NotificationChannel = 'email' | 'whatsapp' | 'both'
type RecruiterChannel = 'email' | 'teams' | 'bell'

const PAUSE_REASONS = [
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

const PAUSE_TEMPLATE_SITUATIONS: TemplateSituation[] = ['vaga_fechada', 'feedback_construtivo']

function formatPausedDuration(pausedSince?: string): string {
  if (!pausedSince) return "—"
  const pausedDate = new Date(pausedSince)
  const now = new Date()
  const diffMs = now.getTime() - pausedDate.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return "Hoje"
  if (diffDays === 1) return "1 dia"
  if (diffDays < 7) return `${diffDays} dias`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} semana${Math.floor(diffDays / 7) > 1 ? 's' : ''}`
  return `${Math.floor(diffDays / 30)} mês${Math.floor(diffDays / 30) > 1 ? 'es' : ''}`
}

function replaceTemplateVariables(content: string, jobTitle: string): string {
  return content
    .replace(/\{\{job_title\}\}/g, jobTitle)
    .replace(/\{\{vaga\}\}/g, jobTitle)
    .replace(/\{\{company_name\}\}/g, 'WeDO Talent')
    .replace(/\{\{empresa\}\}/g, 'WeDO Talent')
}

export function JobStatusModal({
  isOpen,
  onClose,
  jobs,
  candidates = [],
  mode,
  onPause,
  onActivate,
  onStatusChange,
  onNavigateToJobWithCommunication
}: JobStatusModalProps) {
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
  const [fetchedCandidates, setFetchedCandidates] = useState<Array<{
    id: string
    name: string
    email?: string
    phone?: string
    stage: string
    jobId: string
  }>>([])
  
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
      PAUSE_TEMPLATE_SITUATIONS.includes(t.situation as TemplateSituation) &&
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
        const allFetched: typeof fetchedCandidates = []
        
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

  const handleProceed = () => {
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
  }

  const handleCommunicationProceed = () => {
    setCurrentStep('confirmation')
  }

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
        localStorage.setItem('pendingCommunicationAction', JSON.stringify(pendingAction))
        
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

  const getSuccessMessage = () => {
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
  }

  const handleClose = () => {
    onClose()
  }

  const getStepIndicator = () => {
    if (!isPauseMode || !notifyApplicants) return null

    const steps = [
      { id: 'pause', label: 'Pausar', done: currentStep !== 'options' },
      { id: 'message', label: 'Comunicar', done: currentStep === 'confirmation' || currentStep === 'complete' },
      { id: 'done', label: 'Concluído', done: currentStep === 'complete' },
    ]

    return (
      <div className="flex items-center justify-center gap-1 mb-4 pb-3 border-b border-lia-border-subtle">
        {steps.map((step, index) => (
          <React.Fragment key={step.id}>
            <div className="flex items-center gap-1.5">
              <div className={cn(
                "w-5 h-5 rounded-full flex items-center justify-center text-micro font-medium",
                step.done 
                  ? "bg-gray-900 text-white" 
                  : currentStep === 'options' && index === 0 
                    ? "bg-gray-100 text-lia-text-primary border border-gray-900"
                    : currentStep === 'communication' && index === 1
                      ? "bg-gray-100 text-lia-text-primary border border-gray-900"
                      : currentStep === 'confirmation' && index === 1
                        ? "bg-gray-100 text-lia-text-primary border border-gray-900"
                        : "bg-gray-100 text-lia-text-tertiary"
              )}>
                {step.done ? <Check className="w-3 h-3" /> : index + 1}
              </div>
              <span className={cn(
                "text-xs font-medium",
                step.done ? "text-lia-text-primary" : "text-lia-text-secondary"
              )}>
                {step.label}
              </span>
            </div>
            {index < steps.length - 1 && (
              <ChevronRight className="w-3.5 h-3.5 text-lia-text-disabled mx-1" />
            )}
          </React.Fragment>
        ))}
      </div>
    )
  }

  const renderPauseOptionsStep = () => (
    <div className="space-y-4">
      <div>
        <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
          Vagas Selecionadas
        </h4>
        <ScrollArea className="max-h-[100px]">
          <div className="space-y-1 bg-gray-50 rounded-md p-2 border border-lia-border-subtle">
            {jobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between py-1.5 px-2 bg-lia-bg-primary rounded-md border border-lia-border-subtle">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <Briefcase className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
                  <div className="flex items-center gap-1.5 min-w-0 flex-1">
                    {job.code && <span className="text-micro font-medium text-lia-text-secondary bg-gray-100 px-1.5 py-0.5 rounded-full flex-shrink-0">{job.code}</span>}
                    <span className="text-xs font-medium text-lia-text-primary truncate">{job.title}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-micro text-lia-text-tertiary">
                  <span className="flex items-center gap-1">
                    <Users className="w-3 h-3" />
                    {job.candidates_count || 0}
                  </span>
                  <span className="flex items-center gap-1">
                    <Filter className="w-3 h-3" />
                    {job.screening_count || 0}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {job.interviews_scheduled || 0}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {hasProposalBlock && (
        <div className="p-3 rounded-md bg-status-error/10 border border-status-error/30">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-status-error mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs font-semibold text-status-error" aria-live="polite" aria-atomic="true">
                {candidatesInProposal.length} candidato(s) em etapa de Proposta
              </p>
              <p className="text-micro text-status-error mt-0.5" aria-live="polite" aria-atomic="true">
                Finalize ou mova esses candidatos antes de pausar a vaga.
              </p>
              <div className="mt-2 space-y-1">
                {candidatesInProposal.slice(0, 3).map(c => (
                  <Badge key={c.id} variant="outline" className="text-micro bg-lia-bg-primary border-status-error/30 text-status-error">
                    {c.name}
                  </Badge>
                ))}
                {candidatesInProposal.length > 3 && (
                  <span className="text-micro text-status-error">+{candidatesInProposal.length - 3} mais</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
            Motivo (Opcional)
          </h4>
          <Select value={pauseReason} onValueChange={setPauseReason}>
            <SelectTrigger className="h-9 text-xs border-lia-border-subtle">
              <SelectValue placeholder="Selecione um motivo..." />
            </SelectTrigger>
            <SelectContent>
              {PAUSE_REASONS.map((reason) => (
                <SelectItem key={reason.value} value={reason.value} className="text-xs">
                  {reason.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {pauseReason === 'other' && (
            <Textarea
              value={customReason}
              onChange={(e) => setCustomReason(e.target.value)}
              placeholder="Digite o motivo para pausar..."
              className="mt-2 h-16 text-xs border-lia-border-subtle resize-none"
            />
          )}
        </div>

        <div>
          <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
            Impacto
          </h4>
          <div className="space-y-1.5 p-3 rounded-md bg-gray-50 border border-lia-border-subtle">
            <div className="flex items-start gap-2 text-xs text-lia-text-primary">
              <span className="flex-shrink-0">⏸️</span>
              <span>Triagens em andamento serão pausadas</span>
            </div>
            <div className="flex items-start gap-2 text-xs text-lia-text-primary">
              <span className="flex-shrink-0">📅</span>
              <span>{totalInterviews} entrevista(s) agendada(s)</span>
            </div>
            <div className="flex items-start gap-2 text-xs text-lia-text-primary">
              <span className="flex-shrink-0">📢</span>
              <span>Publicações serão desativadas</span>
            </div>
            <div className="flex items-start gap-2 text-xs text-lia-text-primary">
              <span className="flex-shrink-0">📧</span>
              <span aria-live="polite" aria-atomic="true">Novos candidatos → pool de talentos</span>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-3 bg-gray-50 rounded-md p-3 border border-lia-border-subtle">
        <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-2">
          <CalendarOff className="w-3.5 h-3.5 text-lia-text-secondary" />
          Ações ao Pausar
        </h4>

        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="cancelScreenings"
              checked={cancelScreenings}
              onCheckedChange={(checked) => setCancelScreenings(checked === true)}
              disabled={hasProposalBlock}
              className="border-lia-border-default data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
            />
            <Label htmlFor="cancelScreenings" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
              <Filter className="w-3 h-3 text-lia-text-disabled" />
              Desmarcar triagens pendentes ({totalScreenings})
            </Label>
          </div>
          
          <div className="flex items-center space-x-2">
            <Checkbox
              id="cancelInterviews"
              checked={cancelInterviews}
              onCheckedChange={(checked) => setCancelInterviews(checked === true)}
              disabled={hasProposalBlock}
              className="border-lia-border-default data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
            />
            <Label htmlFor="cancelInterviews" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
              <Calendar className="w-3 h-3 text-lia-text-disabled" />
              Desmarcar entrevistas agendadas ({totalInterviews})
            </Label>
          </div>
          
          <div className="flex items-center space-x-2">
            <Checkbox
              id="cancelTests"
              checked={cancelTests}
              onCheckedChange={(checked) => setCancelTests(checked === true)}
              disabled={hasProposalBlock}
              className="border-lia-border-default data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
            />
            <Label htmlFor="cancelTests" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
              <FileText className="w-3 h-3 text-lia-text-disabled" />
              Cancelar testes agendados ({totalTests})
            </Label>
          </div>
        </div>
      </div>

      <div className="space-y-3 bg-gray-50 rounded-md p-3 border border-lia-border-subtle">
        <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-2">
          <Megaphone className="w-3.5 h-3.5 text-lia-text-secondary" />
          Notificações
        </h4>

        <div className="space-y-3">
          <div className="flex items-start gap-2">
            <Checkbox
              id="notifyRecruiters"
              checked={notifyRecruiters}
              onCheckedChange={(checked) => setNotifyRecruiters(checked === true)}
              className="mt-0.5 border-lia-border-default data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
            />
            <div className="flex-1">
              <Label htmlFor="notifyRecruiters" className="text-xs font-medium text-lia-text-primary cursor-pointer">
                Notificar recrutadores
              </Label>
              <p className="text-micro text-lia-text-secondary">Enviar resumo das ações por email ou Teams</p>
              
              {notifyRecruiters && (
                <div className="mt-2 flex items-center gap-2">
                  <Label className="text-micro text-lia-text-secondary">Canal:</Label>
                  <div className="flex gap-1">
                    {(['email', 'teams', 'bell'] as RecruiterChannel[]).map((channel) => (
                      <Button
                        key={channel}
                        type="button"
                        variant={recruiterChannel === channel ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setRecruiterChannel(channel)}
                        className={cn(
                          "h-6 px-2 text-micro gap-1",
                          recruiterChannel === channel 
                            ? "bg-gray-900 hover:bg-gray-800 text-white" 
                            : "border border-lia-border-default text-lia-text-secondary"
                        )}
                      >
                        {channel === 'email' && <Mail className="w-3 h-3" />}
                        {channel === 'teams' && <MessageSquare className="w-3 h-3" />}
                        {channel === 'bell' && <Bell className="w-3 h-3" />}
                        {channel === 'email' ? 'Email' : channel === 'teams' ? 'Teams' : 'Bell'}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="border-t border-lia-border-subtle pt-3">
            <div className="flex items-start gap-2">
              <Checkbox
                id="notifyApplicants"
                checked={notifyApplicants}
                onCheckedChange={(checked) => setNotifyApplicants(checked === true)}
                disabled={hasProposalBlock}
                className="mt-0.5 border-lia-border-default data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
              />
              <div className="flex-1">
                <Label htmlFor="notifyApplicants" className="text-xs font-medium text-lia-text-primary cursor-pointer">
                  Enviar email aos candidatos
                </Label>
                <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                  Comunicar candidatos sobre o congelamento da vaga
                </p>
                {notifyApplicants && (
                  <p className="text-micro text-lia-text-tertiary mt-1 flex items-center gap-1">
                    <Activity className="w-3 h-3" />
                    Após pausar, você selecionará o template e canal
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderActivateOptionsStep = () => (
    <div className="space-y-4">
      <div className="p-2.5 rounded-md border bg-gray-50 border-lia-border-subtle">
        <div className="flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-status-success flex-shrink-0" />
          <span className="text-xs text-lia-text-primary leading-relaxed" aria-live="polite" aria-atomic="true">
            Você está prestes a ativar {jobs.length} vaga{jobs.length > 1 ? 's' : ''} pausada{jobs.length > 1 ? 's' : ''}
          </span>
        </div>
      </div>

      <div>
        <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
          Vagas Selecionadas
        </h4>
        <ScrollArea className="max-h-[120px]">
          <div className="space-y-1 bg-gray-50 rounded-md p-2 border border-lia-border-subtle">
            {jobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between py-1.5 px-2 bg-lia-bg-primary rounded-md border border-lia-border-subtle">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <Briefcase className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
                  <span className="text-xs font-medium text-lia-text-primary truncate">{job.title}</span>
                </div>
                <div className="flex items-center gap-2 text-micro text-lia-text-tertiary">
                  <Clock className="w-3 h-3" />
                  <span>Pausada há {formatPausedDuration(job.paused_since)}</span>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      <div className="space-y-3 bg-gray-50 rounded-md p-3 border border-lia-border-subtle">
        <h4 className="text-xs font-semibold text-lia-text-primary">Ações ao Ativar</h4>
        
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="resumeScreening"
              checked={resumeScreening}
              onCheckedChange={(checked) => setResumeScreening(checked === true)}
              className="border-lia-border-default data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
            />
            <Label htmlFor="resumeScreening" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
              <Filter className="w-3 h-3 text-lia-text-disabled" />
              Retomar triagens pausadas
            </Label>
          </div>
          
          <div className="flex items-center space-x-2">
            <Checkbox
              id="republish"
              checked={republish}
              onCheckedChange={(checked) => setRepublish(checked === true)}
              className="border-lia-border-default data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
            />
            <Label htmlFor="republish" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
              <Megaphone className="w-3 h-3 text-lia-text-disabled" />
              Republicar em job boards
            </Label>
          </div>
          
          <div className="flex items-center space-x-2">
            <Checkbox
              id="updateDeadlines"
              checked={updateDeadlines}
              onCheckedChange={(checked) => setUpdateDeadlines(checked === true)}
              className="border-lia-border-default data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
            />
            <Label htmlFor="updateDeadlines" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
              <Calendar className="w-3 h-3 text-lia-text-disabled" />
              Atualizar deadlines (+15 dias)
            </Label>
          </div>
        </div>
      </div>

      <div className="space-y-2 bg-gray-50 rounded-md p-3 border border-lia-border-subtle">
        <h4 className="text-xs font-semibold text-lia-text-primary">Notificações</h4>
        
        <div className="flex items-center space-x-2">
          <Checkbox
            id="notifyRecruitersActivate"
            checked={notifyRecruiters}
            onCheckedChange={(checked) => setNotifyRecruiters(checked === true)}
            className="border-lia-border-default data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
          />
          <Label htmlFor="notifyRecruitersActivate" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
            <Megaphone className="w-3 h-3 text-lia-text-disabled" />
            Notificar recrutadores
          </Label>
        </div>
        
        <div className="flex items-center space-x-2">
          <Checkbox
            id="notifyApplicantsActivate"
            checked={notifyApplicants}
            onCheckedChange={(checked) => setNotifyApplicants(checked === true)}
            className="border-lia-border-default data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
          />
          <Label htmlFor="notifyApplicantsActivate" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
            <Mail className="w-3 h-3 text-lia-text-disabled" />
            Notificar candidatos sobre retomada
          </Label>
        </div>
      </div>
    </div>
  )

  const renderCommunicationStep = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-2 p-2.5 rounded-md bg-gray-100 border border-lia-border-subtle">
        <Mail className="w-4 h-4 text-lia-text-secondary" />
        <span className="text-xs text-lia-text-primary" aria-live="polite" aria-atomic="true">
          Configure a mensagem para {jobCandidates.length - candidatesInProposal.length} candidato(s)
        </span>
      </div>

      <div>
        <Label className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2 block">
          Canal de Comunicação
        </Label>
        <div className="flex gap-2">
          {(['email', 'whatsapp', 'both'] as NotificationChannel[]).map((channel) => (
            <Button
              key={channel}
              type="button"
              variant={notificationChannel === channel ? 'default' : 'outline'}
              size="sm"
              onClick={() => setNotificationChannel(channel)}
              className={cn(
                "h-8 px-3 text-xs gap-1.5",
                notificationChannel === channel 
                  ? "bg-gray-900 hover:bg-gray-800 text-white" 
                  : "border border-lia-border-default text-lia-text-secondary"
              )}
            >
              {channel === 'email' && <Mail className="w-3.5 h-3.5" />}
              {channel === 'whatsapp' && <MessageSquare className="w-3.5 h-3.5" />}
              {channel === 'both' && <Send className="w-3.5 h-3.5" />}
              {channel === 'email' ? 'Email' : channel === 'whatsapp' ? 'WhatsApp' : 'Ambos'}
            </Button>
          ))}
        </div>
      </div>

      <div role="status" aria-live="polite" aria-label="Carregando...">
        <Label className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2 block">
          Template
        </Label>
        {templatesLoading ? (
          <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-md" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-disabled" />
            <span className="text-xs text-lia-text-tertiary">Carregando templates...</span>
          </div>
        ) : (
          <Select value={selectedTemplateId} onValueChange={handleTemplateChange}>
            <SelectTrigger className="h-9 text-xs border-lia-border-subtle">
              <SelectValue placeholder="Selecione um template..." />
            </SelectTrigger>
            <SelectContent>
              {availableTemplates.map((template) => (
                <SelectItem key={template.id} value={template.id} className="text-xs">
                  {template.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {notificationChannel !== 'whatsapp' && (
        <div>
          <Label className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2 block">
            Assunto do Email
          </Label>
          <Input
            value={notificationSubject}
            onChange={(e) => setNotificationSubject(e.target.value)}
            placeholder="Assunto do email..."
            className="h-9 text-xs border-lia-border-subtle"
          />
        </div>
      )}

      <div>
        <Label className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2 block">
          Mensagem
        </Label>
        <Textarea
          value={notificationMessage}
          onChange={(e) => setNotificationMessage(e.target.value)}
          placeholder="Mensagem para os candidatos..."
          className="h-32 text-xs border-lia-border-subtle resize-none"
        />
      </div>
    </div>
  )

  const renderConfirmationStep = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-2 p-2.5 rounded-md bg-status-success/10 border border-status-success/30">
        <CheckCircle className="w-4 h-4 text-status-success" />
        <span className="text-xs text-status-success font-medium">
          Confirme as ações abaixo
        </span>
      </div>

      <div className="space-y-2 p-3 rounded-md bg-gray-50 border border-lia-border-subtle">
        <h4 className="text-xs font-semibold text-lia-text-primary mb-2">Resumo das Ações</h4>
        
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-xs">
            <Check className="w-3.5 h-3.5 text-status-success" />
            <span className="text-lia-text-primary" aria-live="polite" aria-atomic="true">Pausar {jobs.length} vaga(s)</span>
          </div>
          
          {cancelScreenings && totalScreenings > 0 && (
            <div className="flex items-center gap-2 text-xs">
              <Check className="w-3.5 h-3.5 text-status-success" />
              <span className="text-lia-text-primary">Desmarcar {totalScreenings} triagem(ns)</span>
            </div>
          )}
          
          {cancelInterviews && totalInterviews > 0 && (
            <div className="flex items-center gap-2 text-xs">
              <Check className="w-3.5 h-3.5 text-status-success" />
              <span className="text-lia-text-primary">Desmarcar {totalInterviews} entrevista(s)</span>
            </div>
          )}
          
          {cancelTests && totalTests > 0 && (
            <div className="flex items-center gap-2 text-xs">
              <Check className="w-3.5 h-3.5 text-status-success" />
              <span className="text-lia-text-primary">Cancelar {totalTests} teste(s)</span>
            </div>
          )}
          
          {notifyApplicants && (
            <div className="flex items-center gap-2 text-xs">
              <Check className="w-3.5 h-3.5 text-status-success" />
              <span className="text-lia-text-primary" aria-live="polite" aria-atomic="true">
                Notificar {selectedCandidateIds.size} candidato(s) via {notificationChannel === 'both' ? 'Email e WhatsApp' : notificationChannel}
              </span>
            </div>
          )}
          
          {notifyRecruiters && (
            <div className="flex items-center gap-2 text-xs">
              <Check className="w-3.5 h-3.5 text-status-success" />
              <span className="text-lia-text-primary">
                Enviar resumo para recrutadores via {recruiterChannel === 'teams' ? 'Teams' : recruiterChannel === 'bell' ? 'Notificação interna' : 'Email'}
              </span>
            </div>
          )}
        </div>
      </div>

      {pauseReason && (
        <div className="p-3 rounded-md bg-gray-50 border border-lia-border-subtle">
          <h4 className="text-xs font-semibold text-lia-text-secondary mb-1">Motivo</h4>
          <p className="text-xs text-lia-text-primary">
            {pauseReason === 'other' ? customReason : PAUSE_REASONS.find(r => r.value === pauseReason)?.label}
          </p>
        </div>
      )}
    </div>
  )

  const renderCompleteStep = () => (
    <div className="py-8 text-center space-y-4">
      <div className="w-16 h-16 rounded-full bg-status-success/15 flex items-center justify-center mx-auto">
        <CheckCircle className="w-8 h-8 text-status-success" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-lia-text-primary">Processo Concluído!</h3>
        <p className="text-xs text-lia-text-secondary mt-1">
          {getSuccessMessage()}
        </p>
      </div>
    </div>
  )

  if (jobs.length === 0) return null

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="max-w-2xl bg-lia-bg-primary border border-lia-border-subtle">
        <DialogHeader className="pb-3 border-b border-lia-border-subtle">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md flex items-center justify-center bg-gray-100">
              {isPauseMode ? (
                <Pause className="w-4 h-4 text-lia-text-secondary" />
              ) : (
                <Play className="w-4 h-4 text-lia-text-secondary" />
              )}
            </div>
            <div>
              <DialogTitle className="text-sm font-semibold text-lia-text-primary">
                {isPauseMode ? 'Pausar Vagas' : 'Ativar Vagas'}
              </DialogTitle>
              <p className="text-xs text-lia-text-secondary mt-0.5" aria-live="polite" aria-atomic="true">
                {jobs.length} vaga{jobs.length > 1 ? 's' : ''} selecionada{jobs.length > 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </DialogHeader>

        <div className="py-4">
          {getStepIndicator()}
          
          {currentStep === 'options' && (isPauseMode ? renderPauseOptionsStep() : renderActivateOptionsStep())}
          {currentStep === 'communication' && renderCommunicationStep()}
          {currentStep === 'confirmation' && renderConfirmationStep()}
          {currentStep === 'complete' && renderCompleteStep()}
        </div>

        <DialogFooter className="pt-3 border-t border-lia-border-subtle gap-2">
          {currentStep === 'complete' ? (
            <Button
              onClick={handleClose}
              className="h-9 px-4 text-xs font-medium text-white bg-gray-900 hover:bg-gray-800"
            >
              Fechar
            </Button>
          ) : (
            <>
              {currentStep !== 'options' && (
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep(currentStep === 'confirmation' ? (notifyApplicants ? 'communication' : 'options') : 'options')}
                  className="h-9 px-4 text-xs font-medium border border-lia-border-default text-lia-text-secondary hover:bg-gray-50"
                >
                  Voltar
                </Button>
              )}
              <Button
                variant="outline"
                onClick={handleClose}
                className="h-9 px-4 text-xs font-medium border border-lia-border-default text-lia-text-secondary hover:bg-gray-50"
              >
                Cancelar
              </Button>
              <Button
                onClick={currentStep === 'options' ? handleProceed : currentStep === 'communication' ? handleCommunicationProceed : handleSubmit}
                disabled={isSubmitting || (isPauseMode && hasProposalBlock)}
                className="h-9 px-4 text-xs font-medium text-white bg-gray-900 hover:bg-gray-800 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                ) : currentStep === 'options' ? (
                  <>
                    {notifyApplicants ? 'Continuar' : 'Revisar'}
                    <ChevronRight className="w-3.5 h-3.5 ml-1" />
                  </>
                ) : currentStep === 'communication' ? (
                  <>
                    Revisar
                    <ChevronRight className="w-3.5 h-3.5 ml-1" />
                  </>
                ) : isPauseMode ? (
                  <>
                    <Pause className="w-3.5 h-3.5 mr-1.5" />
                    Pausar {jobs.length} Vaga{jobs.length > 1 ? 's' : ''}
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 mr-1.5" />
                    Ativar {jobs.length} Vaga{jobs.length > 1 ? 's' : ''}
                  </>
                )}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
