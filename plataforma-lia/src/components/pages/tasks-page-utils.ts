import React from "react"
import { Sun, Sunset, Moon, Video } from "lucide-react"

export interface BackendInterview {
  id: string
  title: string
  description?: string
  candidate_id: string | null
  candidate_name: string
  candidate_email: string
  interviewer_name: string
  interviewer_email: string
  interview_type: string
  interview_mode: string
  start_time: string
  end_time: string
  duration_minutes: number
  status: string
  confirmation_status: string
  meeting_url: string | null
  meeting_platform: string | null
  location: string | null
  job_vacancy_id: string | null
  job_title: string | null
  job_code: string | null
  job_manager: string | null
  application_stage: string | null
  is_synced_to_calendar: boolean
  created_at: string | null
  cancelled_at: string | null
  cancellation_reason: string | null
}

export interface ScheduledInterview {
  id: string
  candidateId: string
  time: string
  date: string
  dateLabel: string
  type: string
  interviewType: string
  candidateName: string
  candidateAvatar?: string
  candidateRole?: string
  jobId: string
  jobCode: string
  jobTitle: string
  company?: string
  jobManager?: string
  manager: string
  currentStage: string
  totalStages: number
  currentStageNumber: number
  platform: 'google_meet' | 'microsoft_teams' | 'zoom'
  meetingLink: string
  duration: number
  status: 'scheduled' | 'completed' | 'cancelled' | 'rescheduled' | 'confirmed'
  completedAt?: string
  cancelledAt?: string
  cancelReason?: string
}

export function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Bom dia'
  if (hour < 18) return 'Boa tarde'
  return 'Boa noite'
}

export function getGreetingIcon() {
  const hour = new Date().getHours()
  if (hour < 12) return React.createElement(Sun, { className: "w-5 h-5 text-status-warning" })
  if (hour < 18) return React.createElement(Sunset, { className: "w-5 h-5 text-wedo-orange-text" })
  return React.createElement(Moon, { className: "w-5 h-5 text-wedo-purple-text" })
}

export function getFormattedDate(): string {
  const now = new Date()
  const options: Intl.DateTimeFormatOptions = {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }
  const formatted = now.toLocaleDateString('pt-BR', options)
  return formatted.charAt(0).toUpperCase() + formatted.slice(1)
}

export function getPlatformIcon(platform: 'google_meet' | 'microsoft_teams' | 'zoom') {
  return React.createElement(Video, { className: "w-3 h-3" })
}

export function getPlatformLabel(platform: 'google_meet' | 'microsoft_teams' | 'zoom'): string {
  switch (platform) {
    case 'google_meet': return 'Google Meet'
    case 'microsoft_teams': return 'Teams'
    case 'zoom': return 'Zoom'
  }
}

export function getStatusLabel(status: string): string {
  switch (status) {
    case 'completed': return 'Concluída'
    case 'cancelled': return 'Cancelada'
    case 'rescheduled': return 'Reagendada'
    default: return status
  }
}

export function getStatusClasses(status: string): string {
  switch (status) {
    case 'completed': return 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle'
    case 'cancelled': return 'bg-lia-bg-tertiary text-lia-text-tertiary border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle'
    case 'rescheduled': return 'bg-lia-bg-tertiary text-lia-text-tertiary border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle'
    default: return 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle'
  }
}

export function getStatusIcon(status: string) {
  switch (status) {
    case 'completed': return React.createElement('span', { className: "w-1.5 h-1.5 rounded-full bg-lia-border-medium dark:bg-lia-bg-elevated inline-block" })
    case 'cancelled': return React.createElement('span', { className: "w-1.5 h-1.5 rounded-full bg-lia-border-medium dark:bg-lia-bg-elevated inline-block" })
    case 'rescheduled': return React.createElement('span', { className: "w-1.5 h-1.5 rounded-full bg-lia-border-medium dark:bg-lia-bg-elevated inline-block" })
    default: return React.createElement('span', {
      className: "w-1.5 h-1.5 rounded-full bg-lia-border-medium dark:bg-lia-bg-elevated inline-block"
    })
  }
}

export function getTimeUntilNext(interviews: ScheduledInterview[]): string | null {
  const now = new Date()
  const scheduled = interviews.filter(i => i.status === 'scheduled')
  if (scheduled.length === 0) return null
  const [hours, minutes] = scheduled[0].time.split(':').map(Number)
  const nextTime = new Date()
  nextTime.setHours(hours, minutes, 0, 0)

  const diffMs = nextTime.getTime() - now.getTime()
  if (diffMs <= 0) return 'Agora'

  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
  if (diffHours > 0 && diffMinutes > 0) return `${diffHours}h${diffMinutes}min`
  if (diffHours > 0) return `${diffHours}h`
  return `${diffMinutes}min`
}

export function getAvatarUrl(_id: string, _name: string): string | undefined {
  return undefined
}

export function getInitials(name: string): string {
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

export const INTERVIEW_TYPE_LABELS: Record<string, string> = {
  technical: 'Entrevista Técnica',
  behavioral: 'Entrevista Comportamental',
  cultural: 'Fit Cultural',
  final: 'Entrevista Final',
}

export function mapPlatform(platform: string | null): 'google_meet' | 'microsoft_teams' | 'zoom' {
  if (!platform) return 'google_meet'
  if (platform.includes('teams') || platform.includes('microsoft')) return 'microsoft_teams'
  if (platform.includes('zoom')) return 'zoom'
  return 'google_meet'
}

export function formatDateShort(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' }).replace('.', '')
}

export function getDateLabel(d: Date): string {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const diffDays = Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'Hoje'
  if (diffDays === 1) return 'Amanhã'
  if (diffDays === -1) return 'Ontem'
  return d.toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'short' }).replace('.', '')
}

export function mapBackendToScheduled(bi: BackendInterview, candidateInfo?: Record<string, unknown>): ScheduledInterview {
  const startDate = new Date(bi.start_time)
  const time = startDate.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', hour12: false })
  const dateStr = startDate.toISOString().split('T')[0]
  const displayName = bi.candidate_name.replace('[DEMO] ', '')
  const cid = bi.candidate_id || bi.id
  return {
    id: bi.id,
    candidateId: cid,
    time,
    date: dateStr,
    dateLabel: getDateLabel(startDate),
    type: INTERVIEW_TYPE_LABELS[bi.interview_type] || bi.interview_type,
    interviewType: bi.interview_type || 'technical',
    candidateName: displayName,
    candidateAvatar: candidateInfo?.avatar_url as string | undefined || undefined,
    candidateRole: candidateInfo?.current_title as string | undefined || undefined,
    jobId: bi.job_vacancy_id || '',
    jobCode: bi.job_code || '',
    jobTitle: (bi.job_title || '').replace('[DEMO] ', ''),
    company: candidateInfo?.current_company as string | undefined || undefined,
    jobManager: bi.job_manager || undefined,
    manager: bi.interviewer_name,
    currentStage: bi.application_stage || INTERVIEW_TYPE_LABELS[bi.interview_type] || 'Entrevista',
    totalStages: 5,
    currentStageNumber: 3,
    platform: mapPlatform(bi.meeting_platform),
    meetingLink: bi.meeting_url || '',
    duration: bi.duration_minutes,
    status: bi.status as ScheduledInterview['status'],
    completedAt: bi.status === 'completed' && bi.cancelled_at ? formatDateShort(bi.cancelled_at) : bi.status === 'completed' && bi.created_at ? formatDateShort(bi.created_at) : undefined,
    cancelledAt: bi.cancelled_at ? formatDateShort(bi.cancelled_at) : undefined,
    cancelReason: bi.cancellation_reason || undefined,
  }
}
