import { apiClient, ApiClientOptions, ApiClientError } from './api-client'

export interface ControlLibrary {
  id: string
  framework: string
  controlId: string
  controlName: string
  controlDescription: string
  controlCategory?: string
  domain?: string
  isMandatory: boolean
  implementationGuidance?: string
  evidenceRequirements: string[]
  relatedControls: string[]
}

export interface CompanyControl {
  id: string
  companyId: string
  controlLibraryId: string
  status: 'not_started' | 'in_progress' | 'implemented' | 'verified' | 'not_applicable'
  ownerName?: string
  ownerEmail?: string
  notes?: string
  evidenceFiles: Array<{ filename: string; url: string; uploadedAt: string }>
  lastReviewedAt?: string
  nextReviewDate?: string
  control?: ControlLibrary
  createdAt: string
  updatedAt: string
}

export interface ComplianceAudit {
  id: string
  companyId: string
  framework: string
  auditType: string
  auditorOrganization?: string
  auditorName?: string
  auditStartDate?: string
  auditEndDate?: string
  scopeDescription?: string
  findings?: Record<string, unknown>[]
  status: string
  createdAt: string
  updatedAt: string
}

export interface SOXControl {
  id: string
  companyId: string
  section: string
  controlId: string
  controlName: string
  description: string
  controlType: string
  frequency: string
  testResult: 'effective' | 'ineffective' | 'pending' | 'not_tested'
  testDate?: string
  testerName?: string
  notes?: string
  createdAt: string
  updatedAt: string
}

export interface FrameworkStats {
  totalControls: number
  implemented: number
  inProgress: number
  notStarted: number
  verified: number
  notApplicable: number
  compliancePercentage: number
}

export interface ComplianceDashboard {
  byFramework: Record<string, FrameworkStats>
  totalControls: number
  totalImplemented: number
  overallCompliancePercentage: number
  upcomingReviews: number
  overdueReviews: number
  recentAudits: ComplianceAudit[]
  soxSummary?: Record<string, number>
}

export interface ControlListResponse {
  controls: ControlLibrary[]
  total: number
  limit: number
  offset: number
}

export interface CompanyControlListResponse {
  controls: CompanyControl[]
  total: number
  limit: number
  offset: number
}

export interface AuditListResponse {
  audits: ComplianceAudit[]
  total: number
  limit: number
  offset: number
}

export interface SOXControlListResponse {
  controls: SOXControl[]
  total: number
  limit: number
  offset: number
}

export interface ControlListParams {
  framework?: string
  category?: string
  search?: string
  limit?: number
  offset?: number
}

export interface CompanyControlListParams {
  framework?: string
  status?: string
  limit?: number
  offset?: number
}

export { ApiClientError }

function mapBackendControlLibrary(data: Record<string, unknown>): ControlLibrary {
  return {
    id: data.id,
    framework: data.framework,
    controlId: data.control_id,
    controlName: data.control_name,
    controlDescription: data.control_description,
    controlCategory: data.control_category,
    domain: data.domain,
    isMandatory: data.is_mandatory,
    implementationGuidance: data.implementation_guidance,
    evidenceRequirements: data.evidence_requirements || [],
    relatedControls: data.related_controls || [],
  }
}

function mapBackendCompanyControl(data: Record<string, unknown>): CompanyControl {
  return {
    id: data.id,
    companyId: data.company_id,
    controlLibraryId: data.control_library_id,
    status: data.status,
    ownerName: data.owner_name,
    ownerEmail: data.owner_email,
    notes: data.notes,
    evidenceFiles: data.evidence_files || [],
    lastReviewedAt: data.last_reviewed_at,
    nextReviewDate: data.next_review_date,
    control: data.control ? mapBackendControlLibrary(data.control) : undefined,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  }
}

function mapBackendAudit(data: Record<string, unknown>): ComplianceAudit {
  return {
    id: data.id,
    companyId: data.company_id,
    framework: data.framework,
    auditType: data.audit_type,
    auditorOrganization: data.auditor_organization,
    auditorName: data.auditor_name,
    auditStartDate: data.audit_start_date,
    auditEndDate: data.audit_end_date,
    scopeDescription: data.scope_description,
    findings: data.findings,
    status: data.status,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  }
}

function mapBackendSOXControl(data: Record<string, unknown>): SOXControl {
  return {
    id: data.id,
    companyId: data.company_id,
    section: data.section,
    controlId: data.control_id,
    controlName: data.control_name,
    description: data.description,
    controlType: data.control_type,
    frequency: data.frequency,
    testResult: data.test_result,
    testDate: data.test_date,
    testerName: data.tester_name,
    notes: data.notes,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  }
}

function mapBackendDashboard(data: Record<string, unknown>): ComplianceDashboard {
  const byFramework: Record<string, FrameworkStats> = {}
  if (data.by_framework) {
    for (const [key, value] of Object.entries(data.by_framework as Record<string, unknown>)) {
      byFramework[key] = {
        totalControls: value.total_controls || 0,
        implemented: value.implemented || 0,
        inProgress: value.in_progress || 0,
        notStarted: value.not_started || 0,
        verified: value.verified || 0,
        notApplicable: value.not_applicable || 0,
        compliancePercentage: value.compliance_percentage || 0,
      }
    }
  }

  return {
    byFramework,
    totalControls: data.total_controls || 0,
    totalImplemented: data.total_implemented || 0,
    overallCompliancePercentage: data.overall_compliance_percentage || 0,
    upcomingReviews: data.upcoming_reviews || 0,
    overdueReviews: data.overdue_reviews || 0,
    recentAudits: (data.recent_audits || []).map(mapBackendAudit),
    soxSummary: data.sox_summary,
  }
}

class ComplianceService {
  private baseEndpoint = '/compliance'

  async getControlLibrary(params: ControlListParams = {}): Promise<ControlListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (params.framework) queryParams.set('framework', params.framework)
      if (params.category) queryParams.set('category', params.category)
      if (params.search) queryParams.set('search', params.search)
      if (params.limit) queryParams.set('limit', String(params.limit))
      if (params.offset) queryParams.set('offset', String(params.offset))

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}/controls?${queryParams}`
        : `${this.baseEndpoint}/controls`

      const data = await apiClient.get<any>(endpoint)
      return {
        controls: (data.controls || []).map(mapBackendControlLibrary),
        total: data.total || 0,
        limit: data.limit || 100,
        offset: data.offset || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { controls: [], total: 0, limit: 100, offset: 0 }
    }
  }

  async getCompanyControls(
    clientId: string,
    params: CompanyControlListParams = {}
  ): Promise<CompanyControlListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (params.framework) queryParams.set('framework', params.framework)
      if (params.status) queryParams.set('status', params.status)
      if (params.limit) queryParams.set('limit', String(params.limit))
      if (params.offset) queryParams.set('offset', String(params.offset))

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}/company-controls?${queryParams}`
        : `${this.baseEndpoint}/company-controls`

      const data = await apiClient.get<any>(endpoint, { clientId })
      return {
        controls: (data.controls || []).map(mapBackendCompanyControl),
        total: data.total || 0,
        limit: data.limit || 100,
        offset: data.offset || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { controls: [], total: 0, limit: 100, offset: 0 }
    }
  }

  async getDashboard(clientId: string): Promise<ComplianceDashboard> {
    try {
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/audits/dashboard`,
        { clientId }
      )
      return mapBackendDashboard(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return {
        byFramework: {},
        totalControls: 0,
        totalImplemented: 0,
        overallCompliancePercentage: 0,
        upcomingReviews: 0,
        overdueReviews: 0,
        recentAudits: [],
      }
    }
  }

  async getAudits(clientId: string, framework?: string): Promise<AuditListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (framework) queryParams.set('framework', framework)

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}/audits?${queryParams}`
        : `${this.baseEndpoint}/audits`

      const data = await apiClient.get<any>(endpoint, { clientId })
      return {
        audits: (data.audits || []).map(mapBackendAudit),
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

  async getSOXControls(
    clientId: string,
    section?: string,
    testResult?: string
  ): Promise<SOXControlListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (section) queryParams.set('section', section)
      if (testResult) queryParams.set('test_result', testResult)

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}/sox?${queryParams}`
        : `${this.baseEndpoint}/sox`

      const data = await apiClient.get<any>(endpoint, { clientId })
      return {
        controls: (data.controls || []).map(mapBackendSOXControl),
        total: data.total || 0,
        limit: data.limit || 100,
        offset: data.offset || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { controls: [], total: 0, limit: 100, offset: 0 }
    }
  }
}

export const complianceService = new ComplianceService()
