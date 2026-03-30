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
  operation_count: number
}

interface DailyUsage {
  date: string
  total_tokens: number
  total_cost_cents: number
  operation_count: number
}

interface UsageSummary {
  total_tokens: number
  total_cost_cents: number
  total_operations: number
  period: string
}

interface UseAiCreditsReturn {
  balance: AiCreditsBalance | null
  summary: UsageSummary | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

interface UseAiConsumptionHistoryReturn {
  byDay: DailyUsage[]
  byAgent: AgentUsage[]
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

export function useAiConsumptionHistory(days: number = 30): UseAiConsumptionHistoryReturn {
  const {
    data: dayData,
    error: dayError,
    isLoading: dayLoading,
  } = useSWR<{ usage_by_day?: DailyUsage[] } | DailyUsage[]>(
    `/api/backend-proxy/ai-credits?endpoint=by-day&days=${days}`,
    jsonFetcher
  )

  const {
    data: agentData,
    error: agentError,
    isLoading: agentLoading,
  } = useSWR<{ usage_by_agent?: AgentUsage[] } | AgentUsage[]>(
    '/api/backend-proxy/ai-credits?endpoint=by-agent',
    jsonFetcher
  )

  const byDay: DailyUsage[] = Array.isArray(dayData)
    ? dayData
    : (dayData as { usage_by_day?: DailyUsage[] })?.usage_by_day ?? []

  const byAgent: AgentUsage[] = Array.isArray(agentData)
    ? agentData
    : (agentData as { usage_by_agent?: AgentUsage[] })?.usage_by_agent ?? []

  const error = dayError?.message ?? agentError?.message ?? null

  return {
    byDay,
    byAgent,
    isLoading: dayLoading || agentLoading,
    error,
  }
}
