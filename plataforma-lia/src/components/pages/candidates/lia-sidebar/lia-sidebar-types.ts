export interface ApiExperience {
  company_info?: { name?: string; location?: string; is_startup?: boolean }
  company_roles?: { title?: string; start_date?: string; end_date?: string; description?: string }[]
  company?: string
  title?: string
  start_date?: string
  end_date?: string
  duration?: string
  location?: string
  description?: string
}

export interface ApiEducation {
  school?: string
  degree?: string
  field_of_study?: string
  start_date?: string
  end_date?: string
}

export interface ApiCandidate {
  id?: string
  name?: string
  email?: string
  phone?: string
  headline?: string
  current_title?: string
  current_company?: string
  location?: string
  linkedin_url?: string
  avatar_url?: string
  picture_url?: string
  skills?: string[]
  seniority_level?: string
  years_experience?: number
  total_experience_years?: number
  match_score?: number
  source?: string
  has_email?: boolean
  has_phone?: boolean
  is_opentowork?: boolean
  is_decision_maker?: boolean
  is_top_universities?: boolean
  is_startup?: boolean
  company_info?: { is_startup?: boolean }
  expertise?: string
  outreach_message?: string
  experiences?: ApiExperience[]
  education?: ApiEducation[]
}

import { type SearchAnalytics } from "@/components/proactive-insight-card"
import { type CalibrationCandidate } from "@/components/calibration-card"

export type ChatMessage = {
  id: string
  type: 'user' | 'lia' | 'proactive_insight' | 'calibration'
  content: string
  timestamp: Date
  searchResults?: {
    localCount: number
    globalCount: number
    query: string
  }
  analytics?: SearchAnalytics
  candidates?: CalibrationCandidate[]
  metadata?: {
    action_executed?: boolean
    action_result?: Record<string, unknown>
    action_type?: string
    needs_confirmation?: boolean
    needs_params?: boolean
    pending_action_id?: string
    conversation_id?: string
  }
}

export type SearchTab = 'ia-natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'

export interface SearchResults {
  query: string
  isLoading: boolean
  localCount: number
  globalCount: number
  showGlobalResults: boolean
  globalDismissed: boolean
  local: unknown[]
  global: unknown[]
  isEnrichingContacts: boolean
}
