"use client"

import { useState, useEffect, useCallback } from 'react'
import { 
  saasMetricsService, 
  SaasMetricsSummary,
  RevenueByPlan,
  ClientGrowth,
  UsageMetrics
} from '@/services/admin/saas-metrics'

export type { SaasMetricsSummary, RevenueByPlan, ClientGrowth, UsageMetrics }

interface UseSaasMetricsOptions {
  autoFetch?: boolean
  growthPeriod?: 'week' | 'month' | 'quarter' | 'year'
}

interface UseSaasMetricsResult {
  mrr: number
  mrrDelta?: number
  mrrDeltaPercent?: number
  arr?: number
  activeClients: number
  activeClientsDelta?: number
  totalUsers: number
  totalUsersDelta?: number
  churnRate: number
  churnRateDelta?: number
  ltv?: number
  cac?: number
  ltvCacRatio?: number
  revenueByPlan: RevenueByPlan[]
  clientGrowth: ClientGrowth[]
  usageMetrics: UsageMetrics | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  refetchSummary: () => Promise<void>
  refetchRevenueByPlan: () => Promise<void>
  refetchClientGrowth: () => Promise<void>
  refetchUsageMetrics: () => Promise<void>
}

export function useSaasMetrics(options: UseSaasMetricsOptions = {}): UseSaasMetricsResult {
  const { autoFetch = true, growthPeriod = 'month' } = options

  const [summary, setSummary] = useState<SaasMetricsSummary | null>(null)
  const [revenueByPlan, setRevenueByPlan] = useState<RevenueByPlan[]>([])
  const [clientGrowth, setClientGrowth] = useState<ClientGrowth[]>([])
  const [usageMetrics, setUsageMetrics] = useState<UsageMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refetchSummary = useCallback(async () => {
    try {
      const data = await saasMetricsService.getSummary()
      setSummary(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch summary')
    }
  }, [])

  const refetchRevenueByPlan = useCallback(async () => {
    try {
      const data = await saasMetricsService.getRevenueByPlan()
      setRevenueByPlan(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch revenue by plan')
    }
  }, [])

  const refetchClientGrowth = useCallback(async () => {
    try {
      const data = await saasMetricsService.getClientGrowth(growthPeriod)
      setClientGrowth(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch client growth')
    }
  }, [growthPeriod])

  const refetchUsageMetrics = useCallback(async () => {
    try {
      const data = await saasMetricsService.getUsageMetrics()
      setUsageMetrics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch usage metrics')
    }
  }, [])

  const refetch = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const [summaryData, revenueData, growthData, usageData] = await Promise.all([
        saasMetricsService.getSummary(),
        saasMetricsService.getRevenueByPlan(),
        saasMetricsService.getClientGrowth(growthPeriod),
        saasMetricsService.getUsageMetrics()
      ])
      
      setSummary(summaryData)
      setRevenueByPlan(revenueData)
      setClientGrowth(growthData)
      setUsageMetrics(usageData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch SaaS metrics')
    } finally {
      setIsLoading(false)
    }
  }, [growthPeriod])

  useEffect(() => {
    if (autoFetch) {
      refetch()
    }
  }, [autoFetch, refetch])

  return {
    mrr: summary?.mrr ?? 0,
    mrrDelta: summary?.mrrDelta,
    mrrDeltaPercent: summary?.mrrDeltaPercent,
    arr: summary?.arr,
    activeClients: summary?.activeClients ?? 0,
    activeClientsDelta: summary?.activeClientsDelta,
    totalUsers: summary?.totalUsers ?? 0,
    totalUsersDelta: summary?.totalUsersDelta,
    churnRate: summary?.churnRate ?? 0,
    churnRateDelta: summary?.churnRateDelta,
    ltv: summary?.ltv,
    cac: summary?.cac,
    ltvCacRatio: summary?.ltvCacRatio,
    revenueByPlan,
    clientGrowth,
    usageMetrics,
    isLoading,
    error,
    refetch,
    refetchSummary,
    refetchRevenueByPlan,
    refetchClientGrowth,
    refetchUsageMetrics
  }
}

export default useSaasMetrics
