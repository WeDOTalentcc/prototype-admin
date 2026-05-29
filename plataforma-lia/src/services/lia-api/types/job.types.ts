/**
 * Task #765 — JobVacancy.benefits is JSONB on the backend.
 * Both legacy strings (pre-migration rows) and structured dicts are
 * accepted by the create/update/response schemas. The wizard sends the
 * full object so category, value, value_type, provider, is_highlighted
 * and is_mandatory survive the round-trip.
 */
export type JobBenefitInput =
  | string
  | {
      id?: string
      name: string
      description?: string
      category?: string | null
      // Aligned with backend `_BENEFIT_VALID_VALUE_TYPES` — anything
      // outside this set is clamped to 'informative' on save by
      // `normalize_benefits_payload`. Discount-flavored benefits are
      // expressed via `is_discount: true` on a benefit with one of the
      // three canonical value_types.
      value_type?: 'monetary' | 'percentage' | 'informative'
      value?: number | null
      percentage_value?: number | null
      value_details?: string | null
      provider?: string | null
      is_highlighted?: boolean
      is_mandatory?: boolean
      is_active?: boolean
      is_discount?: boolean
      seniority_levels?: string[]
      waiting_period_days?: number | null
      [extra: string]: unknown
    }

export interface JobCreatedNotificationRequest {
  job_id: string
  job_title: string
  department?: string
  location?: string
  work_model?: string
  seniority_level?: string
  job_description: string
  technical_requirements: { name: string; level: string; required: boolean }[]
  behavioral_competencies: { name: string; weight: string }[]
  languages: { name: string; level: string }[]
  salary_range?: { min?: number; max?: number; currency?: string }
  benefits: string[]
  deadline_screening: string
  deadline_shortlist: string
  deadline_closing: string
  interview_stages: { stageName: string; order: number; sla?: number }[]
  publishing_platforms: { linkedin: boolean; indeed: boolean; website: boolean }
  urgency_level: number
  is_confidential: boolean
  is_affirmative: boolean
  recruiter_email: string
  recruiter_name?: string
  manager_email?: string
  manager_name?: string
  channels: ('email' | 'teams')[]
}

export interface JobCreatedNotificationResponse {
  success: boolean
  notifications_sent: {
    recruiter: { email: boolean; teams: boolean }
    manager: { email: boolean; teams: boolean }
  }
  errors?: string[]
}

// =============================================
// COMMUNICATION HISTORY TYPES
// =============================================

export interface ScreeningQuestion {
  id: string | number
  question: string
  type?: string
  options?: string[]
  weight?: number
  required?: boolean
}

/**
 * Task #1196 — `location` pode chegar do backend como string simples,
 * string contendo JSON de endereço, ou objeto de endereço já parseado.
 * A normalização para texto legível é feita por `formatJobLocation`.
 */
export interface JobLocationAddress {
  city?: string | null
  state?: string | null
  country?: string | null
  [extra: string]: unknown
}

export interface JobVacancy {
  id: string
  title: string
  department?: string
  location?: string | JobLocationAddress
  work_model?: string
  employment_type?: string
  seniority_level?: string
  description?: string
  requirements?: string[]
  technical_requirements?: Record<string, unknown>[]
  languages?: Record<string, unknown>[]
  behavioral_competencies?: Record<string, unknown>[]
  salary?: string
  salary_range?: Record<string, unknown>
  bonus_range?: Record<string, unknown>
  benefits?: JobBenefitInput[]
  manager?: string
  manager_email?: string
  recruiter?: string
  recruiter_email?: string
  is_confidential: boolean
  visibility?: 'public' | 'internal' | 'confidential' | 'hidden'
  public_slug?: string
  status: string
  stage?: string
  priority: string
  created_at?: string
  updated_at?: string
  open_date?: string
  deadline?: string
  deadline_screening?: string
  deadline_shortlist?: string
  deadline_closing?: string
  funnel_data?: {
    total?: number
    screening?: number
    interview?: number
    final?: number
    hired?: number
  }
  lia_metrics?: {
    pipeline_lia?: number
    triagens_agendadas?: number
    triagens_realizadas?: number
    sem_resposta?: number
    entrevistas_agendadas?: number
  }
  nps?: number
  budget?: number
  budget_used?: number
  published_linkedin?: boolean
  published_website?: boolean
  published_indeed?: boolean
  is_affirmative?: boolean
  affirmative_type?: 'pcd' | 'racial' | 'gender' | 'age' | 'lgbtqia+'
  next_actions?: string[]
  urgency_level?: number
  approval_status?: string
  tags?: string[]
  screening_questions?: ScreeningQuestion[]
  interview_stages?: Record<string, unknown>[]
  organizational_structure?: Record<string, unknown>
  timeline?: Record<string, unknown>
  governance_rules?: Record<string, unknown>
  whatsapp_template_type?: string
  target_sector?: string
  target_segment?: string
  target_audience?: string
  masked_company_name?: string
  access_list?: string[]
  hiring_process?: string[]
  conversation_id?: string
  screening_config?: {
    channels?: {
      whatsapp?: { enabled: boolean; label?: string }
      chat_web?: { enabled: boolean; label?: string }
      phone?: { enabled: boolean; label?: string }
    }
    settings?: {
      min_score?: number
      response_timeout_hours?: number
    }
    metrics?: {
      screened_count?: number
      completion_rate?: number
      average_rating?: number
    }
    scheduling?: {
      auto_enabled?: boolean
      min_score_for_auto?: number
      calendar_provider?: string
      available_hours?: string
      interview_duration_min?: number
    }
    feedback_templates?: {
      approved?: string
      rejected?: string
    }
    screening_status?: string
  }
  eligibility_questions?: {
    id?: string
    type: string
    question: string
    required?: boolean
    disqualify_on_fail?: boolean
    expected_answer?: string
    order?: number
  }[]
  confidentiality_config?: {
    can_reveal_company_name?: boolean
    masked_intro?: string
    can_discuss_salary?: boolean
    can_discuss_benefits?: boolean
  }
  published_at?: string
  last_published_at?: string
  closed_at?: string
  created_by?: string
  created_by_email?: string
  /** FK pra company compensation_policies (canonical settings de salário). */
  compensation_policy_id?: string
}

export interface JobVacancyCreateRequest {
  title: string
  department?: string
  location?: string
  work_model?: string
  employment_type?: string
  seniority_level?: string
  description?: string
  requirements?: string[]
  technical_requirements?: Record<string, unknown>[]
  languages?: Record<string, unknown>[]
  behavioral_competencies?: Record<string, unknown>[]
  salary?: string
  salary_range?: {
    min?: number
    max?: number
    currency?: string
    bonus_min?: number
    bonus_max?: number
  }
  benefits?: JobBenefitInput[]
  manager?: string
  manager_email?: string
  recruiter?: string
  recruiter_email?: string
  is_confidential?: boolean
  is_affirmative?: boolean
  visibility?: 'public' | 'internal' | 'confidential'
  urgency_level?: number
  open_date?: string
  status?: string
  priority?: string
  screening_questions?: Record<string, unknown>[]
  eligibility_questions?: Record<string, unknown>[]
  interview_stages?: Record<string, unknown>[]
  conversation_id?: string
  published_linkedin?: boolean
  published_indeed?: boolean
  published_website?: boolean
}

export interface JobVacancyListResponse {
  total: number
  skip: number
  limit: number
  items: JobVacancy[]
  source?: string | null
}

export interface PublishJobResponse {
  success: boolean
  job_id: string
  status: string
  message: string
  sourcing_result?: {
    local_candidates_found: number
    local_candidates_added: number
    global_search_available: boolean
    credits_required: number
    awaiting_global_confirmation: boolean
  }
}

export interface GlobalSearchConfirmResponse {
  success: boolean
  candidates_found: number
  candidates_added: number
  credits_used: number
  message: string
}

export interface SourcingStatusResponse {
  job_id: string
  total_candidates: number
  qualified_candidates: number
  pipeline_status: string
  recommended_action?: string
}

export interface JobVacancyMetrics {
  job_id: string
  funnel: {
    total: number
    screening: number
    interview: number
    offer: number
    hired: number
    rejected: number
  }
  performance: {
    time_to_fill_days: number | null
    avg_time_in_stage_days: number | null
    conversion_rate: number
    source_breakdown: Record<string, number>
  }
  activity: {
    views_7d: number
    applications_7d: number
    interviews_scheduled: number
    last_activity: string | null
  }
  sla: {
    within_sla: boolean
    days_remaining: number | null
    deadline: string | null
  }
}


// =============================================
// CANDIDATES TYPES
// =============================================

export interface AISuggestion {
  id: string
  trigger: string
  candidate_id: string
  candidate_name: string
  vacancy_id: string
  vacancy_title: string
  suggested_action: string
  confidence: number
  reasoning: string[]
  created_at: string
  status: 'pending' | 'approved' | 'rejected' | 'modified'
}

export interface PendingAISuggestionsResponse {
  suggestions: AISuggestion[]
  total: number
}

export interface AISuggestionActionResponse {
  success: boolean
  suggestion_id: string
  new_status: string
  message?: string
}

export interface BulkAISuggestionActionResponse {
  success: boolean
  processed: number
  failed: number
  results: Array<{
    id: string
    success: boolean
    error?: string
  }>
}

// =============================================
// FAST TRACK VACANCY TYPES
// =============================================

export interface VacancySummary {
  id: string
  title: string
  department: string
  manager: string
  hired_candidate?: string
  date_closed: string
  salary_range: { min: number; max: number }
  work_model: string
  status: 'hired' | 'cancelled'
}

export interface VacancyFullDetails {
  id: string
  title: string
  department: string
  location: string
  work_model: string
  employment_type: string
  salary_range: { min: number; max: number; bonus_min?: number; bonus_max?: number }
  benefits: string[]
  technical_skills: Array<{ name: string; level: string; weight: number; required: boolean }>
  behavioral_competencies: Array<{ name: string; weight: number }>
  screening_questions: Array<{ question: string; type: string; expected_answer: Record<string, unknown> }>
  job_description: string
  manager: string
  manager_email: string
}

export interface VacancySearchCriteria {
  title?: string
  department?: string
  manager?: string
  location?: string
  work_model?: string
  status?: 'hired' | 'cancelled' | 'all'
  date_from?: string
  date_to?: string
  limit?: number
}

export interface VacancySearchResponse {
  vacancies: VacancySummary[]
  total: number
}

export interface VacancyAdjustments {
  salary_min?: number
  salary_max?: number
  location?: string
  work_model?: string
  benefits?: string[]
}

export interface PublishFastTrackResponse {
  success: boolean
  vacancy_id?: string
  message: string
}

// =============================================
// ORCHESTRATOR TYPES
// =============================================

export interface WSIQuestionForRegeneration {
  id: string
  question_text: string
  question_type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  competency_validated: string | null
  competency_type: 'technical' | 'behavioral' | 'eligibility' | null
  expected_answer_pattern?: string
  follow_up_question?: string
  weight?: number
}

export interface RegenerateWSIQuestionsRequest {
  company_id: string
  job_title: string
  current_questions: WSIQuestionForRegeneration[]
  technical_skills: string[]
  behavioral_competencies: string[]
  seniority?: string
  max_questions?: number
}

export interface RegenerateWSIQuestionsResponse {
  success: boolean
  questions: WSIQuestionForRegeneration[]
  questions_added: number
  questions_removed: number
  quality_warnings: string[]
}
