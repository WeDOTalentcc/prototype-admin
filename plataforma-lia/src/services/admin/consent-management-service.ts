import { apiClient, ApiClientOptions, ApiClientError } from './api-client'
import { safeData } from '@/lib/safe-data'

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
  metadata?: Record<string, unknown>
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
  metadata?: Record<string, unknown>
}

export interface RevokeConsentData {
  subjectIdentifier: string
  consentType: ConsentType
  reason?: string
}

export { ApiClientError }

function mapBackendVersion(data: Record<string, unknown>): ConsentVersion {
  const d = safeData(data)
  return {
    id: d.str('id'),
    companyId: d.str('company_id'),
    consentType: d.str('consent_type') as ConsentType,
    version: d.str('version'),
    title: d.str('title'),
    content: d.str('content'),
    summary: d.str('summary') || undefined,
    isActive: d.bool('is_active'),
    isCurrent: d.bool('is_current'),
    validityMonths: d.num('validity_months', 12),
    createdBy: d.str('created_by') || undefined,
    createdAt: d.str('created_at'),
    updatedAt: d.str('updated_at'),
    activeConsentsCount: d.num('active_consents_count') || undefined,
    pendingRenewalCount: d.num('pending_renewal_count') || undefined,
    expiredCount: d.num('expired_count') || undefined,
    revokedCount: d.num('revoked_count') || undefined,
  }
}

function mapBackendEvent(data: Record<string, unknown>): ConsentEvent {
  const d = safeData(data)
  return {
    id: d.str('id'),
    companyId: d.str('company_id'),
    versionId: d.str('version_id'),
    subjectIdentifier: d.str('subject_identifier'),
    subjectName: d.str('subject_name') || undefined,
    subjectEmail: d.str('subject_email') || undefined,
    eventType: d.str('event_type') as ConsentEventType,
    consentType: d.str('consent_type') as ConsentType,
    version: d.str('version'),
    grantedAt: d.str('granted_at') || undefined,
    expiresAt: d.str('expires_at') || undefined,
    revokedAt: d.str('revoked_at') || undefined,
    ipAddress: d.str('ip_address') || undefined,
    userAgent: d.str('user_agent') || undefined,
    metadata: d.raw('metadata') as Record<string, unknown> | undefined,
    createdAt: d.str('created_at'),
  }
}

function mapBackendStats(data: Record<string, unknown>): ConsentStats {
  const d = safeData(data)
  const byType: ConsentStats['byType'] = {}
  if (d.raw('by_type')) {
    for (const [key, value] of Object.entries(d.rec('by_type'))) {
      const v = safeData(value as Record<string, unknown>)
      byType[key] = {
        active: v.num('active'),
        pending: v.num('pending'),
        expired: v.num('expired'),
        revoked: v.num('revoked'),
        rate: v.num('rate'),
      }
    }
  }

  const ra = safeData(d.rec('recent_activity'))
  return {
    totalVersions: d.num('total_versions'),
    activeVersions: d.num('active_versions'),
    totalConsents: d.num('total_consents'),
    activeConsents: d.num('active_consents'),
    pendingRenewal: d.num('pending_renewal'),
    expired: d.num('expired'),
    revoked: d.num('revoked'),
    consentRate: d.num('consent_rate'),
    byType,
    recentActivity: {
      grantsToday: ra.num('grants_today'),
      revokesToday: ra.num('revokes_today'),
      expiringThisWeek: ra.num('expiring_this_week'),
    },
  }
}

function mapBackendSubjectHistory(data: Record<string, unknown>): SubjectHistory {
  const d = safeData(data)
  return {
    subjectIdentifier: d.str('subject_identifier'),
    subjectName: d.str('subject_name') || undefined,
    subjectEmail: d.str('subject_email') || undefined,
    events: d.arr<Record<string, unknown>>('events').map(mapBackendEvent),
    currentConsents: d.arr<Record<string, unknown>>('current_consents').map((c: Record<string, unknown>) => {
      const cd = safeData(c)
      return {
        consentType: cd.str('consent_type') as ConsentType,
        version: cd.str('version'),
        grantedAt: cd.str('granted_at'),
        expiresAt: cd.str('expires_at'),
        status: cd.str('status') as 'active' | 'expired' | 'revoked',
      }
    }),
  }
}

class ConsentManagementService {
  private baseEndpoint = '/consent'

  async getStats(clientId?: string): Promise<ConsentStats> {
    try {
      const options: ApiClientOptions = clientId ? { clientId } : {}
      const data = await apiClient.get<Record<string, unknown>>(`${this.baseEndpoint}/stats`, options)
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
      const data = await apiClient.get<Record<string, unknown>>(endpoint, options)
      return {
        versions: (Array.isArray(data.versions) ? data.versions as Record<string, unknown>[] : Array.isArray(data.items) ? data.items as Record<string, unknown>[] : []).map(mapBackendVersion),
        total: Number(data.total ?? 0),
        limit: Number(data.limit ?? 50),
        offset: Number(data.offset ?? 0),
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
      const data = await apiClient.get<Record<string, unknown>>(`${this.baseEndpoint}/versions/${id}`, options)
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
      const data = await apiClient.get<Record<string, unknown>>(
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
    const result = await apiClient.post<Record<string, unknown>>(`${this.baseEndpoint}/versions`, payload, options)
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
      const data = await apiClient.get<Record<string, unknown>>(endpoint, options)
      return {
        events: (Array.isArray(data.events) ? data.events as Record<string, unknown>[] : Array.isArray(data.items) ? data.items as Record<string, unknown>[] : []).map(mapBackendEvent),
        total: Number(data.total ?? 0),
        limit: Number(data.limit ?? 50),
        offset: Number(data.offset ?? 0),
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
      const data = await apiClient.get<Record<string, unknown>>(
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
    const result = await apiClient.post<Record<string, unknown>>(`${this.baseEndpoint}/events`, payload, options)
    return mapBackendEvent(result)
  }

  async revokeConsent(data: RevokeConsentData, clientId?: string): Promise<ConsentEvent> {
    const options: ApiClientOptions = clientId ? { clientId } : {}
    const payload = {
      subject_identifier: data.subjectIdentifier,
      consent_type: data.consentType,
      reason: data.reason,
    }
    const result = await apiClient.post<Record<string, unknown>>(`${this.baseEndpoint}/events/revoke`, payload, options)
    return mapBackendEvent(result)
  }
}

export const consentManagementService = new ConsentManagementService()
