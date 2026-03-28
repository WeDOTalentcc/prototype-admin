import type { BackendRecord } from '@/types/api'
import { apiClient, ApiClientOptions, ApiClientError } from './api-client'

export interface BiasResult {
  category: string
  status: 'clear' | 'consider' | 'concern'
  score?: number
  details?: string
  recommendation?: string
}

export interface BiasAuditReport {
  id: string
  companyId: string
  auditType: string
  auditDate: string
  sampleSize: number
  auditor: string
  auditorName?: string
  auditorOrganization?: string
  biasResults: Record<string, BiasResult>
  overallScore?: number
  clearCount: number
  considerCount: number
  concernCount: number
  complianceFrameworks: string[]
  reportUrl?: string
  notes?: string
  recommendations: string[]
  isPublic: boolean
  createdAt: string
  updatedAt: string
}

export interface BiasAuditSummary {
  totalAudits: number
  latestAuditDate?: string
  latestOverallScore?: number
  byAuditType: Record<string, number>
  byStatus: {
    clear: number
    consider: number
    concern: number
  }
  complianceCoverage: string[]
  publicAuditsCount: number
}

export interface BiasAuditListResponse {
  audits: BiasAuditReport[]
  total: number
  limit: number
  offset: number
}

export interface BiasAuditListParams {
  auditType?: string
  isPublic?: boolean
  startDate?: string
  endDate?: string
  limit?: number
  offset?: number
}

export { ApiClientError }

function mapBackendBiasResult(data: BackendRecord): BiasResult {
  return {
    category: data.category || '',
    status: data.status || 'clear',
    score: data.score,
    details: data.details,
    recommendation: data.recommendation,
  }
}

function mapBackendBiasAudit(data: BackendRecord): BiasAuditReport {
  const biasResults: Record<string, BiasResult> = {}
  if (data.bias_results) {
    for (const [key, value] of Object.entries(data.bias_results as Record<string, any>)) {
      biasResults[key] = mapBackendBiasResult(value)
    }
  }

  return {
    id: data.id,
    companyId: data.company_id,
    auditType: data.audit_type,
    auditDate: data.audit_date,
    sampleSize: data.sample_size,
    auditor: data.auditor,
    auditorName: data.auditor_name,
    auditorOrganization: data.auditor_organization,
    biasResults,
    overallScore: data.overall_score,
    clearCount: data.clear_count || 0,
    considerCount: data.consider_count || 0,
    concernCount: data.concern_count || 0,
    complianceFrameworks: data.compliance_frameworks || [],
    reportUrl: data.report_url,
    notes: data.notes,
    recommendations: data.recommendations || [],
    isPublic: data.is_public || false,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  }
}

function mapBackendSummary(data: BackendRecord): BiasAuditSummary {
  return {
    totalAudits: data.total_audits || 0,
    latestAuditDate: data.latest_audit_date,
    latestOverallScore: data.latest_overall_score,
    byAuditType: data.by_audit_type || {},
    byStatus: {
      clear: data.by_status?.clear || 0,
      consider: data.by_status?.consider || 0,
      concern: data.by_status?.concern || 0,
    },
    complianceCoverage: data.compliance_coverage || [],
    publicAuditsCount: data.public_audits_count || 0,
  }
}

class BiasAuditService {
  private baseEndpoint = '/observability/bias-audits'

  async getSummary(clientId: string): Promise<BiasAuditSummary> {
    try {
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/summary`,
        { clientId }
      )
      return mapBackendSummary(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return {
        totalAudits: 0,
        byAuditType: {},
        byStatus: { clear: 0, consider: 0, concern: 0 },
        complianceCoverage: [],
        publicAuditsCount: 0,
      }
    }
  }

  async getLatest(clientId: string): Promise<BiasAuditReport | null> {
    try {
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/latest`,
        { clientId }
      )
      return mapBackendBiasAudit(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.status === 404) return null
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }

  async getAudits(
    clientId: string,
    params: BiasAuditListParams = {}
  ): Promise<BiasAuditListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (params.auditType) queryParams.set('audit_type', params.auditType)
      if (params.isPublic !== undefined) queryParams.set('is_public', String(params.isPublic))
      if (params.startDate) queryParams.set('start_date', params.startDate)
      if (params.endDate) queryParams.set('end_date', params.endDate)
      if (params.limit) queryParams.set('limit', String(params.limit))
      if (params.offset) queryParams.set('offset', String(params.offset))

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}?${queryParams}`
        : this.baseEndpoint

      const data = await apiClient.get<any>(endpoint, { clientId })
      return {
        audits: (data.audits || []).map(mapBackendBiasAudit),
        total: data.total || 0,
        limit: data.limit || 50,
        offset: data.offset || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { audits: [], total: 0, limit: 50, offset: 0 }
    }
  }

  async getAudit(clientId: string, auditId: string): Promise<BiasAuditReport | null> {
    try {
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/${auditId}`,
        { clientId }
      )
      return mapBackendBiasAudit(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.status === 404) return null
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }
}

export const biasAuditService = new BiasAuditService()
