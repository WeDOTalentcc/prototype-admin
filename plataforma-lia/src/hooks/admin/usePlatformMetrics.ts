"use client"

import useSWR from "swr"
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
  const { data, error, isLoading, mutate } = useSWR(
    "adminPlatformMetrics",
    () => saasMetricsClientService.getPlatformMetrics()
  )

  return {
    metrics: data ?? null,
    isLoading,
    error: error instanceof ApiClientError ? error.message
      : error instanceof Error ? error.message
      : error ? String(error) : null,
    refetch: () => mutate(),
  }
}
