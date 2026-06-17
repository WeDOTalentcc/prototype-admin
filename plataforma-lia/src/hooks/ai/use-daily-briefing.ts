"use client"

/**
 * useDailyBriefing — busca o briefing diário do recrutador (P3-1).
 *
 * Consumidor do endpoint GET /api/v1/briefing?user_id=
 * Proxy: /api/backend-proxy/briefing
 *
 * Vue/Nuxt: mapeia para composable useDailyBriefing() em setup().
 */
import { useState, useCallback } from "react"
import useSWR from "swr"
import { useJWTAuth } from "@/contexts/auth-context"

export interface UrgentAction {
  id: string
  type: string
  title: string
  description: string
  priority: "critical" | "high" | "medium"
  action_label: string
  action_type: string
  related_job_id?: string
  related_candidate_id?: string
}

export interface BriefingInsight {
  type: "attention" | "opportunity" | "suggestion" | "info" | "success"
  icon: string
  title: string
  description: string
}

export interface DailyBriefingData {
  date: string
  greeting: string
  urgent_actions: UrgentAction[]
  pipeline_summary: {
    active_jobs: number
    total_candidates: number
    candidates_to_contact: number
    awaiting_feedback: number
    offers_pending: number
    stages_summary: { stage: string; count: number; label: string }[]
  }
  today_schedule: {
    id: string
    type: string
    title: string
    time: string
    duration_minutes?: number
    location?: string
    status?: string
  }[]
  metrics: {
    backlog_count: number
    critical_count: number
    interviews_today: number
    pending_offers: number
  }
  insights: BriefingInsight[]
}

export interface UseDailyBriefingResult {
  briefing: DailyBriefingData | null
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

const jsonFetcher = (url: string) =>
  fetch(url).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    return r.json()
  })

export function useDailyBriefing(): UseDailyBriefingResult {
  const { user } = useJWTAuth()
  const [refreshError, setRefreshError] = useState<string | null>(null)

  const key = user?.id ? `/api/backend-proxy/briefing?user_id=${user.id}` : null

  const { data, error, isLoading, mutate } = useSWR<DailyBriefingData>(key, jsonFetcher)

  const refresh = useCallback(async () => {
    if (!user?.id) return
    try {
      setRefreshError(null)
      await fetch("/api/backend-proxy/briefing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id }),
      })
      await mutate()
    } catch (err) {
      setRefreshError(err instanceof Error ? err.message : "Erro ao atualizar briefing")
    }
  }, [user?.id, mutate])

  return {
    briefing: data ?? null,
    loading: isLoading,
    error: refreshError ?? error?.message ?? null,
    refresh,
  }
}
