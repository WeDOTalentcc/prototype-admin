'use client'

import useSWR from 'swr'

interface AiCreditsBalance {
  id: string
  company_id: string
  monthly_limit: number
  current_usage: number
  period_start: string
  period_end: string
  overage_allowed: boolean
  usage_percentage: number
  remaining_tokens: number
  updated_at: string
}

interface AgentUsage {
  agent_type: string
  total_tokens: number
  total_cost_cents: number
  total_operations: number
  percentage_of_total: number
  operation_count?: number
}

interface DailyUsage {
  date: string
  total_tokens: number
  total_cost_cents: number
  total_operations: number
  operation_count?: number
}

interface UsageSummary {
  total_tokens: number
  total_cost_cents: number
  total_operations: number
  period: string
  projected_monthly_tokens: number
  projected_monthly_cost_cents: number
  avg_daily_tokens_7d: number
  avg_daily_cost_7d: number
  daily_limit: number
  daily_usage_today: number
  daily_usage_percentage: number
}

interface UseAiCreditsReturn {
  balance: AiCreditsBalance | null
  summary: UsageSummary | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

interface AgentDailyTrend {
  date: string
  agent_type: string
  total_tokens: number
  total_cost_cents: number
  total_operations: number
}

interface DayDataResponse {
  data?: DailyUsage[]
  usage_by_day?: DailyUsage[]
}

interface AgentDataResponse {
  data?: AgentUsage[]
  usage_by_agent?: AgentUsage[]
}

interface AgentTrendResponse {
  data?: AgentDailyTrend[]
  total_days?: number
}

interface UseAiConsumptionHistoryReturn {
  byDay: DailyUsage[]
  byAgent: AgentUsage[]
  agentTrend: AgentDailyTrend[]
  isLoading: boolean
  error: string | null
}

const jsonFetcher = (url: string) =>
  fetch(url).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    return r.json()
  })

export function useAiCredits(): UseAiCreditsReturn {
  const {
    data: balance,
    error: balanceError,
    isLoading: balanceLoading,
    mutate: mutateBalance,
  } = useSWR<AiCreditsBalance>('/api/backend-proxy/ai-credits?endpoint=balance', jsonFetcher)

  const {
    data: summary,
    error: summaryError,
    isLoading: summaryLoading,
    mutate: mutateSummary,
  } = useSWR<UsageSummary>('/api/backend-proxy/ai-credits?endpoint=summary', jsonFetcher)

  const error = balanceError?.message ?? summaryError?.message ?? null

  return {
    balance: balance ?? null,
    summary: summary ?? null,
    isLoading: balanceLoading || summaryLoading,
    error,
    refetch: async () => {
      await Promise.all([mutateBalance(), mutateSummary()])
    },
  }
}

function parseDayData(dayData: DayDataResponse | DailyUsage[] | undefined): DailyUsage[] {
  if (!dayData) return []
  if (Array.isArray(dayData)) return dayData
  return dayData.data ?? dayData.usage_by_day ?? []
}

function parseAgentData(agentData: AgentDataResponse | AgentUsage[] | undefined): AgentUsage[] {
  if (!agentData) return []
  if (Array.isArray(agentData)) return agentData
  return agentData.data ?? agentData.usage_by_agent ?? []
}

function parseTrendData(trendData: AgentTrendResponse | AgentDailyTrend[] | undefined): AgentDailyTrend[] {
  if (!trendData) return []
  if (Array.isArray(trendData)) return trendData
  return trendData.data ?? []
}

export function useAiConsumptionHistory(days: number = 30): UseAiConsumptionHistoryReturn {
  const {
    data: dayData,
    error: dayError,
    isLoading: dayLoading,
  } = useSWR<DayDataResponse | DailyUsage[]>(
    `/api/backend-proxy/ai-credits?endpoint=by-day&days=${days}`,
    jsonFetcher
  )

  const {
    data: agentData,
    error: agentError,
    isLoading: agentLoading,
  } = useSWR<AgentDataResponse | AgentUsage[]>(
    '/api/backend-proxy/ai-credits?endpoint=by-agent',
    jsonFetcher
  )

  const {
    data: trendData,
    error: trendError,
    isLoading: trendLoading,
  } = useSWR<AgentTrendResponse | AgentDailyTrend[]>(
    `/api/backend-proxy/ai-credits?endpoint=agent-trend&days=${days}`,
    jsonFetcher
  )

  const byDay: DailyUsage[] = parseDayData(dayData)
  const byAgent: AgentUsage[] = parseAgentData(agentData)
  const agentTrend: AgentDailyTrend[] = parseTrendData(trendData)

  const error = dayError?.message ?? agentError?.message ?? trendError?.message ?? null

  return {
    byDay,
    byAgent,
    agentTrend,
    isLoading: dayLoading || agentLoading || trendLoading,
    error,
  }
}
