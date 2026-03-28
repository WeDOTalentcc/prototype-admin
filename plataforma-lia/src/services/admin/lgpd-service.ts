import type { BackendRecord } from '@/types/api'
import { apiClient, ApiClientOptions, ApiClientError } from './api-client'

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

function mapBackendDpo(data: BackendRecord): DPORegistry {
  return {
    id: data.id,
    companyId: data.company_id,
    dpoName: data.dpo_name,
    dpoEmail: data.dpo_email,
    dpoPhone: data.dpo_phone,
    appointmentDate: data.appointment_date,
    publicContactUrl: data.public_contact_url,
    isActive: data.is_active,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  }
}

function mapBackendBreach(data: BackendRecord): BreachNotification {
  return {
    id: data.id,
    companyId: data.company_id,
    breachDetectedAt: data.breach_detected_at,
    breachDescription: data.breach_description,
    affectedDataTypes: data.affected_data_types || [],
    affectedCount: data.affected_count,
    severity: data.severity,
    status: data.status,
    notificationSentToAnpd: data.notification_sent_to_anpd,
    anpdNotificationAt: data.anpd_notification_at,
    notificationSentToSubjects: data.notification_sent_to_subjects,
    subjectsNotificationAt: data.subjects_notification_at,
    remediationActions: data.remediation_actions,
    resolvedAt: data.resolved_at,
    hoursUntilDeadline: data.hours_until_deadline,
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  }
}

function mapBackendDecision(data: BackendRecord): AutomatedDecision {
  return {
    id: data.id,
    companyId: data.company_id,
    candidateId: data.candidate_id,
    candidateName: data.candidate_name,
    decisionType: data.decision_type,
    agentType: data.agent_type,
    decision: data.decision,
    confidence: data.confidence,
    explanation: data.explanation,
    humanReviewRequested: data.human_review_requested,
    humanReviewCompletedAt: data.human_review_completed_at,
    humanReviewResult: data.human_review_result,
    createdAt: data.created_at,
  }
}

function mapBackendStats(data: BackendRecord): LGPDStats {
  return {
    dpoRegistered: data.dpo_registered,
    dpoActive: data.dpo_active,
    totalBreaches: data.total_breaches,
    openBreaches: data.open_breaches,
    breachesPendingAnpd: data.breaches_pending_anpd,
    breachesDeadlineExceeded: data.breaches_deadline_exceeded,
    totalAutomatedDecisions: data.total_automated_decisions,
    pendingHumanReviews: data.pending_human_reviews,
    completedHumanReviews: data.completed_human_reviews,
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
