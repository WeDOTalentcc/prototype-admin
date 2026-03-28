'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  auditLogsService,
  AuditLog,
  AuditStats,
  RetentionPolicy,
  AuditLogFilters,
  ActionCategory,
  AuditStatus,
} from '@/services/admin/audit-logs-service'

export interface UseAuditLogsFilters {
  dateFrom?: string
  dateTo?: string
  clientId?: string
  userId?: string
  actionCategory?: ActionCategory | 'all'
  status?: AuditStatus | 'all'
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

export function useAuditLogs(initialFilters?: UseAuditLogsFilters): UseAuditLogsResult {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [stats, setStats] = useState<AuditStats | null>(null)
  const [retentionPolicies, setRetentionPolicies] = useState<RetentionPolicy[]>([])
  const [totalLogs, setTotalLogs] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isExporting, setIsExporting] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const buildFilters = useCallback((filters?: UseAuditLogsFilters, page = 1, pageSize = DEFAULT_PAGE_SIZE): AuditLogFilters => {
    const apiFilters: AuditLogFilters = {
      limit: pageSize,
      offset: (page - 1) * pageSize,
    }

    if (filters?.dateFrom) apiFilters.dateFrom = filters.dateFrom
    if (filters?.dateTo) apiFilters.dateTo = filters.dateTo
    if (filters?.clientId && filters.clientId !== 'all') apiFilters.clientId = filters.clientId
    if (filters?.userId) apiFilters.userId = filters.userId
    if (filters?.actionCategory && filters.actionCategory !== 'all') {
      apiFilters.actionCategory = filters.actionCategory as ActionCategory
    }
    if (filters?.status && filters.status !== 'all') {
      apiFilters.status = filters.status as AuditStatus
    }
    if (filters?.action) apiFilters.action = filters.action
    if (filters?.search) apiFilters.action = filters.search

    return apiFilters
  }, [])

  const fetchLogs = useCallback(async (
    filters?: UseAuditLogsFilters, 
    page = 1, 
    pageSize = DEFAULT_PAGE_SIZE
  ) => {
    setIsLoading(true)
    setError(null)

    try {
      const apiFilters = buildFilters(filters, page, pageSize)
      const response = await auditLogsService.getAuditLogs(apiFilters)
      
      setLogs(response.logs)
      setTotalLogs(response.total)
      setHasMore(response.hasMore)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch audit logs'))
    } finally {
      setIsLoading(false)
    }
  }, [buildFilters])

  const fetchStats = useCallback(async (filters?: Partial<AuditLogFilters>) => {
    try {
      const statsData = await auditLogsService.getAuditStats(filters)
      setStats(statsData)
    } catch (err) {
    }
  }, [])

  const fetchRetentionPolicies = useCallback(async () => {
    try {
      const response = await auditLogsService.getRetentionPolicies()
      setRetentionPolicies(response.policies)
    } catch (err) {
    }
  }, [])

  const exportLogs = useCallback(async (filters?: AuditLogFilters) => {
    setIsExporting(true)
    try {
      const blob = await auditLogsService.exportAuditLogs(filters)
      
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to export audit logs'))
      throw err
    } finally {
      setIsExporting(false)
    }
  }, [])

  const seedRetentionPolicies = useCallback(async (): Promise<{ success: boolean; message: string }> => {
    try {
      const response = await auditLogsService.seedRetentionPolicies()
      await fetchRetentionPolicies()
      return { success: true, message: response.message }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to seed retention policies'
      return { success: false, message }
    }
  }, [fetchRetentionPolicies])

  const refetch = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const [logsResponse, statsData, policiesResponse] = await Promise.all([
        auditLogsService.getAuditLogs(buildFilters(initialFilters)),
        auditLogsService.getAuditStats(),
        auditLogsService.getRetentionPolicies(),
      ])

      setLogs(logsResponse.logs)
      setTotalLogs(logsResponse.total)
      setHasMore(logsResponse.hasMore)
      setStats(statsData)
      setRetentionPolicies(policiesResponse.policies)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch audit data'))
    } finally {
      setIsLoading(false)
    }
  }, [buildFilters, initialFilters])

  useEffect(() => {
    refetch()
  }, [])

  return {
    logs,
    stats,
    retentionPolicies,
    totalLogs,
    hasMore,
    isLoading,
    isExporting,
    error,
    refetch,
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
