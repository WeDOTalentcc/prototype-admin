"use client"

import React, { useState, useEffect, useMemo, useCallback, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import {
  AlertTriangle,
  Loader2,
  Check,
  X,
  Calendar,
  Snowflake,
  Bell,
  Mail,
  MessageSquare,
  Send,
  Briefcase,
  ArrowRight,
  Users,
  CalendarOff,
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  Archive,
} from "lucide-react"
import { toast } from "sonner"
import { useCommunicationTemplates, type TemplateSituation } from "@/hooks/use-communication-templates"

export interface JobUnpublishModalProps {
  isOpen: boolean
  onClose: () => void
  jobs: Array<{
    id: string
    code?: string
    title: string
    status: string
    is_published?: boolean
    published_channels?: string[]
  }>
  candidates?: Array<{
    id: string
    name: string
    email?: string
    phone?: string
    stage: string
    jobId: string
  }>
  onUnpublish: (data: UnpublishData) => Promise<void>
  onComplete?: () => void
  onNavigateToJobWithCommunication?: (jobId: string, params: {
    template: string
    candidateIds: string[]
    channel: 'email' | 'whatsapp' | 'both'
  }) => void
}

export interface UnpublishData {
  jobIds: string[]
  freezeJob: boolean
  freezeReason?: string
  freezeStartDate?: string
  unfreezeDate?: string
  notifyApplicants: boolean
  notificationChannel?: 'email' | 'whatsapp' | 'both'
  notificationMessage?: string
  notificationSubject?: string
  candidateIds?: string[]
  cancelScheduledInterviews: boolean
  cancelScheduledScreenings: boolean
  sendRecruiterSummary: boolean
}

type FlowStep = 'options' | 'communication' | 'confirmation' | 'complete'
type NotificationChannel = 'email' | 'whatsapp' | 'both'

const FREEZE_REASONS = [
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

export function JobUnpublishModal({
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
                allFetched.push(...candidatesData.map((c: any) => ({
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
            console.warn(`Error fetching candidates for job ${job.id}:`, err)
          }
        }
        
        setFetchedCandidates(allFetched)
        setSelectedCandidateIds(new Set(allFetched.map(c => c.id)))
      } catch (error) {
        console.error('Error fetching candidates:', error)
      } finally {
        setLoadingCandidates(false)
      }
    }
    
    fetchCandidatesForJobs()
  }, [isOpen, jobs.length, candidates.length])
  
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

  const handleProceed = () => {
    if (hasProposalBlock) {
      toast.error(`${candidatesInProposal.length} candidato(s) em etapa de Proposta devem ser finalizados antes de continuar.`)
      return
    }

    if (notifyApplicants && onNavigateToJobWithCommunication) {
      handleSubmitAndNavigate()
    } else if (notifyApplicants) {
      setCurrentStep('communication')
    } else if (freezeJob) {
      handleSubmit()
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
        localStorage.setItem('pendingCommunicationAction', JSON.stringify(pendingAction))
        
        onClose()
        
        if (onNavigateToJobWithCommunication) {
          onNavigateToJobWithCommunication(jobs[0].id, pendingAction)
        }
      } else {
        onClose()
      }
    } catch (error) {
      console.error('Erro ao despublicar:', error)
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
      console.error('Erro ao despublicar:', error)
      toast.error('Erro ao processar. Tente novamente.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const getSuccessMessage = () => {
    const parts = ['Vaga(s) despublicada(s) com sucesso']
    if (freezeJob) parts.push('e status alterado para Paralisada')
    if (notifyApplicants) parts.push(`${selectedCandidateIds.size} candidato(s) notificado(s)`)
    return parts.join('. ') + '.'
  }

  const handleClose = () => {
    if (currentStep === 'complete') {
      onComplete?.()
    }
    onClose()
  }

  const getStepIndicator = () => {
    if (!notifyApplicants) return null

    const steps = [
      { id: 'unpublish', label: 'Despublicar', done: currentStep !== 'options' },
      { id: 'message', label: 'Enviar mensagem', done: currentStep === 'confirmation' || currentStep === 'complete' },
      { id: 'done', label: 'Processo finalizado', done: currentStep === 'complete' },
    ]

    return (
      <div className="flex items-center justify-center gap-1 mb-4 pb-3 border-b border-gray-200">
        {steps.map((step, index) => (
          <React.Fragment key={step.id}>
            <div className="flex items-center gap-1.5">
              <div className={cn(
                "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-medium",
                step.done 
                  ? "bg-gray-900 text-white" 
                  : currentStep === 'options' && index === 0 
                    ? "bg-gray-100 text-gray-900 border border-gray-900"
                    : currentStep === 'communication' && index === 1
                      ? "bg-gray-100 text-gray-900 border border-gray-900"
                      : currentStep === 'confirmation' && index === 1
                        ? "bg-gray-100 text-gray-900 border border-gray-900"
                        : "bg-gray-100 text-gray-500"
              )}>
                {step.done ? <Check className="w-3 h-3" /> : index + 1}
              </div>
              <span className={cn(
                "text-[11px] font-medium",
                step.done ? "text-gray-900" : "text-gray-600"
              )}>
                {step.label}
              </span>
            </div>
            {index < steps.length - 1 && (
              <ChevronRight className="w-3.5 h-3.5 text-gray-400 mx-1" />
            )}
          </React.Fragment>
        ))}
      </div>
    )
  }

  const renderOptionsStep = () => (
    <div className="space-y-4">
      <div>
        <h4 className="text-[11px] font-semibold text-gray-600 uppercase tracking-wide mb-2">
          Vagas Selecionadas
        </h4>
        <div className="max-h-[100px] overflow-y-auto space-y-1 bg-gray-50 rounded-md p-2 border border-gray-200">
          {jobs.map((job) => (
            <div key={job.id} className="flex items-center justify-between py-1.5 px-2 bg-white rounded-md border border-gray-200">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <Briefcase className="w-3.5 h-3.5 text-gray-600 flex-shrink-0" />
                <div className="flex items-center gap-1.5 min-w-0 flex-1">
                  {job.code && <span className="text-[10px] font-medium text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded-full flex-shrink-0">{job.code}</span>}
                  <span className="text-xs font-medium text-gray-950 truncate">{job.title}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-3 bg-gray-50 rounded-md p-3 border border-gray-200">
        <div className="flex items-center gap-2 text-gray-800 mb-2">
          <AlertTriangle className="w-3.5 h-3.5 text-gray-600" />
          <span className="text-[11px] font-semibold text-gray-950">Opções ao despublicar</span>
        </div>

        <div className="space-y-2">
          <div className="flex items-start gap-2">
            <Checkbox
              id="freezeJob"
              checked={freezeJob}
              onCheckedChange={(checked) => setFreezeJob(!!checked)}
              className="mt-0.5 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
            />
            <div className="flex-1">
              <Label htmlFor="freezeJob" className="text-[11px] font-medium text-gray-950 cursor-pointer flex items-center gap-1">
                <Snowflake className="w-3 h-3 text-gray-600" />
                Congelar vaga
              </Label>
              <p className="text-[10px] text-gray-600">Pausar temporariamente o processo seletivo (status → Paralisada)</p>
            </div>
          </div>

          {freezeJob && (
            <div className="ml-6 space-y-3 pt-2 pl-3 border-l-2 border-gray-300">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-[10px] text-gray-600 mb-1 block">Data início congelamento</Label>
                  <Input
                    type="date"
                    value={freezeStartDate}
                    onChange={(e) => setFreezeStartDate(e.target.value)}
                    className="h-8 text-[11px] border-gray-200"
                  />
                </div>
                <div>
                  <Label className="text-[10px] text-gray-600 mb-1 block">
                    Previsão descongelamento
                    <span className="text-gray-400 ml-1">(opcional)</span>
                  </Label>
                  <Input
                    type="date"
                    value={unfreezeDate}
                    onChange={(e) => setUnfreezeDate(e.target.value)}
                    min={freezeStartDate || new Date().toISOString().split('T')[0]}
                    className="h-8 text-[11px] border-gray-200"
                  />
                </div>
              </div>

              <div>
                <Label className="text-[10px] text-gray-600 mb-1 block">Motivo do congelamento</Label>
                <Select value={freezeReason} onValueChange={setFreezeReason}>
                  <SelectTrigger className="h-8 text-[11px] border-gray-200">
                    <SelectValue placeholder="Selecione um motivo..." />
                  </SelectTrigger>
                  <SelectContent>
                    {FREEZE_REASONS.map((reason) => (
                      <SelectItem key={reason.value} value={reason.value} className="text-[11px]">
                        {reason.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-gray-200 pt-3">
          <div className="flex items-start gap-2">
            <Checkbox
              id="notifyApplicants"
              checked={notifyApplicants}
              onCheckedChange={(checked) => setNotifyApplicants(!!checked)}
              className="mt-0.5 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
            />
            <div className="flex-1">
              <Label htmlFor="notifyApplicants" className="text-[11px] font-medium text-gray-950 cursor-pointer flex items-center gap-1">
                <Bell className="w-3 h-3 text-gray-600" />
                Notificar candidatos
              </Label>
              <p className="text-[10px] text-gray-600">
                Todos os candidatos do processo receberão uma mensagem
              </p>
              {notifyApplicants && (
                <p className="text-[10px] text-gray-500 mt-1 flex items-center gap-1">
                  <Archive className="w-3 h-3" />
                  LIA abrirá o modal de envio por email/WhatsApp com template sugerido
                </p>
              )}
            </div>
          </div>
        </div>

        {hasProposalBlock && (
          <div className="mt-3 p-2.5 bg-amber-50 border border-amber-200 rounded-md">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-[11px] font-medium text-amber-800">
                  {candidatesInProposal.length} candidato(s) em etapa de Proposta
                </p>
                <p className="text-[10px] text-amber-700 mt-0.5">
                  Finalize o status destes candidatos antes de despublicar a vaga:
                </p>
                <ul className="mt-1 space-y-0.5">
                  {candidatesInProposal.slice(0, 3).map(c => (
                    <li key={c.id} className="text-[10px] text-amber-700 flex items-center gap-1">
                      <span className="w-1 h-1 rounded-full bg-amber-500" />
                      {c.name}
                    </li>
                  ))}
                  {candidatesInProposal.length > 3 && (
                    <li className="text-[10px] text-amber-600 italic">
                      e mais {candidatesInProposal.length - 3}...
                    </li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )

  const renderCommunicationStep = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="flex gap-2">
          <Button
            type="button"
            size="sm"
            variant={notificationChannel === 'email' || notificationChannel === 'both' ? 'default' : 'outline'}
            onClick={() => setNotificationChannel(notificationChannel === 'whatsapp' ? 'email' : notificationChannel === 'email' ? 'both' : 'email')}
            className={cn(
              "h-7 px-2.5 text-[10px]",
              (notificationChannel === 'email' || notificationChannel === 'both') 
                ? "bg-gray-800 text-white" 
                : "border-gray-200 text-gray-600"
            )}
          >
            <Mail className="w-3 h-3 mr-1" />
            Email
          </Button>
          <Button
            type="button"
            size="sm"
            variant={notificationChannel === 'whatsapp' || notificationChannel === 'both' ? 'default' : 'outline'}
            onClick={() => setNotificationChannel(notificationChannel === 'email' ? 'whatsapp' : notificationChannel === 'whatsapp' ? 'both' : 'whatsapp')}
            className={cn(
              "h-7 px-2.5 text-[10px]",
              (notificationChannel === 'whatsapp' || notificationChannel === 'both') 
                ? "bg-green-600 text-white hover:bg-green-700" 
                : "border-gray-200 text-gray-600"
            )}
          >
            <MessageSquare className="w-3 h-3 mr-1" />
            WhatsApp
          </Button>
        </div>
      </div>

      <div>
        <Label className="text-[10px] text-gray-600 mb-1 block">Template de mensagem</Label>
        <Select value={selectedTemplateId} onValueChange={handleTemplateChange}>
          <SelectTrigger className="h-8 text-[11px] border-gray-200">
            <SelectValue placeholder="Selecione um template..." />
          </SelectTrigger>
          <SelectContent>
            {availableTemplates.map((template) => (
              <SelectItem key={template.id} value={template.id} className="text-[11px]">
                {template.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {notificationChannel !== 'whatsapp' && (
        <div>
          <Label className="text-[10px] text-gray-600 mb-1 block">Assunto</Label>
          <Input
            value={notificationSubject}
            onChange={(e) => setNotificationSubject(e.target.value)}
            placeholder="Assunto do email..."
            className="h-8 text-[11px] border-gray-200"
          />
        </div>
      )}

      <div>
        <Label className="text-[10px] text-gray-600 mb-1 block">Mensagem</Label>
        <Textarea
          value={notificationMessage}
          onChange={(e) => setNotificationMessage(e.target.value)}
          placeholder="Conteúdo da mensagem..."
          className="min-h-[100px] text-[11px] border-gray-200 resize-none"
        />
        <p className="text-[9px] text-gray-500 mt-1">
          Variáveis disponíveis: {'{{candidato_nome}}'}, {'{{vaga}}'}, {'{{empresa_nome}}'}
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <Label className="text-[10px] text-gray-600">
            Candidatos selecionados ({selectedCandidateIds.size}/{jobCandidates.length - candidatesInProposal.length})
          </Label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={selectAllCandidates}
              className="text-[10px] text-gray-600 hover:underline"
            >
              Selecionar todos
            </button>
            <button
              type="button"
              onClick={deselectAllCandidates}
              className="text-[10px] text-gray-500 hover:underline"
            >
              Limpar
            </button>
          </div>
        </div>
        <ScrollArea className="h-[120px] border border-gray-200 rounded-md p-2">
          {loadingCandidates ? (
            <div className="flex items-center justify-center h-full py-8">
              <Loader2 className="w-5 h-5 animate-spin text-gray-600" />
              <span className="ml-2 text-[11px] text-gray-500">Carregando candidatos...</span>
            </div>
          ) : jobCandidates.length === 0 ? (
            <div className="flex items-center justify-center h-full py-8">
              <Users className="w-4 h-4 text-gray-400 mr-2" />
              <span className="text-[11px] text-gray-500">Nenhum candidato encontrado</span>
            </div>
          ) : (
            <div className="space-y-1">
              {jobCandidates.filter(c => !candidatesInProposal.find(p => p.id === c.id)).map((candidate) => (
                <div
                  key={candidate.id}
                  className={cn(
                    "flex items-center gap-2 p-1.5 rounded-md cursor-pointer transition-colors",
                    selectedCandidateIds.has(candidate.id)
                      ? "bg-gray-100 border border-gray-900"
                      : "bg-white border border-gray-200 hover:border-gray-300"
                  )}
                  onClick={() => toggleCandidateSelection(candidate.id)}
                >
                  <Checkbox
                    checked={selectedCandidateIds.has(candidate.id)}
                    className="data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] font-medium text-gray-900 truncate">{candidate.name}</p>
                    <p className="text-[10px] text-gray-500">{candidate.email || candidate.phone || 'Sem contato'}</p>
                  </div>
                  <Badge className="text-[9px] px-1.5 py-0.5 bg-gray-100 text-gray-600 font-normal">
                    {candidate.stage}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </div>
  )

  const renderConfirmationStep = () => (
    <div className="space-y-4">
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-md">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-xs font-semibold text-amber-800">Confirmação de ações</h4>
            <p className="text-[11px] text-amber-700 mt-1">
              Ao confirmar, as seguintes ações serão executadas:
            </p>
            <ul className="mt-2 space-y-1.5">
              <li className="text-[11px] text-amber-700 flex items-center gap-2">
                <Check className="w-3.5 h-3.5 text-amber-600" />
                A vaga será despublicada dos job boards
              </li>
              <li className="text-[11px] text-amber-700 flex items-center gap-2">
                <Check className="w-3.5 h-3.5 text-amber-600" />
                Status alterado para "Paralisada"
              </li>
              <li className="text-[11px] text-amber-700 flex items-center gap-2">
                <Check className="w-3.5 h-3.5 text-amber-600" />
                {selectedCandidateIds.size} candidato(s) serão notificados via {notificationChannel === 'both' ? 'email e WhatsApp' : notificationChannel}
              </li>
              <li className="text-[11px] text-amber-700 flex items-center gap-2">
                <CalendarOff className="w-3.5 h-3.5 text-amber-600" />
                Entrevistas e triagens agendadas serão canceladas
              </li>
              <li className="text-[11px] text-amber-700 flex items-center gap-2">
                <Mail className="w-3.5 h-3.5 text-amber-600" />
                Você receberá um email com o resumo de todas as ações
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div className="flex items-start gap-2 p-3 bg-gray-50 rounded-md border border-gray-200">
        <Checkbox
          id="acknowledgeWarning"
          checked={acknowledgedWarning}
          onCheckedChange={(checked) => setAcknowledgedWarning(!!checked)}
          className="mt-0.5 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
        />
        <Label htmlFor="acknowledgeWarning" className="text-[11px] text-gray-700 cursor-pointer">
          Li e estou ciente de que todas as ações acima serão executadas e não podem ser desfeitas.
        </Label>
      </div>
    </div>
  )

  const renderCompleteStep = () => (
    <div className="py-6 text-center">
      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-100 flex items-center justify-center">
        <CheckCircle2 className="w-8 h-8 text-green-600" />
      </div>
      <h3 className="text-[14px] font-semibold text-gray-950 mb-2">Processo finalizado!</h3>
      <p className="text-xs text-gray-600 mb-4">
        A vaga foi despublicada e congelada com sucesso.
      </p>
      <div className="bg-gray-50 rounded-md p-3 border border-gray-200 text-left space-y-2">
        <div className="flex items-center gap-2 text-[11px] text-gray-700">
          <Check className="w-3.5 h-3.5 text-green-600" />
          <span>Vaga despublicada dos job boards</span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-gray-700">
          <Check className="w-3.5 h-3.5 text-green-600" />
          <span>Status alterado para "Paralisada"</span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-gray-700">
          <Check className="w-3.5 h-3.5 text-green-600" />
          <span>{selectedCandidateIds.size} candidatos notificados</span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-gray-700">
          <Check className="w-3.5 h-3.5 text-green-600" />
          <span>Agendamentos cancelados</span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-gray-700">
          <Mail className="w-3.5 h-3.5 text-gray-600" />
          <span>Resumo enviado para seu email</span>
        </div>
      </div>
    </div>
  )

  const getFooterButtons = () => {
    switch (currentStep) {
      case 'options':
        return (
          <>
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={isSubmitting}
              className="h-9 px-4 text-xs font-medium border-gray-200 text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </Button>
            <Button
              onClick={handleProceed}
              disabled={isSubmitting || hasProposalBlock || (freezeJob && !freezeReason)}
              className="h-9 px-4 text-xs font-medium bg-gray-800 hover:bg-gray-900 text-white"
            >
              {isSubmitting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
              ) : notifyApplicants ? (
                <ArrowRight className="w-3.5 h-3.5 mr-1.5" />
              ) : (
                <X className="w-3.5 h-3.5 mr-1.5" />
              )}
              {notifyApplicants ? 'Continuar' : 'Despublicar'}
            </Button>
          </>
        )

      case 'communication':
        return (
          <>
            <Button
              variant="outline"
              onClick={() => setCurrentStep('options')}
              disabled={isSubmitting}
              className="h-9 px-4 text-xs font-medium border-gray-200 text-gray-700 hover:bg-gray-50"
            >
              Voltar
            </Button>
            <Button
              onClick={handleCommunicationProceed}
              disabled={isSubmitting || selectedCandidateIds.size === 0 || !notificationMessage}
              className="h-9 px-4 text-xs font-medium bg-gray-800 hover:bg-gray-900 text-white"
            >
              {isSubmitting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
              ) : freezeJob ? (
                <ArrowRight className="w-3.5 h-3.5 mr-1.5" />
              ) : (
                <Send className="w-3.5 h-3.5 mr-1.5" />
              )}
              {freezeJob ? 'Revisar e Confirmar' : 'Enviar e Despublicar'}
            </Button>
          </>
        )

      case 'confirmation':
        return (
          <>
            <Button
              variant="outline"
              onClick={() => setCurrentStep('communication')}
              disabled={isSubmitting}
              className="h-9 px-4 text-xs font-medium border-gray-200 text-gray-700 hover:bg-gray-50"
            >
              Voltar
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={isSubmitting || !acknowledgedWarning}
              className="h-9 px-4 text-xs font-medium bg-gray-800 hover:bg-gray-900 text-white"
            >
              {isSubmitting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
              ) : (
                <Check className="w-3.5 h-3.5 mr-1.5" />
              )}
              Confirmar e Executar
            </Button>
          </>
        )

      case 'complete':
        return (
          <Button
            onClick={handleClose}
            className="h-9 px-4 text-xs font-medium bg-gray-800 hover:bg-gray-900 text-white"
          >
            <Check className="w-3.5 h-3.5 mr-1.5" />
            Concluir
          </Button>
        )
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="max-w-lg bg-white border border-gray-200">
        <DialogHeader className="pb-3 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-gray-100 flex items-center justify-center">
              {currentStep === 'complete' ? (
                <CheckCircle2 className="w-4 h-4 text-green-600" />
              ) : (
                <X className="w-4 h-4 text-gray-600" />
              )}
            </div>
            <div>
              <DialogTitle className="text-[14px] font-semibold text-gray-950">
                {currentStep === 'complete' ? 'Processo Finalizado' : 'Despublicar Vagas'}
              </DialogTitle>
              <p className="text-xs text-gray-600 mt-0.5">
                {jobs.length} vaga{jobs.length > 1 ? 's' : ''} selecionada{jobs.length > 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </DialogHeader>

        <div className="py-4">
          {getStepIndicator()}
          
          {currentStep === 'options' && renderOptionsStep()}
          {currentStep === 'communication' && renderCommunicationStep()}
          {currentStep === 'confirmation' && renderConfirmationStep()}
          {currentStep === 'complete' && renderCompleteStep()}
        </div>

        <DialogFooter className="border-t border-gray-200 pt-3 gap-2">
          {getFooterButtons()}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function replaceTemplateVariables(body: string, vacancyTitle: string): string {
  return body
    .replace(/\{\{candidato_nome\}\}/g, '{{candidato_nome}}')
    .replace(/\{\{vaga\}\}/g, vacancyTitle)
    .replace(/\{\{empresa_nome\}\}/g, 'Nossa Empresa')
    .replace(/\{\{recrutador_nome\}\}/g, 'Equipe de Recrutamento')
}
