import { apiClient, ApiClientOptions, ApiClientError } from './api-client'

export interface UsageSummary {
  totalTokens: number
  monthlyLimit: number
  usagePercentage: number
  estimatedCostBRL: number
  apiCalls: number
  creditsRemaining: number
}

export interface DailyUsage {
  date: string
  tokens: number
  calls?: number
  cost?: number
}

export interface AgentUsage {
  agent: string
  label: string
  tokens: number
  calls: number
  percentage: number
}

export interface AIConsumptionFilters {
  companyId: string
  startDate?: string
  endDate?: string
  period?: 'day' | 'week' | 'month'
}

export { ApiClientError }

class AIConsumptionService {
  async getSummary(clientId: string, options?: Omit<ApiClientOptions, 'clientId'>): Promise<UsageSummary> {
    try {
      return await apiClient.get<UsageSummary>(
        `/ai-consumption/summary?company_id=${encodeURIComponent(clientId)}`,
        { clientId, ...options }
      )
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return this.getMockSummary()
    }
  }

  async getDailyUsage(
    clientId: string, 
    startDate?: string, 
    endDate?: string,
    options?: Omit<ApiClientOptions, 'clientId'>
  ): Promise<DailyUsage[]> {
    try {
      const params = new URLSearchParams({ company_id: clientId })
      if (startDate) params.set('start_date', startDate)
      if (endDate) params.set('end_date', endDate)
      
      const data = await apiClient.get<DailyUsage[] | { items: DailyUsage[] }>(
        `/ai-consumption/daily?${params}`,
        { clientId, ...options }
      )
      
      return Array.isArray(data) ? data : data.items || []
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return this.getMockDailyUsage()
    }
  }

  async getByAgent(clientId: string, options?: Omit<ApiClientOptions, 'clientId'>): Promise<AgentUsage[]> {
    try {
      const data = await apiClient.get<AgentUsage[] | { items: AgentUsage[] }>(
        `/ai-consumption/by-agent?company_id=${encodeURIComponent(clientId)}`,
        { clientId, ...options }
      )
      
      return Array.isArray(data) ? data : data.items || []
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) {
          throw error
        }
      }
      return this.getMockAgentUsage()
    }
  }

  async getAll(
    clientId: string,
    options?: Omit<ApiClientOptions, 'clientId'>
  ): Promise<{
    summary: UsageSummary
    dailyUsage: DailyUsage[]
    agentUsage: AgentUsage[]
  }> {
    const [summary, dailyUsage, agentUsage] = await Promise.all([
      this.getSummary(clientId, options),
      this.getDailyUsage(clientId, undefined, undefined, options),
      this.getByAgent(clientId, options)
    ])

    return { summary, dailyUsage, agentUsage }
  }

  private getMockSummary(): UsageSummary {
    return {
      totalTokens: 847523,
      monthlyLimit: 1000000,
      usagePercentage: 84.75,
      estimatedCostBRL: 423.76,
      apiCalls: 12847,
      creditsRemaining: 152477
    }
  }

  private getMockDailyUsage(): DailyUsage[] {
    return Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      tokens: Math.floor(Math.random() * 50000) + 10000,
      calls: Math.floor(Math.random() * 500) + 100
    }))
  }

  private getMockAgentUsage(): AgentUsage[] {
    return [
      { agent: 'screening', label: 'Screening Agent', tokens: 312450, calls: 4521, percentage: 36.8 },
      { agent: 'scoring', label: 'Scoring Agent', tokens: 234120, calls: 3892, percentage: 27.6 },
      { agent: 'interview', label: 'Interview Agent', tokens: 156780, calls: 892, percentage: 18.5 },
      { agent: 'cv_parsing', label: 'CV Parsing', tokens: 98432, calls: 2341, percentage: 11.6 },
      { agent: 'search', label: 'Search Agent', tokens: 45741, calls: 1201, percentage: 5.4 },
    ]
  }
}

export const aiConsumptionService = new AIConsumptionService()
