'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  lgpdService,
  LGPDStats,
  DPORegistry,
  BreachNotification,
  AutomatedDecision,
  BreachListParams,
  AutomatedDecisionListParams,
} from '@/services/admin/lgpd-service'

export interface UseLGPDComplianceResult {
  stats: LGPDStats | null
  dpo: DPORegistry | null
  breaches: BreachNotification[]
  decisions: AutomatedDecision[]
  totalBreaches: number
  totalDecisions: number
  isLoading: boolean
  error: Error | null
  refetch: () => void
  fetchBreaches: (params?: BreachListParams) => Promise<void>
  fetchDecisions: (params?: AutomatedDecisionListParams) => Promise<void>
}

export function useLGPDCompliance(clientId: string): UseLGPDComplianceResult {
  const [stats, setStats] = useState<LGPDStats | null>(null)
  const [dpo, setDpo] = useState<DPORegistry | null>(null)
  const [breaches, setBreaches] = useState<BreachNotification[]>([])
  const [decisions, setDecisions] = useState<AutomatedDecision[]>([])
  const [totalBreaches, setTotalBreaches] = useState(0)
  const [totalDecisions, setTotalDecisions] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchData = useCallback(async () => {
    if (!clientId) return

    setIsLoading(true)
    setError(null)

    try {
      const [statsData, dpoData, breachesData, decisionsData] = await Promise.all([
        lgpdService.getStats(clientId),
        lgpdService.getDPO(clientId),
        lgpdService.getBreaches(clientId, { limit: 10 }),
        lgpdService.getAutomatedDecisions(clientId, { limit: 10 }),
      ])

      setStats(statsData)
      setDpo(dpoData)
      setBreaches(breachesData.breaches)
      setTotalBreaches(breachesData.total)
      setDecisions(decisionsData.decisions)
      setTotalDecisions(decisionsData.total)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch LGPD data'))
    } finally {
      setIsLoading(false)
    }
  }, [clientId])

  const fetchBreaches = useCallback(async (params?: BreachListParams) => {
    if (!clientId) return

    try {
      const data = await lgpdService.getBreaches(clientId, params)
      setBreaches(data.breaches)
      setTotalBreaches(data.total)
    } catch (err) {
    }
  }, [clientId])

  const fetchDecisions = useCallback(async (params?: AutomatedDecisionListParams) => {
    if (!clientId) return

    try {
      const data = await lgpdService.getAutomatedDecisions(clientId, params)
      setDecisions(data.decisions)
      setTotalDecisions(data.total)
    } catch (err) {
    }
  }, [clientId])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    stats,
    dpo,
    breaches,
    decisions,
    totalBreaches,
    totalDecisions,
    isLoading,
    error,
    refetch: fetchData,
    fetchBreaches,
    fetchDecisions,
  }
}

export type { LGPDStats, DPORegistry, BreachNotification, AutomatedDecision }
