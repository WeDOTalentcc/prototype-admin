import { apiClient, ApiClientOptions, ApiClientError } from './api-client'

export type DataSubjectRequestType = 
  | 'access'
  | 'correction'
  | 'deletion'
  | 'portability'
  | 'objection'
  | 'restriction'
  | 'explanation'

export type DataSubjectRequestStatus = 
  | 'pending'
  | 'in_review'
  | 'processing'
  | 'completed'
  | 'rejected'
  | 'cancelled'

export interface DataSubjectRequest {
  id: string
  companyId: string
  requestType: DataSubjectRequestType
  status: DataSubjectRequestStatus
  requesterName: string
  requesterEmail: string
  requesterCpf?: string
  requesterPhone?: string
  description?: string
  assignedTo?: string
  assignedToName?: string
  identityVerified: boolean
  identityVerifiedAt?: string
  identityVerifiedBy?: string
  processedAt?: string
  processedBy?: string
  completedAt?: string
  completedBy?: string
  rejectedAt?: string
  rejectedBy?: string
  rejectionReason?: string
  response?: string
  responseAttachments?: string[]
  deadlineAt: string
  daysUntilDeadline?: number
  isOverdue?: boolean
  slaStatus?: 'on_track' | 'at_risk' | 'overdue'
  createdAt: string
  updatedAt: string
}

export interface DataSubjectRequestStats {
  totalRequests: number
  pendingRequests: number
  inProgressRequests: number
  completedRequests: number
  rejectedRequests: number
  overdueRequests: number
  avgResponseTime: number
  slaComplianceRate: number
  byType: Record<string, number>
  byStatus: Record<string, number>
}

export interface DataSubjectRequestListResponse {
  requests: DataSubjectRequest[]
  total: number
  limit: number
  offset: number
}

export interface DataSubjectRequestListParams {
  status?: string
  requestType?: string
  isOverdue?: boolean
  search?: string
  limit?: number
  offset?: number
}

export interface CreateDataSubjectRequestData {
  requestType: DataSubjectRequestType
  requesterName: string
  requesterEmail: string
  requesterCpf?: string
  requesterPhone?: string
  description?: string
}

export interface AssignRequestData {
  assignedTo: string
}

export interface ProcessRequestData {
  notes?: string
}

export interface CompleteRequestData {
  response: string
  attachments?: string[]
}

export interface RejectRequestData {
  reason: string
}

export interface TrackingResult {
  id: string
  status: DataSubjectRequestStatus
  requestType: DataSubjectRequestType
  createdAt: string
  deadlineAt: string
  completedAt?: string
  response?: string
}

export { ApiClientError }

function mapBackendRequest(data: Record<string, unknown>): DataSubjectRequest {
  return {
    id: data.id,
    companyId: data.company_id,
    requestType: data.request_type,
    status: data.status,
    requesterName: data.requester_name,
    requesterEmail: data.requester_email,
    requesterCpf: data.requester_cpf,
    requesterPhone: data.requester_phone,
    description: data.description,
    assignedTo: data.assigned_to,
    assignedToName: data.assigned_to_name,
    identityVerified: data.identity_verified || false,
    identityVerifiedAt: data.identity_verified_at,
    identityVerifiedBy: data.identity_verified_by,
    processedAt: data.processed_at,
    processedBy: data.processed_by,
    completedAt: data.completed_at,
    completedBy: data.completed_by,
    rejectedAt: data.rejected_at,
    rejectedBy: data.rejected_by,
    rejectionReason: data.rejection_reason,
    response: data.response,
    responseAttachments: data.response_attachments || [],
    deadlineAt: data.deadline_at,
    daysUntilDeadline: data.days_until_deadline,
    isOverdue: data.is_overdue,
    slaStatus: data.sla_status,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  }
}

function mapBackendStats(data: Record<string, unknown>): DataSubjectRequestStats {
  return {
    totalRequests: data.total_requests || 0,
    pendingRequests: data.pending_requests || 0,
    inProgressRequests: data.in_progress_requests || 0,
    completedRequests: data.completed_requests || 0,
    rejectedRequests: data.rejected_requests || 0,
    overdueRequests: data.overdue_requests || 0,
    avgResponseTime: data.avg_response_time || 0,
    slaComplianceRate: data.sla_compliance_rate || 0,
    byType: data.by_type || {},
    byStatus: data.by_status || {},
  }
}

function mapBackendTracking(data: Record<string, unknown>): TrackingResult {
  return {
    id: data.id,
    status: data.status,
    requestType: data.request_type,
    createdAt: data.created_at,
    deadlineAt: data.deadline_at,
    completedAt: data.completed_at,
    response: data.response,
  }
}

class DataSubjectRequestsService {
  private baseEndpoint = '/data-subject-requests'

  async getStats(clientId?: string): Promise<DataSubjectRequestStats> {
    try {
      const options: ApiClientOptions = clientId ? { clientId } : {}
      const data = await apiClient.get<any>(`${this.baseEndpoint}/stats`, options)
      return mapBackendStats(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return {
        totalRequests: 0,
        pendingRequests: 0,
        inProgressRequests: 0,
        completedRequests: 0,
        rejectedRequests: 0,
        overdueRequests: 0,
        avgResponseTime: 0,
        slaComplianceRate: 0,
        byType: {},
        byStatus: {},
      }
    }
  }

  async getRequests(
    params: DataSubjectRequestListParams = {},
    clientId?: string
  ): Promise<DataSubjectRequestListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (params.status) queryParams.set('status', params.status)
      if (params.requestType) queryParams.set('request_type', params.requestType)
      if (params.isOverdue !== undefined) queryParams.set('is_overdue', String(params.isOverdue))
      if (params.search) queryParams.set('search', params.search)
      if (params.limit) queryParams.set('limit', String(params.limit))
      if (params.offset) queryParams.set('offset', String(params.offset))

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}?${queryParams}`
        : this.baseEndpoint

      const options: ApiClientOptions = clientId ? { clientId } : {}
      const data = await apiClient.get<any>(endpoint, options)
      return {
        requests: (data.requests || data.items || []).map(mapBackendRequest),
        total: data.total || 0,
        limit: data.limit || 50,
        offset: data.offset || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { requests: [], total: 0, limit: 50, offset: 0 }
    }
  }

  async getRequest(id: string, clientId?: string): Promise<DataSubjectRequest | null> {
    try {
      const options: ApiClientOptions = clientId ? { clientId } : {}
      const data = await apiClient.get<any>(`${this.baseEndpoint}/${id}`, options)
      return mapBackendRequest(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.status === 404) return null
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }

  async createRequest(data: CreateDataSubjectRequestData): Promise<DataSubjectRequest> {
    const payload = {
      request_type: data.requestType,
      requester_name: data.requesterName,
      requester_email: data.requesterEmail,
      requester_cpf: data.requesterCpf,
      requester_phone: data.requesterPhone,
      description: data.description,
    }
    const result = await apiClient.post<any>(this.baseEndpoint, payload)
    return mapBackendRequest(result)
  }

  async trackRequest(id: string): Promise<TrackingResult | null> {
    try {
      const response = await fetch(`/api/backend-proxy/data-subject-requests/track/${id}`)
      if (!response.ok) {
        if (response.status === 404) return null
        throw new Error('Failed to track request')
      }
      const data = await response.json()
      return mapBackendTracking(data)
    } catch (error) {
      return null
    }
  }

  async assignRequest(id: string, data: AssignRequestData, clientId?: string): Promise<DataSubjectRequest> {
    const options: ApiClientOptions = clientId ? { clientId } : {}
    const payload = { assigned_to: data.assignedTo }
    const result = await apiClient.put<any>(`${this.baseEndpoint}/${id}/assign`, payload, options)
    return mapBackendRequest(result)
  }

  async verifyIdentity(id: string, clientId?: string): Promise<DataSubjectRequest> {
    const options: ApiClientOptions = clientId ? { clientId } : {}
    const result = await apiClient.put<any>(`${this.baseEndpoint}/${id}/verify-identity`, {}, options)
    return mapBackendRequest(result)
  }

  async processRequest(id: string, data: ProcessRequestData = {}, clientId?: string): Promise<DataSubjectRequest> {
    const options: ApiClientOptions = clientId ? { clientId } : {}
    const payload = { notes: data.notes }
    const result = await apiClient.put<any>(`${this.baseEndpoint}/${id}/process`, payload, options)
    return mapBackendRequest(result)
  }

  async completeRequest(id: string, data: CompleteRequestData, clientId?: string): Promise<DataSubjectRequest> {
    const options: ApiClientOptions = clientId ? { clientId } : {}
    const payload = {
      response: data.response,
      attachments: data.attachments,
    }
    const result = await apiClient.put<any>(`${this.baseEndpoint}/${id}/complete`, payload, options)
    return mapBackendRequest(result)
  }

  async rejectRequest(id: string, data: RejectRequestData, clientId?: string): Promise<DataSubjectRequest> {
    const options: ApiClientOptions = clientId ? { clientId } : {}
    const payload = { reason: data.reason }
    const result = await apiClient.put<any>(`${this.baseEndpoint}/${id}/reject`, payload, options)
    return mapBackendRequest(result)
  }
}

export const dataSubjectRequestsService = new DataSubjectRequestsService()
