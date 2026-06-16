"use client"

import { useState, useEffect, useCallback } from "react"
import { useNavigationStore } from "@/stores/navigation-store"
import type { ScheduledInterview, BackendInterview } from "./tasks-page-utils"
import { mapBackendToScheduled, getTimeUntilNext } from "./tasks-page-utils"

export function useTasksPageData(onNavigate?: (page: string) => void) {
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
      for (let attempt = 0; attempt <= 6; attempt++) {
        try {
          res = await fetch('/api/backend-proxy/interviews/?limit=100', {
            cache: 'no-store',
            headers: { 'Cache-Control': 'no-cache' },
            signal: AbortSignal.timeout(30000),
          })
          if (res.ok || (res.status >= 400 && res.status < 500)) break
        } catch {
          res = null
        }
        const delay = Math.min(3000 * Math.pow(1.5, attempt), 15000)
        await new Promise(r => setTimeout(r, delay))
      }
      if (!res || !res.ok) throw new Error(`Erro ${res?.status || 'desconhecido'}`)
      const data: BackendInterview[] = await res.json()

      const candidateIds = [...new Set(data.map(i => i.candidate_id).filter(Boolean))]
      const candidateMap: Record<string, Record<string, unknown>> = {}
      await Promise.all(
        candidateIds.map(async (cid) => {
          try {
            const cRes = await fetch(`/api/backend-proxy/candidates/${cid}`)
            if (cRes.ok) { candidateMap[cid!] = await cRes.json() }
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
        .filter(i => { const raw = startTimeMap[i.id]; if (!raw) return false; const d = new Date(raw); return activeStatuses.includes(i.status) && d >= today })
        .sort((a, b) => (startTimeMap[a.id] || '').localeCompare(startTimeMap[b.id] || ''))

      const pastItems = mapped
        .filter(i => {
          if (i.status === 'completed' || i.status === 'cancelled' || i.status === 'rescheduled') return true
          const raw = startTimeMap[i.id]; if (!raw) return false; const d = new Date(raw)
          return activeStatuses.includes(i.status) && d < today
        })
        .sort((a, b) => (startTimeMap[b.id] || '').localeCompare(startTimeMap[a.id] || ''))

      setTodayInterviews(upcomingItems)
      setPastInterviews(pastItems)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar entrevistas')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { fetchInterviews() }, [fetchInterviews])

  const todayOnlyInterviews = todayInterviews.filter(i => i.dateLabel === 'Hoje')
  const morningInterviews = todayOnlyInterviews.filter(i => i.time < '12:00')
  const afternoonInterviews = todayOnlyInterviews.filter(i => i.time >= '12:00')
  const futureInterviews = todayInterviews.filter(i => i.dateLabel !== 'Hoje')
  const scheduledCount = todayOnlyInterviews.length
  const timeUntilNext = getTimeUntilNext(todayOnlyInterviews)

  const handleOpenMeeting = (interview: ScheduledInterview) => {
    if (interview.meetingLink) window.open(interview.meetingLink, '_blank', 'noopener,noreferrer')
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
    const { setNavigateToCandidate, setLiaPrompt } = useNavigationStore.getState()
    setNavigateToCandidate({
      candidateId: interview.candidateId, candidateName: interview.candidateName,
      jobId: interview.jobId, jobTitle: interview.jobTitle, currentStage: interview.currentStage,
      interviewType: interview.interviewType, action: 'reschedule', openTransitionModal: true,
    })
    setLiaPrompt(`Reagendar entrevista "${interview.type}" com ${interview.candidateName} para a vaga ${interview.jobTitle}, originalmente às ${interview.time}. Por favor, pergunte ao recrutador qual o dia e horário de preferência para o novo agendamento.`)
    if (onNavigate) onNavigate('Vagas')
  }

  const handleReject = (interview: ScheduledInterview) => {
    const { setNavigateToCandidate, setLiaPrompt } = useNavigationStore.getState()
    setNavigateToCandidate({
      candidateId: interview.candidateId, candidateName: interview.candidateName,
      jobId: interview.jobId, jobTitle: interview.jobTitle, currentStage: interview.currentStage,
      interviewType: interview.interviewType, action: 'cancel', openTransitionModal: true,
    })
    setLiaPrompt(`Cancelar entrevista "${interview.type}" com ${interview.candidateName} para a vaga ${interview.jobTitle} às ${interview.time}.`)
    if (onNavigate) onNavigate('Vagas')
  }

  const handleOpenJob = (interview: ScheduledInterview) => {
    const { setNavigateToCandidate } = useNavigationStore.getState()
    setNavigateToCandidate({
      candidateId: interview.candidateId, candidateName: interview.candidateName,
      jobId: interview.jobId, jobTitle: interview.jobTitle, currentStage: interview.currentStage,
      action: 'view', openTransitionModal: false,
    })
    if (onNavigate) onNavigate('Vagas')
  }

  return {
    todayInterviews, pastInterviews, isLoading, error, copiedId,
    morningInterviews, afternoonInterviews, futureInterviews,
    scheduledCount, timeUntilNext, fetchInterviews,
    handleOpenMeeting, handleCopyLink, handleReschedule,
    handleReject, handleOpenJob,
  }
}
