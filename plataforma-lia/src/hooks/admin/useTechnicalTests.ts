'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  technicalTestsService,
  TechnicalTest,
  ClientTest,
  ClientTestStats,
  ClientTestConfig,
  TestFilters,
} from '@/services/admin/technical-tests-service'

export interface UseTechnicalTestsResult {
  tests: ClientTest[]
  stats: ClientTestStats | null
  totalTests: number
  isLoading: boolean
  isUpdating: boolean
  error: Error | null
  refetch: () => void
  toggleTestEnabled: (testId: string, enabled: boolean) => Promise<boolean>
  configureTest: (testId: string, config: ClientTestConfig) => Promise<boolean>
  seedTests: () => Promise<boolean>
}

export function useTechnicalTests(clientId: string): UseTechnicalTestsResult {
  const [tests, setTests] = useState<ClientTest[]>([])
  const [stats, setStats] = useState<ClientTestStats | null>(null)
  const [totalTests, setTotalTests] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [isUpdating, setIsUpdating] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const fetchData = useCallback(async () => {
    if (!clientId) return

    setIsLoading(true)
    setError(null)

    try {
      const [testsData, statsData] = await Promise.all([
        technicalTestsService.getClientTests(clientId),
        technicalTestsService.getClientTestStats(clientId),
      ])

      setTests(testsData.tests)
      setTotalTests(testsData.total)
      setStats(statsData)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch technical tests'))
    } finally {
      setIsLoading(false)
    }
  }, [clientId])

  const toggleTestEnabled = useCallback(async (testId: string, enabled: boolean): Promise<boolean> => {
    if (!clientId) return false

    setIsUpdating(true)
    try {
      const result = await technicalTestsService.configureClientTest(clientId, testId, { enabled })
      if (result) {
        setTests(prev => prev.map(t => 
          t.testId === testId ? { ...t, enabled } : t
        ))
        return true
      }
      return false
    } catch (err) {
      return false
    } finally {
      setIsUpdating(false)
    }
  }, [clientId])

  const configureTest = useCallback(async (testId: string, config: ClientTestConfig): Promise<boolean> => {
    if (!clientId) return false

    setIsUpdating(true)
    try {
      const result = await technicalTestsService.configureClientTest(clientId, testId, config)
      if (result) {
        setTests(prev => prev.map(t => 
          t.testId === testId ? { ...t, ...config } : t
        ))
        return true
      }
      return false
    } catch (err) {
      return false
    } finally {
      setIsUpdating(false)
    }
  }, [clientId])

  const seedTests = useCallback(async (): Promise<boolean> => {
    setIsUpdating(true)
    try {
      const result = await technicalTestsService.seedTests()
      if (result) {
        await fetchData()
        return true
      }
      return false
    } catch (err) {
      return false
    } finally {
      setIsUpdating(false)
    }
  }, [fetchData])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    tests,
    stats,
    totalTests,
    isLoading,
    isUpdating,
    error,
    refetch: fetchData,
    toggleTestEnabled,
    configureTest,
    seedTests,
  }
}

export type {
  TechnicalTest,
  ClientTest,
  ClientTestStats,
  ClientTestConfig,
  TestFilters,
}
