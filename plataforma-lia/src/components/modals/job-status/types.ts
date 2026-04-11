import type { TemplateSituation } from "@/hooks/chat/use-communication-templates"

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

export interface JobItem {
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
}

export interface CandidateItem {
  id: string
  name: string
  email?: string
  phone?: string
  stage: string
  jobId: string
}

export interface CancelData {
  jobIds: string[]
  cancelReason?: string
  closeReason?: string
  notifyApplicants: boolean
  notificationChannel?: 'email' | 'whatsapp' | 'both'
  notificationMessage?: string
  notificationSubject?: string
  candidateIds?: string[]
  notifyStages?: string[]
  sendRecruiterSummary: boolean
  recruiterNotificationChannel?: 'email' | 'teams' | 'bell'
}

export type FlowStep = 'options' | 'communication' | 'confirmation' | 'complete'
export type NotificationChannel = 'email' | 'whatsapp' | 'both'
export type RecruiterChannel = 'email' | 'teams' | 'bell'

export const PAUSE_REASONS = [
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

export const CANCEL_REASONS = [
  { value: 'cancelled_by_client', label: 'Cancelada pelo cliente' },
  { value: 'budget', label: 'Corte de orçamento' },
  { value: 'duplicate', label: 'Vaga duplicada' },
  { value: 'internal_hire', label: 'Contratação interna' },
  { value: 'position_eliminated', label: 'Posição eliminada' },
  { value: 'restructuring', label: 'Reestruturação da área' },
  { value: 'other', label: 'Outro motivo' },
]

export const CLOSE_REASONS = [
  { value: 'filled', label: 'Vaga preenchida' },
  { value: 'not_filled', label: 'Fechada sem contratação' },
  { value: 'cancelled_by_client', label: 'Cancelada pelo cliente' },
  { value: 'budget', label: 'Corte de orçamento' },
  { value: 'duplicate', label: 'Vaga duplicada' },
  { value: 'other', label: 'Outro motivo' },
]

export const PAUSE_TEMPLATE_SITUATIONS: TemplateSituation[] = ['vaga_pausada', 'feedback_construtivo']
export const CANCEL_TEMPLATE_SITUATIONS: TemplateSituation[] = ['vaga_cancelada', 'feedback_construtivo']
