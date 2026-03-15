import { apiClient, ApiClientOptions, ApiClientError } from './api-client'

export interface SaasMetricsSummary {
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
}

export interface RevenueByPlan {
  planId: string
  planName: string
  clientsCount: number
  revenue: number
  percentage: number
}

export interface ClientGrowth {
  date: string
  totalClients: number
  newClients: number
  churnedClients: number
}

export interface UsageMetrics {
  totalApiCalls: number
  totalTokensUsed: number
  avgTokensPerClient: number
  peakHour?: string
  peakUsage?: number
}

export { ApiClientError }

class SaasMetricsService {
  async getSummary(options?: ApiClientOptions): Promise<SaasMetricsSummary> {
    try {
      return await apiClient.get<SaasMetricsSummary>(
        `/saas-metrics/summary`,
        options
      )
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching SaaS metrics summary:', error.message)
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return this.getMockSummary()
    }
  }

  async getRevenueByPlan(options?: ApiClientOptions): Promise<RevenueByPlan[]> {
    try {
      const data = await apiClient.get<RevenueByPlan[] | { items: RevenueByPlan[] }>(
        `/saas-metrics/revenue-by-plan`,
        options
      )
      return Array.isArray(data) ? data : data.items || []
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching revenue by plan:', error.message)
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return this.getMockRevenueByPlan()
    }
  }

  async getClientGrowth(
    period: 'week' | 'month' | 'quarter' | 'year' = 'month',
    options?: ApiClientOptions
  ): Promise<ClientGrowth[]> {
    try {
      const data = await apiClient.get<ClientGrowth[] | { items: ClientGrowth[] }>(
        `/saas-metrics/client-growth?period=${period}`,
        options
      )
      return Array.isArray(data) ? data : data.items || []
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching client growth:', error.message)
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return this.getMockClientGrowth()
    }
  }

  async getUsageMetrics(options?: ApiClientOptions): Promise<UsageMetrics> {
    try {
      return await apiClient.get<UsageMetrics>(
        `/saas-metrics/usage`,
        options
      )
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching usage metrics:', error.message)
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return this.getMockUsageMetrics()
    }
  }

  private getMockSummary(): SaasMetricsSummary {
    return {
      mrr: 125750,
      mrrDelta: 8230,
      mrrDeltaPercent: 7.0,
      arr: 1509000,
      activeClients: 47,
      activeClientsDelta: 3,
      totalUsers: 342,
      totalUsersDelta: 28,
      churnRate: 2.1,
      churnRateDelta: -0.3,
      ltv: 18500,
      cac: 3200,
      ltvCacRatio: 5.78
    }
  }

  private getMockRevenueByPlan(): RevenueByPlan[] {
    return [
      { planId: 'enterprise', planName: 'Enterprise', clientsCount: 12, revenue: 71400, percentage: 56.8 },
      { planId: 'professional', planName: 'Professional', clientsCount: 23, revenue: 39100, percentage: 31.1 },
      { planId: 'starter', planName: 'Starter', clientsCount: 12, revenue: 15250, percentage: 12.1 },
    ]
  }

  private getMockClientGrowth(): ClientGrowth[] {
    return Array.from({ length: 12 }, (_, i) => {
      const date = new Date()
      date.setMonth(date.getMonth() - (11 - i))
      return {
        date: date.toISOString().split('T')[0],
        totalClients: 35 + i * 1 + Math.floor(Math.random() * 2),
        newClients: Math.floor(Math.random() * 5) + 1,
        churnedClients: Math.floor(Math.random() * 2)
      }
    })
  }

  private getMockUsageMetrics(): UsageMetrics {
    return {
      totalApiCalls: 1547832,
      totalTokensUsed: 45678234,
      avgTokensPerClient: 971877,
      peakHour: '14:00',
      peakUsage: 12450
    }
  }
}

export const saasMetricsService = new SaasMetricsService()
