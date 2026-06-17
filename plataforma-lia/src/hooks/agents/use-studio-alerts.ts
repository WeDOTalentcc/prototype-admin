"use client"

import { useEffect, useState, useRef, useCallback } from "react"

// ── Types ──────────────────────────────────────────────────────────────────

export type AlertType =
  | "SOURCING_PAUSED"
  | "QUOTA_NEAR"
  | "TWIN_LOW_ACCURACY"
  | "ALIGNMENT_PENDING"

export interface StudioAlert {
  type: AlertType
  /** Human-readable short description */
  message: string
  /** Related entity ID (agent, twin, job) */
  entityId?: string
  severity: "warning" | "error"
}

export interface TwinSummary {
  totalTwins: number
  avgAccuracy: number | null
}

interface UseStudioAlertsReturn {
  alerts: StudioAlert[]
  alertCount: number
  twinSummary: TwinSummary
  isLoading: boolean
  refresh: () => void
}

const POLL_INTERVAL_MS = 60_000

// ── Fetcher ────────────────────────────────────────────────────────────────

interface FetchAlertsResult {
  alerts: StudioAlert[]
  twinSummary: TwinSummary
}

async function fetchAlerts(): Promise<FetchAlertsResult> {
  const results: StudioAlert[] = []
  let twinSummary: TwinSummary = { totalTwins: 0, avgAccuracy: null }

  const [agentsRes, twinsRes, quotaRes, alignmentsRes] = await Promise.allSettled([
    fetch("/api/backend-proxy/custom-agents?limit=100", { credentials: "include" }),
    fetch("/api/backend-proxy/digital-twins?limit=100",  { credentials: "include" }),
    fetch("/api/backend-proxy/agent-quota",              { credentials: "include" }),
    fetch("/api/backend-proxy/manager-alignments?status=pending&limit=50", { credentials: "include" }),
  ])

  // SOURCING_PAUSED — active sourcing agent paused for > 24h
  if (agentsRes.status === "fulfilled" && agentsRes.value.ok) {
    try {
      const data = await agentsRes.value.json()
      const agents = Array.isArray(data?.agents) ? data.agents : Array.isArray(data) ? data : []
      const cutoff = Date.now() - 24 * 60 * 60 * 1000

      for (const a of agents) {
        if (
          a.status === "paused" &&
          a.updated_at &&
          new Date(a.updated_at).getTime() < cutoff
        ) {
          results.push({
            type: "SOURCING_PAUSED",
            message: `Agente "${a.name ?? a.agent_name ?? a.id}" pausado há mais de 24h`,
            entityId: String(a.id),
            severity: "warning",
          })
        }
      }
    } catch (error) { /* */ }
      console.error("[use-studio-alerts] Error:", error)
  }

  // TWIN_LOW_ACCURACY — accuracy_pct < 60%
  if (twinsRes.status === "fulfilled" && twinsRes.value.ok) {
    try {
      const data = await twinsRes.value.json()
      const twins = Array.isArray(data?.twins) ? data.twins : Array.isArray(data) ? data : []

      const accuracies = twins
        .map((tw: { accuracy_pct?: number }) => tw.accuracy_pct)
        .filter((v: number | undefined): v is number => typeof v === "number")
      twinSummary = {
        totalTwins: twins.length,
        avgAccuracy: accuracies.length > 0
          ? Math.round(accuracies.reduce((a: number, b: number) => a + b, 0) / accuracies.length)
          : null,
      }

      for (const tw of twins) {
        if (
          typeof tw.accuracy_pct === "number" &&
          tw.accuracy_pct < 60
        ) {
          results.push({
            type: "TWIN_LOW_ACCURACY",
            message: `Twin "${tw.name ?? tw.id}" com acurácia baixa (${tw.accuracy_pct}%)`,
            entityId: String(tw.id),
            severity: "warning",
          })
        }
      }
        console.error("[use-studio-alerts] Error:", error)
    } catch { /* */ }
  }

  // QUOTA_NEAR — agent usage > 80%
  if (quotaRes.status === "fulfilled" && quotaRes.value.ok) {
    try {
      const data = await quotaRes.value.json()
      const used = data?.used ?? data?.agent_count ?? 0
      const limit = data?.limit ?? data?.max_agents ?? 10
      if (limit > 0 && used / limit >= 0.8) {
        results.push({
          type: "QUOTA_NEAR",
          message: `Quota de agentes quase esgotada (${used}/${limit})`,
          severity: "error",
        })
          console.error("[use-studio-alerts] Error:", error)
      }
    } catch { /* */ }
  }

  // ALIGNMENT_PENDING — pending alignment requests nearing expiry (>48h pending)
  if (alignmentsRes.status === "fulfilled" && alignmentsRes.value.ok) {
    try {
      const data = await alignmentsRes.value.json()
      const alignments = Array.isArray(data?.alignments) ? data.alignments
        : Array.isArray(data) ? data : []
      const cutoff = Date.now() - 48 * 60 * 60 * 1000
      for (const al of alignments) {
        if (
          al.status === "pending" &&
          al.created_at &&
          new Date(al.created_at).getTime() < cutoff
        ) {
          results.push({
            type: "ALIGNMENT_PENDING",
            message: `Alinhamento para vaga "${al.job_vacancy_id}" aguarda gestor há mais de 48h`,
            entityId: String(al.id),
            severity: "warning",
          })
            console.error("[use-studio-alerts] Error:", error)
        }
      }
    } catch { /* */ }
  }

  return { alerts: results, twinSummary }
}

// ── Hook ───────────────────────────────────────────────────────────────────

export function useStudioAlerts(): UseStudioAlertsReturn {
  const [alerts, setAlerts] = useState<StudioAlert[]>([])
  const [twinSummary, setTwinSummary] = useState<TwinSummary>({ totalTwins: 0, avgAccuracy: null })
  const [isLoading, setIsLoading] = useState(true)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const refresh = useCallback(() => {
    fetchAlerts().then(({ alerts: a, twinSummary: ts }) => {
      setAlerts(a)
      setTwinSummary(ts)
      setIsLoading(false)
    }).catch(() => setIsLoading(false))
  }, [])

  useEffect(() => {
    refresh()
    intervalRef.current = setInterval(refresh, POLL_INTERVAL_MS)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [refresh])

  return {
    alerts,
    alertCount: alerts.length,
    twinSummary,
    isLoading,
    refresh,
  }
}
