import { apiClient, ApiClientOptions, ApiClientError } from './api-client'

export interface ClientRevenueMetrics {
  mrr: number
  mrrChange: number
  mrrTrend: 'up' | 'down' | 'stable'
  arr: number
  ltv: number
  ltvMonths: number
  planName: string
  contractStart: string
  contractEnd: string
  billingCycle: 'monthly' | 'yearly' | 'quarterly'
}

export interface ClientAcquisitionMetrics {
  cac: number
  paybackMonths: number
  referralSource: string
  salesCycle: number
}

export interface ClientUsageMetrics {
  aiCreditsUsed: number
  aiCreditsLimit: number
  usersActive: number
  usersLimit: number
  jobsActive: number
  jobsLimit: number
  storageUsedMB: number
  storageLimitMB: number
}

export interface ClientHealthMetrics {
  churnRisk: 'low' | 'medium' | 'high'
  healthScore: number
  lastLoginDays: number
  npsScore: number
  supportTickets: number
  engagementLevel: 'low' | 'medium' | 'high'
}

export interface ClientPayment {
  id: string
  date: string
  amount: number
  status: 'paid' | 'pending' | 'overdue' | 'failed'
  method: string
}

export interface ClientSaasMetrics {
  revenue: ClientRevenueMetrics
  acquisition: ClientAcquisitionMetrics
  usage: ClientUsageMetrics
  health: ClientHealthMetrics
  payments: ClientPayment[]
}

export interface PlatformAggregateMetrics {
  revenue: {
    mrr: number
    arr: number
    growthRate: number
    mrrChange: number
  }
  clients: {
    activeClients: number
    trialClients: number
    churnedClients: number
    totalClients: number
    churnRate: number
  }
  usage: {
    totalAITokens: number
    totalUsers: number
    avgTokensPerClient: number
    activeSessionsToday: number
  }
  costs: {
    infrastructureCost: number
    aiApiCost: number
    totalMonthlyCost: number
    costPerClient: number
  }
  lastUpdated: string
}

export { ApiClientError }

const MOCK_CLIENT_METRICS: ClientSaasMetrics = {
  revenue: {
    mrr: 4500,
    mrrChange: 500,
    mrrTrend: 'up',
    arr: 54000,
    ltv: 162000,
    ltvMonths: 36,
    planName: 'Professional',
    contractStart: '2024-03-15',
    contractEnd: '2025-03-14',
    billingCycle: 'monthly'
  },
  acquisition: {
    cac: 2800,
    paybackMonths: 0.62,
    referralSource: 'Indicação',
    salesCycle: 45
  },
  usage: {
    aiCreditsUsed: 8500,
    aiCreditsLimit: 15000,
    usersActive: 12,
    usersLimit: 20,
    jobsActive: 8,
    jobsLimit: 25,
    storageUsedMB: 2340,
    storageLimitMB: 5000
  },
  health: {
    churnRisk: 'low',
    healthScore: 92,
    lastLoginDays: 1,
    npsScore: 9,
    supportTickets: 2,
    engagementLevel: 'high'
  },
  payments: [
    { id: '1', date: '2024-12-01', amount: 4500, status: 'paid', method: 'Cartão' },
    { id: '2', date: '2024-11-01', amount: 4500, status: 'paid', method: 'Cartão' },
    { id: '3', date: '2024-10-01', amount: 4000, status: 'paid', method: 'Boleto' },
    { id: '4', date: '2024-09-01', amount: 4000, status: 'paid', method: 'Boleto' },
    { id: '5', date: '2024-08-01', amount: 4000, status: 'paid', method: 'Pix' }
  ]
}

const MOCK_PLATFORM_METRICS: PlatformAggregateMetrics = {
  revenue: {
    mrr: 24500,
    arr: 294000,
    growthRate: 12.5,
    mrrChange: 2800,
  },
  clients: {
    activeClients: 12,
    trialClients: 3,
    churnedClients: 1,
    totalClients: 16,
    churnRate: 2.1,
  },
  usage: {
    totalAITokens: 1245000,
    totalUsers: 47,
    avgTokensPerClient: 103750,
    activeSessionsToday: 23,
  },
  costs: {
    infrastructureCost: 850,
    aiApiCost: 3200,
    totalMonthlyCost: 4050,
    costPerClient: 337.5,
  },
  lastUpdated: new Date().toISOString(),
}

class SaasMetricsClientService {
  async getClientMetrics(
    clientId: string,
    options?: Omit<ApiClientOptions, 'clientId'>
  ): Promise<ClientSaasMetrics> {
    try {
      return await apiClient.get<ClientSaasMetrics>(
        `/saas-metrics/${clientId}`,
        { clientId, ...options }
      )
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return { ...MOCK_CLIENT_METRICS }
    }
  }

  async getClientRevenue(
    clientId: string,
    options?: Omit<ApiClientOptions, 'clientId'>
  ): Promise<ClientRevenueMetrics> {
    try {
      return await apiClient.get<ClientRevenueMetrics>(
        `/saas-metrics/${clientId}/revenue`,
        { clientId, ...options }
      )
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return { ...MOCK_CLIENT_METRICS.revenue }
    }
  }

  async getClientUsage(
    clientId: string,
    options?: Omit<ApiClientOptions, 'clientId'>
  ): Promise<ClientUsageMetrics> {
    try {
      return await apiClient.get<ClientUsageMetrics>(
        `/saas-metrics/${clientId}/usage`,
        { clientId, ...options }
      )
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return { ...MOCK_CLIENT_METRICS.usage }
    }
  }

  async getClientHealth(
    clientId: string,
    options?: Omit<ApiClientOptions, 'clientId'>
  ): Promise<ClientHealthMetrics> {
    try {
      return await apiClient.get<ClientHealthMetrics>(
        `/saas-metrics/${clientId}/health`,
        { clientId, ...options }
      )
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return { ...MOCK_CLIENT_METRICS.health }
    }
  }

  async getClientPayments(
    clientId: string,
    options?: Omit<ApiClientOptions, 'clientId'>
  ): Promise<ClientPayment[]> {
    try {
      const data = await apiClient.get<ClientPayment[] | { items: ClientPayment[] }>(
        `/saas-metrics/${clientId}/payments`,
        { clientId, ...options }
      )
      return Array.isArray(data) ? data : data.items || []
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return [...MOCK_CLIENT_METRICS.payments]
    }
  }

  async getPlatformMetrics(options?: ApiClientOptions): Promise<PlatformAggregateMetrics> {
    try {
      return await apiClient.get<PlatformAggregateMetrics>(
        `/saas-metrics/aggregate`,
        options
      )
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return {
        ...MOCK_PLATFORM_METRICS,
        lastUpdated: new Date().toISOString()
      }
    }
  }
}

export const saasMetricsClientService = new SaasMetricsClientService()
