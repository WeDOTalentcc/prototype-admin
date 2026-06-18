"use client"

import { useState, useCallback } from "react"
import { useQuery } from "@tanstack/react-query"
import { useNavigationStore } from "@/stores/navigation-store"
import type { BackendInterview, ScheduledInterview } from "./tasks-page-utils"
import { mapBackendToScheduled } from "./tasks-page-utils"

const INTERVIEWS_QUERY_KEY = ["interviews"] as const

async function fetchInterviewsWithCandidates(): Promise<{
  todayInterviews: ScheduledInterview[]
  pastInterviews: ScheduledInterview[]
}> {
  let res: Response | null = null
  for (let attempt = 0; attempt < 3; attempt++) {
    res = await fetch("/api/backend-proxy/interviews/?limit=100", {
      cache: "no-store",
      headers: { "Cache-Control": "no-cache" },
      signal: AbortSignal.timeout(10_000),
    })
    if (res.ok || (res.status >= 400 && res.status < 500)) break
    await new Promise((r) => setTimeout(r, 2000 * (attempt + 1)))
  }
  if (!res || !res.ok) throw new Error(`Erro ${res?.status || "desconhecido"}`)
  const data: BackendInterview[] = await res.json()

  const candidateIds = [...new Set(data.map((i) => i.candidate_id).filter(Boolean))]
  const candidateMap: Record<string, Record<string, unknown>> = {}
  await Promise.all(
    candidateIds.map(async (cid) => {
      try {
        const cRes = await fetch(`/api/backend-proxy/candidates/${cid}`, {
          signal: AbortSignal.timeout(5000),
        })
        if (cRes.ok) {
          candidateMap[cid!] = await cRes.json()
        }
      } catch (err) {
        if (err instanceof Error && err.name !== "AbortError") {
          console.warn("[useTasksInterviews] candidate fetch failed", cid, err)
        }
      }
    }),
  )

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const mapped = data.map((bi) =>
    mapBackendToScheduled(bi, bi.candidate_id ? candidateMap[bi.candidate_id] : undefined),
  )
  const activeStatuses = ["scheduled", "confirmed"]
  const startTimeMap: Record<string, string> = {}
  data.forEach((bi) => {
    startTimeMap[bi.id] = bi.start_time
  })

  const todayInterviews = mapped
    .filter((i) => {
      const raw = startTimeMap[i.id]
      if (!raw) return false
      const d = new Date(raw)
      return activeStatuses.includes(i.status) && d >= today
    })
    .sort((a, b) => (startTimeMap[a.id] || "").localeCompare(startTimeMap[b.id] || ""))

  const pastInterviews = mapped
    .filter((i) => {
      if (i.status === "completed" || i.status === "cancelled" || i.status === "rescheduled") return true
      const raw = startTimeMap[i.id]
      if (!raw) return false
      const d = new Date(raw)
      return activeStatuses.includes(i.status) && d < today
    })
    .sort((a, b) => (startTimeMap[b.id] || "").localeCompare(startTimeMap[a.id] || ""))

  return { todayInterviews, pastInterviews }
}

export function useTasksInterviews(onNavigate?: (page: string) => void) {
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const {
    data,
    isLoading,
    error,
    refetch: fetchInterviews,
  } = useQuery({
    queryKey: INTERVIEWS_QUERY_KEY,
    queryFn: fetchInterviewsWithCandidates,
    staleTime: 60_000,
    retry: false,
  })

  const handleOpenMeeting = (interview: ScheduledInterview) => {
    if (interview.meetingLink) {
      window.open(interview.meetingLink, "_blank", "noopener,noreferrer")
    }
  }

  const handleCopyLink = (interview: ScheduledInterview) => {
    if (interview.meetingLink && typeof navigator !== "undefined") {
      navigator.clipboard.writeText(interview.meetingLink).then(() => {
        setCopiedId(interview.id)
        setTimeout(() => setCopiedId(null), 2000)
      })
    }
  }

  const handleReschedule = useCallback(
    (interview: ScheduledInterview) => {
      const { setNavigateToCandidate, setLiaPrompt } = useNavigationStore.getState()
      setNavigateToCandidate({
        candidateId: interview.candidateId,
        candidateName: interview.candidateName,
        jobId: interview.jobId,
        jobTitle: interview.jobTitle,
        currentStage: interview.currentStage,
        interviewType: interview.interviewType,
        action: "reschedule",
        openTransitionModal: true,
      })
      setLiaPrompt(
        `Reagendar entrevista "${interview.type}" com ${interview.candidateName} para a vaga ${interview.jobTitle}, originalmente às ${interview.time}. Por favor, pergunte ao recrutador qual o dia e horário de preferência para o novo agendamento.`,
      )
      if (onNavigate) {
        onNavigate("Vagas")
      }
    },
    [onNavigate],
  )

  const handleReject = useCallback(
    (interview: ScheduledInterview) => {
      const { setNavigateToCandidate, setLiaPrompt } = useNavigationStore.getState()
      setNavigateToCandidate({
        candidateId: interview.candidateId,
        candidateName: interview.candidateName,
        jobId: interview.jobId,
        jobTitle: interview.jobTitle,
        currentStage: interview.currentStage,
        interviewType: interview.interviewType,
        action: "cancel",
        openTransitionModal: true,
      })
      setLiaPrompt(
        `Cancelar entrevista "${interview.type}" com ${interview.candidateName} para a vaga ${interview.jobTitle} às ${interview.time}.`,
      )
      if (onNavigate) {
        onNavigate("Vagas")
      }
    },
    [onNavigate],
  )

  const handleOpenJob = useCallback(
    (interview: ScheduledInterview) => {
      const { setNavigateToCandidate } = useNavigationStore.getState()
      setNavigateToCandidate({
        candidateId: interview.candidateId,
        candidateName: interview.candidateName,
        jobId: interview.jobId,
        jobTitle: interview.jobTitle,
        currentStage: interview.currentStage,
        action: "view",
        openTransitionModal: false,
      })
      if (onNavigate) {
        onNavigate("Vagas")
      }
    },
    [onNavigate],
  )

  return {
    todayInterviews: data?.todayInterviews ?? [],
    pastInterviews: data?.pastInterviews ?? [],
    isLoading,
    error: error instanceof Error ? error.message : null,
    copiedId,
    fetchInterviews,
    handleOpenMeeting,
    handleCopyLink,
    handleReschedule,
    handleReject,
    handleOpenJob,
  }
}
