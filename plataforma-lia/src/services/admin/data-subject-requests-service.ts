import { apiClient, ApiClientOptions, ApiClientError } from './api-client'
import { safeData } from '@/lib/safe-data'

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
  const d = safeData(data)
  return {
    id: d.str('id'),
    companyId: d.str('company_id'),
    requestType: d.str('request_type') as DataSubjectRequestType,
    status: d.str('status') as DataSubjectRequestStatus,
    requesterName: d.str('requester_name'),
    requesterEmail: d.str('requester_email'),
    requesterCpf: d.str('requester_cpf') || undefined,
    requesterPhone: d.str('requester_phone') || undefined,
    description: d.str('description') || undefined,
    assignedTo: d.str('assigned_to') || undefined,
    assignedToName: d.str('assigned_to_name') || undefined,
    identityVerified: d.bool('identity_verified'),
    identityVerifiedAt: d.str('identity_verified_at') || undefined,
    identityVerifiedBy: d.str('identity_verified_by') || undefined,
    processedAt: d.str('processed_at') || undefined,
    processedBy: d.str('processed_by') || undefined,
    completedAt: d.str('completed_at') || undefined,
    completedBy: d.str('completed_by') || undefined,
    rejectedAt: d.str('rejected_at') || undefined,
    rejectedBy: d.str('rejected_by') || undefined,
    rejectionReason: d.str('rejection_reason') || undefined,
    response: d.str('response') || undefined,
    responseAttachments: d.arr<string>('response_attachments') || undefined,
    deadlineAt: d.str('deadline_at'),
    daysUntilDeadline: d.num('days_until_deadline') || undefined,
    isOverdue: d.bool('is_overdue') || undefined,
    slaStatus: (d.str('sla_status') || undefined) as DataSubjectRequest['slaStatus'],
    createdAt: d.str('created_at'),
    updatedAt: d.str('updated_at'),
  }
}

function mapBackendStats(data: Record<string, unknown>): DataSubjectRequestStats {
  const d = safeData(data)
  return {
    totalRequests: d.num('total_requests'),
    pendingRequests: d.num('pending_requests'),
    inProgressRequests: d.num('in_progress_requests'),
    completedRequests: d.num('completed_requests'),
    rejectedRequests: d.num('rejected_requests'),
    overdueRequests: d.num('overdue_requests'),
    avgResponseTime: d.num('avg_response_time'),
    slaComplianceRate: d.num('sla_compliance_rate'),
    byType: d.rec('by_type') as Record<string, number>,
    byStatus: d.rec('by_status') as Record<string, number>,
  }
}

function mapBackendTracking(data: Record<string, unknown>): TrackingResult {
  const d = safeData(data)
  return {
    id: d.str('id'),
    status: d.str('status') as DataSubjectRequestStatus,
    requestType: d.str('request_type') as DataSubjectRequestType,
    createdAt: d.str('created_at'),
    deadlineAt: d.str('deadline_at'),
    completedAt: d.str('completed_at') || undefined,
    response: d.str('response') || undefined,
  }
}

class DataSubjectRequestsService {
  private baseEndpoint = '/data-subject-requests'

  async getStats(clientId?: string): Promise<DataSubjectRequestStats> {
    try {
      const options: ApiClientOptions = clientId ? { clientId } : {}
      const data = await apiClient.get<Record<string, unknown>>(`${this.baseEndpoint}/stats`, options)
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
      const data = await apiClient.get<Record<string, unknown>>(endpoint, options)
      return {
        requests: (Array.isArray(data.requests) ? data.requests as Record<string, unknown>[] : Array.isArray(data.items) ? data.items as Record<string, unknown>[] : []).map(mapBackendRequest),
        total: Number(data.total ?? 0),
        limit: Number(data.limit ?? 50),
        offset: Number(data.offset ?? 0),
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
      const data = await apiClient.get<Record<string, unknown>>(`${this.baseEndpoint}/${id}`, options)
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
    const result = await apiClient.post<Record<string, unknown>>(this.baseEndpoint, payload)
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
    const result = await apiClient.put<Record<string, unknown>>(`${this.baseEndpoint}/${id}/assign`, payload, options)
    return mapBackendRequest(result)
  }

  async verifyIdentity(id: string, clientId?: string): Promise<DataSubjectRequest> {
    const options: ApiClientOptions = clientId ? { clientId } : {}
    const result = await apiClient.put<Record<string, unknown>>(`${this.baseEndpoint}/${id}/verify-identity`, {}, options)
    return mapBackendRequest(result)
  }

  async processRequest(id: string, data: ProcessRequestData = {}, clientId?: string): Promise<DataSubjectRequest> {
    const options: ApiClientOptions = clientId ? { clientId } : {}
    const payload = { notes: data.notes }
    const result = await apiClient.put<Record<string, unknown>>(`${this.baseEndpoint}/${id}/process`, payload, options)
    return mapBackendRequest(result)
  }

  async completeRequest(id: string, data: CompleteRequestData, clientId?: string): Promise<DataSubjectRequest> {
    const options: ApiClientOptions = clientId ? { clientId } : {}
    const payload = {
      response: data.response,
      attachments: data.attachments,
    }
    const result = await apiClient.put<Record<string, unknown>>(`${this.baseEndpoint}/${id}/complete`, payload, options)
    return mapBackendRequest(result)
  }

  async rejectRequest(id: string, data: RejectRequestData, clientId?: string): Promise<DataSubjectRequest> {
    const options: ApiClientOptions = clientId ? { clientId } : {}
    const payload = { reason: data.reason }
    const result = await apiClient.put<Record<string, unknown>>(`${this.baseEndpoint}/${id}/reject`, payload, options)
    return mapBackendRequest(result)
  }
}

export const dataSubjectRequestsService = new DataSubjectRequestsService()
