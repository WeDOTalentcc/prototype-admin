import { apiClient, ApiClientOptions, ApiClientError } from './api-client'

export type ConsentType = 
  | 'personal_data'
  | 'marketing'
  | 'sensitive_data'
  | 'data_sharing'
  | 'cookies'
  | 'analytics'
  | 'third_party'

export type ConsentEventType = 'granted' | 'revoked' | 'expired' | 'renewed'

export interface ConsentVersion {
  id: string
  companyId: string
  consentType: ConsentType
  version: string
  title: string
  content: string
  summary?: string
  isActive: boolean
  isCurrent: boolean
  validityMonths: number
  createdBy?: string
  createdAt: string
  updatedAt: string
  activeConsentsCount?: number
  pendingRenewalCount?: number
  expiredCount?: number
  revokedCount?: number
}

export interface ConsentEvent {
  id: string
  companyId: string
  versionId: string
  subjectIdentifier: string
  subjectName?: string
  subjectEmail?: string
  eventType: ConsentEventType
  consentType: ConsentType
  version: string
  grantedAt?: string
  expiresAt?: string
  revokedAt?: string
  ipAddress?: string
  userAgent?: string
  metadata?: Record<string, any>
  createdAt: string
}

export interface ConsentStats {
  totalVersions: number
  activeVersions: number
  totalConsents: number
  activeConsents: number
  pendingRenewal: number
  expired: number
  revoked: number
  consentRate: number
  byType: Record<string, {
    active: number
    pending: number
    expired: number
    revoked: number
    rate: number
  }>
  recentActivity: {
    grantsToday: number
    revokesToday: number
    expiringThisWeek: number
  }
}

export interface ConsentVersionListResponse {
  versions: ConsentVersion[]
  total: number
  limit: number
  offset: number
}

export interface ConsentEventListResponse {
  events: ConsentEvent[]
  total: number
  limit: number
  offset: number
}

export interface SubjectHistory {
  subjectIdentifier: string
  subjectName?: string
  subjectEmail?: string
  events: ConsentEvent[]
  currentConsents: {
    consentType: ConsentType
    version: string
    grantedAt: string
    expiresAt: string
    status: 'active' | 'expired' | 'revoked'
  }[]
}

export interface ConsentVersionListParams {
  consentType?: string
  isActive?: boolean
  isCurrent?: boolean
  limit?: number
  offset?: number
}

export interface ConsentEventListParams {
  consentType?: string
  eventType?: string
  subjectIdentifier?: string
  startDate?: string
  endDate?: string
  limit?: number
  offset?: number
}

export interface CreateConsentVersionData {
  consentType: ConsentType
  title: string
  content: string
  summary?: string
  validityMonths?: number
}

export interface RegisterConsentEventData {
  versionId: string
  subjectIdentifier: string
  subjectName?: string
  subjectEmail?: string
  eventType: ConsentEventType
  ipAddress?: string
  userAgent?: string
  metadata?: Record<string, any>
}

export interface RevokeConsentData {
  subjectIdentifier: string
  consentType: ConsentType
  reason?: string
}

export { ApiClientError }

function mapBackendVersion(data: Record<string, unknown>): ConsentVersion {
  return {
    id: data.id,
    companyId: data.company_id,
    consentType: data.consent_type,
    version: data.version,
    title: data.title,
    content: data.content,
    summary: data.summary,
    isActive: data.is_active,
    isCurrent: data.is_current,
    validityMonths: data.validity_months || 12,
    createdBy: data.created_by,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
    activeConsentsCount: data.active_consents_count,
    pendingRenewalCount: data.pending_renewal_count,
    expiredCount: data.expired_count,
    revokedCount: data.revoked_count,
  }
}

function mapBackendEvent(data: Record<string, unknown>): ConsentEvent {
  return {
    id: data.id,
    companyId: data.company_id,
    versionId: data.version_id,
    subjectIdentifier: data.subject_identifier,
    subjectName: data.subject_name,
    subjectEmail: data.subject_email,
    eventType: data.event_type,
    consentType: data.consent_type,
    version: data.version,
    grantedAt: data.granted_at,
    expiresAt: data.expires_at,
    revokedAt: data.revoked_at,
    ipAddress: data.ip_address,
    userAgent: data.user_agent,
    metadata: data.metadata,
    createdAt: data.created_at,
  }
}

function mapBackendStats(data: Record<string, unknown>): ConsentStats {
  const byType: Record<string, any> = {}
  if (data.by_type) {
    for (const [key, value] of Object.entries(data.by_type as Record<string, any>)) {
      byType[key] = {
        active: value.active || 0,
        pending: value.pending || 0,
        expired: value.expired || 0,
        revoked: value.revoked || 0,
        rate: value.rate || 0,
      }
    }
  }

  return {
    totalVersions: data.total_versions || 0,
    activeVersions: data.active_versions || 0,
    totalConsents: data.total_consents || 0,
    activeConsents: data.active_consents || 0,
    pendingRenewal: data.pending_renewal || 0,
    expired: data.expired || 0,
    revoked: data.revoked || 0,
    consentRate: data.consent_rate || 0,
    byType,
    recentActivity: {
      grantsToday: data.recent_activity?.grants_today || 0,
      revokesToday: data.recent_activity?.revokes_today || 0,
      expiringThisWeek: data.recent_activity?.expiring_this_week || 0,
    },
  }
}

function mapBackendSubjectHistory(data: Record<string, unknown>): SubjectHistory {
  return {
    subjectIdentifier: data.subject_identifier,
    subjectName: data.subject_name,
    subjectEmail: data.subject_email,
    events: (data.events || []).map(mapBackendEvent),
    currentConsents: (data.current_consents || []).map((c: Record<string, unknown>) => ({
      consentType: c.consent_type,
      version: c.version,
      grantedAt: c.granted_at,
      expiresAt: c.expires_at,
      status: c.status,
    })),
  }
}

class ConsentManagementService {
  private baseEndpoint = '/consent'

  async getStats(clientId?: string): Promise<ConsentStats> {
    try {
      const options: ApiClientOptions = clientId ? { clientId } : {}
      const data = await apiClient.get<any>(`${this.baseEndpoint}/stats`, options)
      return mapBackendStats(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return {
        totalVersions: 0,
        activeVersions: 0,
        totalConsents: 0,
        activeConsents: 0,
        pendingRenewal: 0,
        expired: 0,
        revoked: 0,
        consentRate: 0,
        byType: {},
        recentActivity: {
          grantsToday: 0,
          revokesToday: 0,
          expiringThisWeek: 0,
        },
      }
    }
  }

  async getVersions(
    params: ConsentVersionListParams = {},
    clientId?: string
  ): Promise<ConsentVersionListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (params.consentType) queryParams.set('consent_type', params.consentType)
      if (params.isActive !== undefined) queryParams.set('is_active', String(params.isActive))
      if (params.isCurrent !== undefined) queryParams.set('is_current', String(params.isCurrent))
      if (params.limit) queryParams.set('limit', String(params.limit))
      if (params.offset) queryParams.set('offset', String(params.offset))

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}/versions?${queryParams}`
        : `${this.baseEndpoint}/versions`

      const options: ApiClientOptions = clientId ? { clientId } : {}
      const data = await apiClient.get<any>(endpoint, options)
      return {
        versions: (data.versions || data.items || []).map(mapBackendVersion),
        total: data.total || 0,
        limit: data.limit || 50,
        offset: data.offset || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { versions: [], total: 0, limit: 50, offset: 0 }
    }
  }

  async getVersion(id: string, clientId?: string): Promise<ConsentVersion | null> {
    try {
      const options: ApiClientOptions = clientId ? { clientId } : {}
      const data = await apiClient.get<any>(`${this.baseEndpoint}/versions/${id}`, options)
      return mapBackendVersion(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.status === 404) return null
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }

  async getCurrentVersion(consentType: ConsentType, clientId?: string): Promise<ConsentVersion | null> {
    try {
      const options: ApiClientOptions = clientId ? { clientId } : {}
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/versions/current/${consentType}`,
        options
      )
      return mapBackendVersion(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.status === 404) return null
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }

  async createVersion(data: CreateConsentVersionData, clientId?: string): Promise<ConsentVersion> {
    const options: ApiClientOptions = clientId ? { clientId } : {}
    const payload = {
      consent_type: data.consentType,
      title: data.title,
      content: data.content,
      summary: data.summary,
      validity_months: data.validityMonths || 12,
    }
    const result = await apiClient.post<any>(`${this.baseEndpoint}/versions`, payload, options)
    return mapBackendVersion(result)
  }

  async getEvents(
    params: ConsentEventListParams = {},
    clientId?: string
  ): Promise<ConsentEventListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (params.consentType) queryParams.set('consent_type', params.consentType)
      if (params.eventType) queryParams.set('event_type', params.eventType)
      if (params.subjectIdentifier) queryParams.set('subject_identifier', params.subjectIdentifier)
      if (params.startDate) queryParams.set('start_date', params.startDate)
      if (params.endDate) queryParams.set('end_date', params.endDate)
      if (params.limit) queryParams.set('limit', String(params.limit))
      if (params.offset) queryParams.set('offset', String(params.offset))

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}/events?${queryParams}`
        : `${this.baseEndpoint}/events`

      const options: ApiClientOptions = clientId ? { clientId } : {}
      const data = await apiClient.get<any>(endpoint, options)
      return {
        events: (data.events || data.items || []).map(mapBackendEvent),
        total: data.total || 0,
        limit: data.limit || 50,
        offset: data.offset || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { events: [], total: 0, limit: 50, offset: 0 }
    }
  }

  async getSubjectHistory(subjectIdentifier: string, clientId?: string): Promise<SubjectHistory | null> {
    try {
      const options: ApiClientOptions = clientId ? { clientId } : {}
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/events/subject/${encodeURIComponent(subjectIdentifier)}`,
        options
      )
      return mapBackendSubjectHistory(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.status === 404) return null
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }

  async registerEvent(data: RegisterConsentEventData, clientId?: string): Promise<ConsentEvent> {
    const options: ApiClientOptions = clientId ? { clientId } : {}
    const payload = {
      version_id: data.versionId,
      subject_identifier: data.subjectIdentifier,
      subject_name: data.subjectName,
      subject_email: data.subjectEmail,
      event_type: data.eventType,
      ip_address: data.ipAddress,
      user_agent: data.userAgent,
      metadata: data.metadata,
    }
    const result = await apiClient.post<any>(`${this.baseEndpoint}/events`, payload, options)
    return mapBackendEvent(result)
  }

  async revokeConsent(data: RevokeConsentData, clientId?: string): Promise<ConsentEvent> {
    const options: ApiClientOptions = clientId ? { clientId } : {}
    const payload = {
      subject_identifier: data.subjectIdentifier,
      consent_type: data.consentType,
      reason: data.reason,
    }
    const result = await apiClient.post<any>(`${this.baseEndpoint}/events/revoke`, payload, options)
    return mapBackendEvent(result)
  }
}

export const consentManagementService = new ConsentManagementService()
