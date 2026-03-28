import { apiClient, ApiClientOptions, ApiClientError } from './api-client'
import { safeData } from '@/lib/safe-data'

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
  const d = safeData(data)
  return {
    id: d.str('id'),
    framework: d.str('framework'),
    controlId: d.str('control_id'),
    controlName: d.str('control_name'),
    controlDescription: d.str('control_description'),
    controlCategory: d.str('control_category') || undefined,
    domain: d.str('domain') || undefined,
    isMandatory: d.bool('is_mandatory'),
    implementationGuidance: d.str('implementation_guidance') || undefined,
    evidenceRequirements: d.arr<string>('evidence_requirements'),
    relatedControls: d.arr<string>('related_controls'),
  }
}

function mapBackendCompanyControl(data: Record<string, unknown>): CompanyControl {
  const d = safeData(data)
  return {
    id: d.str('id'),
    companyId: d.str('company_id'),
    controlLibraryId: d.str('control_library_id'),
    status: d.str('status') as CompanyControl['status'],
    ownerName: d.str('owner_name') || undefined,
    ownerEmail: d.str('owner_email') || undefined,
    notes: d.str('notes') || undefined,
    evidenceFiles: d.arr<{ filename: string; url: string; uploadedAt: string }>('evidence_files'),
    lastReviewedAt: d.str('last_reviewed_at') || undefined,
    nextReviewDate: d.str('next_review_date') || undefined,
    control: d.raw('control') ? mapBackendControlLibrary(d.rec('control')) : undefined,
    createdAt: d.str('created_at'),
    updatedAt: d.str('updated_at'),
  }
}

function mapBackendAudit(data: Record<string, unknown>): ComplianceAudit {
  const d = safeData(data)
  return {
    id: d.str('id'),
    companyId: d.str('company_id'),
    framework: d.str('framework'),
    auditType: d.str('audit_type'),
    auditorOrganization: d.str('auditor_organization') || undefined,
    auditorName: d.str('auditor_name') || undefined,
    auditStartDate: d.str('audit_start_date') || undefined,
    auditEndDate: d.str('audit_end_date') || undefined,
    scopeDescription: d.str('scope_description') || undefined,
    findings: d.arr<Record<string, unknown>>('findings') || undefined,
    status: d.str('status'),
    createdAt: d.str('created_at'),
    updatedAt: d.str('updated_at'),
  }
}

function mapBackendSOXControl(data: Record<string, unknown>): SOXControl {
  const d = safeData(data)
  return {
    id: d.str('id'),
    companyId: d.str('company_id'),
    section: d.str('section'),
    controlId: d.str('control_id'),
    controlName: d.str('control_name'),
    description: d.str('description'),
    controlType: d.str('control_type'),
    frequency: d.str('frequency'),
    testResult: d.str('test_result') as SOXControl['testResult'],
    testDate: d.str('test_date') || undefined,
    testerName: d.str('tester_name') || undefined,
    notes: d.str('notes') || undefined,
    createdAt: d.str('created_at'),
    updatedAt: d.str('updated_at'),
  }
}

function mapBackendDashboard(data: Record<string, unknown>): ComplianceDashboard {
  const d = safeData(data)
  const byFramework: Record<string, FrameworkStats> = {}
  if (d.raw('by_framework')) {
    for (const [key, value] of Object.entries(d.rec('by_framework'))) {
      const v = safeData(value as Record<string, unknown>)
      byFramework[key] = {
        totalControls: v.num('total_controls'),
        implemented: v.num('implemented'),
        inProgress: v.num('in_progress'),
        notStarted: v.num('not_started'),
        verified: v.num('verified'),
        notApplicable: v.num('not_applicable'),
        compliancePercentage: v.num('compliance_percentage'),
      }
    }
  }

  return {
    byFramework,
    totalControls: d.num('total_controls'),
    totalImplemented: d.num('total_implemented'),
    overallCompliancePercentage: d.num('overall_compliance_percentage'),
    upcomingReviews: d.num('upcoming_reviews'),
    overdueReviews: d.num('overdue_reviews'),
    recentAudits: d.arr<Record<string, unknown>>('recent_audits').map(mapBackendAudit),
    soxSummary: d.raw('sox_summary') as Record<string, number> | undefined,
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

      const data = await apiClient.get<Record<string, unknown>>(endpoint)
      return {
        controls: ((data.controls || []) as Record<string, unknown>[]).map(mapBackendControlLibrary),
        total: (data.total as number) || 0,
        limit: (data.limit as number) || 100,
        offset: (data.offset as number) || 0,
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

      const data = await apiClient.get<Record<string, unknown>>(endpoint, { clientId })
      return {
        controls: ((data.controls || []) as Record<string, unknown>[]).map(mapBackendCompanyControl),
        total: (data.total as number) || 0,
        limit: (data.limit as number) || 100,
        offset: (data.offset as number) || 0,
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
      const data = await apiClient.get<Record<string, unknown>>(
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

      const data = await apiClient.get<Record<string, unknown>>(endpoint, { clientId })
      return {
        audits: ((data.audits || []) as Record<string, unknown>[]).map(mapBackendAudit),
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

      const data = await apiClient.get<Record<string, unknown>>(endpoint, { clientId })
      return {
        controls: ((data.controls || []) as Record<string, unknown>[]).map(mapBackendSOXControl),
        total: (data.total as number) || 0,
        limit: (data.limit as number) || 100,
        offset: (data.offset as number) || 0,
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
