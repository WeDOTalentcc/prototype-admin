"use client"

import { useState, useEffect, useCallback } from "react"
import {
  Mail, MessageSquare, FileText, Calendar, CheckCircle
} from "lucide-react"
import { liaApi } from "@/services/lia-api"
import { CommunicationTemplate, TemplateSituation } from '@/hooks/chat/use-communication-templates'
import { toast } from "sonner"
import { useModalA11y } from "@/hooks/ui/use-modal-a11y"
import { runBulkSequential } from '@/lib/bulk'
import { useFailedDeliveryStore } from '@/stores/failedDeliveryStore'
import type {
  CommunicationType,
  CommunicationChannel,
  CommunicationResult,
  Candidate,
  InterviewSettings,
  JobVacancy
} from "./unified-communication-types"

interface UseUnifiedCommunicationParams {
  isOpen: boolean
  onClose: () => void
  propCandidate: Candidate | null
  type: CommunicationType
  jobTitle?: string
  onSend?: (data: CommunicationResult) => void
  companyId: string
  selectedCandidates: Array<{ id: string; name: string; email?: string; phone?: string; avatar?: string }>
  explicitSituation?: TemplateSituation
  aiFeedbackContext?: { vacancyCandidateId: string; toStage: string; subStatus?: string | null } | null
}

export function useUnifiedCommunication({
  isOpen,
  onClose,
  propCandidate,
  type,
  jobTitle,
  onSend,
  companyId,
  selectedCandidates,
  explicitSituation,
  aiFeedbackContext
}: UseUnifiedCommunicationParams) {
  const isBulkMode = !propCandidate && selectedCandidates.length > 0

  const candidate: Candidate | null = propCandidate || (isBulkMode ? {
    id: 'bulk',
    name: `${selectedCandidates.length} candidato${selectedCandidates.length > 1 ? 's' : ''}`,
    role: '',
    email: selectedCandidates[0]?.email || '',
    phone: selectedCandidates[0]?.phone || ''
  } : null)

  const [channel, setChannel] = useState<CommunicationChannel>('email')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [isSending, setIsSending] = useState(false)
  const [isGeneratingAi, setIsGeneratingAi] = useState(false)
  const [aiFeedbackMeta, setAiFeedbackMeta] = useState<{ highRisk: boolean; fairnessBlocked: boolean; usesTemplateOnly: boolean; aiPersonalized: boolean; generatedBy: string } | null>(null)

  const [interviewSettings, setInterviewSettings] = useState<InterviewSettings>({
    interviewType: 'funcional',
    platform: 'zoom',
    duration: '60',
    date: '',
    time: '',
    interviewer: ''
  })

  const [linkToVacancy, setLinkToVacancy] = useState(false)
  const [selectedVacancyId, setSelectedVacancyId] = useState<string | null>(null)
  const [selectedStage, setSelectedStage] = useState('triagem')
  const [vacancies, setVacancies] = useState<JobVacancy[]>([])
  const [isLoadingVacancies, setIsLoadingVacancies] = useState(false)
  const [linkOnCompletionOnly, setLinkOnCompletionOnly] = useState(type === 'triagem')

  const roleOrJob = jobTitle || candidate?.role || 'a vaga'

  const getSituationForType = useCallback((communicationType: CommunicationType): TemplateSituation | undefined => {
    if (explicitSituation) return explicitSituation
    switch (communicationType) {
      case 'triagem':
        return 'triagem'
      case 'agendamento':
        return 'agendamento'
      case 'feedback':
        return 'feedback_positivo'
      default:
        return undefined
    }
  }, [explicitSituation])

  const getModalInfo = () => {
    switch (type) {
      case 'email':
        return { title: 'Enviar Email', description: 'Envie uma mensagem por email', icon: Mail }
      case 'whatsapp':
        return { title: 'Enviar WhatsApp', description: 'Envie uma mensagem pelo WhatsApp', icon: MessageSquare }
      case 'triagem':
        return { title: 'Convidar para Triagem', description: 'Convide o candidato para a triagem com a LIA', icon: FileText }
      case 'agendamento':
        return { title: 'Agendar Entrevista', description: 'Envie convite para agendar entrevista', icon: Calendar }
      case 'feedback':
        return { title: 'Enviar Feedback', description: 'Envie feedback sobre o processo seletivo', icon: CheckCircle }
      default:
        return { title: 'Comunicação', description: '', icon: Mail }
    }
  }

  const handleTemplateSelect = useCallback((template: CommunicationTemplate) => {
    setSelectedTemplate(template.id)
    setMessage(template.body)
    if (template.subject) {
      setSubject(template.subject)
    }
  }, [])

  const loadVacancies = useCallback(async () => {
    if (vacancies.length > 0) return
    setIsLoadingVacancies(true)
    try {
      const response = await fetch('/api/backend-proxy/job-vacancies/')
      if (response.ok) {
        const data = await response.json()
        const vacancyList = data.vacancies || data.items || data || []
        setVacancies(Array.isArray(vacancyList) ? vacancyList : [])
      }
    } catch (error) {
      setVacancies([])
    } finally {
      setIsLoadingVacancies(false)
    }
  }, [vacancies.length])

  useEffect(() => {
    if (linkToVacancy) {
      loadVacancies()
    }
  }, [linkToVacancy, loadVacancies])

  useEffect(() => {
    if (isOpen) {
      if (type === 'whatsapp') {
        setChannel('whatsapp')
      } else {
        setChannel('email')
      }
      setSelectedTemplate('')
    }
  }, [isOpen, type])

  useEffect(() => {
    if (!isOpen) {
      setSelectedTemplate('')
      setMessage('')
      setSubject('')
      setLinkToVacancy(false)
      setSelectedVacancyId(null)
      setSelectedStage('triagem')
    }
  }, [isOpen])

  const dialogRef = useModalA11y(isOpen, onClose)

  const handleSend = async () => {
    if (linkToVacancy && !selectedVacancyId) {
      toast.error("Selecione uma vaga", { description: "Para vincular o(s) candidato(s), você precisa selecionar uma vaga." })
      return
    }

    setIsSending(true)

    try {
      const shouldLinkNow = linkToVacancy && selectedVacancyId && !(type === 'triagem' && linkOnCompletionOnly)

      if (shouldLinkNow) {
        try {
          const candidateIds = isBulkMode
            ? selectedCandidates.map(c => c.id)
            : [candidate!.id]

          const response = await fetch(`/api/backend-proxy/search/vacancy/${selectedVacancyId}/add-candidates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              candidate_ids: candidateIds,
              stage: selectedStage
            })
          })

          if (response.ok) {
            const selectedVacancy = vacancies.find(v => v.id === selectedVacancyId)
            const candidateCount = isBulkMode ? selectedCandidates.length : 1
            toast.success("Candidato(s) vinculado(s) à vaga", { description: `${candidateCount} candidato(s) adicionado(s) à vaga "${selectedVacancy?.title || 'selecionada'}"` })
          }
        } catch (error) {
        }
      }

      const selectedVacancy = vacancies.find(v => v.id === selectedVacancyId)

      type CandidateRef = { id: string; name: string; email?: string; phone?: string }

      const sendEmailFor = async (c: CandidateRef) => {
        const response = await fetch('/api/backend-proxy/communication/send-email', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Company-ID': companyId
          },
          body: JSON.stringify({
            to_email: c.email,
            to_name: c.name,
            subject: subject,
            body_html: `<div style="font-family: Arial, sans-serif;">${message.replace(/\n/g, '<br>')}</div>`,
            body_text: message,
            candidate_id: c.id,
            candidate_name: c.name,
            vacancy_id: selectedVacancyId || undefined,
            vacancy_title: selectedVacancy?.title,
            communication_type: type,
            metadata: {
              source: 'unified_communication_modal',
              type: type,
              channel: 'email'
            }
          })
        })
        const result = await response.json()
        if (!response.ok || !result.success) {
          throw new Error(result.error || 'Falha ao enviar email')
        }
        return result as { mock?: boolean; success: boolean }
      }

      const sendWhatsAppFor = async (c: CandidateRef) => {
        const response = await fetch('/api/backend-proxy/communication/send-whatsapp', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Company-ID': companyId
          },
          body: JSON.stringify({
            to_phone: (c.phone || '').replace(/\D/g, ''),
            message: message,
            candidate_id: c.id,
            candidate_name: c.name,
            vacancy_id: selectedVacancyId || undefined,
            vacancy_title: selectedVacancy?.title,
            communication_type: type,
            metadata: {
              source: 'unified_communication_modal',
              type: type,
              channel: 'whatsapp'
            }
          })
        })
        const result = await response.json()
        if (!response.ok || !result.success) {
          throw new Error(result.error || 'Falha ao enviar WhatsApp')
        }
        return result as { mock?: boolean; success: boolean }
      }

      // ── BULK MODE ─────────────────────────────────────────────────────────
      if (isBulkMode) {
        const failureStore = useFailedDeliveryStore.getState()

        const allResults = await runBulkSequential(
          selectedCandidates,
          async (c) => {
            if (channel === 'email') return sendEmailFor(c)
            if (channel === 'whatsapp') return sendWhatsAppFor(c)
            if (channel === 'both') {
              await sendEmailFor(c)
              return sendWhatsAppFor(c)
            }
            throw new Error('Canal desconhecido')
          }
        )

        // Persist failures in Zustand store for ContactCells badge
        allResults.forEach(r => {
          if (!r.ok) {
            failureStore.addFailure({ candidateId: r.id, reason: r.reason ?? 'falha', channel, at: Date.now() })
          } else {
            failureStore.clearFailure(r.id)
          }
        })

        // Log communications for successful sends (fire-and-forget)
        for (const r of allResults.filter(x => x.ok)) {
          const c = selectedCandidates.find(sc => sc.id === r.id)
          if (!c) continue
          liaApi.logCommunication({
            company_id: companyId,
            candidate_id: c.id,
            candidate_name: c.name,
            candidate_email: c.email,
            candidate_phone: c.phone,
            communication_type: type,
            channel: channel === 'both' ? 'email' : channel,
            direction: 'outbound',
            subject: (channel === 'email' || channel === 'both') ? subject : undefined,
            message_content: message,
            sent_by: 'recruiter',
          }).catch(() => undefined)
        }

        onSend?.({ type, channel, message, bulkResults: allResults } as unknown as CommunicationResult)

      } else {
        // ── SINGLE MODE (comportamento existente, inalterado) ────────────────
        const safeCandidate = candidate!

        if (channel === 'email') {
          const result = await sendEmailFor(safeCandidate)
          toast.success(result.mock ? "Email simulado!" : "Email enviado!", { description: result.mock
              ? `Modo desenvolvimento: email para ${safeCandidate.email}`
              : `Email enviado para ${safeCandidate.email}` })
        } else if (channel === 'whatsapp') {
          const result = await sendWhatsAppFor(safeCandidate)
          toast.success(result.mock ? "WhatsApp simulado!" : "WhatsApp enviado!", { description: result.mock
              ? `Modo desenvolvimento: mensagem para ${safeCandidate.name}`
              : `WhatsApp enviado para ${safeCandidate.name}` })
        } else if (channel === 'both') {
          const emailResult = await sendEmailFor(safeCandidate)
          const waResult = await sendWhatsAppFor(safeCandidate)
          const isMock = emailResult.mock || waResult.mock
          toast.success(isMock ? "Mensagens simuladas!" : "Mensagens enviadas!", { description: isMock
              ? `Modo desenvolvimento: email e WhatsApp para ${safeCandidate.name}`
              : `Mensagens enviadas para ${safeCandidate.name}` })
        }

        try {
          await liaApi.logCommunication({
            company_id: companyId,
            candidate_id: safeCandidate.id,
            candidate_name: safeCandidate.name,
            candidate_email: safeCandidate.email,
            candidate_phone: safeCandidate.phone,
            communication_type: type,
            channel: channel === 'both' ? 'email' : channel,
            direction: 'outbound',
            subject: (channel === 'email' || channel === 'both') ? subject : undefined,
            message_content: message,
            sent_by: 'recruiter',
            metadata: type === 'agendamento' ? interviewSettings as unknown as Record<string, unknown> : undefined
          })

          const activityDescriptions: Record<CommunicationType, string> = {
            email: `Enviou email para ${safeCandidate.name}`,
            whatsapp: `Enviou WhatsApp para ${safeCandidate.name}`,
            triagem: `Convidou ${safeCandidate.name} para triagem`,
            agendamento: `Enviou convite de entrevista para ${safeCandidate.name}`,
            feedback: `Enviou feedback para ${safeCandidate.name}`
          }

          await liaApi.createActivity({
            company_id: companyId,
            activity_type: `communication_${type}`,
            description: activityDescriptions[type],
            candidate_id: safeCandidate.id,
            performed_by: 'recruiter',
            metadata: {
              channel,
              type,
              subject: (channel === 'email' || channel === 'both') ? subject : undefined
            }
          })
        } catch (logError) {
          toast.warning("Aviso", { description: "Mensagem enviada, mas o registro do histórico falhou." })
        }

        onSend?.({
          type,
          channel,
          message,
          subject: (channel === 'email' || channel === 'both') ? subject : undefined,
          recipient: (channel === 'email' || channel === 'both') ? safeCandidate.email : safeCandidate.phone,
          metadata: {
            ...(type === 'agendamento' ? interviewSettings : {}),
            ...(linkToVacancy && selectedVacancyId ? {
              vacancyId: selectedVacancyId,
              stage: selectedStage,
              linkOnCompletionOnly: type === 'triagem' && linkOnCompletionOnly,
              pendingVacancyLink: type === 'triagem' && linkOnCompletionOnly
            } : {})
          }
        } as CommunicationResult)
      }

      onClose()
    } catch (error) {
      toast.error("Erro ao enviar", { description: error instanceof Error ? error.message : 'Erro desconhecido' })
    } finally {
      setIsSending(false)
    }
  }

  const generateAiFeedback = useCallback(async () => {
    if (!aiFeedbackContext?.vacancyCandidateId) return
    setIsGeneratingAi(true)
    try {
      const resp = await fetch('/api/backend-proxy/transition/preview-feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vacancy_candidate_id: aiFeedbackContext.vacancyCandidateId,
          to_stage: aiFeedbackContext.toStage,
          sub_status: aiFeedbackContext.subStatus ?? null,
          channel: type === 'whatsapp' ? 'whatsapp' : 'email',
        }),
      })
      if (resp.ok) {
        const data = await resp.json()
        if (data.body) setMessage(data.body)
        if (data.subject) setSubject(data.subject)
        setAiFeedbackMeta({
          highRisk: !!data.high_risk,
          fairnessBlocked: !!data.fairness_blocked,
          usesTemplateOnly: !!data.uses_template_only,
          aiPersonalized: !!data.ai_personalized,
          generatedBy: data.generated_by || 'unknown',
        })
      }
    } catch {
      // fail-soft: recrutador escreve manualmente
    } finally {
      setIsGeneratingAi(false)
    }
  }, [aiFeedbackContext, type])

  // Ao abrir com contexto de feedback por IA, gera o texto uma vez (corpo vazio).
  useEffect(() => {
    if (isOpen && aiFeedbackContext?.vacancyCandidateId && !message) {
      generateAiFeedback()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, aiFeedbackContext?.vacancyCandidateId])

  return {
    isBulkMode,
    candidate,
    channel,
    setChannel,
    subject,
    setSubject,
    message,
    setMessage,
    selectedTemplate,
    isSending,
    interviewSettings,
    setInterviewSettings,
    linkToVacancy,
    setLinkToVacancy,
    selectedVacancyId,
    setSelectedVacancyId,
    selectedStage,
    setSelectedStage,
    vacancies,
    isLoadingVacancies,
    linkOnCompletionOnly,
    setLinkOnCompletionOnly,
    roleOrJob,
    getSituationForType,
    getModalInfo,
    handleTemplateSelect,
    handleSend,
    dialogRef,
    isGeneratingAi,
    regenerateAiFeedback: generateAiFeedback,
    aiFeedbackMeta
  }
}
