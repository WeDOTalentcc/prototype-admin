"use client"

import React, { useState, useEffect, useCallback } from "react"
import { createPortal } from "react-dom"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Mail, Phone, MessageSquare, Calendar, Send, Copy,
  X, Check, Clock, User, Briefcase, Video, AlertCircle,
  RefreshCw, Eye, ChevronRight, Building,
  Globe, FileText, Users, Link2, ExternalLink, CalendarDays,
  CheckCircle, Info, Download
} from "lucide-react"
import { liaApi } from "@/services/lia-api"
import { useToast } from "@/hooks/use-toast"
import { Switch } from "@/components/ui/switch"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { CommunicationTemplate, TemplateSituation } from '@/hooks/use-communication-templates'
import { MessageComposer } from '@/components/communication'

// Types
export type CommunicationType = 'email' | 'whatsapp' | 'triagem' | 'agendamento' | 'feedback'
export type CommunicationChannel = 'email' | 'whatsapp' | 'both'

interface Candidate {
  id: string
  name: string
  role: string
  email: string
  phone: string
  location?: string
  avatar?: string
  score?: number
  matchPercentage?: number
  skills?: string[]
}

interface UnifiedCommunicationModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Candidate | null
  type: CommunicationType
  jobTitle?: string
  onSend?: (data: CommunicationResult) => void
  /** Required: Company ID for multi-tenancy. Must come from auth context. */
  companyId: string
  /** Optional: List of selected candidates for bulk operations */
  selectedCandidates?: Array<{ id: string; name: string; email?: string; phone?: string; avatar?: string }>
  situation?: import('@/hooks/use-communication-templates').TemplateSituation
}

interface CommunicationResult {
  type: CommunicationType
  channel: CommunicationChannel
  message: string
  subject?: string
  recipient: string
  metadata?: any
}

interface Template {
  id: string
  name: string
  subject?: string
  message: string
  icon?: React.ReactNode
}

interface InterviewSettings {
  interviewType: 'funcional' | 'tecnica' | 'completa' | 'cultural'
  platform: 'zoom' | 'teams' | 'meet' | 'presencial'
  duration: string
  date: string
  time: string
  interviewer: string
}

interface JobVacancy {
  id: string
  title: string
  department?: string
  location?: string
  status?: string
}

const PIPELINE_STAGES = [
  { value: 'novo', label: 'Novo' },
  { value: 'triagem', label: 'Triagem' },
  { value: 'entrevista', label: 'Entrevista' },
  { value: 'avaliacao', label: 'Avaliação' },
  { value: 'oferta', label: 'Oferta' }
]

const interviewTypes = [
  { id: 'funcional', name: 'Funcional', description: 'Avaliação de competências da função', icon: Briefcase },
  { id: 'tecnica', name: 'Técnica', description: 'Avaliação de skills técnicos', icon: FileText },
  { id: 'completa', name: 'Completa', description: 'Avaliação abrangente', icon: Users },
  { id: 'cultural', name: 'Cultural', description: 'Fit cultural e valores', icon: Building }
]

const platforms = [
  { id: 'zoom', name: 'Zoom', icon: Video },
  { id: 'teams', name: 'Teams', icon: Users },
  { id: 'meet', name: 'Google Meet', icon: Video },
  { id: 'presencial', name: 'Presencial', icon: Building }
]

const interviewers = [
  'Ana Silva - Recrutadora Sênior',
  'Carlos Mendes - Tech Lead',
  'Marina Costa - Gerente de Produto',
  'Roberto Santos - RH'
]

export function UnifiedCommunicationModal({ 
  isOpen, 
  onClose, 
  candidate: propCandidate, 
  type,
  jobTitle,
  onSend,
  companyId,
  selectedCandidates = [],
  situation: explicitSituation
}: UnifiedCommunicationModalProps) {
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
  
  // Interview specific settings
  const [interviewSettings, setInterviewSettings] = useState<InterviewSettings>({
    interviewType: 'funcional',
    platform: 'zoom',
    duration: '60',
    date: '',
    time: '',
    interviewer: ''
  })
  
  // Vacancy linking states
  const [linkToVacancy, setLinkToVacancy] = useState(false)
  const [selectedVacancyId, setSelectedVacancyId] = useState<string | null>(null)
  const [selectedStage, setSelectedStage] = useState('triagem')
  const [vacancies, setVacancies] = useState<JobVacancy[]>([])
  const [isLoadingVacancies, setIsLoadingVacancies] = useState(false)
  // For WSI screening: link to vacancy only after candidate completes screening
  const [linkOnCompletionOnly, setLinkOnCompletionOnly] = useState(type === 'triagem')
  
  const { toast } = useToast()
  const roleOrJob = jobTitle || candidate?.role || 'a vaga'

  // Map CommunicationType to TemplateSituation for MessageComposer
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

  // Get title and description based on type
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

  // Handle template selection from MessageComposer
  const handleTemplateSelect = useCallback((template: CommunicationTemplate) => {
    setSelectedTemplate(template.id)
    setMessage(template.body)
    if (template.subject) {
      setSubject(template.subject)
    }
  }, [])

  // Load vacancies for vacancy linking feature
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
      console.error('Error loading vacancies:', error)
      setVacancies([])
    } finally {
      setIsLoadingVacancies(false)
    }
  }, [vacancies.length])

  // Load vacancies when toggle is activated
  useEffect(() => {
    if (linkToVacancy) {
      loadVacancies()
    }
  }, [linkToVacancy, loadVacancies])

  // Sync channel with communication type when modal opens
  useEffect(() => {
    if (isOpen) {
      // Set default channel based on communication type
      if (type === 'whatsapp') {
        setChannel('whatsapp')
      } else {
        // For other types (email, triagem, agendamento, feedback), default to email
        setChannel('email')
      }
      // Reset template selection to trigger re-selection with correct channel
      setSelectedTemplate('')
    }
  }, [isOpen, type])

  // Reset state when modal closes
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
  

  if (!isOpen || (!candidate && selectedCandidates.length === 0)) return null

  const safeCandidate = candidate!
  const modalInfo = getModalInfo()

  const handleSend = async () => {
    // Validação: se toggle ativo, exigir seleção de vaga
    if (linkToVacancy && !selectedVacancyId) {
      toast({
        title: "Selecione uma vaga",
        description: "Para vincular o(s) candidato(s), você precisa selecionar uma vaga.",
        variant: "destructive"
      })
      return
    }
    
    setIsSending(true)

    try {
      // Handle vacancy linking if enabled
      // For WSI screening with linkOnCompletionOnly, we don't link immediately
      const shouldLinkNow = linkToVacancy && selectedVacancyId && !(type === 'triagem' && linkOnCompletionOnly)
      
      if (shouldLinkNow) {
        try {
          // Get candidate IDs - support both individual and bulk mode
          const candidateIds = isBulkMode 
            ? selectedCandidates.map(c => c.id)
            : [safeCandidate.id]
          
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
            toast({
              title: "Candidato(s) vinculado(s) à vaga",
              description: `${candidateCount} candidato(s) adicionado(s) à vaga "${selectedVacancy?.title || 'selecionada'}"`,
            })
          } else {
            console.warn('Failed to add candidate(s) to vacancy')
          }
        } catch (error) {
          console.error('Error adding candidate(s) to vacancy:', error)
        }
      }

      const selectedVacancy = vacancies.find(v => v.id === selectedVacancyId)

      const sendEmail = async () => {
        const response = await fetch('/api/backend-proxy/communication/send-email', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'X-Company-ID': companyId
          },
          body: JSON.stringify({
            to_email: safeCandidate.email,
            to_name: safeCandidate.name,
            subject: subject,
            body_html: `<div style="font-family: Arial, sans-serif;">${message.replace(/\n/g, '<br>')}</div>`,
            body_text: message,
            candidate_id: safeCandidate.id,
            candidate_name: safeCandidate.name,
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
        return result
      }

      const sendWhatsApp = async () => {
        const response = await fetch('/api/backend-proxy/communication/send-whatsapp', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'X-Company-ID': companyId
          },
          body: JSON.stringify({
            to_phone: (safeCandidate.phone || '').replace(/\D/g, ''),
            message: message,
            candidate_id: safeCandidate.id,
            candidate_name: safeCandidate.name,
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
        return result
      }

      if (channel === 'email') {
        const result = await sendEmail()
        toast({
          title: result.mock ? "Email simulado!" : "Email enviado!",
          description: result.mock 
            ? `Modo desenvolvimento: email para ${safeCandidate.email} foi simulado com sucesso`
            : `Mensagem enviada para ${safeCandidate.email}`,
        })
      } else if (channel === 'whatsapp') {
        const result = await sendWhatsApp()
        toast({
          title: result.mock ? "WhatsApp simulado!" : "WhatsApp enviado!",
          description: result.mock 
            ? `Modo desenvolvimento: mensagem para ${safeCandidate.name} foi simulada com sucesso`
            : `Mensagem enviada para ${safeCandidate.name}`,
        })
      } else if (channel === 'both') {
        const emailResult = await sendEmail()
        const waResult = await sendWhatsApp()
        const isMock = emailResult.mock || waResult.mock
        toast({
          title: isMock ? "Mensagens simuladas!" : "Mensagens enviadas!",
          description: isMock 
            ? `Modo desenvolvimento: email e WhatsApp para ${safeCandidate.name} foram simulados com sucesso`
            : `Mensagem enviada por email e WhatsApp para ${safeCandidate.name}`,
        })
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
          metadata: type === 'agendamento' ? interviewSettings : undefined
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
        console.warn('Failed to log communication (non-blocking):', logError)
        toast({
          title: "Aviso",
          description: "Mensagem enviada, mas o registro do histórico falhou.",
          variant: "default"
        })
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
            // For WSI screening: flag to indicate linking should happen only after completion
            linkOnCompletionOnly: type === 'triagem' && linkOnCompletionOnly,
            pendingVacancyLink: type === 'triagem' && linkOnCompletionOnly
          } : {})
        }
      })

      onClose()
    } catch (error) {
      console.error('Error sending message:', error)
      toast({
        title: "Erro ao enviar",
        description: error instanceof Error ? error.message : 'Erro desconhecido',
        variant: "destructive"
      })
    } finally {
      setIsSending(false)
    }
  }

  const formatPreviewMessage = (text: string) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\[(.*?)\]/g, '<span class="text-gray-600 dark:text-gray-400 underline cursor-pointer">$1</span>')
      .replace(/•/g, '&bull;')
      .replace(/\n/g, '<br>')
  }

  const modalContent = (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-[1px] z-[9999] flex items-center justify-center p-4">
      <div 
        className={`${cardStyles.default} dark:bg-gray-900 dark:border-gray-700 rounded-md w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col`}
       
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center">
              <modalInfo.icon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h3 className={textStyles.title}>
                {modalInfo.title}
              </h3>
              <p className={textStyles.description}>
                {safeCandidate.name} • {safeCandidate.role || 'a vaga'}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 rounded-md text-gray-600 hover:text-gray-800 hover:bg-gray-100 transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Panel - Form */}
          <div className="w-1/2 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
            <div className="p-5 space-y-5">
              {/* Channel Selection */}
              <div>
                <h4 className={`${textStyles.label} mb-2`}>
                  Canal de Envio
                </h4>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => setChannel('email')}
                    className={`flex items-center gap-2 p-3 rounded-md border transition-all ${
                      channel === 'email'
                        ? 'border-gray-900 bg-gray-50 text-gray-900'
                        : 'border-gray-200 hover:border-gray-300 text-gray-800'
                    }`}
                    aria-label="Enviar por Email"
                  >
                    <Mail className="w-4 h-4" />
                    <div className="text-left">
                      <div className="text-xs font-medium">Email</div>
                      <div className="text-micro opacity-70 truncate max-w-[120px]">{safeCandidate.email}</div>
                    </div>
                  </button>
                  <button
                    onClick={() => setChannel('whatsapp')}
                    className={`flex items-center gap-2 p-3 rounded-md border transition-all ${
                      channel === 'whatsapp'
                        ? 'border-green-500 bg-green-50 text-green-600'
                        : 'border-gray-200 hover:border-gray-300 text-gray-800'
                    }`}
                    aria-label="Enviar por WhatsApp"
                  >
                    <MessageSquare className="w-4 h-4" />
                    <div className="text-left">
                      <div className="text-xs font-medium">WhatsApp</div>
                      <div className="text-micro opacity-70">{safeCandidate.phone}</div>
                    </div>
                  </button>
                  <button
                    onClick={() => setChannel('both')}
                    className={`flex items-center gap-2 p-3 rounded-md border transition-all ${
                      channel === 'both'
                        ? 'border-gray-900 bg-gray-50 text-gray-900'
                        : 'border-gray-200 hover:border-gray-300 text-gray-800'
                    }`}
                    aria-label="Enviar por Email e WhatsApp"
                  >
                    <div className="flex items-center -space-x-1">
                      <Mail className="w-3.5 h-3.5" />
                      <MessageSquare className="w-3.5 h-3.5" />
                    </div>
                    <div className="text-left">
                      <div className="text-xs font-medium">Ambos</div>
                      <div className="text-micro opacity-70">Email + WA</div>
                    </div>
                  </button>
                </div>
              </div>

              {/* Interview Settings (only for agendamento) */}
              {type === 'agendamento' && (
                <div className={`space-y-4 p-4 ${cardStyles.flat} dark:bg-gray-800 dark:border-gray-700`}>
                  <h4 className={`${textStyles.label} flex items-center gap-2`}>
                    <Calendar className="w-3.5 h-3.5 text-gray-600" />
                    Configurações da Entrevista
                  </h4>
                  
                  {/* Interview Type */}
                  <div>
                    <label className={`${textStyles.caption} font-medium mb-1.5 block`}>Tipo de Entrevista</label>
                    <div className="grid grid-cols-2 gap-2">
                      {interviewTypes.map((iType) => (
                        <button
                          key={iType.id}
                          onClick={() => setInterviewSettings(prev => ({ ...prev, interviewType: iType.id as any }))}
                          className={`p-2 rounded-md border text-left transition-all ${
                            interviewSettings.interviewType === iType.id
                              ? 'border-gray-900 bg-gray-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <iType.icon className={`w-3.5 h-3.5 mb-1 ${
                            interviewSettings.interviewType === iType.id ? 'text-gray-900' : 'text-gray-600'
                          }`} />
                          <div className="text-micro font-medium text-gray-800">{iType.name}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Platform */}
                  <div>
                    <label className={`${textStyles.caption} font-medium mb-1.5 block`}>Plataforma</label>
                    <div className="grid grid-cols-4 gap-2">
                      {platforms.map((plat) => (
                        <button
                          key={plat.id}
                          onClick={() => setInterviewSettings(prev => ({ ...prev, platform: plat.id as any }))}
                          className={`p-2 rounded-md border text-center transition-all ${
                            interviewSettings.platform === plat.id
                              ? 'border-gray-900 bg-gray-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <plat.icon className={`w-3.5 h-3.5 mx-auto mb-1 ${
                            interviewSettings.platform === plat.id ? 'text-gray-900' : 'text-gray-600'
                          }`} />
                          <div className="text-micro text-gray-800">{plat.name}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Duration, Date, Time */}
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className={`${textStyles.caption} font-medium mb-1 block`}>Duração</label>
                      <select
                        value={interviewSettings.duration}
                        onChange={(e) => setInterviewSettings(prev => ({ ...prev, duration: e.target.value }))}
                        className="w-full h-9 text-xs border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-100/20"
                      >
                        <option value="30">30 min</option>
                        <option value="45">45 min</option>
                        <option value="60">1 hora</option>
                        <option value="90">1h 30min</option>
                      </select>
                    </div>
                    <div>
                      <label className={`${textStyles.caption} font-medium mb-1 block`}>Data</label>
                      <input
                        type="date"
                        value={interviewSettings.date}
                        onChange={(e) => setInterviewSettings(prev => ({ ...prev, date: e.target.value }))}
                        min={new Date().toISOString().split('T')[0]}
                        className="w-full h-9 text-xs border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-100/20"
                      />
                    </div>
                    <div>
                      <label className={`${textStyles.caption} font-medium mb-1 block`}>Horário</label>
                      <input
                        type="time"
                        value={interviewSettings.time}
                        onChange={(e) => setInterviewSettings(prev => ({ ...prev, time: e.target.value }))}
                        className="w-full h-9 text-xs border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-100/20"
                      />
                    </div>
                  </div>

                  {/* Interviewer */}
                  <div>
                    <label className={`${textStyles.caption} font-medium mb-1 block`}>Entrevistador</label>
                    <select
                      value={interviewSettings.interviewer}
                      onChange={(e) => setInterviewSettings(prev => ({ ...prev, interviewer: e.target.value }))}
                      className="w-full h-9 text-xs border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-100/20"
                    >
                      <option value="">Selecione...</option>
                      {interviewers.map((person) => (
                        <option key={person} value={person}>{person}</option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {/* MessageComposer - Templates, LIA Adjust, Subject, Message, Variables */}
              <MessageComposer
                channel={channel === 'both' ? 'email' : channel}
                situation={getSituationForType(type)}
                initialSubject={subject}
                initialMessage={message}
                onSubjectChange={setSubject}
                onMessageChange={setMessage}
                onTemplateSelect={handleTemplateSelect}
                showTemplateSelector={true}
                showLiaAdjust={true}
                showVariableSelector={true}
                candidateContext={{
                  name: safeCandidate.name,
                  role: safeCandidate.role,
                  location: safeCandidate.location,
                  skills: safeCandidate.skills
                }}
                jobContext={{
                  title: jobTitle || roleOrJob
                }}
              />

              {/* Vacancy Linking Section */}
              <div className={`${cardStyles.default} dark:bg-gray-800 dark:border-gray-700 p-4`}>
                <div className="flex items-center justify-between mb-3">
                  <h4 className={`${textStyles.label} flex items-center gap-2`}>
                    <Briefcase className="w-4 h-4 text-gray-600" />
                    Vincular à Vaga
                  </h4>
                  <Switch
                    checked={linkToVacancy}
                    onCheckedChange={setLinkToVacancy}
                  />
                </div>
                
                {linkToVacancy && (
                  <div className="space-y-3">
                    {/* Vacancy Selection */}
                    <div>
                      <label className={`${textStyles.caption} font-medium mb-1.5 block`}>
                        Selecionar Vaga
                      </label>
                      <select
                        value={selectedVacancyId || ''}
                        onChange={(e) => setSelectedVacancyId(e.target.value || null)}
                        disabled={isLoadingVacancies}
                        className="w-full h-9 text-xs border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-100/20 bg-white disabled:bg-gray-100 disabled:cursor-not-allowed"
                      >
                        <option value="">
                          {isLoadingVacancies ? 'Carregando vagas...' : 'Selecione uma vaga'}
                        </option>
                        {vacancies.map((vacancy) => (
                          <option key={vacancy.id} value={vacancy.id}>
                            {vacancy.title}
                            {vacancy.department ? ` - ${vacancy.department}` : ''}
                            {vacancy.status ? ` (${vacancy.status})` : ''}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    {/* Pipeline Stage Selection */}
                    <div>
                      <label className={`${textStyles.caption} font-medium mb-1.5 block`}>
                        Etapa do Pipeline
                      </label>
                      <select
                        value={selectedStage}
                        onChange={(e) => setSelectedStage(e.target.value)}
                        className="w-full h-9 text-xs border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-100/20 bg-white"
                      >
                        {PIPELINE_STAGES.map((stage) => (
                          <option key={stage.value} value={stage.value}>
                            {stage.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    {/* WSI Screening - Link on Completion Option */}
                    {type === 'triagem' && (
                      <div className="bg-amber-50 border border-amber-200 rounded-md p-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Clock className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                            <div>
                              <span className="text-xs font-medium text-amber-800">
                                Vincular após completar triagem
                              </span>
                              <p className="text-micro text-amber-600 mt-0.5">
                                Candidato só entra na vaga se responder a triagem
                              </p>
                            </div>
                          </div>
                          <Switch
                            checked={linkOnCompletionOnly}
                            onCheckedChange={setLinkOnCompletionOnly}
                          />
                        </div>
                      </div>
                    )}
                    
                    {/* Confirmation Message */}
                    {selectedVacancyId && (
                      <div className={`${type === 'triagem' && linkOnCompletionOnly ? 'bg-amber-50 border-amber-200' : 'bg-green-50 border-green-200'} border rounded-md p-2.5`}>
                        <div className="flex items-center gap-2">
                          {type === 'triagem' && linkOnCompletionOnly ? (
                            <Clock className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
                          ) : (
                            <CheckCircle className="w-3.5 h-3.5 text-green-600 flex-shrink-0" />
                          )}
                          <span className={`text-micro ${type === 'triagem' && linkOnCompletionOnly ? 'text-amber-700' : 'text-green-700'}`}>
                            {type === 'triagem' && linkOnCompletionOnly ? (
                              isBulkMode 
                                ? `${selectedCandidates.length} candidato(s) serão vinculados à vaga "${PIPELINE_STAGES.find(s => s.value === selectedStage)?.label}" somente após completarem a triagem`
                                : `Candidato será vinculado à vaga na etapa "${PIPELINE_STAGES.find(s => s.value === selectedStage)?.label}" somente após completar a triagem`
                            ) : (
                              isBulkMode 
                                ? `${selectedCandidates.length} candidato(s) serão vinculados à vaga selecionada na etapa "${PIPELINE_STAGES.find(s => s.value === selectedStage)?.label}"`
                                : `Candidato será vinculado à vaga selecionada na etapa "${PIPELINE_STAGES.find(s => s.value === selectedStage)?.label}"`
                            )}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Panel - Preview */}
          <div className="w-1/2 bg-gray-50 overflow-y-auto">
            <div className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h4 className={`${textStyles.label} flex items-center gap-2`}>
                  <Eye className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                  Preview da Mensagem
                </h4>
                <Badge variant="outline" className={badgeStyles.default}>
                  {channel === 'email' ? 'Email' : channel === 'whatsapp' ? 'WhatsApp' : 'Email + WhatsApp'}
                </Badge>
              </div>

              {/* Preview Card */}
              <div className={`rounded-md overflow-hidden ${
                channel === 'whatsapp' ? 'bg-[#e5ddd5]' : 'bg-white border border-gray-200'
              }`}>
                {(channel === 'email' || channel === 'both') ? (
                  <div>
                    {/* Email Header */}
                    <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                      <div className="flex items-center gap-2 mb-2">
                        <Avatar className="h-8 w-8">
                          <AvatarFallback className="text-micro bg-gray-900 dark:bg-gray-50 text-white">RH</AvatarFallback>
                        </Avatar>
                        <div>
                          <div className={textStyles.bodySmall}>Equipe de Recrutamento</div>
                          <div className={textStyles.caption}>recrutamento@empresa.com</div>
                        </div>
                      </div>
                      <div className={textStyles.caption}>
                        Para: <span className="text-gray-800">{safeCandidate.email}</span>
                      </div>
                    </div>
                    {/* Email Subject */}
                    <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                      <div className={textStyles.subtitle}>
                        {subject || 'Sem assunto'}
                      </div>
                    </div>
                    {/* Email Body */}
                    <div className="px-4 py-4">
                      <div 
                        className={`${textStyles.body} leading-relaxed`}
                        dangerouslySetInnerHTML={{ __html: formatPreviewMessage(message) || '<span class="text-gray-600">A mensagem aparecerá aqui...</span>' }}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="p-3">
                    {/* WhatsApp Chat Bubble */}
                    <div className="flex justify-end mb-2">
                      <div className="bg-[#dcf8c6] rounded-md p-3 max-w-[85%]">
                        <div 
                          className={`${textStyles.body} leading-relaxed whitespace-pre-wrap`}
                          dangerouslySetInnerHTML={{ __html: formatPreviewMessage(message) || '<span class="text-gray-600">A mensagem aparecerá aqui...</span>' }}
                        />
                        <div className={`${textStyles.caption} text-right mt-1`}>
                          {new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} ✓✓
                        </div>
                      </div>
                    </div>
                    {/* WhatsApp Info */}
                    <div className={`text-center ${textStyles.caption} mt-3 bg-white/60 rounded-full py-1 px-3 inline-block mx-auto`}>
                      Será enviado via WhatsApp Business API
                    </div>
                  </div>
                )}
              </div>

              {/* Additional Info based on type */}
              {type === 'triagem' && (
                <div className="mt-4 bg-amber-50 border border-amber-200 rounded-md p-3">
                  <div className="flex items-start gap-2">
                    <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div className="text-micro text-amber-700">
                      <strong>Fluxo de Triagem:</strong>
                      <ul className="mt-1 space-y-0.5 ml-2">
                        <li>• Candidato recebe a mensagem com link</li>
                        <li>• Ao clicar, visualiza aviso LGPD e aceita termos</li>
                        <li>• LIA inicia a conversa de triagem automaticamente</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {type === 'agendamento' && (
                <div className="mt-4 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md p-3">
                  <div className="flex items-start gap-2">
                    <CalendarDays className="w-4 h-4 text-gray-600 dark:text-gray-400 flex-shrink-0 mt-0.5" />
                    <div className="text-micro text-wedo-cyan-dark">
                      <strong>Após Confirmação:</strong>
                      <ul className="mt-1 space-y-0.5 ml-2">
                        <li>• Candidato escolhe horário disponível</li>
                        <li>• Recebe email de confirmação automático</li>
                        <li>• Convite de calendário (Outlook/Google)</li>
                        <li>• Link da plataforma de vídeo incluso</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {type === 'feedback' && (
                <div className="mt-4 bg-green-50 border border-green-200 rounded-md p-3">
                  <div className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                    <div className="text-micro text-green-700">
                      <strong>Dica:</strong> Um feedback bem estruturado fortalece a marca empregadora e mantém bom relacionamento com candidatos.
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 dark:bg-gray-900 dark:border-gray-700 flex items-center justify-between">
          <div className={textStyles.caption}>
            {channel === 'email' && (
              <span className="flex items-center gap-1">
                <Mail className="w-3 h-3" />
                Email será enviado via sistema
              </span>
            )}
            {channel === 'whatsapp' && (
              <span className="flex items-center gap-1">
                <MessageSquare className="w-3 h-3" />
                WhatsApp será enviado via sistema
              </span>
            )}
            {channel === 'both' && (
              <span className="flex items-center gap-1">
                <Mail className="w-3 h-3" />
                <MessageSquare className="w-3 h-3" />
                Email e WhatsApp serão enviados via sistema
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              className="h-9 px-4 text-xs font-medium bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 dark:text-gray-200"
            >
              Cancelar
            </Button>
            <Button
              size="sm"
              onClick={handleSend}
              disabled={isSending || !message.trim() || ((channel === 'email' || channel === 'both') && !subject.trim())}
              className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 gap-2"
            >
              {isSending ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Enviando...
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  {channel === 'email' ? 'Enviar Email' : channel === 'whatsapp' ? 'Enviar WhatsApp' : 'Enviar Ambos'}
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )

  if (typeof document === 'undefined') return null
  
  return createPortal(modalContent, document.body)
}

export default UnifiedCommunicationModal
