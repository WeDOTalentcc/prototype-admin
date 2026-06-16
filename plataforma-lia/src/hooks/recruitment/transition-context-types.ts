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

export interface UseTransitionContextOptions {
  candidates: CandidateContext[]
  fromStage: string
  toStage: string
  jobContext: JobContext
  companyId?: string
}

export interface UseTransitionContextReturn {
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

export const TRANSITION_API_BASE = '/api/backend-proxy'

export async function fetchWithTimeoutTransition(url: string, options: RequestInit, timeout = 30000): Promise<Response> {
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

export function getAvailableActionsForTransition(fromStage: string, toStage: string): TransitionAction[] {
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
      description: 'Comunica\u00e7\u00e3o r\u00e1pida via WhatsApp',
      recommended: false,
      template_category: 'feedback_construtivo'
    })
  } else if (toStage === 'screening' || fromStage === 'sourcing') {
    actions.push({
      id: 'triagem_wsi',
      name: 'Convidar para Triagem WSI',
      description: 'IA ir\u00e1 conduzir a triagem automaticamente',
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
      description: 'Proposta formal de contrata\u00e7\u00e3o',
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
      name: 'Enviar email de aprova\u00e7\u00e3o',
      description: 'Comunicar avan\u00e7o no processo',
      recommended: false,
      template_category: 'aprovacao'
    })
  } else {
    actions.push({
      id: 'email',
      name: 'Enviar email',
      description: 'Comunicar atualiza\u00e7\u00e3o',
      recommended: false,
      template_category: 'follow_up'
    })
  }

  actions.push({
    id: 'apenas_mover',
    name: 'Apenas mover',
    description: 'Mover sem enviar comunica\u00e7\u00e3o',
    recommended: false,
    template_category: undefined
  })

  return actions
}

export function getDefaultSubStatus(stage: string): string {
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

export function getDefaultSubStatusOptions(stage: string): SubStatusOption[] {
  if (stage === 'rejected') {
    return [
      { code: 'another_candidate_selected', display_name: 'Outro candidato selecionado' },
      { code: 'insufficient_technical_skills', display_name: 'Compet\u00eancias t\u00e9cnicas insuficientes' },
      { code: 'cultural_fit', display_name: 'Fit cultural' },
      { code: 'profile_not_aligned', display_name: 'Perfil n\u00e3o alinhado' },
      { code: 'overqualified', display_name: 'Superqualificado' },
      { code: 'underqualified', display_name: 'Experi\u00eancia insuficiente' },
      { code: 'salary_expectation', display_name: 'Expectativa salarial incompat\u00edvel' },
      { code: 'manager_decision', display_name: 'Decis\u00e3o do gestor' },
      { code: 'candidate_withdrew', display_name: 'Candidato desistiu' }
    ]
  }
  return []
}

export function generateFallbackMessage(
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
    body = `Ol\u00e1 ${firstName},

Agradecemos muito sua participa\u00e7\u00e3o em nosso processo seletivo para ${jobTitle}.

Ap\u00f3s an\u00e1lise cuidadosa, decidimos seguir com outros candidatos cujos perfis est\u00e3o mais alinhados com as necessidades atuais da posi\u00e7\u00e3o.

Mantemos seu curr\u00edculo em nosso banco de talentos para futuras oportunidades que possam ser compat\u00edveis com seu perfil.

Desejamos sucesso em sua carreira!

Atenciosamente,
Equipe de Recrutamento`
  } else if (toStage === 'screening') {
    body = `Ol\u00e1 ${firstName},

Ficamos muito felizes com seu interesse em nossa vaga de ${jobTitle}!

Gostar\u00edamos de convid\u00e1-lo(a) para a pr\u00f3xima etapa: uma triagem r\u00e1pida com nossa assistente de IA.

\ud83d\udccb Sobre a triagem:
\u2022 Dura\u00e7\u00e3o estimada: 15-20 minutos
\u2022 Formato: Conversa por chat
\u2022 Objetivo: Conhecer melhor sua forma de pensar

Em breve enviaremos o link para iniciar.

Atenciosamente,
Equipe de Recrutamento`
  } else if (toStage.includes('interview')) {
    body = `Ol\u00e1 ${firstName},

Parab\u00e9ns por avan\u00e7ar em nosso processo seletivo para ${jobTitle}! \ud83c\udf89

Gostar\u00edamos de convid\u00e1-lo(a) para a pr\u00f3xima etapa: uma entrevista.

Em breve entraremos em contato com os detalhes do agendamento.

Atenciosamente,
Equipe de Recrutamento`
  } else {
    body = `Ol\u00e1 ${firstName},

Gostar\u00edamos de inform\u00e1-lo(a) sobre uma atualiza\u00e7\u00e3o em sua candidatura para ${jobTitle}.

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

export function getSubStatusFromMessage(message: string): string {
  return 'profile_not_aligned'
}
