'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  policiesService,
  Policy,
  PolicyCategory,
  PolicyHistoryEntry,
} from '@/services/admin/policies-service'

export interface UseGlobalPoliciesResult {
  policies: Policy[]
  history: PolicyHistoryEntry[]
  categories: PolicyCategory[]
  isLoading: boolean
  isUpdating: boolean
  error: Error | null
  refetch: () => Promise<void>
  fetchPolicies: (category?: string) => Promise<void>
  fetchHistory: (policyId?: string) => Promise<void>
  updatePolicy: (
    id: string,
    value: string | number | boolean,
    reason?: string
  ) => Promise<Policy | null>
  togglePolicy: (id: string, isActive: boolean) => Promise<Policy | null>
  seedPolicies: () => Promise<{ success: boolean; message: string }>
}

export function useGlobalPolicies(initialCategory?: string): UseGlobalPoliciesResult {
  const [policies, setPolicies] = useState<Policy[]>([])
  const [history, setHistory] = useState<PolicyHistoryEntry[]>([])
  const [categories, setCategories] = useState<PolicyCategory[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUpdating, setIsUpdating] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const fetchPolicies = useCallback(async (category?: string) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await policiesService.getPolicies(category)
      setPolicies(response.policies)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch policies'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  const fetchHistory = useCallback(async (policyId?: string) => {
    try {
      if (policyId) {
        const response = await policiesService.getPolicyHistory(policyId)
        setHistory(response.history)
      } else {
        const response = await policiesService.getAllHistory()
        setHistory(response.history)
      }
    } catch (err) {
      console.error('Error fetching policy history:', err)
    }
  }, [])

  const fetchCategories = useCallback(async () => {
    try {
      const response = await policiesService.getCategories()
      setCategories(response.categories)
    } catch (err) {
      console.error('Error fetching categories:', err)
    }
  }, [])

  const updatePolicy = useCallback(
    async (
      id: string,
      value: string | number | boolean,
      reason?: string
    ): Promise<Policy | null> => {
      setIsUpdating(true)
      setError(null)

      try {
        const updatedPolicy = await policiesService.updatePolicy(id, value, reason)
        setPolicies((prev) =>
          prev.map((p) => (p.id === id ? updatedPolicy : p))
        )
        await fetchHistory()
        return updatedPolicy
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to update policy'))
        return null
      } finally {
        setIsUpdating(false)
      }
    },
    [fetchHistory]
  )

  const togglePolicy = useCallback(
    async (id: string, isActive: boolean): Promise<Policy | null> => {
      setIsUpdating(true)
      setError(null)

      try {
        const updatedPolicy = await policiesService.togglePolicy(id, isActive)
        setPolicies((prev) =>
          prev.map((p) => (p.id === id ? updatedPolicy : p))
        )
        await fetchHistory()
        return updatedPolicy
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to toggle policy'))
        return null
      } finally {
        setIsUpdating(false)
      }
    },
    [fetchHistory]
  )

  const seedPolicies = useCallback(async (): Promise<{ success: boolean; message: string }> => {
    try {
      const response = await policiesService.seedPolicies()
      await fetchPolicies(initialCategory)
      return { success: true, message: response.message }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to seed policies'
      return { success: false, message }
    }
  }, [fetchPolicies, initialCategory])

  const refetch = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const [policiesResponse, historyResponse, categoriesResponse] = await Promise.all([
        policiesService.getPolicies(initialCategory),
        policiesService.getAllHistory(),
        policiesService.getCategories(),
      ])

      setPolicies(policiesResponse.policies)
      setHistory(historyResponse.history)
      setCategories(categoriesResponse.categories)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch policies data'))
    } finally {
      setIsLoading(false)
    }
  }, [initialCategory])

  useEffect(() => {
    refetch()
  }, [])

  return {
    policies,
    history,
    categories,
    isLoading,
    isUpdating,
    error,
    refetch,
    fetchPolicies,
    fetchHistory,
    updatePolicy,
    togglePolicy,
    seedPolicies,
  }
}

export type { Policy, PolicyCategory, PolicyHistoryEntry }
