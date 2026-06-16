"use client"

import { useState, useEffect, useCallback } from 'react'
import { 
  aiConsumptionService, 
  UsageSummary, 
  DailyUsage, 
  AgentUsage 
} from '@/services/ai-consumption'

export type { UsageSummary, DailyUsage, AgentUsage }

interface UseAIConsumptionOptions {
  clientId: string
  autoFetch?: boolean
  startDate?: string
  endDate?: string
}

interface UseAIConsumptionResult {
  summary: UsageSummary | null
  dailyUsage: DailyUsage[]
  agentUsage: AgentUsage[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  refetchSummary: () => Promise<void>
  refetchDailyUsage: () => Promise<void>
  refetchAgentUsage: () => Promise<void>
}

export function useAIConsumption(options: UseAIConsumptionOptions): UseAIConsumptionResult {
  const { clientId, autoFetch = true, startDate, endDate } = options

  const [summary, setSummary] = useState<UsageSummary | null>(null)
  const [dailyUsage, setDailyUsage] = useState<DailyUsage[]>([])
  const [agentUsage, setAgentUsage] = useState<AgentUsage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refetchSummary = useCallback(async () => {
    if (!clientId) return
    
    try {
      const data = await aiConsumptionService.getSummary(clientId)
      setSummary(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch summary')
    }
  }, [clientId])

  const refetchDailyUsage = useCallback(async () => {
    if (!clientId) return
    
    try {
      const data = await aiConsumptionService.getDailyUsage(clientId, startDate, endDate)
      setDailyUsage(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch daily usage')
    }
  }, [clientId, startDate, endDate])

  const refetchAgentUsage = useCallback(async () => {
    if (!clientId) return
    
    try {
      const data = await aiConsumptionService.getByAgent(clientId)
      setAgentUsage(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agent usage')
    }
  }, [clientId])

  const refetch = useCallback(async () => {
    if (!clientId) return
    
    setIsLoading(true)
    setError(null)

    try {
      const data = await aiConsumptionService.getAll(clientId)
      setSummary(data.summary)
      setDailyUsage(data.dailyUsage)
      setAgentUsage(data.agentUsage)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch AI consumption data')
    } finally {
      setIsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    if (autoFetch && clientId) {
      refetch()
    }
  }, [autoFetch, clientId, refetch])

  return {
    summary,
    dailyUsage,
    agentUsage,
    isLoading,
    error,
    refetch,
    refetchSummary,
    refetchDailyUsage,
    refetchAgentUsage
  }
}

export default useAIConsumption
