import type { TemplateSituation } from "@/hooks/use-communication-templates"

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

export const PAUSE_TEMPLATE_SITUATIONS: TemplateSituation[] = ['vaga_fechada', 'feedback_construtivo']
