"use client"

import { useCallback } from "react"
import useSWR from "swr"
import {
  lgpdService,
  LGPDStats,
  DPORegistry,
  BreachNotification,
  AutomatedDecision,
  BreachListParams,
  AutomatedDecisionListParams,
} from "@/services/admin/lgpd-service"

export interface UseLGPDComplianceResult {
  stats: LGPDStats | null
  dpo: DPORegistry | null
  breaches: BreachNotification[]
  decisions: AutomatedDecision[]
  totalBreaches: number
  totalDecisions: number
  isLoading: boolean
  error: Error | null
  refetch: () => void
  fetchBreaches: (params?: BreachListParams) => Promise<void>
  fetchDecisions: (params?: AutomatedDecisionListParams) => Promise<void>
}

export function useLGPDCompliance(clientId: string): UseLGPDComplianceResult {
  const { data, error, isLoading, mutate } = useSWR(
    clientId ? ["adminLGPDCompliance", clientId] : null,
    async ([, id]) => {
      const [statsData, dpoData, breachesData, decisionsData] = await Promise.all([
        lgpdService.getStats(id),
        lgpdService.getDPO(id),
        lgpdService.getBreaches(id, { limit: 10 }),
        lgpdService.getAutomatedDecisions(id, { limit: 10 }),
      ])
      return {
        stats: statsData,
        dpo: dpoData,
        breaches: breachesData.breaches,
        totalBreaches: breachesData.total,
        decisions: decisionsData.decisions,
        totalDecisions: decisionsData.total,
      }
    }
  )

  const fetchBreaches = useCallback(async (params?: BreachListParams) => {
    if (!clientId) return
    try {
      const result = await lgpdService.getBreaches(clientId, params)
      await mutate(
        (prev) => prev ? { ...prev, breaches: result.breaches, totalBreaches: result.total } : prev,
        false
      )
    } catch (err) {
    }
  }, [clientId, mutate])

  const fetchDecisions = useCallback(async (params?: AutomatedDecisionListParams) => {
    if (!clientId) return
    try {
      const result = await lgpdService.getAutomatedDecisions(clientId, params)
      await mutate(
        (prev) => prev ? { ...prev, decisions: result.decisions, totalDecisions: result.total } : prev,
        false
      )
    } catch (err) {
    }
  }, [clientId, mutate])

  return {
    stats: data?.stats ?? null,
    dpo: data?.dpo ?? null,
    breaches: data?.breaches ?? [],
    decisions: data?.decisions ?? [],
    totalBreaches: data?.totalBreaches ?? 0,
    totalDecisions: data?.totalDecisions ?? 0,
    isLoading,
    error: error instanceof Error ? error : error ? new Error(String(error)) : null,
    refetch: () => mutate(),
    fetchBreaches,
    fetchDecisions,
  }
}

export type { LGPDStats, DPORegistry, BreachNotification, AutomatedDecision }
