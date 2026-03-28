import { apiClient, ApiClientOptions, ApiClientError } from './api-client'
import { safeData } from '@/lib/safe-data'

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

function mapBackendBiasResult(data: Record<string, unknown>): BiasResult {
  const d = safeData(data)
  return {
    category: d.str('category'),
    status: d.str('status', 'clear') as BiasResult['status'],
    score: d.num('score'),
    details: d.str('details'),
    recommendation: d.str('recommendation'),
  }
}

function mapBackendBiasAudit(data: Record<string, unknown>): BiasAuditReport {
  const d = safeData(data)
  const biasResults: Record<string, BiasResult> = {}
  const rawBiasResults = d.rec('bias_results')
  for (const [key, value] of Object.entries(rawBiasResults)) {
    biasResults[key] = mapBackendBiasResult(value as Record<string, unknown>)
  }

  return {
    id: d.str('id'),
    companyId: d.str('company_id'),
    auditType: d.str('audit_type'),
    auditDate: d.str('audit_date'),
    sampleSize: d.num('sample_size'),
    auditor: d.str('auditor'),
    auditorName: d.str('auditor_name') || undefined,
    auditorOrganization: d.str('auditor_organization') || undefined,
    biasResults,
    overallScore: d.num('overall_score') || undefined,
    clearCount: d.num('clear_count'),
    considerCount: d.num('consider_count'),
    concernCount: d.num('concern_count'),
    complianceFrameworks: d.arr<string>('compliance_frameworks'),
    reportUrl: d.str('report_url') || undefined,
    notes: d.str('notes') || undefined,
    recommendations: d.arr<string>('recommendations'),
    isPublic: d.bool('is_public'),
    createdAt: d.str('created_at'),
    updatedAt: d.str('updated_at'),
  }
}

function mapBackendSummary(data: Record<string, unknown>): BiasAuditSummary {
  const d = safeData(data)
  const byStatusRec = safeData(d.rec('by_status'))
  return {
    totalAudits: d.num('total_audits'),
    latestAuditDate: d.str('latest_audit_date') || undefined,
    latestOverallScore: d.num('latest_overall_score') || undefined,
    byAuditType: d.rec('by_audit_type') as Record<string, number>,
    byStatus: {
      clear: byStatusRec.num('clear'),
      consider: byStatusRec.num('consider'),
      concern: byStatusRec.num('concern'),
    },
    complianceCoverage: d.arr<string>('compliance_coverage'),
    publicAuditsCount: d.num('public_audits_count'),
  }
}

class BiasAuditService {
  private baseEndpoint = '/observability/bias-audits'

  async getSummary(clientId: string): Promise<BiasAuditSummary> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(
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
      const data = await apiClient.get<Record<string, unknown>>(
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

      const data = await apiClient.get<Record<string, unknown>>(endpoint, { clientId })
      return {
        audits: ((data.audits || []) as Record<string, unknown>[]).map(mapBackendBiasAudit),
        total: (data.total as number) || 0,
        limit: (data.limit as number) || 50,
        offset: (data.offset as number) || 0,
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
      const data = await apiClient.get<Record<string, unknown>>(
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
