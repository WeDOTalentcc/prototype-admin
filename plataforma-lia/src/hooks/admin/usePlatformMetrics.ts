"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import {
  saasMetricsClientService,
  PlatformAggregateMetrics,
  ApiClientError,
} from "@/services/admin/saas-metrics-service"

export interface RevenueMetrics {
  mrr: number
  arr: number
  growthRate: number
  mrrChange: number
}

export interface ClientMetrics {
  activeClients: number
  trialClients: number
  churnedClients: number
  totalClients: number
  churnRate: number
}

export interface UsageMetrics {
  totalAITokens: number
  totalUsers: number
  avgTokensPerClient: number
  activeSessionsToday: number
}

export interface CostMetrics {
  infrastructureCost: number
  aiApiCost: number
  totalMonthlyCost: number
  costPerClient: number
}

export interface PlatformMetrics {
  revenue: RevenueMetrics
  clients: ClientMetrics
  usage: UsageMetrics
  costs: CostMetrics
  lastUpdated: string
}

export interface UsePlatformMetricsResult {
  metrics: PlatformMetrics | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function usePlatformMetrics(): UsePlatformMetricsResult {
  const [metrics, setMetrics] = useState<PlatformMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const isMountedRef = useRef(true)

  const fetchMetrics = useCallback(async () => {
    if (isMountedRef.current) setIsLoading(true)
    if (isMountedRef.current) setError(null)

    try {
      const data: PlatformAggregateMetrics = await saasMetricsClientService.getPlatformMetrics()
      if (isMountedRef.current) setMetrics(data)
    } catch (err) {
      if (!isMountedRef.current) return
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else {
        setError("Erro ao carregar métricas da plataforma")
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    fetchMetrics()
    return () => { isMountedRef.current = false }
  }, [fetchMetrics])

  return {
    metrics,
    isLoading,
    error,
    refetch: fetchMetrics,
  }
}
