"use client"

import React, { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  Calendar, ExternalLink, CalendarClock, XCircle as XCircleIcon,
  Clock, Briefcase, Building2, Sun, Sunset, Moon, User,
  Video, Loader2, RefreshCw, Share2, Check,
  LayoutDashboard
} from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

interface BackendInterview {
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

interface ScheduledInterview {
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

interface TasksPageMVPProps {
  onNavigate?: (page: string) => void
}

function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Bom dia'
  if (hour < 18) return 'Boa tarde'
  return 'Boa noite'
}

function getGreetingIcon() {
  const hour = new Date().getHours()
  if (hour < 12) return <Sun className="w-5 h-5 text-status-warning" />
  if (hour < 18) return <Sunset className="w-5 h-5 text-wedo-orange" />
  return <Moon className="w-5 h-5 text-wedo-purple" />
}

function getFormattedDate(): string {
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

function getPlatformIcon(platform: 'google_meet' | 'microsoft_teams' | 'zoom') {
  switch (platform) {
    case 'google_meet': return <Video className="w-3 h-3" />
    case 'microsoft_teams': return <Video className="w-3 h-3" />
    case 'zoom': return <Video className="w-3 h-3" />
  }
}

function getPlatformLabel(platform: 'google_meet' | 'microsoft_teams' | 'zoom'): string {
  switch (platform) {
    case 'google_meet': return 'Google Meet'
    case 'microsoft_teams': return 'Teams'
    case 'zoom': return 'Zoom'
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case 'completed': return 'Concluída'
    case 'cancelled': return 'Cancelada'
    case 'rescheduled': return 'Reagendada'
    default: return status
  }
}

function getStatusClasses(status: string): string {
  switch (status) {
    case 'completed': return 'bg-gray-100 text-lia-text-secondary border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle'
    case 'cancelled': return 'bg-gray-100 text-lia-text-tertiary border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle'
    case 'rescheduled': return 'bg-gray-100 text-lia-text-tertiary border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle'
    default: return 'bg-gray-100 text-lia-text-secondary border-lia-border-subtle dark:bg-lia-bg-secondary dark:border-lia-border-subtle'
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'completed': return <span className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-lia-bg-elevated inline-block" />
    case 'cancelled': return <span className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-lia-bg-elevated inline-block" />
    case 'rescheduled': return <span className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-lia-bg-elevated inline-block" />
    default: return null
  }
}


function getTimeUntilNext(interviews: ScheduledInterview[]): string | null {
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

function getAvatarUrl(id: string, name: string): string {
  let hash = 0
  const str = id + name
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash |= 0
  }
  const num = Math.abs(hash) % 99
  const gender = num % 2 === 0 ? 'men' : 'women'
  return `https://randomuser.me/api/portraits/thumb/${gender}/${num}.jpg`
}

function getInitials(name: string): string {
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

const INTERVIEW_TYPE_LABELS: Record<string, string> = {
  technical: 'Entrevista Técnica',
  behavioral: 'Entrevista Comportamental',
  cultural: 'Fit Cultural',
  final: 'Entrevista Final',
}

function mapPlatform(platform: string | null): 'google_meet' | 'microsoft_teams' | 'zoom' {
  if (!platform) return 'google_meet'
  if (platform.includes('teams') || platform.includes('microsoft')) return 'microsoft_teams'
  if (platform.includes('zoom')) return 'zoom'
  return 'google_meet'
}

function formatDateShort(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' }).replace('.', '')
}

function getDateLabel(d: Date): string {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const diffDays = Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'Hoje'
  if (diffDays === 1) return 'Amanhã'
  if (diffDays === -1) return 'Ontem'
  return d.toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'short' }).replace('.', '')
}

function mapBackendToScheduled(bi: BackendInterview, candidateInfo?: Record<string, unknown>): ScheduledInterview {
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

export function TasksPageMVP({ onNavigate }: TasksPageMVPProps = {}) {
  const [todayInterviews, setTodayInterviews] = useState<ScheduledInterview[]>([])
  const [pastInterviews, setPastInterviews] = useState<ScheduledInterview[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const fetchInterviews = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      let res: Response | null = null
      for (let attempt = 0; attempt < 3; attempt++) {
        res = await fetch('/api/backend-proxy/interviews/?limit=100', {
          cache: 'no-store',
          headers: { 'Cache-Control': 'no-cache' },
        })
        if (res.ok || (res.status >= 400 && res.status < 500)) break
        await new Promise(r => setTimeout(r, 2000 * (attempt + 1)))
      }
      if (!res || !res.ok) throw new Error(`Erro ${res?.status || 'desconhecido'}`)
      const data: BackendInterview[] = await res.json()

      const candidateIds = [...new Set(data.map(i => i.candidate_id).filter(Boolean))]
      const candidateMap: Record<string, Record<string, unknown>> = {}
      await Promise.all(
        candidateIds.map(async (cid) => {
          try {
            const cRes = await fetch(`/api/backend-proxy/candidates/${cid}`)
            if (cRes.ok) {
              candidateMap[cid!] = await cRes.json()
            }
          } catch {}
        })
      )

      const today = new Date()
      today.setHours(0, 0, 0, 0)

      const mapped = data.map(bi => mapBackendToScheduled(bi, bi.candidate_id ? candidateMap[bi.candidate_id] : undefined))

      const activeStatuses = ['scheduled', 'confirmed']

      const startTimeMap: Record<string, string> = {}
      data.forEach(bi => { startTimeMap[bi.id] = bi.start_time })

      const upcomingItems = mapped
        .filter(i => {
          const raw = startTimeMap[i.id]
          if (!raw) return false
          const d = new Date(raw)
          return activeStatuses.includes(i.status) && d >= today
        })
        .sort((a, b) => {
          const rawA = startTimeMap[a.id] || ''
          const rawB = startTimeMap[b.id] || ''
          return rawA.localeCompare(rawB)
        })

      const pastItems = mapped
        .filter(i => {
          if (i.status === 'completed' || i.status === 'cancelled' || i.status === 'rescheduled') return true
          const raw = startTimeMap[i.id]
          if (!raw) return false
          const d = new Date(raw)
          return activeStatuses.includes(i.status) && d < today
        })
        .sort((a, b) => {
          const rawA = startTimeMap[a.id] || ''
          const rawB = startTimeMap[b.id] || ''
          return rawB.localeCompare(rawA)
        })

      setTodayInterviews(upcomingItems)
      setPastInterviews(pastItems)
    } catch (err: unknown) {
      setError(err instanceof Error ? err instanceof Error ? err.message : String(err) : 'Erro ao carregar entrevistas')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchInterviews()
  }, [fetchInterviews])

  const todayOnlyInterviews = todayInterviews.filter(i => i.dateLabel === 'Hoje')
  const morningInterviews = todayOnlyInterviews.filter(i => i.time < '12:00')
  const afternoonInterviews = todayOnlyInterviews.filter(i => i.time >= '12:00')
  const futureInterviews = todayInterviews.filter(i => i.dateLabel !== 'Hoje')
  const scheduledCount = todayOnlyInterviews.length
  const timeUntilNext = getTimeUntilNext(todayOnlyInterviews)

  const handleOpenMeeting = (interview: ScheduledInterview) => {
    if (interview.meetingLink) {
      window.open(interview.meetingLink, '_blank', 'noopener,noreferrer')
    }
  }

  const handleCopyLink = (interview: ScheduledInterview) => {
    if (interview.meetingLink && typeof navigator !== 'undefined') {
      navigator.clipboard.writeText(interview.meetingLink).then(() => {
        setCopiedId(interview.id)
        setTimeout(() => setCopiedId(null), 2000)
      })
    }
  }

  const handleReschedule = (interview: ScheduledInterview) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('navigateToCandidate', JSON.stringify({
        candidateId: interview.candidateId,
        candidateName: interview.candidateName,
        jobId: interview.jobId,
        jobTitle: interview.jobTitle,
        currentStage: interview.currentStage,
        interviewType: interview.interviewType,
        action: 'reschedule',
        openTransitionModal: true,
      }))
      localStorage.setItem('liaPrompt', `Reagendar entrevista "${interview.type}" com ${interview.candidateName} para a vaga ${interview.jobTitle}, originalmente às ${interview.time}. Por favor, pergunte ao recrutador qual o dia e horário de preferência para o novo agendamento.`)
    }
    if (onNavigate) {
      onNavigate('Vagas')
    }
  }

  const handleReject = (interview: ScheduledInterview) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('navigateToCandidate', JSON.stringify({
        candidateId: interview.candidateId,
        candidateName: interview.candidateName,
        jobId: interview.jobId,
        jobTitle: interview.jobTitle,
        currentStage: interview.currentStage,
        interviewType: interview.interviewType,
        action: 'cancel',
        openTransitionModal: true,
      }))
      localStorage.setItem('liaPrompt', `Cancelar entrevista "${interview.type}" com ${interview.candidateName} para a vaga ${interview.jobTitle} às ${interview.time}.`)
    }
    if (onNavigate) {
      onNavigate('Vagas')
    }
  }

  const handleOpenJob = (interview: ScheduledInterview) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('navigateToCandidate', JSON.stringify({
        candidateId: interview.candidateId,
        candidateName: interview.candidateName,
        jobId: interview.jobId,
        jobTitle: interview.jobTitle,
        currentStage: interview.currentStage,
        action: 'view',
        openTransitionModal: false,
      }))
    }
    if (onNavigate) {
      onNavigate('Vagas')
    }
  }

  const renderJobLink = (interview: ScheduledInterview) => {
    if (!interview.jobCode && !interview.jobTitle) return null
    return (
      <button
        onClick={() => handleOpenJob(interview)}
        className="text-xs font-[Open_Sans,sans-serif] font-medium text-wedo-cyan-dark dark:text-wedo-cyan-dark hover:text-wedo-cyan-dark dark:hover:text-wedo-cyan-dark hover:underline truncate cursor-pointer"
        title="Abrir vaga no kanban"
      >
        {interview.jobCode && <span className="font-[Inter,sans-serif] mr-0.5">{interview.jobCode}</span>}
        {interview.jobTitle}
      </button>
    )
  }

  const renderCandidateInfo = (interview: ScheduledInterview) => (
    <div className="grid grid-cols-2 gap-4 text-xs">
      <div className="space-y-0.5 min-w-0">
        <span className="text-base-ui font-[Open_Sans,sans-serif] font-medium text-lia-text-primary truncate block">
          {interview.candidateName}
        </span>
        {interview.candidateRole && (
          <span className="flex items-center gap-1 text-lia-text-tertiary truncate">
            <Briefcase className="w-3 h-3 flex-shrink-0" />
            {interview.candidateRole}
          </span>
        )}
        {interview.company && (
          <span className="flex items-center gap-1 text-lia-text-tertiary truncate">
            <Building2 className="w-3 h-3 flex-shrink-0" />
            {interview.company}
          </span>
        )}
      </div>
      <div className="space-y-0.5 min-w-0">
        {renderJobLink(interview)}
        {interview.jobManager && (
          <span className="flex items-center gap-1 text-lia-text-tertiary truncate">
            <User className="w-3 h-3 flex-shrink-0" />
            {interview.jobManager}
          </span>
        )}
      </div>
    </div>
  )

  return (
    <div className="h-full flex flex-col bg-white dark:bg-lia-bg-primary overflow-hidden">
      <div className="flex-shrink-0 px-4 pt-3 pb-0 bg-white dark:bg-lia-bg-primary">
        <div className="flex items-center justify-between mb-0.5">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-xl font-['Open_Sans',sans-serif] font-semibold wedo-text-black flex items-center gap-2">
                <LayoutDashboard className="w-5 h-5 text-lia-text-secondary" />
                Painel de Controle
              </h1>
            </div>
          </div>
        </div>
      </div>
      <div className="flex-shrink-0 px-4 pt-2 pb-1">
        <div className="flex items-center gap-2 mb-0.5">
          {getGreetingIcon()}
          <h1 className="text-lg font-[Open_Sans,sans-serif] font-semibold text-lia-text-primary">
            {getGreeting()}, Ana
          </h1>
        </div>
        <p className="text-base-ui font-[Open_Sans,sans-serif] text-lia-text-tertiary pl-7">
          Sua agenda — {getFormattedDate()}
        </p>
        {!isLoading && todayInterviews.length > 0 && (
          <p className="text-xs font-[Open_Sans,sans-serif] text-lia-text-tertiary pl-7 mt-1">
            <span className="font-[Inter,sans-serif] font-semibold text-lia-text-primary">{scheduledCount}</span> entrevista{scheduledCount !== 1 ? 's' : ''} hoje{futureInterviews.length > 0 ? ` · ${futureInterviews.length} próxima${futureInterviews.length !== 1 ? 's' : ''}` : ''}
            {timeUntilNext && (
              <>
                <span className="text-lia-text-disabled mx-2">|</span>
                Próxima em <span className="font-[Inter,sans-serif] font-semibold text-lia-text-primary">{timeUntilNext}</span>
              </>
            )}
          </p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-4 pt-3 pb-4">
        <Tabs defaultValue="entrevistas" className="w-full">
          <TabsList className="grid w-full grid-cols-2 h-9 bg-gray-100 dark:bg-lia-bg-secondary p-1 rounded-md">
            <TabsTrigger
              value="entrevistas"
              className="text-sm-ui font-[Open_Sans,sans-serif] h-7 rounded-md data-[state=active]:font-semibold data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-primary data-[state=active]:shadow-lia-sm dark:data-[state=active]:bg-gray-900 dark:data-[state=active]:text-lia-text-inverse"
            >
              Entrevistas ({todayInterviews.length})
            </TabsTrigger>
            <TabsTrigger
              value="historico"
              className="text-sm-ui font-[Open_Sans,sans-serif] h-7 rounded-md data-[state=active]:font-semibold data-[state=active]:bg-lia-bg-primary data-[state=active]:text-lia-text-primary data-[state=active]:shadow-lia-sm dark:data-[state=active]:bg-gray-900 dark:data-[state=active]:text-lia-text-inverse"
            >
              Histórico ({pastInterviews.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="entrevistas" className="mt-3">
            {isLoading ? (
              <div className="py-16 text-center" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-8 h-8 text-lia-text-disabled mx-auto mb-3 animate-spin motion-reduce:animate-none" />
                <p className="text-base-ui font-[Open_Sans,sans-serif] text-lia-text-tertiary">Carregando entrevistas...</p>
              </div>
            ) : error ? (
              <div className="py-16 text-center">
                <Calendar className="w-12 h-12 text-lia-text-disabled mx-auto mb-3" />
                <p className="text-base-ui font-semibold text-lia-text-secondary mb-1">Erro ao carregar</p>
                <p className="text-xs text-lia-text-tertiary mb-3">{error}</p>
                <Button size="sm" variant="outline" onClick={fetchInterviews} className="h-7 px-3 text-xs gap-1.5">
                  <RefreshCw className="w-3 h-3" /> Tentar novamente
                </Button>
              </div>
            ) : todayInterviews.length === 0 ? (
              <div className="py-16 text-center">
                <Calendar className="w-12 h-12 text-lia-text-disabled mx-auto mb-3" />
                <p className="text-base-ui font-semibold text-lia-text-secondary mb-1">Nenhuma entrevista agendada</p>
                <p className="text-xs text-lia-text-tertiary">Sua agenda está livre.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {morningInterviews.length > 0 && (
                  <div className="flex items-center gap-2 pt-1 pb-0.5 px-1">
                    <Sun className="w-3.5 h-3.5 text-status-warning" />
                    <span className="text-xs font-[Inter,sans-serif] font-medium text-lia-text-disabled uppercase tracking-wider">Manhã</span>
                    <div className="flex-1 border-t border-lia-border-subtle dark:border-lia-border-subtle" />
                  </div>
                )}
                {morningInterviews.map((interview) => (
                  <div
                    key={interview.id}
                    className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-3.5 bg-white dark:bg-lia-bg-primary transition-colors motion-reduce:transition-none duration-150 hover:border-lia-border-default dark:hover:border-gray-600"
                  >
                    <div className="flex gap-3">
                      <Avatar className="w-10 h-10 flex-shrink-0 mt-0.5">
                        <AvatarImage src={interview.candidateAvatar || getAvatarUrl(interview.id, interview.candidateName)} />
                        <AvatarFallback className="text-micro font-medium text-lia-text-secondary bg-wedo-cyan/15">
                          {getInitials(interview.candidateName)}
                        </AvatarFallback>
                      </Avatar>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <div className="flex items-center gap-1.5 min-w-0">
                            <span className="text-base-ui font-[Inter,sans-serif] font-semibold text-lia-text-primary tabular-nums">
                              {interview.time}
                            </span>
                            <span className="text-lia-text-disabled">·</span>
                            <span className="text-sm-ui font-[Open_Sans,sans-serif] font-semibold text-lia-text-primary truncate">
                              {interview.type}
                            </span>
                            <span className="text-lia-text-disabled">·</span>
                            <span className="text-xs font-[Open_Sans,sans-serif] text-lia-text-tertiary flex items-center gap-1">
                              {getPlatformIcon(interview.platform)}
                              {getPlatformLabel(interview.platform)}
                              <button
                                onClick={(e) => { e.stopPropagation(); handleCopyLink(interview) }}
                                className="ml-0.5 text-lia-text-disabled hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
                                title={copiedId === interview.id ? 'Link copiado!' : 'Copiar link da reunião'}
                              >
                                {copiedId === interview.id ? <Check className="w-3.5 h-3.5 text-status-success stroke-[2.5]" /> : <Share2 className="w-3.5 h-3.5 stroke-[2.5]" />}
                              </button>
                            </span>
                            <span className="text-lia-text-disabled">·</span>
                            <span className="text-xs font-[Inter,sans-serif] tabular-nums text-lia-text-tertiary">
                              {interview.duration}min
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5 flex-shrink-0">
                            <Button
                              size="sm"
                              onClick={() => handleOpenMeeting(interview)}
                              className="h-7 px-3 text-xs font-[Open_Sans,sans-serif] font-medium gap-1.5 bg-gray-900 text-white hover:bg-gray-800 dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover rounded-md"
                            >
                              <ExternalLink className="w-3 h-3" />
                              Abrir Reunião
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleReschedule(interview)}
                              className="h-7 px-2.5 text-xs font-[Open_Sans,sans-serif] font-medium gap-1 text-lia-text-secondary border-lia-border-default hover:bg-gray-50 hover:border-gray-400 dark:border-lia-border-default dark:hover:bg-gray-800 rounded-md"
                            >
                              <CalendarClock className="w-3 h-3" />
                              Alterar Horário
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleReject(interview)}
                              className="h-7 px-2.5 text-xs font-[Open_Sans,sans-serif] font-medium gap-1 text-status-error border-status-error/30 hover:bg-status-error/10 hover:border-status-error/30 dark:text-status-error dark:border-status-error/30 dark:hover:bg-status-error/20 rounded-md"
                            >
                              <XCircleIcon className="w-3 h-3" />
                              Cancelar
                            </Button>
                          </div>
                        </div>

                        {renderCandidateInfo(interview)}
                      </div>
                    </div>
                  </div>
                ))}
                {afternoonInterviews.length > 0 && (
                  <div className="flex items-center gap-2 pt-2 pb-0.5 px-1">
                    <Sunset className="w-3.5 h-3.5 text-wedo-orange" />
                    <span className="text-xs font-[Inter,sans-serif] font-medium text-lia-text-disabled uppercase tracking-wider">Tarde</span>
                    <div className="flex-1 border-t border-lia-border-subtle dark:border-lia-border-subtle" />
                  </div>
                )}
                {afternoonInterviews.map((interview) => (
                  <div
                    key={interview.id}
                    className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-3.5 bg-white dark:bg-lia-bg-primary transition-colors motion-reduce:transition-none duration-150 hover:border-lia-border-default dark:hover:border-gray-600"
                  >
                    <div className="flex gap-3">
                      <Avatar className="w-10 h-10 flex-shrink-0 mt-0.5">
                        <AvatarImage src={interview.candidateAvatar || getAvatarUrl(interview.id, interview.candidateName)} />
                        <AvatarFallback className="text-micro font-medium text-lia-text-secondary bg-wedo-cyan/15">
                          {getInitials(interview.candidateName)}
                        </AvatarFallback>
                      </Avatar>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <div className="flex items-center gap-1.5 min-w-0">
                            <span className="text-base-ui font-[Inter,sans-serif] font-semibold text-lia-text-primary tabular-nums">
                              {interview.time}
                            </span>
                            <span className="text-lia-text-disabled">·</span>
                            <span className="text-sm-ui font-[Open_Sans,sans-serif] font-semibold text-lia-text-primary truncate">
                              {interview.type}
                            </span>
                            <span className="text-lia-text-disabled">·</span>
                            <span className="text-xs font-[Open_Sans,sans-serif] text-lia-text-tertiary flex items-center gap-1">
                              {getPlatformIcon(interview.platform)}
                              {getPlatformLabel(interview.platform)}
                              <button
                                onClick={(e) => { e.stopPropagation(); handleCopyLink(interview) }}
                                className="ml-0.5 text-lia-text-disabled hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
                                title={copiedId === interview.id ? 'Link copiado!' : 'Copiar link da reunião'}
                              >
                                {copiedId === interview.id ? <Check className="w-3.5 h-3.5 text-status-success stroke-[2.5]" /> : <Share2 className="w-3.5 h-3.5 stroke-[2.5]" />}
                              </button>
                            </span>
                            <span className="text-lia-text-disabled">·</span>
                            <span className="text-xs font-[Inter,sans-serif] tabular-nums text-lia-text-tertiary">
                              {interview.duration}min
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5 flex-shrink-0">
                            <Button
                              size="sm"
                              onClick={() => handleOpenMeeting(interview)}
                              className="h-7 px-3 text-xs font-[Open_Sans,sans-serif] font-medium gap-1.5 bg-gray-900 text-white hover:bg-gray-800 dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover rounded-md"
                            >
                              <ExternalLink className="w-3 h-3" />
                              Abrir Reunião
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleReschedule(interview)}
                              className="h-7 px-2.5 text-xs font-[Open_Sans,sans-serif] font-medium gap-1 text-lia-text-secondary border-lia-border-default hover:bg-gray-50 hover:border-gray-400 dark:border-lia-border-default dark:hover:bg-gray-800 rounded-md"
                            >
                              <CalendarClock className="w-3 h-3" />
                              Alterar Horário
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleReject(interview)}
                              className="h-7 px-2.5 text-xs font-[Open_Sans,sans-serif] font-medium gap-1 text-status-error border-status-error/30 hover:bg-status-error/10 hover:border-status-error/30 dark:text-status-error dark:border-status-error/30 dark:hover:bg-status-error/20 rounded-md"
                            >
                              <XCircleIcon className="w-3 h-3" />
                              Cancelar
                            </Button>
                          </div>
                        </div>

                        {renderCandidateInfo(interview)}
                      </div>
                    </div>
                  </div>
                ))}
                {futureInterviews.length > 0 && (() => {
                  const groupedByDate: Record<string, ScheduledInterview[]> = {}
                  futureInterviews.forEach(i => {
                    if (!groupedByDate[i.dateLabel]) groupedByDate[i.dateLabel] = []
                    groupedByDate[i.dateLabel].push(i)
                  })
                  return Object.entries(groupedByDate).map(([dateLabel, interviews]) => (
                    <React.Fragment key={dateLabel}>
                      <div className="flex items-center gap-2 pt-3 pb-0.5 px-1">
                        <Calendar className="w-3.5 h-3.5 text-lia-text-disabled" />
                        <span className="text-xs font-[Inter,sans-serif] font-medium text-lia-text-disabled uppercase tracking-wider">{dateLabel}</span>
                        <div className="flex-1 border-t border-lia-border-subtle dark:border-lia-border-subtle" />
                      </div>
                      {interviews.map((interview) => (
                        <div
                          key={interview.id}
                          className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-3.5 bg-white dark:bg-lia-bg-primary transition-colors motion-reduce:transition-none duration-150 hover:border-lia-border-default dark:hover:border-gray-600"
                        >
                          <div className="flex gap-3">
                            <Avatar className="w-10 h-10 flex-shrink-0 mt-0.5">
                              <AvatarImage src={interview.candidateAvatar || getAvatarUrl(interview.id, interview.candidateName)} />
                              <AvatarFallback className="text-micro font-medium text-lia-text-secondary bg-wedo-cyan/15">
                                {getInitials(interview.candidateName)}
                              </AvatarFallback>
                            </Avatar>

                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between gap-2 mb-1">
                                <div className="flex items-center gap-1.5 min-w-0">
                                  <span className="text-base-ui font-[Inter,sans-serif] font-semibold text-lia-text-primary tabular-nums">
                                    {interview.time}
                                  </span>
                                  <span className="text-lia-text-disabled">·</span>
                                  <span className="text-sm-ui font-[Open_Sans,sans-serif] font-semibold text-lia-text-primary truncate">
                                    {interview.type}
                                  </span>
                                  <span className="text-lia-text-disabled">·</span>
                                  <span className="text-xs font-[Open_Sans,sans-serif] text-lia-text-tertiary flex items-center gap-1">
                                    {getPlatformIcon(interview.platform)}
                                    {getPlatformLabel(interview.platform)}
                                    <button
                                      onClick={(e) => { e.stopPropagation(); handleCopyLink(interview) }}
                                      className="ml-0.5 text-lia-text-disabled hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
                                      title={copiedId === interview.id ? 'Link copiado!' : 'Copiar link da reunião'}
                                    >
                                      {copiedId === interview.id ? <Check className="w-3.5 h-3.5 text-status-success stroke-[2.5]" /> : <Share2 className="w-3.5 h-3.5 stroke-[2.5]" />}
                                    </button>
                                  </span>
                                  <span className="text-lia-text-disabled">·</span>
                                  <span className="text-xs font-[Inter,sans-serif] tabular-nums text-lia-text-tertiary">
                                    {interview.duration}min
                                  </span>
                                </div>

                                <div className="flex items-center gap-1.5 flex-shrink-0">
                                  <Button
                                    size="sm"
                                    onClick={() => handleOpenMeeting(interview)}
                                    className="h-7 px-3 text-xs font-[Open_Sans,sans-serif] font-medium gap-1.5 bg-gray-900 text-white hover:bg-gray-800 dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover rounded-md"
                                  >
                                    <ExternalLink className="w-3 h-3" />
                                    Abrir Reunião
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleReschedule(interview)}
                                    className="h-7 px-2.5 text-xs font-[Open_Sans,sans-serif] font-medium gap-1 text-lia-text-secondary border-lia-border-default hover:bg-gray-50 hover:border-gray-400 dark:border-lia-border-default dark:hover:bg-gray-800 rounded-md"
                                  >
                                    <CalendarClock className="w-3 h-3" />
                                    Alterar Horário
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleReject(interview)}
                                    className="h-7 px-2.5 text-xs font-[Open_Sans,sans-serif] font-medium gap-1 text-status-error border-status-error/30 hover:bg-status-error/10 hover:border-status-error/30 dark:text-status-error dark:border-status-error/30 dark:hover:bg-status-error/20 rounded-md"
                                  >
                                    <XCircleIcon className="w-3 h-3" />
                                    Cancelar
                                  </Button>
                                </div>
                              </div>

                              {renderCandidateInfo(interview)}
                            </div>
                          </div>
                        </div>
                      ))}
                    </React.Fragment>
                  ))
                })()}
              </div>
            )}
          </TabsContent>

          <TabsContent value="historico" className="mt-3">
            {pastInterviews.length === 0 ? (
              <div className="py-16 text-center">
                <Clock className="w-12 h-12 text-lia-text-disabled mx-auto mb-3" />
                <p className="text-base-ui font-semibold text-lia-text-secondary mb-1">Nenhum histórico</p>
                <p className="text-xs text-lia-text-tertiary">Suas entrevistas passadas aparecerão aqui.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {pastInterviews.map((interview) => (
                  <div
                    key={interview.id}
                    className="border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-3.5 bg-white dark:bg-lia-bg-primary transition-colors motion-reduce:transition-none duration-150"
                  >
                    <div className="flex gap-3">
                      <Avatar className="w-10 h-10 flex-shrink-0 mt-0.5">
                        <AvatarImage src={getAvatarUrl(interview.id, interview.candidateName)} />
                        <AvatarFallback className="text-micro font-medium text-lia-text-secondary bg-wedo-cyan/15">
                          {getInitials(interview.candidateName)}
                        </AvatarFallback>
                      </Avatar>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <div className="flex items-center gap-1.5 min-w-0">
                            <span className="text-base-ui font-[Inter,sans-serif] font-semibold text-lia-text-primary tabular-nums">
                              {interview.time}
                            </span>
                            <span className="text-lia-text-disabled">·</span>
                            <span className="text-sm-ui font-[Open_Sans,sans-serif] font-semibold text-lia-text-primary truncate">
                              {interview.type}
                            </span>
                            <span className="text-lia-text-disabled">·</span>
                            <span className="text-xs font-[Open_Sans,sans-serif] text-lia-text-tertiary">
                              {getPlatformLabel(interview.platform)}
                              <button
                                onClick={(e) => { e.stopPropagation(); handleCopyLink(interview) }}
                                className="ml-0.5 text-lia-text-disabled hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
                                title={copiedId === interview.id ? 'Link copiado!' : 'Copiar link da reunião'}
                              >
                                {copiedId === interview.id ? <Check className="w-3.5 h-3.5 text-status-success stroke-[2.5]" /> : <Share2 className="w-3.5 h-3.5 stroke-[2.5]" />}
                              </button>
                            </span>
                            <span className="text-lia-text-disabled">·</span>
                            <span className="text-xs font-[Inter,sans-serif] tabular-nums text-lia-text-tertiary">
                              {interview.duration}min
                            </span>
                            <Badge className={`text-micro px-1.5 py-0 ml-1 border font-medium flex items-center gap-1 ${getStatusClasses(interview.status)}`}>
                              {getStatusIcon(interview.status)}
                              {getStatusLabel(interview.status)}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-1.5 flex-shrink-0">
                            <Button
                              size="sm"
                              onClick={() => handleOpenMeeting(interview)}
                              className="h-7 px-3 text-xs font-[Open_Sans,sans-serif] font-medium gap-1.5 bg-gray-900 text-white hover:bg-gray-800 dark:bg-lia-btn-primary-bg dark:hover:bg-lia-btn-primary-hover rounded-md"
                            >
                              <ExternalLink className="w-3 h-3" />
                              Abrir Reunião
                            </Button>
                            <span className="text-xs font-[Inter,sans-serif] text-lia-text-tertiary tabular-nums">
                              {interview.completedAt || interview.cancelledAt}
                            </span>
                          </div>
                        </div>

                        {renderCandidateInfo(interview)}

                        {interview.cancelReason && (
                          <p className="text-xs text-lia-text-disabled italic mt-1.5">
                            {interview.cancelReason}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

    </div>
  )
}
