"use client"

import { useState, useCallback, useMemo, useEffect } from 'react'

export interface WSIScore {
  overall?: number
  technical?: number
  behavioral?: number
  cultural?: number
}

export interface InterviewNote {
  stage: string
  interviewer?: string
  rating?: number
  strengths: string[]
  gaps: string[]
  recommendation?: string
  notes?: string
}

export interface LiaParecer {
  summary?: string
  strengths: string[]
  development_areas: string[]
  cultural_fit?: number
  recommendation?: string
}

export interface CandidateContext {
  id: string
  name: string
  email?: string
  phone?: string
  avatar?: string
  current_title?: string
  current_company?: string
  wsi_score?: WSIScore
  interview_notes?: InterviewNote[]
  lia_parecer?: LiaParecer
}

export interface JobContext {
  id: string
  title: string
  department?: string
  seniority?: string
  requirements?: string[]
  has_hired_candidate?: boolean
}

export interface TransitionAction {
  id: string
  name: string
  description: string
  recommended: boolean
  template_category?: string
}

export interface GeneratedMessage {
  subject?: string
  body: string
  isEdited: boolean
  originalBody: string
  ai_personalized?: boolean
  predicted_sub_status?: string
}

export interface SubStatusOption {
  code: string
  display_name: string
  category?: string
  is_default?: boolean
}

interface UseTransitionContextOptions {
  candidates: CandidateContext[]
  fromStage: string
  toStage: string
  jobContext: JobContext
  companyId?: string
}

interface UseTransitionContextReturn {
  availableActions: TransitionAction[]
  predictedSubStatuses: Record<string, string>
  predictionReasonings: Record<string, string>
  updateSubStatus: (candidateId: string, subStatus: string) => void
  messages: Record<string, GeneratedMessage>
  generateMessages: (personalized: boolean) => Promise<void>
  regenerateMessage: (candidateId: string) => Promise<void>
  updateMessage: (candidateId: string, body: string, subject?: string) => void
  isGenerating: boolean
  isPredicting: boolean
  error: string | null
  subStatusOptions: SubStatusOption[]
  selectedAction: TransitionAction | null
  setSelectedAction: (action: TransitionAction | null) => void
  channel: 'email' | 'whatsapp'
  setChannel: (channel: 'email' | 'whatsapp') => void
}

const API_BASE = '/api/backend-proxy'

async function fetchWithTimeout(url: string, options: RequestInit, timeout = 30000): Promise<Response> {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeout)
  try {
    const response = await fetch(url, { ...options, signal: controller.signal })
    clearTimeout(id)
    return response
  } catch (error) {
    clearTimeout(id)
    throw error
  }
}

export function useTransitionContext(options: UseTransitionContextOptions): UseTransitionContextReturn {
  const { candidates, fromStage, toStage, jobContext, companyId } = options
  
  const [predictedSubStatuses, setPredictedSubStatuses] = useState<Record<string, string>>({})
  const [predictionReasonings, setPredictionReasonings] = useState<Record<string, string>>({})
  const [messages, setMessages] = useState<Record<string, GeneratedMessage>>({})
  const [isGenerating, setIsGenerating] = useState(false)
  const [isPredicting, setIsPredicting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [subStatusOptions, setSubStatusOptions] = useState<SubStatusOption[]>([])
  const [selectedAction, setSelectedAction] = useState<TransitionAction | null>(null)
  const [channel, setChannel] = useState<'email' | 'whatsapp'>('email')
  
  const availableActions = useMemo(() => {
    return getAvailableActionsForTransition(fromStage, toStage)
  }, [fromStage, toStage])
  
  useEffect(() => {
    if (availableActions.length > 0) {
      const recommended = availableActions.find(a => a.recommended) || availableActions[0]
      setSelectedAction(recommended)
    }
  }, [availableActions])
  
  useEffect(() => {
    async function fetchSubStatusOptions() {
      try {
        const response = await fetchWithTimeout(
          `${API_BASE}/stage-automation/substatus-options/${toStage}`,
          { method: 'GET', headers: { 'Content-Type': 'application/json' } }
        )
        if (response.ok) {
          const data = await response.json()
          setSubStatusOptions(data.options || [])
        }
      } catch (err) {
        setSubStatusOptions(getDefaultSubStatusOptions(toStage))
      }
    }
    
    fetchSubStatusOptions()
  }, [toStage])
  
  useEffect(() => {
    async function predictAllBulk() {
      if (candidates.length === 0) return
      
      setIsPredicting(true)
      const predictions: Record<string, string> = {}
      const reasonings: Record<string, string> = {}
      
      try {
        const response = await fetchWithTimeout(
          `${API_BASE}/stage-automation/bulk-predict-substatus`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              candidates: candidates.map(c => ({
                id: c.id,
                name: c.name,
                email: c.email,
                phone: c.phone,
                current_title: c.current_title,
                current_company: c.current_company,
                wsi_score: c.wsi_score,
                interview_notes: c.interview_notes || [],
                lia_parecer: c.lia_parecer
              })),
              from_stage: fromStage,
              to_stage: toStage,
              job_context: jobContext
            })
          }
        )
        
        if (response.ok) {
          const data = await response.json()
          if (data.predictions && Array.isArray(data.predictions)) {
            for (const pred of data.predictions) {
              predictions[pred.candidate_id] = pred.predicted_substatus
              if (pred.reasoning) {
                reasonings[pred.candidate_id] = pred.reasoning
              }
            }
          }
        }
        
        for (const candidate of candidates) {
          if (!predictions[candidate.id]) {
            predictions[candidate.id] = getDefaultSubStatus(toStage)
          }
        }
        
        setPredictedSubStatuses(predictions)
        setPredictionReasonings(reasonings)
      } catch (err) {
        for (const candidate of candidates) {
          predictions[candidate.id] = getDefaultSubStatus(toStage)
        }
        setPredictedSubStatuses(predictions)
      } finally {
        setIsPredicting(false)
      }
    }

    async function predictAllOneByOne() {
      if (candidates.length === 0) return
      
      setIsPredicting(true)
      const predictions: Record<string, string> = {}
      
      try {
        for (const candidate of candidates) {
          try {
            const response = await fetchWithTimeout(
              `${API_BASE}/stage-automation/predict-substatus`,
              {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  candidate_context: {
                    id: candidate.id,
                    name: candidate.name,
                    email: candidate.email,
                    phone: candidate.phone,
                    current_title: candidate.current_title,
                    current_company: candidate.current_company,
                    wsi_score: candidate.wsi_score,
                    interview_notes: candidate.interview_notes || [],
                    lia_parecer: candidate.lia_parecer
                  },
                  from_stage: fromStage,
                  to_stage: toStage,
                  job_context: jobContext
                })
              }
            )
            
            if (response.ok) {
              const data = await response.json()
              predictions[candidate.id] = data.predicted_substatus
            } else {
              predictions[candidate.id] = getDefaultSubStatus(toStage)
            }
          } catch (err) {
            predictions[candidate.id] = getDefaultSubStatus(toStage)
          }
        }
        
        setPredictedSubStatuses(predictions)
      } finally {
        setIsPredicting(false)
      }
    }
    
    if (candidates.length > 1 && toStage === 'rejected') {
      predictAllBulk()
    } else {
      predictAllOneByOne()
    }
  }, [candidates, fromStage, toStage, jobContext])
  
  const generateMessages = useCallback(async (personalized: boolean) => {
    if (candidates.length === 0 || !selectedAction) return
    
    setIsGenerating(true)
    setError(null)
    const generated: Record<string, GeneratedMessage> = {}
    
    try {
      for (const candidate of candidates) {
        const subStatus = predictedSubStatuses[candidate.id] || getDefaultSubStatus(toStage)
        
        try {
          if (personalized) {
            const response = await fetchWithTimeout(
              `${API_BASE}/stage-automation/generate-message`,
              {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  candidate_context: {
                    id: candidate.id,
                    name: candidate.name,
                    email: candidate.email,
                    phone: candidate.phone,
                    current_title: candidate.current_title,
                    current_company: candidate.current_company,
                    wsi_score: candidate.wsi_score,
                    interview_notes: candidate.interview_notes || [],
                    lia_parecer: candidate.lia_parecer
                  },
                  job_context: jobContext,
                  to_stage: toStage,
                  substatus: subStatus,
                  message_type: selectedAction.template_category || 'feedback_construtivo',
                  channel: channel
                })
              },
              45000
            )
            
            if (response.ok) {
              const data = await response.json()
              generated[candidate.id] = {
                subject: data.subject,
                body: data.body,
                isEdited: false,
                originalBody: data.body,
                ai_personalized: data.ai_personalized ?? false,
                predicted_sub_status: data.predicted_sub_status ?? subStatus
              }
            } else {
              generated[candidate.id] = generateFallbackMessage(candidate, toStage, subStatus, jobContext, channel)
            }
          } else {
            generated[candidate.id] = generateFallbackMessage(candidate, toStage, subStatus, jobContext, channel)
          }
        } catch (err) {
          generated[candidate.id] = generateFallbackMessage(candidate, toStage, subStatus, jobContext, channel)
        }
      }
      
      setMessages(generated)
    } catch (err) {
      setError('Erro ao gerar mensagens')
    } finally {
      setIsGenerating(false)
    }
  }, [candidates, predictedSubStatuses, toStage, jobContext, selectedAction, channel])
  
  const regenerateMessage = useCallback(async (candidateId: string) => {
    const candidate = candidates.find(c => c.id === candidateId)
    if (!candidate || !selectedAction) return
    
    const currentMessage = messages[candidateId]
    const oldSubStatus = currentMessage ? getSubStatusFromMessage(currentMessage.originalBody) : ''
    const newSubStatus = predictedSubStatuses[candidateId] || getDefaultSubStatus(toStage)
    
    setIsGenerating(true)
    
    try {
      if (currentMessage && oldSubStatus !== newSubStatus) {
        const response = await fetchWithTimeout(
          `${API_BASE}/stage-automation/regenerate-for-substatus`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              original_message: currentMessage.originalBody,
              old_substatus: oldSubStatus || 'profile_not_aligned',
              new_substatus: newSubStatus,
              candidate_context: {
                id: candidate.id,
                name: candidate.name,
                email: candidate.email,
                phone: candidate.phone,
                current_title: candidate.current_title,
                wsi_score: candidate.wsi_score,
                interview_notes: candidate.interview_notes || [],
                lia_parecer: candidate.lia_parecer
              },
              job_context: jobContext,
              channel: channel
            })
          },
          45000
        )
        
        if (response.ok) {
          const data = await response.json()
          setMessages(prev => ({
            ...prev,
            [candidateId]: {
              subject: data.subject || prev[candidateId]?.subject,
              body: data.body,
              isEdited: false,
              originalBody: data.body
            }
          }))
          return
        }
      }
      
      const response = await fetchWithTimeout(
        `${API_BASE}/stage-automation/generate-message`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            candidate_context: {
              id: candidate.id,
              name: candidate.name,
              email: candidate.email,
              phone: candidate.phone,
              current_title: candidate.current_title,
              wsi_score: candidate.wsi_score,
              interview_notes: candidate.interview_notes || [],
              lia_parecer: candidate.lia_parecer
            },
            job_context: jobContext,
            to_stage: toStage,
            substatus: newSubStatus,
            message_type: selectedAction.template_category || 'feedback_construtivo',
            channel: channel
          })
        },
        45000
      )
      
      if (response.ok) {
        const data = await response.json()
        setMessages(prev => ({
          ...prev,
          [candidateId]: {
            subject: data.subject,
            body: data.body,
            isEdited: false,
            originalBody: data.body
          }
        }))
      }
    } catch (err) {
    } finally {
      setIsGenerating(false)
    }
  }, [candidates, messages, predictedSubStatuses, toStage, jobContext, selectedAction, channel])
  
  const updateSubStatus = useCallback((candidateId: string, subStatus: string) => {
    setPredictedSubStatuses(prev => ({
      ...prev,
      [candidateId]: subStatus
    }))
    
    regenerateMessage(candidateId)
  }, [regenerateMessage])
  
  const updateMessage = useCallback((candidateId: string, body: string, subject?: string) => {
    setMessages(prev => ({
      ...prev,
      [candidateId]: {
        ...prev[candidateId],
        body,
        subject: subject !== undefined ? subject : prev[candidateId]?.subject,
        isEdited: body !== prev[candidateId]?.originalBody
      }
    }))
  }, [])
  
  return {
    availableActions,
    predictedSubStatuses,
    predictionReasonings,
    updateSubStatus,
    messages,
    generateMessages,
    regenerateMessage,
    updateMessage,
    isGenerating,
    isPredicting,
    error,
    subStatusOptions,
    selectedAction,
    setSelectedAction,
    channel,
    setChannel
  }
}

function getAvailableActionsForTransition(fromStage: string, toStage: string): TransitionAction[] {
  const actions: TransitionAction[] = []
  
  if (toStage === 'rejected') {
    actions.push({
      id: 'email',
      name: 'Enviar feedback por email',
      description: 'Comunicar resultado com feedback construtivo',
      recommended: true,
      template_category: 'feedback_construtivo'
    })
    actions.push({
      id: 'whatsapp',
      name: 'Enviar feedback por WhatsApp',
      description: 'Comunicação rápida via WhatsApp',
      recommended: false,
      template_category: 'feedback_construtivo'
    })
  } else if (toStage === 'screening' || fromStage === 'sourcing') {
    actions.push({
      id: 'triagem_wsi',
      name: 'Convidar para Triagem WSI',
      description: 'LIA irá conduzir a triagem automaticamente',
      recommended: true,
      template_category: 'convite_triagem'
    })
    actions.push({
      id: 'email',
      name: 'Enviar email de contato',
      description: 'Primeiro contato por email',
      recommended: false,
      template_category: 'contato_inicial'
    })
  } else if (toStage.includes('interview')) {
    actions.push({
      id: 'agendar_entrevista',
      name: 'Agendar entrevista',
      description: 'Enviar convite para agendamento',
      recommended: true,
      template_category: 'agendamento'
    })
    actions.push({
      id: 'email',
      name: 'Enviar convite por email',
      description: 'Email com detalhes da entrevista',
      recommended: false,
      template_category: 'agendamento'
    })
  } else if (toStage === 'offer') {
    actions.push({
      id: 'email',
      name: 'Enviar proposta por email',
      description: 'Proposta formal de contratação',
      recommended: true,
      template_category: 'proposta'
    })
  } else if (toStage === 'hired') {
    actions.push({
      id: 'email',
      name: 'Enviar boas-vindas',
      description: 'Email de boas-vindas e onboarding',
      recommended: true,
      template_category: 'boas_vindas'
    })
  } else if (toStage === 'long_list' || toStage === 'short_list') {
    actions.push({
      id: 'email',
      name: 'Enviar email de aprovação',
      description: 'Comunicar avanço no processo',
      recommended: false,
      template_category: 'aprovacao'
    })
  } else {
    actions.push({
      id: 'email',
      name: 'Enviar email',
      description: 'Comunicar atualização',
      recommended: false,
      template_category: 'follow_up'
    })
  }
  
  actions.push({
    id: 'apenas_mover',
    name: 'Apenas mover',
    description: 'Mover sem enviar comunicação',
    recommended: false,
    template_category: undefined
  })
  
  return actions
}

function getDefaultSubStatus(stage: string): string {
  const defaults: Record<string, string> = {
    rejected: 'profile_not_aligned',
    screening: 'cv_received',
    long_list: 'added_to_long_list',
    short_list: 'added_to_short_list',
    interview_hr: 'awaiting_hr_schedule',
    interview_technical: 'awaiting_technical_schedule',
    interview_manager: 'awaiting_manager1_schedule',
    interview_final: 'awaiting_final_schedule',
    offer: 'preparing_offer',
    hired: 'onboarding_scheduled',
    offer_declined: 'accepted_other_offer'
  }
  return defaults[stage] || 'in_progress'
}

function getDefaultSubStatusOptions(stage: string): SubStatusOption[] {
  if (stage === 'rejected') {
    return [
      { code: 'another_candidate_selected', display_name: 'Outro candidato selecionado' },
      { code: 'insufficient_technical_skills', display_name: 'Competências técnicas insuficientes' },
      { code: 'cultural_fit', display_name: 'Fit cultural' },
      { code: 'profile_not_aligned', display_name: 'Perfil não alinhado' },
      { code: 'overqualified', display_name: 'Superqualificado' },
      { code: 'underqualified', display_name: 'Experiência insuficiente' },
      { code: 'salary_expectation', display_name: 'Expectativa salarial incompatível' },
      { code: 'manager_decision', display_name: 'Decisão do gestor' },
      { code: 'candidate_withdrew', display_name: 'Candidato desistiu' }
    ]
  }
  return []
}

function generateFallbackMessage(
  candidate: CandidateContext,
  toStage: string,
  subStatus: string,
  jobContext: JobContext,
  channel: string
): GeneratedMessage {
  const firstName = candidate.name?.split(' ')[0] || 'Candidato'
  const jobTitle = jobContext.title || 'a vaga'
  
  let body: string
  
  if (toStage === 'rejected') {
    body = `Olá ${firstName},

Agradecemos muito sua participação em nosso processo seletivo para ${jobTitle}.

Após análise cuidadosa, decidimos seguir com outros candidatos cujos perfis estão mais alinhados com as necessidades atuais da posição.

Mantemos seu currículo em nosso banco de talentos para futuras oportunidades que possam ser compatíveis com seu perfil.

Desejamos sucesso em sua carreira!

Atenciosamente,
Equipe de Recrutamento`
  } else if (toStage === 'screening') {
    body = `Olá ${firstName},

Ficamos muito felizes com seu interesse em nossa vaga de ${jobTitle}!

Gostaríamos de convidá-lo(a) para a próxima etapa: uma triagem rápida com a nossa assistente LIA.

📋 Sobre a triagem:
• Duração estimada: 15-20 minutos
• Formato: Conversa por chat
• Objetivo: Conhecer melhor sua forma de pensar

Em breve enviaremos o link para iniciar.

Atenciosamente,
Equipe de Recrutamento`
  } else if (toStage.includes('interview')) {
    body = `Olá ${firstName},

Parabéns por avançar em nosso processo seletivo para ${jobTitle}! 🎉

Gostaríamos de convidá-lo(a) para a próxima etapa: uma entrevista.

Em breve entraremos em contato com os detalhes do agendamento.

Atenciosamente,
Equipe de Recrutamento`
  } else {
    body = `Olá ${firstName},

Gostaríamos de informá-lo(a) sobre uma atualização em sua candidatura para ${jobTitle}.

Em breve entraremos em contato com mais detalhes.

Atenciosamente,
Equipe de Recrutamento`
  }
  
  return {
    subject: channel === 'email' ? `Retorno sobre sua candidatura - ${jobTitle}` : undefined,
    body,
    isEdited: false,
    originalBody: body
  }
}

function getSubStatusFromMessage(message: string): string {
  return 'profile_not_aligned'
}
