'use client'

import { useState, useEffect, useCallback } from 'react'

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

export function useAiCredits(): UseAiCreditsReturn {
  const [balance, setBalance] = useState<AiCreditsBalance | null>(null)
  const [summary, setSummary] = useState<UsageSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [balanceRes, summaryRes] = await Promise.all([
        fetch('/api/backend-proxy/ai-credits?endpoint=balance'),
        fetch('/api/backend-proxy/ai-credits?endpoint=summary'),
      ])

      if (balanceRes.ok) {
        const data = await balanceRes.json()
        setBalance(data)
      }

      if (summaryRes.ok) {
        const data = await summaryRes.json()
        setSummary(data)
      }
    } catch (err) {
      setError('Falha ao carregar dados de consumo de IA')
      console.error('useAiCredits error:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { balance, summary, isLoading, error, refetch: fetchData }
}

export function useAiConsumptionHistory(days: number = 30): UseAiConsumptionHistoryReturn {
  const [byDay, setByDay] = useState<DailyUsage[]>([])
  const [byAgent, setByAgent] = useState<AgentUsage[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const [dayRes, agentRes] = await Promise.all([
          fetch(`/api/backend-proxy/ai-credits?endpoint=by-day&days=${days}`),
          fetch('/api/backend-proxy/ai-credits?endpoint=by-agent'),
        ])

        if (dayRes.ok) {
          const data = await dayRes.json()
          setByDay(data.usage_by_day || data || [])
        }

        if (agentRes.ok) {
          const data = await agentRes.json()
          setByAgent(data.usage_by_agent || data || [])
        }
      } catch (err) {
        setError('Falha ao carregar histórico de consumo de IA')
        console.error('useAiConsumptionHistory error:', err)
      } finally {
        setIsLoading(false)
      }
    }

    fetchHistory()
  }, [days])

  return { byDay, byAgent, isLoading, error }
}
