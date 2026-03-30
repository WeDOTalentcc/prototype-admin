"use client"

import { useState, useCallback } from "react"
import useSWR from "swr"
import {
  policiesService,
  Policy,
  PolicyCategory,
  PolicyHistoryEntry,
} from "@/services/admin/policies-service"

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
  const [isUpdating, setIsUpdating] = useState(false)

  const { data, error, isLoading, mutate } = useSWR(
    ["adminGlobalPolicies", initialCategory ?? ""],
    async ([, category]) => {
      const [policiesResponse, historyResponse, categoriesResponse] = await Promise.all([
        policiesService.getPolicies(category || undefined),
        policiesService.getAllHistory(),
        policiesService.getCategories(),
      ])
      return {
        policies: policiesResponse.policies,
        history: historyResponse.history,
        categories: categoriesResponse.categories,
      }
    }
  )

  const fetchPolicies = useCallback(async (category?: string) => {
    try {
      const result = await policiesService.getPolicies(category)
      await mutate(
        (prev) => prev ? { ...prev, policies: result.policies } : prev,
        false
      )
    } catch (err) {
    }
  }, [mutate])

  const fetchHistory = useCallback(async (policyId?: string) => {
    try {
      const result = policyId
        ? await policiesService.getPolicyHistory(policyId)
        : await policiesService.getAllHistory()
      await mutate(
        (prev) => prev ? { ...prev, history: result.history } : prev,
        false
      )
    } catch (err) {
    }
  }, [mutate])

  const updatePolicy = useCallback(
    async (
      id: string,
      value: string | number | boolean,
      reason?: string
    ): Promise<Policy | null> => {
      setIsUpdating(true)
      try {
        const updatedPolicy = await policiesService.updatePolicy(id, value, reason)
        await mutate()
        return updatedPolicy
      } catch (err) {
        return null
      } finally {
        setIsUpdating(false)
      }
    },
    [mutate]
  )

  const togglePolicy = useCallback(
    async (id: string, isActive: boolean): Promise<Policy | null> => {
      setIsUpdating(true)
      try {
        const updatedPolicy = await policiesService.togglePolicy(id, isActive)
        await mutate()
        return updatedPolicy
      } catch (err) {
        return null
      } finally {
        setIsUpdating(false)
      }
    },
    [mutate]
  )

  const seedPolicies = useCallback(async (): Promise<{ success: boolean; message: string }> => {
    try {
      const response = await policiesService.seedPolicies()
      await mutate()
      return { success: true, message: response.message }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to seed policies"
      return { success: false, message }
    }
  }, [mutate])

  return {
    policies: data?.policies ?? [],
    history: data?.history ?? [],
    categories: data?.categories ?? [],
    isLoading,
    isUpdating,
    error: error instanceof Error ? error : error ? new Error(String(error)) : null,
    refetch: async () => { await mutate() },
    fetchPolicies,
    fetchHistory,
    updatePolicy,
    togglePolicy,
    seedPolicies,
  }
}

export type { Policy, PolicyCategory, PolicyHistoryEntry }
