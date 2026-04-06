export interface UsageSummary {
  total_tokens: number
  total_cost: number
  total_requests: number
  period_start: string
  period_end: string
}

export interface DailyUsage {
  date: string
  tokens: number
  cost: number
  requests: number
}

export interface AgentUsage {
  agent_id: string
  agent_name: string
  tokens: number
  cost: number
  requests: number
  percentage: number
}

const BASE_URL = '/api/backend-proxy'

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.statusText}`)
  return res.json()
}

export const aiConsumptionService = {
  getSummary: (clientId: string) =>
    fetchJSON<UsageSummary>(`${BASE_URL}/ai-consumption/${clientId}/summary`),

  getDailyUsage: (clientId: string, startDate?: string, endDate?: string) => {
    const params = new URLSearchParams()
    if (startDate) params.set('start_date', startDate)
    if (endDate) params.set('end_date', endDate)
    const qs = params.toString()
    return fetchJSON<DailyUsage[]>(`${BASE_URL}/ai-consumption/${clientId}/daily${qs ? `?${qs}` : ''}`)
  },

  getByAgent: (clientId: string) =>
    fetchJSON<AgentUsage[]>(`${BASE_URL}/ai-consumption/${clientId}/by-agent`),

  getAll: async (clientId: string) => {
    const [summary, dailyUsage, agentUsage] = await Promise.all([
      aiConsumptionService.getSummary(clientId),
      aiConsumptionService.getDailyUsage(clientId),
      aiConsumptionService.getByAgent(clientId),
    ])
    return { summary, dailyUsage, agentUsage }
  },
}
