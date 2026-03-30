"use client"

import useSWR from "swr"
import { getDashboardSummary, DashboardSummary, ApiClientError } from "@/services/admin/dashboard-service"

export interface UseDashboardSummaryResult {
  data: DashboardSummary | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useDashboardSummary(startDate?: Date, endDate?: Date): UseDashboardSummaryResult {
  const { data, error, isLoading, mutate } = useSWR(
    ["adminDashboardSummary", startDate?.getTime() ?? 0, endDate?.getTime() ?? 0],
    ([, , ]) => getDashboardSummary(startDate, endDate)
  )

  return {
    data: data ?? null,
    isLoading,
    error: error instanceof ApiClientError ? error.message
      : error instanceof Error ? error.message
      : error ? String(error) : null,
    refetch: () => mutate(),
  }
}
