import { apiClient, ApiClientOptions, ApiClientError } from './api-client'

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

function mapBackendPolicy(data: any): InsurancePolicy {
  return {
    id: data.id,
    companyId: data.company_id,
    policyNumber: data.policy_number,
    insurer: data.insurer,
    coverage: data.coverage,
    deductible: data.deductible,
    startDate: data.start_date,
    endDate: data.end_date,
    status: data.status,
    policyType: data.policy_type || 'cyber',
    notes: data.notes,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  }
}

function mapBackendCoverage(data: any): InsuranceCoverage {
  return {
    id: data.id,
    policyId: data.policy_id,
    coverageType: data.coverage_type,
    name: data.name,
    description: data.description,
    coverageLimit: data.coverage_limit,
    isActive: data.is_active,
    bcbArticle: data.bcb_article,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  }
}

function mapBackendDocument(data: any): InsuranceDocument {
  return {
    id: data.id,
    policyId: data.policy_id,
    filename: data.filename,
    fileType: data.file_type,
    fileSize: data.file_size,
    documentType: data.document_type,
    uploadedAt: data.uploaded_at,
    uploadedBy: data.uploaded_by,
    url: data.url,
  }
}

function mapBackendClaim(data: any): InsuranceClaim {
  return {
    id: data.id,
    policyId: data.policy_id,
    claimNumber: data.claim_number,
    incidentDate: data.incident_date,
    reportedDate: data.reported_date,
    description: data.description,
    claimAmount: data.claim_amount,
    status: data.status,
    resolution: data.resolution,
    resolvedAt: data.resolved_at,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  }
}

function mapBackendAlert(data: any): InsuranceAlert {
  return {
    id: data.id,
    type: data.type,
    severity: data.severity,
    title: data.title,
    message: data.message,
    dueDate: data.due_date,
    isRead: data.is_read,
    createdAt: data.created_at,
  }
}

function mapBackendDashboard(data: any): InsuranceDashboard {
  return {
    activePolicy: data.active_policy ? mapBackendPolicy(data.active_policy) : undefined,
    daysUntilExpiry: data.days_until_expiry ?? -1,
    totalCoverage: data.total_coverage ?? 0,
    totalClaims: data.total_claims ?? 0,
    openClaims: data.open_claims ?? 0,
    coverageGaps: data.coverage_gaps || [],
    complianceScore: data.compliance_score ?? 0,
  }
}

function mapBackendChecklistItem(data: any): BCBCoverageChecklistItem {
  return {
    coverageType: data.coverage_type,
    name: data.name,
    description: data.description,
    bcbArticle: data.bcb_article,
    isMandatory: data.is_mandatory,
    isCovered: data.is_covered,
    coverageId: data.coverage_id,
    policyId: data.policy_id,
  }
}

class InsuranceService {
  private baseEndpoint = '/insurance'

  async getDashboard(clientId: string): Promise<InsuranceDashboard> {
    try {
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/dashboard`,
        { clientId }
      )
      return mapBackendDashboard(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching insurance dashboard:', error.message)
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
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/alerts`,
        { clientId }
      )
      return {
        alerts: (data.alerts || []).map(mapBackendAlert),
        total: data.total || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching insurance alerts:', error.message)
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { alerts: [], total: 0 }
    }
  }

  async getCoverageChecklist(clientId: string): Promise<ChecklistResponse> {
    try {
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/coverage-checklist`,
        { clientId }
      )
      return {
        items: (data.items || []).map(mapBackendChecklistItem),
        totalItems: data.total_items || 0,
        coveredItems: data.covered_items || 0,
        compliancePercentage: data.compliance_percentage || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching coverage checklist:', error.message)
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

      const data = await apiClient.get<any>(endpoint, { clientId })
      return {
        policies: (data.policies || data.items || []).map(mapBackendPolicy),
        total: data.total || 0,
        limit: data.limit || 50,
        offset: data.offset || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching policies:', error.message)
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { policies: [], total: 0, limit: 50, offset: 0 }
    }
  }

  async getPolicy(clientId: string, policyId: string): Promise<InsurancePolicy | null> {
    try {
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/policies/${policyId}`,
        { clientId }
      )
      return mapBackendPolicy(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.status === 404) return null
        console.error('Error fetching policy:', error.message)
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
    const data = await apiClient.post<any>(
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
    const payload: any = {}
    if (input.policyNumber !== undefined) payload.policy_number = input.policyNumber
    if (input.insurer !== undefined) payload.insurer = input.insurer
    if (input.coverage !== undefined) payload.coverage = input.coverage
    if (input.deductible !== undefined) payload.deductible = input.deductible
    if (input.startDate !== undefined) payload.start_date = input.startDate
    if (input.endDate !== undefined) payload.end_date = input.endDate
    if (input.policyType !== undefined) payload.policy_type = input.policyType
    if (input.notes !== undefined) payload.notes = input.notes
    if (input.status !== undefined) payload.status = input.status

    const data = await apiClient.put<any>(
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
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/policies/${policyId}/coverages`,
        { clientId }
      )
      return {
        coverages: (data.coverages || data.items || []).map(mapBackendCoverage),
        total: data.total || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching coverages:', error.message)
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
    const data = await apiClient.post<any>(
      `${this.baseEndpoint}/policies/${policyId}/coverages`,
      payload,
      { clientId }
    )
    return mapBackendCoverage(data)
  }

  async getDocuments(clientId: string, policyId: string): Promise<DocumentListResponse> {
    try {
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/policies/${policyId}/documents`,
        { clientId }
      )
      return {
        documents: (data.documents || data.items || []).map(mapBackendDocument),
        total: data.total || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching documents:', error.message)
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

      const data = await apiClient.get<any>(endpoint, { clientId })
      return {
        claims: (data.claims || data.items || []).map(mapBackendClaim),
        total: data.total || 0,
        limit: data.limit || 50,
        offset: data.offset || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        console.error('Error fetching claims:', error.message)
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
    const data = await apiClient.post<any>(
      `${this.baseEndpoint}/claims`,
      payload,
      { clientId }
    )
    return mapBackendClaim(data)
  }
}

export const insuranceService = new InsuranceService()
