"use client"

import { useState, useEffect, useCallback } from 'react'
import { getDashboardSummary, DashboardSummary, ApiClientError } from '@/services/admin/dashboard-service'

export interface UseDashboardSummaryResult {
  data: DashboardSummary | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useDashboardSummary(startDate?: Date, endDate?: Date): UseDashboardSummaryResult {
  const [data, setData] = useState<DashboardSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const summary = await getDashboardSummary(startDate, endDate)
      setData(summary)
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Erro ao carregar resumo do dashboard')
      }
    } finally {
      setIsLoading(false)
    }
  }, [startDate?.getTime(), endDate?.getTime()])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}
