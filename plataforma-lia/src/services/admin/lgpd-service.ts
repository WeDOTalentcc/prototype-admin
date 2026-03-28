import { apiClient, ApiClientOptions, ApiClientError } from './api-client'
import { safeData } from '@/lib/safe-data'

export interface DPORegistry {
  id: string
  companyId: string
  dpoName: string
  dpoEmail: string
  dpoPhone?: string
  appointmentDate?: string
  publicContactUrl?: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface BreachNotification {
  id: string
  companyId: string
  breachDetectedAt: string
  breachDescription: string
  affectedDataTypes: string[]
  affectedCount?: number
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: 'detected' | 'investigating' | 'notified' | 'resolved'
  notificationSentToAnpd: boolean
  anpdNotificationAt?: string
  notificationSentToSubjects: boolean
  subjectsNotificationAt?: string
  remediationActions?: string
  resolvedAt?: string
  hoursUntilDeadline?: number
  createdAt: string
  updatedAt: string
}

export interface AutomatedDecision {
  id: string
  companyId: string
  candidateId?: string
  candidateName?: string
  decisionType: string
  agentType: string
  decision: string
  confidence: number
  explanation: string
  humanReviewRequested: boolean
  humanReviewCompletedAt?: string
  humanReviewResult?: string
  createdAt: string
}

export interface LGPDStats {
  dpoRegistered: boolean
  dpoActive: boolean
  totalBreaches: number
  openBreaches: number
  breachesPendingAnpd: number
  breachesDeadlineExceeded: number
  totalAutomatedDecisions: number
  pendingHumanReviews: number
  completedHumanReviews: number
}

export interface DPOListResponse {
  dpos: DPORegistry[]
  total: number
  limit: number
  offset: number
}

export interface BreachListResponse {
  breaches: BreachNotification[]
  total: number
  limit: number
  offset: number
}

export interface AutomatedDecisionListResponse {
  decisions: AutomatedDecision[]
  total: number
  limit: number
  offset: number
}

export interface BreachListParams {
  severity?: string
  status?: string
  pendingAnpd?: boolean
  limit?: number
  offset?: number
}

export interface AutomatedDecisionListParams {
  decisionType?: string
  humanReviewRequested?: boolean
  limit?: number
  offset?: number
}

export { ApiClientError }

function mapBackendDpo(data: Record<string, unknown>): DPORegistry {
  const d = safeData(data)
  return {
    id: d.str('id'),
    companyId: d.str('company_id'),
    dpoName: d.str('dpo_name'),
    dpoEmail: d.str('dpo_email'),
    dpoPhone: d.str('dpo_phone') || undefined,
    appointmentDate: d.str('appointment_date') || undefined,
    publicContactUrl: d.str('public_contact_url') || undefined,
    isActive: d.bool('is_active'),
    createdAt: d.str('created_at'),
    updatedAt: d.str('updated_at'),
  }
}

function mapBackendBreach(data: Record<string, unknown>): BreachNotification {
  const d = safeData(data)
  return {
    id: d.str('id'),
    companyId: d.str('company_id'),
    breachDetectedAt: d.str('breach_detected_at'),
    breachDescription: d.str('breach_description'),
    affectedDataTypes: d.arr<string>('affected_data_types'),
    affectedCount: d.num('affected_count') || undefined,
    severity: d.str('severity', 'low') as BreachNotification['severity'],
    status: d.str('status', 'detected') as BreachNotification['status'],
    notificationSentToAnpd: d.bool('notification_sent_to_anpd'),
    anpdNotificationAt: d.str('anpd_notification_at') || undefined,
    notificationSentToSubjects: d.bool('notification_sent_to_subjects'),
    subjectsNotificationAt: d.str('subjects_notification_at') || undefined,
    remediationActions: d.str('remediation_actions') || undefined,
    resolvedAt: d.str('resolved_at') || undefined,
    hoursUntilDeadline: d.num('hours_until_deadline') || undefined,
    createdAt: d.str('created_at'),
    updatedAt: d.str('updated_at'),
  }
}

function mapBackendDecision(data: Record<string, unknown>): AutomatedDecision {
  const d = safeData(data)
  return {
    id: d.str('id'),
    companyId: d.str('company_id'),
    candidateId: d.str('candidate_id') || undefined,
    candidateName: d.str('candidate_name') || undefined,
    decisionType: d.str('decision_type'),
    agentType: d.str('agent_type'),
    decision: d.str('decision'),
    confidence: d.num('confidence'),
    explanation: d.str('explanation'),
    humanReviewRequested: d.bool('human_review_requested'),
    humanReviewCompletedAt: d.str('human_review_completed_at') || undefined,
    humanReviewResult: d.str('human_review_result') || undefined,
    createdAt: d.str('created_at'),
  }
}

function mapBackendStats(data: Record<string, unknown>): LGPDStats {
  const d = safeData(data)
  return {
    dpoRegistered: d.bool('dpo_registered'),
    dpoActive: d.bool('dpo_active'),
    totalBreaches: d.num('total_breaches'),
    openBreaches: d.num('open_breaches'),
    breachesPendingAnpd: d.num('breaches_pending_anpd'),
    breachesDeadlineExceeded: d.num('breaches_deadline_exceeded'),
    totalAutomatedDecisions: d.num('total_automated_decisions'),
    pendingHumanReviews: d.num('pending_human_reviews'),
    completedHumanReviews: d.num('completed_human_reviews'),
  }
}

class LGPDService {
  private baseEndpoint = '/lgpd'

  async getStats(clientId: string): Promise<LGPDStats> {
    try {
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/stats`,
        { clientId }
      )
      return mapBackendStats(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return {
        dpoRegistered: false,
        dpoActive: false,
        totalBreaches: 0,
        openBreaches: 0,
        breachesPendingAnpd: 0,
        breachesDeadlineExceeded: 0,
        totalAutomatedDecisions: 0,
        pendingHumanReviews: 0,
        completedHumanReviews: 0,
      }
    }
  }

  async getDPO(clientId: string): Promise<DPORegistry | null> {
    try {
      const data = await apiClient.get<any>(
        `${this.baseEndpoint}/dpo/${clientId}`,
        { clientId }
      )
      return mapBackendDpo(data)
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.status === 404) return null
        if (error.isAuthError || error.isForbidden) throw error
      }
      return null
    }
  }

  async getBreaches(
    clientId: string,
    params: BreachListParams = {}
  ): Promise<BreachListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (params.severity) queryParams.set('severity', params.severity)
      if (params.status) queryParams.set('status', params.status)
      if (params.pendingAnpd !== undefined) queryParams.set('pending_anpd', String(params.pendingAnpd))
      if (params.limit) queryParams.set('limit', String(params.limit))
      if (params.offset) queryParams.set('offset', String(params.offset))

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}/breaches?${queryParams}`
        : `${this.baseEndpoint}/breaches`

      const data = await apiClient.get<any>(endpoint, { clientId })
      return {
        breaches: (data.breaches || []).map(mapBackendBreach),
        total: data.total || 0,
        limit: data.limit || 50,
        offset: data.offset || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { breaches: [], total: 0, limit: 50, offset: 0 }
    }
  }

  async getAutomatedDecisions(
    clientId: string,
    params: AutomatedDecisionListParams = {}
  ): Promise<AutomatedDecisionListResponse> {
    try {
      const queryParams = new URLSearchParams()
      if (params.decisionType) queryParams.set('decision_type', params.decisionType)
      if (params.humanReviewRequested !== undefined) {
        queryParams.set('human_review_requested', String(params.humanReviewRequested))
      }
      if (params.limit) queryParams.set('limit', String(params.limit))
      if (params.offset) queryParams.set('offset', String(params.offset))

      const endpoint = queryParams.toString()
        ? `${this.baseEndpoint}/decisions?${queryParams}`
        : `${this.baseEndpoint}/decisions`

      const data = await apiClient.get<any>(endpoint, { clientId })
      return {
        decisions: (data.decisions || []).map(mapBackendDecision),
        total: data.total || 0,
        limit: data.limit || 50,
        offset: data.offset || 0,
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        if (error.isAuthError || error.isForbidden) throw error
      }
      return { decisions: [], total: 0, limit: 50, offset: 0 }
    }
  }
}

export const lgpdService = new LGPDService()
