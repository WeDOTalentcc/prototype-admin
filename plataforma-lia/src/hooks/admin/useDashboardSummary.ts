"use client"

import { useState, useEffect, useCallback, useRef } from 'react'
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
  const isMountedRef = useRef(true)

  const fetchData = useCallback(async () => {
    if (isMountedRef.current) setIsLoading(true)
    if (isMountedRef.current) setError(null)
    try {
      const summary = await getDashboardSummary(startDate, endDate)
      if (isMountedRef.current) setData(summary)
    } catch (err) {
      if (!isMountedRef.current) return
      if (err instanceof ApiClientError) {
        setError(err.message)
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Erro ao carregar resumo do dashboard')
      }
    } finally {
      if (isMountedRef.current) setIsLoading(false)
    }
  }, [startDate?.getTime(), endDate?.getTime()])

  useEffect(() => {
    isMountedRef.current = true
    fetchData()
    return () => { isMountedRef.current = false }
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}
