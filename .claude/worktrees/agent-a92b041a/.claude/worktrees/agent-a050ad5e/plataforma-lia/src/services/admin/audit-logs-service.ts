import { apiClient, ApiClientOptions, ApiClientError } from './api-client'

export type ActionCategory = 'authentication' | 'data_access' | 'configuration' | 'ai_decision' | 'financial' | 'user_management' | 'system'
export type AuditStatus = 'success' | 'failed' | 'pending' | 'partial'

export interface AuditLog {
  id: string
  timestamp: string | null
  userId: string | null
  userEmail: string | null
  clientId: string | null
  clientName: string | null
  action: string
  actionCategory: ActionCategory
  resourceType: string | null
  resourceId: string | null
  ipAddress: string | null
  userAgent: string | null
  status: AuditStatus
  details: Record<string, unknown>
  retentionYears: number
  retentionUntil: string | null
  requestId: string | null
  sessionId: string | null
  createdAt: string | null
}

export interface AuditLogListResponse {
  logs: AuditLog[]
  total: number
  limit: number
  offset: number
  hasMore: boolean
}

export interface AuditLogFilters {
  dateFrom?: string
  dateTo?: string
  clientId?: string
  userId?: string
  actionCategory?: ActionCategory
  status?: AuditStatus
  action?: string
  resourceType?: string
  limit?: number
  offset?: number
}

export interface AuditStats {
  totalLogs: number
  logsByCategory: Record<string, number>
  logsByStatus: Record<string, number>
  failedActionsCount: number
  aiDecisionsCount: number
  uniqueUsers: number
  uniqueClients: number
  periodStart: string | null
  periodEnd: string | null
  topActions: Array<{ action: string; count: number }>
}

export interface RetentionPolicy {
  id: string
  category: string
  retentionMonths: number
  description: string | null
  isSoxRequired: boolean
  legalBasis: string | null
  isActive: boolean
  createdAt: string | null
  updatedAt: string | null
}

export interface RetentionPolicyListResponse {
  policies: RetentionPolicy[]
  total: number
}

export interface SeedRetentionPoliciesResponse {
  createdCount: number
  skippedCount: number
  message: string
}

export { ApiClientError }

function mapBackendAuditLog(data: Record<string, unknown>): AuditLog {
  return {
    id: data.id as string,
    timestamp: data.timestamp as string | null,
    userId: data.user_id as string | null,
    userEmail: data.user_email as string | null,
    clientId: data.client_id as string | null,
    clientName: data.client_name as string | null,
    action: data.action as string,
    actionCategory: data.action_category as ActionCategory,
    resourceType: data.resource_type as string | null,
    resourceId: data.resource_id as string | null,
    ipAddress: data.ip_address as string | null,
    userAgent: data.user_agent as string | null,
    status: data.status as AuditStatus,
    details: (data.details as Record<string, unknown>) || {},
    retentionYears: (data.retention_years as number) || 7,
    retentionUntil: data.retention_until as string | null,
    requestId: data.request_id as string | null,
    sessionId: data.session_id as string | null,
    createdAt: data.created_at as string | null,
  }
}

function mapBackendStats(data: Record<string, unknown>): AuditStats {
  return {
    totalLogs: (data.total_logs as number) || 0,
    logsByCategory: (data.logs_by_category as Record<string, number>) || {},
    logsByStatus: (data.logs_by_status as Record<string, number>) || {},
    failedActionsCount: (data.failed_actions_count as number) || 0,
    aiDecisionsCount: (data.ai_decisions_count as number) || 0,
    uniqueUsers: (data.unique_users as number) || 0,
    uniqueClients: (data.unique_clients as number) || 0,
    periodStart: data.period_start as string | null,
    periodEnd: data.period_end as string | null,
    topActions: (data.top_actions as Array<{ action: string; count: number }>) || [],
  }
}

function mapBackendRetentionPolicy(data: Record<string, unknown>): RetentionPolicy {
  return {
    id: data.id as string,
    category: data.category as string,
    retentionMonths: (data.retention_months as number) || 0,
    description: data.description as string | null,
    isSoxRequired: (data.is_sox_required as boolean) || false,
    legalBasis: data.legal_basis as string | null,
    isActive: data.is_active !== false,
    createdAt: data.created_at as string | null,
    updatedAt: data.updated_at as string | null,
  }
}

class AuditLogsService {
  private baseEndpoint = '/audit-logs'

  async getAuditLogs(filters: AuditLogFilters = {}): Promise<AuditLogListResponse> {
    try {
      const queryParams = new URLSearchParams()
      
      if (filters.dateFrom) queryParams.set('date_from', filters.dateFrom)
      if (filters.dateTo) queryParams.set('date_to', filters.dateTo)
      if (filters.clientId) queryParams.set('client_id', filters.clientId)
      if (filters.userId) queryParams.set('user_id', filters.userId)
      if (filters.actionCategory) queryParams.set('action_category', filters.actionCategory)
      if (filters.status) queryParams.set('status', filters.status)
      if (filters.action) queryParams.set('action', filters.action)
      if (filters.resourceType) queryParams.set('resource_type', filters.resourceType)
      if (filters.limit !== undefined) queryParams.set('limit', String(filters.limit))
      if (filters.offset !== undefined) queryParams.set('offset', String(filters.offset))

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}?${queryParams}`
        : this.baseEndpoint

      const data = await apiClient.get<Record<string, unknown>>(endpoint)
      
      return {
        logs: ((data.logs as Array<Record<string, unknown>>) || []).map(mapBackendAuditLog),
        total: (data.total as number) || 0,
        limit: (data.limit as number) || 50,
        offset: (data.offset as number) || 0,
        hasMore: (data.has_more as boolean) || false,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching audit logs:', error.message)
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { logs: [], total: 0, limit: 50, offset: 0, hasMore: false }
    }
  }

  async getAuditLogById(logId: string): Promise<AuditLog | null> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(`${this.baseEndpoint}/${logId}`)
      return mapBackendAuditLog(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching audit log:', error.message)
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }

  async getAuditStats(filters: Partial<AuditLogFilters> = {}): Promise<AuditStats> {
    try {
      const queryParams = new URLSearchParams()
      
      if (filters.dateFrom) queryParams.set('date_from', filters.dateFrom)
      if (filters.dateTo) queryParams.set('date_to', filters.dateTo)
      if (filters.clientId) queryParams.set('client_id', filters.clientId)

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}/stats?${queryParams}`
        : `${this.baseEndpoint}/stats`

      const data = await apiClient.get<Record<string, unknown>>(endpoint)
      return mapBackendStats(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching audit stats:', error.message)
        if (error.isAuthError || error.isForbidden) throw error
      }
      return {
        totalLogs: 0,
        logsByCategory: {},
        logsByStatus: {},
        failedActionsCount: 0,
        aiDecisionsCount: 0,
        uniqueUsers: 0,
        uniqueClients: 0,
        periodStart: null,
        periodEnd: null,
        topActions: [],
      }
    }
  }

  async exportAuditLogs(filters: AuditLogFilters = {}): Promise<Blob> {
    try {
      const queryParams = new URLSearchParams()
      
      if (filters.dateFrom) queryParams.set('date_from', filters.dateFrom)
      if (filters.dateTo) queryParams.set('date_to', filters.dateTo)
      if (filters.clientId) queryParams.set('client_id', filters.clientId)
      if (filters.actionCategory) queryParams.set('action_category', filters.actionCategory)

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}/export?${queryParams}`
        : `${this.baseEndpoint}/export`

      const url = `/api/backend-proxy${endpoint}`
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`)
      }

      return await response.blob()
    } catch (error) {
      console.error('Error exporting audit logs:', error)
      throw error
    }
  }

  async getRetentionPolicies(): Promise<RetentionPolicyListResponse> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(`${this.baseEndpoint}/retention-policies`)
      
      return {
        policies: ((data.policies as Array<Record<string, unknown>>) || []).map(mapBackendRetentionPolicy),
        total: (data.total as number) || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching retention policies:', error.message)
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { policies: [], total: 0 }
    }
  }

  async seedRetentionPolicies(): Promise<SeedRetentionPoliciesResponse> {
    try {
      const data = await apiClient.post<Record<string, unknown>>(`${this.baseEndpoint}/retention-policies/seed`, {})
      
      return {
        createdCount: (data.created_count as number) || 0,
        skippedCount: (data.skipped_count as number) || 0,
        message: (data.message as string) || 'Seed completed',
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error seeding retention policies:', error.message)
        throw error
      }
      throw error
    }
  }
}

export const auditLogsService = new AuditLogsService()
