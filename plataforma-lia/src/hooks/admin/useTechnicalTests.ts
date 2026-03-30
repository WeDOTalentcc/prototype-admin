"use client"

import { useState, useCallback } from "react"
import useSWR from "swr"
import {
  technicalTestsService,
  TechnicalTest,
  ClientTest,
  ClientTestStats,
  ClientTestConfig,
  TestFilters,
} from "@/services/admin/technical-tests-service"

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
  const [isUpdating, setIsUpdating] = useState(false)

  const { data, error, isLoading, mutate } = useSWR(
    clientId ? ["adminTechnicalTests", clientId] : null,
    async ([, id]) => {
      const [testsData, statsData] = await Promise.all([
        technicalTestsService.getClientTests(id),
        technicalTestsService.getClientTestStats(id),
      ])
      return { tests: testsData.tests, total: testsData.total, stats: statsData }
    }
  )

  const toggleTestEnabled = useCallback(async (testId: string, enabled: boolean): Promise<boolean> => {
    if (!clientId) return false
    setIsUpdating(true)
    try {
      const result = await technicalTestsService.configureClientTest(clientId, testId, { enabled })
      if (result) {
        await mutate()
        return true
      }
      return false
    } catch (err) {
      return false
    } finally {
      setIsUpdating(false)
    }
  }, [clientId, mutate])

  const configureTest = useCallback(async (testId: string, config: ClientTestConfig): Promise<boolean> => {
    if (!clientId) return false
    setIsUpdating(true)
    try {
      const result = await technicalTestsService.configureClientTest(clientId, testId, config)
      if (result) {
        await mutate()
        return true
      }
      return false
    } catch (err) {
      return false
    } finally {
      setIsUpdating(false)
    }
  }, [clientId, mutate])

  const seedTests = useCallback(async (): Promise<boolean> => {
    setIsUpdating(true)
    try {
      const result = await technicalTestsService.seedTests()
      if (result) {
        await mutate()
        return true
      }
      return false
    } catch (err) {
      return false
    } finally {
      setIsUpdating(false)
    }
  }, [mutate])

  return {
    tests: data?.tests ?? [],
    stats: data?.stats ?? null,
    totalTests: data?.total ?? 0,
    isLoading,
    isUpdating,
    error: error instanceof Error ? error : error ? new Error(String(error)) : null,
    refetch: () => mutate(),
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
