"use client"

import { useState, useEffect, useCallback, useMemo, type RefObject } from "react"
import { useRouter } from "next/navigation"
import { liaApi } from "@/services/lia-api"
import { type CommunicationType } from "@/components/modals/unified-communication-modal"

interface UseKanbanDataEffectsParams {
  job?: Record<string, unknown>
  candidatesData: Record<string, Record<string, unknown>[]>
  setCandidatesData: (fn: (prev: Record<string, Record<string, unknown>[]>) => Record<string, Record<string, unknown>[]>) => void
  isLoadingCandidates: boolean
  currentJob: Record<string, unknown>
  allTableCandidates: Record<string, unknown>[]
  chatScrollRef: RefObject<HTMLElement | null>
  liaMessages: unknown[]
  isLiaLoading: boolean
  setUnifiedModalCandidate: (c: unknown) => void
  setUnifiedModalType: (t: CommunicationType) => void
  setUnifiedModalOpen: (v: boolean) => void
}

export function useKanbanDataEffects({
  job, candidatesData, setCandidatesData, isLoadingCandidates,
  currentJob, allTableCandidates, chatScrollRef, liaMessages, isLiaLoading,
  setUnifiedModalCandidate, setUnifiedModalType, setUnifiedModalOpen,
}: UseKanbanDataEffectsParams) {
  const router = useRouter()

  const [saturationData, setSaturationData] = useState<{ is_saturated: boolean; approved_count: number; saturation_threshold: number; saturation_percentage: number } | null>(null)

  const saturationJobId = job?.backendId || job?.id
  useEffect(() => {
    if (!saturationJobId) return
    fetch(`/api/backend-proxy/job-vacancies/${saturationJobId}/saturation-status/`)
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data) setSaturationData(data) })
      .catch((err) => { console.error('[useKanbanDataEffects] saturation-status fetch failed', err) })
  }, [saturationJobId])

  useEffect(() => {
    if (isLoadingCandidates) return
    const jobId = (currentJob?.backendId || currentJob?.id)?.toString()
    if (!jobId) return

    const hasAnyCandidates = Object.values(candidatesData).some(arr => arr.length > 0)
    if (!hasAnyCandidates) return

    liaApi.wsiGetCandidatesScores(jobId)
      .then(data => {
        if (!data?.candidates || Object.keys(data.candidates).length === 0) return

        setCandidatesData(prev => {
          const updated: Record<string, Record<string, unknown>[]> = {}
          for (const [stageId, candidates] of Object.entries(prev)) {
            updated[stageId] = candidates.map((c: Record<string, unknown>) => {
              const wsiData = data.candidates[c.id as string]
              if (!wsiData) return c
              return {
                ...c,
                liaScore: wsiData.overall_wsi,
                score: wsiData.overall_wsi,
                wsiScore: wsiData.overall_wsi,
                wsiTechnical: wsiData.technical_wsi,
                wsiBehavioral: wsiData.behavioral_wsi,
                wsiClassification: wsiData.classification,
                wsiPercentile: wsiData.percentile,
                // Audit task #530 (G23-02 frontend) — flag exposta pelo backend
                // para o kanban marcar visualmente o score WSI calculado em
                // modo degradado (sem Camada 2). UI consome em
                // KanbanCardScores e KanbanScoreCells.
                triagemDegraded: wsiData.degraded_quality === true,
              }
            })
          }
          return updated
        })
      })
      .catch((err: Error & { status?: number }) => {
        // Bug #303: 401/403 já dispara o redirect de relogin no helper do
        // wsi-api; aqui só engolimos pra não estourar o overlay do Next.
        // Para 5xx/erros de rede, mantemos o board renderizado (sem badges
        // de score) e logamos discretamente em debug — sem `console.error`,
        // que estoura o overlay em dev e polui o Sentry/console em prod.
        if (err?.status === 401 || err?.status === 403) return
        if (typeof console !== 'undefined' && typeof console.debug === 'function') {
          console.debug('[useKanbanDataEffects] wsiGetCandidatesScores indisponível (board segue sem scores)', {
            status: err?.status,
            message: err?.message,
          })
        }
      })
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: candidatesData/setCandidatesData excluded to avoid infinite loop
  }, [isLoadingCandidates, currentJob?.id, currentJob?.backendId])

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [liaMessages, isLiaLoading, chatScrollRef])

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (detail?.action_id === "move_candidate") {
        setTimeout(() => router.refresh(), 500)
      }
    }
    window.addEventListener("lia:action-executed", handler)
    return () => window.removeEventListener("lia:action-executed", handler)
  }, [router])

  const findCandidateById = useCallback((id: string) => {
    return allTableCandidates.find((c: Record<string, unknown>) => String(c.id) === String(id))
  }, [allTableCandidates])

  const openUnifiedModal = useCallback((candidate: Record<string, unknown>, type: CommunicationType) => {
    setUnifiedModalCandidate(candidate)
    setUnifiedModalType(type)
    setUnifiedModalOpen(true)
  }, [setUnifiedModalCandidate, setUnifiedModalType, setUnifiedModalOpen])

  return { saturationData, setSaturationData, findCandidateById, openUnifiedModal, router }
}
