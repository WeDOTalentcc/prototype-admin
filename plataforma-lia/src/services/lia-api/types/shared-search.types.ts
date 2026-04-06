export interface SharedSearchRecipient {
  email: string
  name?: string
  role?: string
}

export interface CreateSharedSearchRequest {
  share_type: 'search' | 'list'
  title: string
  description?: string
  source_query?: string
  source_list_id?: string
  candidate_ids: string[]
  recipients: SharedSearchRecipient[]
  expires_at?: string
  message?: string
}

export interface SharedSearchFeedbackSummary {
  approved: number
  maybe: number
  rejected: number
  pending: number
}

export interface SharedSearchRecipientSummary {
  email: string
  name?: string
  role: string
  first_accessed_at?: string
  last_accessed_at?: string
  total_views: number
  feedback_count: number
}

export interface SharedSearch {
  id: string
  company_id: string
  share_type: 'search' | 'list'
  title: string
  description?: string
  status: 'active' | 'expired' | 'revoked'
  expires_at?: string
  created_at: string
  candidate_count: number
  feedback_summary: SharedSearchFeedbackSummary
  recipients: SharedSearchRecipientSummary[]
}

import type { CandidateSnapshot, CandidateFeedback } from "./candidate.types"

export interface SharedSearchDetail extends SharedSearch {
  candidates: CandidateSnapshot[]
  feedbacks: CandidateFeedback[]
}

export interface AddToJobRequest {
  job_id: string
  candidate_ids?: string[]
  all_approved?: boolean
  include_notes?: boolean
}

// =============================================
// INTERVIEW NOTES TYPES
// =============================================
