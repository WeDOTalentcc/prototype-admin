"use client"

/**
 * useDailyBriefing — busca o briefing diário do recrutador (P3-1).
 *
 * Consumidor do endpoint GET /api/v1/briefing?user_id=
 * Proxy: /api/backend-proxy/briefing
 *
 * Vue/Nuxt: mapeia para composable useDailyBriefing() em setup().
 */
import { useState, useEffect, useCallback } from "react"
import { useAuth } from "@/components/auth-context"

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

export function useDailyBriefing(): UseDailyBriefingResult {
  const { user } = useAuth()
  const [briefing, setBriefing] = useState<DailyBriefingData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchBriefing = useCallback(async () => {
    if (!user?.id) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/backend-proxy/briefing?user_id=${user.id}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setBriefing(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar briefing")
    } finally {
      setLoading(false)
    }
  }, [user?.id])

  const refresh = useCallback(async () => {
    if (!user?.id) return
    setLoading(true)
    setError(null)
    try {
      await fetch("/api/backend-proxy/briefing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: user.id }),
      })
      await fetchBriefing()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar briefing")
      setLoading(false)
    }
  }, [user?.id, fetchBriefing])

  useEffect(() => {
    fetchBriefing()
  }, [fetchBriefing])

  return { briefing, loading, error, refresh }
}
