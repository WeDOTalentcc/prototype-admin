import { apiClient, ApiClientOptions, ApiClientError } from './api-client'
import { safeData } from '@/lib/safe-data'

export interface InsurancePolicy {
  id: string
  companyId: string
  policyNumber: string
  insurer: string
  coverage: number
  deductible: number
  startDate: string
  endDate: string
  status: 'active' | 'expired' | 'pending' | 'cancelled'
  policyType: string
  notes?: string
  createdAt: string
  updatedAt: string
}

export interface InsuranceCoverage {
  id: string
  policyId: string
  coverageType: string
  name: string
  description?: string
  coverageLimit?: number
  isActive: boolean
  bcbArticle?: string
  createdAt: string
  updatedAt: string
}

export interface InsuranceDocument {
  id: string
  policyId: string
  filename: string
  fileType: string
  fileSize?: number
  documentType: string
  uploadedAt: string
  uploadedBy?: string
  url?: string
}

export interface InsuranceClaim {
  id: string
  policyId: string
  claimNumber: string
  incidentDate: string
  reportedDate: string
  description: string
  claimAmount?: number
  status: 'open' | 'under_review' | 'approved' | 'denied' | 'paid' | 'closed'
  resolution?: string
  resolvedAt?: string
  createdAt: string
  updatedAt: string
}

export interface InsuranceDashboard {
  activePolicy?: InsurancePolicy
  daysUntilExpiry: number
  totalCoverage: number
  totalClaims: number
  openClaims: number
  coverageGaps: string[]
  complianceScore: number
}

export interface InsuranceAlert {
  id: string
  type: 'renewal' | 'gap' | 'expiry' | 'claim'
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  message: string
  dueDate?: string
  isRead: boolean
  createdAt: string
}

export interface BCBCoverageChecklistItem {
  coverageType: string
  name: string
  description: string
  bcbArticle: string
  isMandatory: boolean
  isCovered: boolean
  coverageId?: string
  policyId?: string
}

export interface PolicyListResponse {
  policies: InsurancePolicy[]
  total: number
  limit: number
  offset: number
}

export interface CoverageListResponse {
  coverages: InsuranceCoverage[]
  total: number
}

export interface DocumentListResponse {
  documents: InsuranceDocument[]
  total: number
}

export interface ClaimListResponse {
  claims: InsuranceClaim[]
  total: number
  limit: number
  offset: number
}

export interface AlertListResponse {
  alerts: InsuranceAlert[]
  total: number
}

export interface ChecklistResponse {
  items: BCBCoverageChecklistItem[]
  totalItems: number
  coveredItems: number
  compliancePercentage: number
}

export interface PolicyListParams {
  status?: string
  limit?: number
  offset?: number
}

export interface ClaimListParams {
  policyId?: string
  status?: string
  limit?: number
  offset?: number
}

export interface CreatePolicyInput {
  policyNumber: string
  insurer: string
  coverage: number
  deductible: number
  startDate: string
  endDate: string
  policyType?: string
  notes?: string
}

export interface UpdatePolicyInput {
  policyNumber?: string
  insurer?: string
  coverage?: number
  deductible?: number
  startDate?: string
  endDate?: string
  policyType?: string
  notes?: string
  status?: string
}

export interface CreateCoverageInput {
  coverageType: string
  name: string
  description?: string
  coverageLimit?: number
  bcbArticle?: string
}

export interface CreateClaimInput {
  policyId: string
  incidentDate: string
  description: string
  claimAmount?: number
}

export { ApiClientError }

function mapBackendPolicy(data: Record<string, unknown>): InsurancePolicy {
  const d = safeData(data)
  return {
    id: d.str('id'),
    companyId: d.str('company_id'),
    policyNumber: d.str('policy_number'),
    insurer: d.str('insurer'),
    coverage: d.num('coverage'),
    deductible: d.num('deductible'),
    startDate: d.str('start_date'),
    endDate: d.str('end_date'),
    status: d.str('status') as InsurancePolicy['status'],
    policyType: d.str('policy_type') || 'cyber',
    notes: d.str('notes') || undefined,
    createdAt: d.str('created_at'),
    updatedAt: d.str('updated_at'),
  }
}

function mapBackendCoverage(data: Record<string, unknown>): InsuranceCoverage {
  const d = safeData(data)
  return {
    id: d.str('id'),
    policyId: d.str('policy_id'),
    coverageType: d.str('coverage_type'),
    name: d.str('name'),
    description: d.str('description') || undefined,
    coverageLimit: d.num('coverage_limit') || undefined,
    isActive: d.bool('is_active'),
    bcbArticle: d.str('bcb_article') || undefined,
    createdAt: d.str('created_at'),
    updatedAt: d.str('updated_at'),
  }
}

function mapBackendDocument(data: Record<string, unknown>): InsuranceDocument {
  const d = safeData(data)
  return {
    id: d.str('id'),
    policyId: d.str('policy_id'),
    filename: d.str('filename'),
    fileType: d.str('file_type'),
    fileSize: d.num('file_size') || undefined,
    documentType: d.str('document_type'),
    uploadedAt: d.str('uploaded_at'),
    uploadedBy: d.str('uploaded_by') || undefined,
    url: d.str('url') || undefined,
  }
}

function mapBackendClaim(data: Record<string, unknown>): InsuranceClaim {
  const d = safeData(data)
  return {
    id: d.str('id'),
    policyId: d.str('policy_id'),
    claimNumber: d.str('claim_number'),
    incidentDate: d.str('incident_date'),
    reportedDate: d.str('reported_date'),
    description: d.str('description'),
    claimAmount: d.num('claim_amount') || undefined,
    status: d.str('status') as InsuranceClaim['status'],
    resolution: d.str('resolution') || undefined,
    resolvedAt: d.str('resolved_at') || undefined,
    createdAt: d.str('created_at'),
    updatedAt: d.str('updated_at'),
  }
}

function mapBackendAlert(data: Record<string, unknown>): InsuranceAlert {
  const d = safeData(data)
  return {
    id: d.str('id'),
    type: d.str('type') as InsuranceAlert['type'],
    severity: d.str('severity') as InsuranceAlert['severity'],
    title: d.str('title'),
    message: d.str('message'),
    dueDate: d.str('due_date') || undefined,
    isRead: d.bool('is_read'),
    createdAt: d.str('created_at'),
  }
}

function mapBackendDashboard(data: Record<string, unknown>): InsuranceDashboard {
  const d = safeData(data)
  return {
    activePolicy: d.raw('active_policy') ? mapBackendPolicy(d.rec('active_policy')) : undefined,
    daysUntilExpiry: d.num('days_until_expiry', -1),
    totalCoverage: d.num('total_coverage'),
    totalClaims: d.num('total_claims'),
    openClaims: d.num('open_claims'),
    coverageGaps: d.arr<string>('coverage_gaps'),
    complianceScore: d.num('compliance_score'),
  }
}

function mapBackendChecklistItem(data: Record<string, unknown>): BCBCoverageChecklistItem {
  const d = safeData(data)
  return {
    coverageType: d.str('coverage_type'),
    name: d.str('name'),
    description: d.str('description'),
    bcbArticle: d.str('bcb_article'),
    isMandatory: d.bool('is_mandatory'),
    isCovered: d.bool('is_covered'),
    coverageId: d.str('coverage_id') || undefined,
    policyId: d.str('policy_id') || undefined,
  }
}

class InsuranceService {
  private baseEndpoint = '/insurance'

  async getDashboard(clientId: string): Promise<InsuranceDashboard> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(
        `${this.baseEndpoint}/dashboard`,
        { clientId }
      )
      return mapBackendDashboard(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return {
        daysUntilExpiry: -1,
        totalCoverage: 0,
        totalClaims: 0,
        openClaims: 0,
        coverageGaps: [],
        complianceScore: 0,
      }
    }
  }

  async getAlerts(clientId: string): Promise<AlertListResponse> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(
        `${this.baseEndpoint}/alerts`,
        { clientId }
      )
      return {
        alerts: (Array.isArray(data.alerts) ? data.alerts as Record<string, unknown>[] : []).map(mapBackendAlert),
        total: Number(data.total ?? 0),
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { alerts: [], total: 0 }
    }
  }

  async getCoverageChecklist(clientId: string): Promise<ChecklistResponse> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(
        `${this.baseEndpoint}/coverage-checklist`,
        { clientId }
      )
      return {
        items: (Array.isArray(data.items) ? data.items as Record<string, unknown>[] : []).map(mapBackendChecklistItem),
        totalItems: Number(data.total_items ?? 0),
        coveredItems: Number(data.covered_items ?? 0),
        compliancePercentage: Number(data.compliance_percentage ?? 0),
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { items: [], totalItems: 0, coveredItems: 0, compliancePercentage: 0 }
    }
  }

  async getPolicies(
    clientId: string,
    params: PolicyListParams = {}
  ): Promise<PolicyListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (params.status) queryParams.set('status', params.status)
      if (params.limit) queryParams.set('limit', String(params.limit))
      if (params.offset) queryParams.set('offset', String(params.offset))

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}/policies?${queryParams}`
        : `${this.baseEndpoint}/policies`

      const data = await apiClient.get<Record<string, unknown>>(endpoint, { clientId })
      return {
        policies: (Array.isArray(data.policies) ? data.policies as Record<string, unknown>[] : Array.isArray(data.items) ? data.items as Record<string, unknown>[] : []).map(mapBackendPolicy),
        total: Number(data.total ?? 0),
        limit: Number(data.limit ?? 50),
        offset: Number(data.offset ?? 0),
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { policies: [], total: 0, limit: 50, offset: 0 }
    }
  }

  async getPolicy(clientId: string, policyId: string): Promise<InsurancePolicy | null> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(
        `${this.baseEndpoint}/policies/${policyId}`,
        { clientId }
      )
      return mapBackendPolicy(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.status === 404) return null
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }

  async createPolicy(clientId: string, input: CreatePolicyInput): Promise<InsurancePolicy> {
    const payload = {
      policy_number: input.policyNumber,
      insurer: input.insurer,
      coverage: input.coverage,
      deductible: input.deductible,
      start_date: input.startDate,
      end_date: input.endDate,
      policy_type: input.policyType || 'cyber',
      notes: input.notes,
    }
    const data = await apiClient.post<Record<string, unknown>>(
      `${this.baseEndpoint}/policies`,
      payload,
      { clientId }
    )
    return mapBackendPolicy(data)
  }

  async updatePolicy(
    clientId: string,
    policyId: string,
    input: UpdatePolicyInput
  ): Promise<InsurancePolicy> {
    const payload: Record<string, string | number | undefined> = {}
    if (input.policyNumber !== undefined) payload.policy_number = input.policyNumber
    if (input.insurer !== undefined) payload.insurer = input.insurer
    if (input.coverage !== undefined) payload.coverage = input.coverage
    if (input.deductible !== undefined) payload.deductible = input.deductible
    if (input.startDate !== undefined) payload.start_date = input.startDate
    if (input.endDate !== undefined) payload.end_date = input.endDate
    if (input.policyType !== undefined) payload.policy_type = input.policyType
    if (input.notes !== undefined) payload.notes = input.notes
    if (input.status !== undefined) payload.status = input.status

    const data = await apiClient.put<Record<string, unknown>>(
      `${this.baseEndpoint}/policies/${policyId}`,
      payload,
      { clientId }
    )
    return mapBackendPolicy(data)
  }

  async deletePolicy(clientId: string, policyId: string): Promise<void> {
    await apiClient.delete(
      `${this.baseEndpoint}/policies/${policyId}`,
      { clientId }
    )
  }

  async getCoverages(clientId: string, policyId: string): Promise<CoverageListResponse> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(
        `${this.baseEndpoint}/policies/${policyId}/coverages`,
        { clientId }
      )
      return {
        coverages: (Array.isArray(data.coverages) ? data.coverages as Record<string, unknown>[] : Array.isArray(data.items) ? data.items as Record<string, unknown>[] : []).map(mapBackendCoverage),
        total: Number(data.total ?? 0),
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { coverages: [], total: 0 }
    }
  }

  async addCoverage(
    clientId: string,
    policyId: string,
    input: CreateCoverageInput
  ): Promise<InsuranceCoverage> {
    const payload = {
      coverage_type: input.coverageType,
      name: input.name,
      description: input.description,
      coverage_limit: input.coverageLimit,
      bcb_article: input.bcbArticle,
    }
    const data = await apiClient.post<Record<string, unknown>>(
      `${this.baseEndpoint}/policies/${policyId}/coverages`,
      payload,
      { clientId }
    )
    return mapBackendCoverage(data)
  }

  async getDocuments(clientId: string, policyId: string): Promise<DocumentListResponse> {
    try {
      const data = await apiClient.get<Record<string, unknown>>(
        `${this.baseEndpoint}/policies/${policyId}/documents`,
        { clientId }
      )
      return {
        documents: (Array.isArray(data.documents) ? data.documents as Record<string, unknown>[] : Array.isArray(data.items) ? data.items as Record<string, unknown>[] : []).map(mapBackendDocument),
        total: Number(data.total ?? 0),
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { documents: [], total: 0 }
    }
  }

  async getClaims(
    clientId: string,
    params: ClaimListParams = {}
  ): Promise<ClaimListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (params.policyId) queryParams.set('policy_id', params.policyId)
      if (params.status) queryParams.set('status', params.status)
      if (params.limit) queryParams.set('limit', String(params.limit))
      if (params.offset) queryParams.set('offset', String(params.offset))

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}/claims?${queryParams}`
        : `${this.baseEndpoint}/claims`

      const data = await apiClient.get<Record<string, unknown>>(endpoint, { clientId })
      return {
        claims: (Array.isArray(data.claims) ? data.claims as Record<string, unknown>[] : Array.isArray(data.items) ? data.items as Record<string, unknown>[] : []).map(mapBackendClaim),
        total: Number(data.total ?? 0),
        limit: Number(data.limit ?? 50),
        offset: Number(data.offset ?? 0),
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { claims: [], total: 0, limit: 50, offset: 0 }
    }
  }

  async createClaim(clientId: string, input: CreateClaimInput): Promise<InsuranceClaim> {
    const payload = {
      policy_id: input.policyId,
      incident_date: input.incidentDate,
      description: input.description,
      claim_amount: input.claimAmount,
    }
    const data = await apiClient.post<Record<string, unknown>>(
      `${this.baseEndpoint}/claims`,
      payload,
      { clientId }
    )
    return mapBackendClaim(data)
  }
}

export const insuranceService = new InsuranceService()
