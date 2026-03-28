'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  biasAuditService,
  BiasAuditReport,
  BiasAuditSummary,
  BiasResult,
  BiasAuditListParams,
} from '@/services/admin/bias-service'

export interface UseBiasAuditsResult {
  summary: BiasAuditSummary | null
  latestAudit: BiasAuditReport | null
  audits: BiasAuditReport[]
  totalAudits: number
  isLoading: boolean
  error: Error | null
  refetch: () => void
  fetchAudits: (params?: BiasAuditListParams) => Promise<void>
  fetchAudit: (auditId: string) => Promise<BiasAuditReport | null>
}

export function useBiasAudits(clientId: string): UseBiasAuditsResult {
  const [summary, setSummary] = useState<BiasAuditSummary | null>(null)
  const [latestAudit, setLatestAudit] = useState<BiasAuditReport | null>(null)
  const [audits, setAudits] = useState<BiasAuditReport[]>([])
  const [totalAudits, setTotalAudits] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchData = useCallback(async () => {
    if (!clientId) return

    setIsLoading(true)
    setError(null)

    try {
      const [summaryData, latestData, auditsData] = await Promise.all([
        biasAuditService.getSummary(clientId),
        biasAuditService.getLatest(clientId),
        biasAuditService.getAudits(clientId, { limit: 10 }),
      ])

      setSummary(summaryData)
      setLatestAudit(latestData)
      setAudits(auditsData.audits)
      setTotalAudits(auditsData.total)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch bias audit data'))
    } finally {
      setIsLoading(false)
    }
  }, [clientId])

  const fetchAudits = useCallback(async (params?: BiasAuditListParams) => {
    if (!clientId) return

    try {
      const data = await biasAuditService.getAudits(clientId, params)
      setAudits(data.audits)
      setTotalAudits(data.total)
    } catch (err) {
    }
  }, [clientId])

  const fetchAudit = useCallback(async (auditId: string): Promise<BiasAuditReport | null> => {
    if (!clientId) return null

    try {
      return await biasAuditService.getAudit(clientId, auditId)
    } catch (err) {
      return null
    }
  }, [clientId])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    summary,
    latestAudit,
    audits,
    totalAudits,
    isLoading,
    error,
    refetch: fetchData,
    fetchAudits,
    fetchAudit,
  }
}

export type { BiasAuditReport, BiasAuditSummary, BiasResult }
