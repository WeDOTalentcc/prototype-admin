"use client"

import { useState, useCallback } from "react"
import useSWR from "swr"
import {
  auditLogsService,
  AuditLog,
  AuditStats,
  RetentionPolicy,
  AuditLogFilters,
  ActionCategory,
  AuditStatus,
} from "@/services/admin/audit-logs-service"

export interface UseAuditLogsFilters {
  dateFrom?: string
  dateTo?: string
  clientId?: string
  userId?: string
  actionCategory?: ActionCategory | "all"
  status?: AuditStatus | "all"
  action?: string
  search?: string
}

export interface UseAuditLogsResult {
  logs: AuditLog[]
  stats: AuditStats | null
  retentionPolicies: RetentionPolicy[]
  totalLogs: number
  hasMore: boolean
  isLoading: boolean
  isExporting: boolean
  error: Error | null
  refetch: () => Promise<void>
  fetchLogs: (filters?: UseAuditLogsFilters, page?: number, pageSize?: number) => Promise<void>
  fetchStats: (filters?: Partial<AuditLogFilters>) => Promise<void>
  fetchRetentionPolicies: () => Promise<void>
  exportLogs: (filters?: AuditLogFilters) => Promise<void>
  seedRetentionPolicies: () => Promise<{ success: boolean; message: string }>
}

const DEFAULT_PAGE_SIZE = 50

const buildFilters = (filters?: UseAuditLogsFilters, page = 1, pageSize = DEFAULT_PAGE_SIZE): AuditLogFilters => {
  const apiFilters: AuditLogFilters = {
    limit: pageSize,
    offset: (page - 1) * pageSize,
  }

  if (filters?.dateFrom) apiFilters.dateFrom = filters.dateFrom
  if (filters?.dateTo) apiFilters.dateTo = filters.dateTo
  if (filters?.clientId && filters.clientId !== "all") apiFilters.clientId = filters.clientId
  if (filters?.userId) apiFilters.userId = filters.userId
  if (filters?.actionCategory && filters.actionCategory !== "all") {
    apiFilters.actionCategory = filters.actionCategory as ActionCategory
  }
  if (filters?.status && filters.status !== "all") {
    apiFilters.status = filters.status as AuditStatus
  }
  if (filters?.action) apiFilters.action = filters.action
  if (filters?.search) apiFilters.action = filters.search

  return apiFilters
}

export function useAuditLogs(initialFilters?: UseAuditLogsFilters): UseAuditLogsResult {
  const [isExporting, setIsExporting] = useState(false)

  const { data, error, isLoading, mutate } = useSWR(
    "adminAuditLogs",
    async () => {
      const [logsResponse, statsData, policiesResponse] = await Promise.all([
        auditLogsService.getAuditLogs(buildFilters(initialFilters)),
        auditLogsService.getAuditStats(),
        auditLogsService.getRetentionPolicies(),
      ])
      return {
        logs: logsResponse.logs,
        total: logsResponse.total,
        hasMore: logsResponse.hasMore,
        stats: statsData,
        retentionPolicies: policiesResponse.policies,
      }
    }
  )

  const fetchLogs = useCallback(async (
    filters?: UseAuditLogsFilters,
    page = 1,
    pageSize = DEFAULT_PAGE_SIZE
  ) => {
    try {
      const result = await auditLogsService.getAuditLogs(buildFilters(filters, page, pageSize))
      await mutate(
        (prev) => prev ? { ...prev, logs: result.logs, total: result.total, hasMore: result.hasMore } : prev,
        false
      )
    } catch (err) {
    }
  }, [mutate])

  const fetchStats = useCallback(async (filters?: Partial<AuditLogFilters>) => {
    try {
      const result = await auditLogsService.getAuditStats(filters)
      await mutate(
        (prev) => prev ? { ...prev, stats: result } : prev,
        false
      )
    } catch (err) {
    }
  }, [mutate])

  const fetchRetentionPolicies = useCallback(async () => {
    try {
      const result = await auditLogsService.getRetentionPolicies()
      await mutate(
        (prev) => prev ? { ...prev, retentionPolicies: result.policies } : prev,
        false
      )
    } catch (err) {
    }
  }, [mutate])

  const exportLogs = useCallback(async (filters?: AuditLogFilters) => {
    setIsExporting(true)
    try {
      const blob = await auditLogsService.exportAuditLogs(filters)

      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = `audit-logs-${new Date().toISOString().slice(0, 10)}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (err) {
      throw err
    } finally {
      setIsExporting(false)
    }
  }, [])

  const seedRetentionPolicies = useCallback(async (): Promise<{ success: boolean; message: string }> => {
    try {
      const response = await auditLogsService.seedRetentionPolicies()
      await mutate()
      return { success: true, message: response.message }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to seed retention policies"
      return { success: false, message }
    }
  }, [mutate])

  return {
    logs: data?.logs ?? [],
    stats: data?.stats ?? null,
    retentionPolicies: data?.retentionPolicies ?? [],
    totalLogs: data?.total ?? 0,
    hasMore: data?.hasMore ?? false,
    isLoading,
    isExporting,
    error: error instanceof Error ? error : error ? new Error(String(error)) : null,
    refetch: async () => { await mutate() },
    fetchLogs,
    fetchStats,
    fetchRetentionPolicies,
    exportLogs,
    seedRetentionPolicies,
  }
}

export type {
  AuditLog,
  AuditStats,
  RetentionPolicy,
  AuditLogFilters,
  ActionCategory,
  AuditStatus,
}
