export type { CompanyBenefit } from '@/types/benefits'

export interface ChatMessage {
  conversation_id?: string
  content: string
  user_id?: string
  attachments?: File[]
  audio?: Blob
}

export interface ChatResponse {
  message: {
    id: string
    conversation_id: string
    role: string
    content: string
    message_metadata: Record<string, unknown>
    created_at: string
  }
  conversation: {
    id: string
    user_id: string
    user_role: string
    title?: string
    intent?: string
    workflow_type?: string
    workflow_step: number
    workflow_data?: Record<string, unknown>
    status: string
    created_at: string
    updated_at: string
  }
}

export interface Conversation {
  id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  last_message_preview?: string
}

export interface CandidateSearchRequest {
  query: string
  search_type?: 'fast' | 'deep'
  limit?: number
  timeout?: number
}

export interface CandidateProfile {
  id: string | null
  name: string | null
  headline: string | null
  current_title: string | null
  current_company: string | null
  location: string | null
  contact: {
    email?: string
    phone?: string
    linkedin_url?: string
  } | null
  experience: Record<string, unknown>[]
  education: Record<string, unknown>[]
  skills: string[]
  summary: string | null
  match_score: number | null
  match_reasoning: string | null
}

export interface CandidateSearchResponse {
  query: string
  total_results: number
  candidates: CandidateProfile[]
  search_time_seconds: number
  credits_used: number | null
}

export interface CalibrationCandidateExperience {
  id: string
  company: string
  role: string
  period: string
  duration: string
  location?: string
  isPromotion?: boolean
  skills: string[]
}

export interface CalibrationCandidateEducation {
  id: string
  institution: string
  degree: string
  field: string
  period: string
}

export interface CalibrationMatchCriteria {
  id: string
  criteria: string
  met: boolean
  score?: number
}

export interface CalibrationCandidate {
  id: string
  name: string
  photoUrl?: string
  linkedinUrl?: string
  currentRole: string
  currentCompany: string
  location: string
  education: string
  highlights: {
    icon: string
    label: string
    value: string
  }[]
  experiences: CalibrationCandidateExperience[]
  educationHistory: CalibrationCandidateEducation[]
  skillMap: {
    category: string
    skills: string[]
  }[]
  languages: string[]
  additionalSkills: string[]
  matchCriteria: CalibrationMatchCriteria[]
  overallScore: number
  averageTenure: string
  currentTenure: string
}

export interface StartCalibrationSessionRequest {
  job_vacancy_id: string
  job_description: string
  technical_skills: string[]
  behavioral_competencies: string[]
  location?: string
  limit?: number
}

export interface StartCalibrationSessionResponse {
  session_id: string
  candidates: CalibrationCandidate[]
  total_found: number
}

export interface SubmitCalibrationFeedbackRequest {
  session_id: string
  candidate_id: string
  job_id: string
  approved: boolean
  lia_score?: number
  feedback_reason?: string
}

export interface CalibrationStatusResponse {
  approved_count: number
  rejected_count: number
  is_complete: boolean
}

export interface AddCandidatesToPipelineRequest {
  candidate_ids: string[]
  job_vacancy_id: string
  source?: string
}

export interface AddCandidatesToPipelineResponse {
  success: boolean
  added_count: number
}

export interface SendNotificationRequest {
  user_id: string
  title: string
  message: string
  notification_type: string
  related_job_id?: string
  action_url?: string
}

export interface SendNotificationResponse {
  success: boolean
  notification_id: string
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

export interface CommunicationHistoryCreate {
  company_id: string
  candidate_id: string
  candidate_name?: string
  candidate_email?: string
  candidate_phone?: string
  vacancy_id?: string
  communication_type: 'email' | 'whatsapp' | 'triagem' | 'agendamento' | 'feedback' | 'phone' | 'sms'
  channel: 'email' | 'whatsapp' | 'phone' | 'sms' | 'chat'
  direction: 'inbound' | 'outbound'
  subject?: string
  message_content: string
  sent_by?: string
  template_id?: string
  metadata?: Record<string, unknown>
}

export interface CommunicationHistoryRecord extends CommunicationHistoryCreate {
  id: string
  status: 'pending' | 'sent' | 'delivered' | 'read' | 'failed' | 'bounced'
  sent_at?: string
  delivered_at?: string
  read_at?: string
  error_message?: string
  created_at: string
  updated_at: string
}

export interface CommunicationHistoryListResponse {
  total: number
  items: CommunicationHistoryRecord[]
  limit: number
  offset: number
}

// =============================================
// JOB VACANCIES TYPES
// =============================================

export interface ScreeningQuestion {
  id: string | number
  question: string
  type?: string
  options?: string[]
  weight?: number
  required?: boolean
}

export interface JobVacancy {
  id: string
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
  salary_range?: Record<string, unknown>
  bonus_range?: Record<string, unknown>
  benefits?: string[]
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
  benefits?: string[]
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

export interface CandidateLocal {
  id: string
  name: string
  email?: string | null
  secondary_email?: string | null
  phone?: string | null
  mobile_phone?: string | null
  secondary_phone?: string | null
  linkedin_url?: string
  github_url?: string
  portfolio_url?: string
  avatar_url?: string
  
  date_of_birth?: string | null
  gender?: string | null
  nationality?: string | null
  marital_status?: string | null
  cpf?: string | null
  
  current_title?: string
  current_company?: string
  seniority_level?: string
  years_of_experience?: number
  self_introduction?: string | null
  
  technical_skills: string[]
  soft_skills: string[]
  languages: Record<string, string> | { language: string; level: string }[]
  certifications: string[]
  interests?: string[]
  
  location_city?: string
  location_state?: string
  location_country?: string
  address_street?: string | null
  address_number?: string | null
  address_district?: string | null
  address_zip?: string | null
  address_complement?: string | null
  
  is_remote: boolean
  willing_to_relocate: boolean
  mobility?: boolean
  work_model_preference?: string
  contract_type_preference?: string
  
  current_salary?: number | null
  salary_currency?: string
  desired_salary_min?: number
  desired_salary_max?: number
  salary_expectation_clt?: number | null
  salary_expectation_pj?: number | null
  salary_expectation_freelance?: number | null
  
  resume_url?: string | null
  resume_text?: string | null
  cover_letter?: string | null
  
  source: string
  ats_source_name?: string | null
  ats_candidate_id?: string | null
  pearch_profile_id?: string | null
  
  lia_score?: number
  lia_insights: Record<string, unknown>
  skills_match_percentage?: number
  
  status: string
  is_active: boolean
  is_blacklisted?: boolean
  blacklist_reason?: string | null
  
  preferred_contact_method?: string | null
  best_time_to_contact?: string | null
  communication_consent?: boolean
  
  completed_register?: boolean
  accept_terms?: boolean
  
  tags: string[]
  notes?: string
  additional_data?: Record<string, unknown>
  
  created_at?: string
  updated_at?: string
  last_contacted_at?: string
  last_activity_at?: string
  
  is_opentowork?: boolean
  is_decision_maker?: boolean
  is_top_universities?: boolean
  is_startup?: boolean
  is_tech?: boolean
  is_potential?: boolean
  candidate_status?: string
  stackoverflow_url?: string
  twitter_url?: string
  x_url?: string
  behance_url?: string
  company_info?: Record<string, unknown>
  expertise?: string[]
  outreach_message?: string
  screeningQuestions?: unknown[]
  [key: string]: unknown
}

export interface CandidateCreateRequest {
  name: string
  email?: string | null
  phone?: string | null
  linkedin_url?: string
  github_url?: string
  portfolio_url?: string
  current_title?: string
  current_company?: string
  seniority_level?: string
  years_of_experience?: number
  technical_skills?: string[]
  soft_skills?: string[]
  languages?: Record<string, string>
  certifications?: string[]
  location_city?: string
  location_state?: string
  location_country?: string
  is_remote?: boolean
  willing_to_relocate?: boolean
  desired_salary_min?: number
  desired_salary_max?: number
  salary_currency?: string
  work_model_preference?: string
  contract_type_preference?: string
  source: string
  tags?: string[]
  notes?: string
}

export interface CandidateListResponse {
  total: number
  skip: number
  limit: number
  items: CandidateLocal[]
}


// =============================================
// WSI (WeDoTalent Skill Index) TYPES
// =============================================

export interface WSICompetency {
  name: string
  type: 'technical' | 'behavioral' | 'cultural'
  level?: 'junior' | 'pleno' | 'senior' | 'lead' | 'executive'
  weight: number
}

export interface WSIQuestion {
  id: string
  competency: string
  framework: string
  question_type: string
  question_text: string
  weight: number
  sequence_order: number
}

export interface GenerateQuestionsRequest {
  session_id: string
  candidate_id: string
  job_vacancy_id: string
  competencies: WSICompetency[]
  mode?: 'compact' | 'compact_plus'
}

export interface GenerateQuestionsResponse {
  session_id: string
  questions: WSIQuestion[]
  total_questions: number
}

export interface AnalyzeResponseRequest {
  session_id: string
  question_id: string
  candidate_id: string
  job_vacancy_id: string
  question_text: string
  response_text: string
  response_audio_url?: string
  competency: string
  framework: string
}

export interface AnalyzeResponseResponse {
  analysis_id: string
  competency: string
  autodeclaration_score?: number
  context_score?: number
  bloom_level?: number
  dreyfus_level?: number
  evidences: string[]
  red_flags: string[]
  final_score: number
  justification: string
}

export interface CalculateWSIRequest {
  session_id: string
  candidate_id: string
  job_vacancy_id: string
  weights: Record<string, number>
}

export interface CalculateWSIResponse {
  result_id: string
  candidate_id: string
  job_vacancy_id: string
  technical_wsi: number
  behavioral_wsi: number
  overall_wsi: number
  classification: 'excelente' | 'alto' | 'medio' | 'regular' | 'baixo'
  percentile?: number
}

export interface StartVoiceScreeningRequest {
  candidate_id: string
  job_vacancy_id: string
  competencies: WSICompetency[]
  candidate_phone: string
  candidate_name: string
  job_title?: string
  job_description?: string
  mode?: 'compact' | 'compact_plus'
}

export interface StartVoiceScreeningResponse {
  session_id: string
  call_id: string
  agent_id: string
  candidate_id: string
  job_vacancy_id: string
  status: string
  questions_generated: number
}

export interface VoiceScreeningStatusResponse {
  session_id: string
  candidate_id: string
  job_vacancy_id: string
  screening_type: string
  mode: string
  status: 'pending' | 'in_progress' | 'processing' | 'completed' | 'failed'
  call_id?: string
  agent_id?: string
  started_at?: string
  completed_at?: string
  result?: CalculateWSIResponse
}

export interface WSIResultsResponse {
  candidate_id: string
  total_screenings: number
  results: {
    result_id: string
    job_vacancy_id: string
    overall_wsi: number
    technical_wsi: number
    behavioral_wsi: number
    classification: string
    percentile?: number
    created_at: string
    screening_type: string
  }[]
}

export interface WSISessionResponse {
  session: {
    id: string
    candidate_id: string
    job_vacancy_id: string
    screening_type: string
    mode: string
    status: string
    started_at?: string
    completed_at?: string
  }
  questions: WSIQuestion[]
  responses: {
    question_id: string
    competency: string
    final_score: number
    justification: string
  }[]
}

export interface WSIResultDetails {
  result_id: string
  session_id: string
  candidate_id: string
  job_vacancy_id: string
  scores: {
    technical_wsi: number
    behavioral_wsi: number
    overall_wsi: number
    classification: string
    percentile?: number
  }
  session: {
    screening_type: string
    mode: string
    started_at?: string
    completed_at?: string
    duration_minutes?: number
  }
  responses: {
    competency: string
    response_text: string
    scores: {
      autodeclaration?: number
      context?: number
      bloom_level?: number
      dreyfus_level?: number
      final_score: number
    }
    evidences: string[]
    red_flags: string[]
    consistency_penalty: number
    justification: string
    question: {
      text: string
      framework: string
      type: string
      weight: number
      expected_signals: string[]
      sequence: number
    }
  }[]
  report?: {
    executive_summary?: string
    technical_analysis: Record<string, unknown>
    behavioral_analysis: Record<string, unknown>
    cultural_fit: Record<string, unknown>
    recommendation: Record<string, unknown>
  }
  feedback?: {
    decision?: string
    main_message?: string
    technical_strengths: string[]
    development_opportunities: string[]
    behavioral_strengths: string[]
    next_steps?: string
    personalized_tip?: string
    development_plan: Record<string, unknown>
    recommended_resources: Record<string, unknown>[]
  }
  created_at?: string
}

export interface WSIVacancyRanking {
  job_vacancy_id: string
  total_screened: number
  averages: {
    overall: number
    technical: number
    behavioral: number
  }
  ranking: {
    rank: number
    total: number
    result_id: string
    candidate_id: string
    candidate_name: string
    candidate_title?: string
    overall_wsi: number
    technical_wsi: number
    behavioral_wsi: number
    classification: string
    percentile?: number
    screening_type: string
    created_at?: string
  }[]
}

export interface WSICandidateRanking {
  candidate_id: string
  job_vacancy_id: string
  ranked: boolean
  rank?: number
  total?: number
  overall_wsi?: number
}

export interface WSICandidatesScores {
  candidates: Record<string, {
    overall_wsi: number
    technical_wsi: number
    behavioral_wsi: number
    classification: string
    percentile: number
  }>
}

// =============================================
// COMPANY USERS TYPES
// =============================================

export interface CompanyUser {
  id: string
  name: string
  email: string
  role: string
  is_active: boolean
  active_jobs_count: number
  performance_score: number
}

export interface CompanyUsersResponse {
  users: CompanyUser[]
  total: number
}

// =============================================
// EMAIL TEMPLATES TYPES
// =============================================

export interface EmailTemplate {
  id: string
  name: string
  subject: string
  body_html: string
  body_text?: string
  category?: 'interview' | 'rejection' | 'offer' | 'followup' | 'screening'
  variables: string[]
  is_active: boolean
  created_by?: string
  created_at: string
  updated_at: string
}

export interface EmailTemplateCreateRequest {
  name: string
  subject: string
  body_html: string
  body_text?: string
  category?: 'interview' | 'rejection' | 'offer' | 'followup' | 'screening'
  variables?: string[]
  created_by?: string
}

export interface EmailTemplateUpdateRequest {
  name?: string
  subject?: string
  body_html?: string
  body_text?: string
  category?: 'interview' | 'rejection' | 'offer' | 'followup' | 'screening'
  variables?: string[]
  is_active?: boolean
}

export interface EmailTemplateListResponse {
  total: number
  items: EmailTemplate[]
}

export interface EmailPreviewRequest {
  template_id?: string
  subject?: string
  body_html?: string
  body_text?: string
  variables: Record<string, unknown>
}

export interface EmailPreviewResponse {
  subject: string
  body_html: string
  body_text?: string
  variables_used: Record<string, unknown>
  missing_variables: string[]
}

export interface EmailSendRequest {
  recipient_email: string
  recipient_name?: string
  candidate_id?: string
  variables: Record<string, unknown>
  send_immediately?: boolean
  subject_override?: string
  body_override?: string
}

export interface EmailSendResponse {
  success: boolean
  email_log_id: string
  status: string
  message: string
  recipient_email: string
  subject: string
}

export interface EmailCategory {
  value: string
  label: string
  description: string
}

// =============================================
// PIPELINE TYPES
// =============================================

export interface PipelineAction {
  id: string
  label: string
  icon: string
  action: string
  variant?: string
}

export interface StaleCandidateData {
  id: string
  name: string
  email: string
  current_title: string
  current_company: string
  status: string
  status_label: string
  days_stale: number
  stale_message: string
  urgency: "critical" | "high" | "normal"
  lia_score: number | null
  actions: PipelineAction[]
  last_activity: string | null
}

export interface PipelineGroup {
  job_id: string | null
  job_title: string
  job_department: string
  candidates: StaleCandidateData[]
}

export interface PipelineReportResponse {
  total_stale: number
  critical_count: number
  stale_threshold_days: number
  generated_at: string
  groups: PipelineGroup[]
  summary: {
    message: string
    urgency: "high" | "medium" | "low"
  }
}

export interface PipelineActionResponse {
  success: boolean
  candidate_id: string
  candidate_name: string
  message: string
  new_status?: string
  open_modal?: string
  navigate?: string
  action?: string
}


// =============================================
// BULK ACTIONS TYPES
// =============================================

export interface BulkOperationResult {
  success: boolean
  processed: number
  failed: number
  errors: Array<{
    id: string
    error: string
  }>
  results?: Array<{
    id: string
    status: string
    success: boolean
    error?: string
  }>
}

export interface BulkUpdateStatusRequest {
  candidate_ids: string[]
  new_status: string
}

export interface BulkAssignJobRequest {
  candidate_ids: string[]
  job_id: string
}

export interface BulkSendEmailRequest {
  candidate_ids: string[]
  template_id: string
  custom_data?: Record<string, unknown>
}

export interface BulkStartScreeningRequest {
  candidate_ids: string[]
  screening_type?: string
}

export interface BulkExportRequest {
  candidate_ids: string[]
  format: 'csv' | 'xlsx'
  fields?: string[]
}

export interface BulkDeleteRequest {
  candidate_ids: string[]
  hard_delete?: boolean
}

// =============================================
// NOTIFICATION TYPES
// =============================================

export interface BackendNotification {
  id: string
  user_id: string
  title: string
  message: string | null
  notification_type: string
  proactive_type: string | null
  category: string | null
  priority: string
  source_agent: string | null
  source_trigger: string | null
  related_job_id: string | null
  related_candidate_id: string | null
  related_task_id: string | null
  action_url: string | null
  action_label: string | null
  is_read: boolean
  read_at: string | null
  is_dismissed: boolean
  channels: string[]
  channels_sent: string[]
  extra_data: Record<string, unknown>
  created_at: string
  expires_at: string | null
}

export interface NotificationsResponse {
  success: boolean
  data: {
    notifications: BackendNotification[]
    total: number
    unread_count: number
    urgent_count: number
    has_more: boolean
  }
}

export interface NotificationSummaryResponse {
  success: boolean
  data: {
    unread_count: number
    urgent_count: number
    by_category?: Record<string, number>
    by_type?: Record<string, number>
  }
}

export interface NotificationActionResponse {
  success: boolean
  message: string
}

// =============================================
// CANDIDATE LISTS TYPES
// =============================================

export interface CandidateList {
  id: string
  name: string
  description: string | null
  color: string | null
  created_by: string
  created_at: string | null
  updated_at: string | null
  candidate_count: number
}

export interface CandidateListMember {
  member_id: string
  added_at: string | null
  added_by: string
  notes: string | null
  source: string
  candidate: CandidateLocal
}

export interface CandidateListDetail extends CandidateList {
  candidates: {
    total: number
    skip: number
    limit: number
    items: CandidateListMember[]
  }
}

export interface CandidateListsResponse {
  total: number
  skip: number
  limit: number
  items: CandidateList[]
}

export interface AddCandidatesResult {
  success: boolean
  added: number
  already_exists: number
  errors: Array<{ candidate_id: string; error: string }>
  total_in_list: number
}

export interface RemoveCandidatesResult {
  success: boolean
  removed: number
  total_in_list: number
}

export interface AssignJobsResult {
  success: boolean
  assigned: number
  already_in_job: number
  jobs_count: number
  candidates_count: number
}

export interface DirectEmailRequest {
  recipient_email: string
  recipient_name?: string
  subject: string
  body_html: string
  body_text?: string
  candidate_id?: string
  vacancy_id?: string
  metadata?: Record<string, unknown>
}

export interface DirectEmailResponse {
  success: boolean
  email_id: string
  status: string
  message: string
  recipient_email: string
  subject: string
  queued_at: string
  smtp_configured: boolean
}

export interface EmailHistoryItem {
  id: string
  recipient_email: string
  subject: string
  status: string
  body_preview?: string
  template_id?: string
  sent_at?: string
  created_at: string
  error_message?: string
}

export interface EmailHistoryResponse {
  total: number
  candidate_id?: string
  items: EmailHistoryItem[]
}

export interface EmailSystemStatus {
  status: string
  mode: string
  providers: {
    smtp: { configured: boolean; host?: string }
    sendgrid: { configured: boolean }
    resend: { configured: boolean }
  }
  message: string
  database_logging: boolean
  audit_trail: boolean
}

export interface CreateInterviewRequest {
  candidate_id: string
  candidate_name: string
  candidate_email: string
  interviewer_name: string
  interviewer_email: string
  start_time: string
  duration_minutes?: number
  interview_type?: string
  interview_mode?: string
  job_title?: string
  job_vacancy_id?: string
  location?: string
  notes?: string
  additional_interviewers?: Array<{ name?: string; email?: string }>
}

export interface InterviewApiResponse {
  id: string
  title: string
  candidate_id?: string
  candidate_name: string
  candidate_email: string
  interviewer_name: string
  interviewer_email: string
  additional_interviewers: Array<{ name?: string; email?: string }>
  start_time: string
  end_time: string
  duration_minutes: number
  interview_type: string
  interview_mode: string
  location?: string
  meeting_url?: string
  job_title?: string
  job_vacancy_id?: string
  status: string
  confirmation_status: string
  notes?: string
  is_synced_to_calendar: boolean
  created_at: string
  updated_at: string
}

export interface InterviewListResponse {
  total: number
  items: InterviewApiResponse[]
  calendar_status: string
}

export interface SchedulingStatus {
  status: string
  mode: string
  providers: {
    microsoft_graph: { configured: boolean; features: string[] }
    google_calendar: { configured: boolean; features: string[] }
  }
  local_features: {
    database_storage: boolean
    ics_generation: boolean
    email_notifications: string
  }
  message: string
}

// =============================================
// SHARED SEARCH TYPES
// =============================================

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

export interface CandidateFeedback {
  id: string
  candidate_id: string
  reviewer_email: string
  decision: 'approved' | 'maybe' | 'rejected'
  rating?: number
  comment?: string
  created_at: string
}

export interface CandidateSnapshot {
  id: string
  name: string
  title?: string
  company?: string
  location?: string
  experience_years?: number
  skills: string[]
  wsi_score?: number
  feedback?: CandidateFeedback
}

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

export interface GenerateInterviewQuestionsRequest {
  jobId: string
  candidateId: string
  includeVagaQuestions: boolean
  includeGapQuestions: boolean
  includeFitCultural: boolean
  wsiLevel?: string
}

export interface GenerateInterviewQuestionsResponse {
  questions: Array<{
    id: string
    text: string
    category: string
    subcategory?: string
    rationale?: string
    expectedResponse?: string
    wsiLevel?: string
  }>
  totalCount: number
  generatedAt: string
}

export interface GenerateInterviewParecerRequest {
  interviewNoteId: string
  candidateId?: string
  jobId?: string
  questions: Array<{
    id?: string
    questionId?: string
    text?: string
    questionText?: string
    starRating?: number | null
    rating?: number | null
    likertRating?: string | null
    notes?: string
    answer?: string
    skipped?: boolean
    category?: string
    source?: string
  }>
  generalNotes?: string
  transcription?: string | null
}

export interface GenerateInterviewParecerResponse {
  parecer: string
  recommendation: string
  strengths: string[]
  concerns: string[]
  overallScore?: number | null
  generatedAt: string
}

// =============================================
// INTERVIEW ANALYSIS TYPES
// =============================================

export interface InterviewAnalysisStatus {
  interview_id: string
  status: 'awaiting_transcript' | 'transcript_ready' | 'analyzed' | 'scheduled' | 'completed'
  has_transcript: boolean
  has_analysis: boolean
  analysis_result?: InterviewAnalysisResult
  error?: string
}

export interface InterviewAnalysisResult {
  overall_wsi_score: number
  recommendation: 'approve' | 'reject' | 'pending_review'
  bloom_scores: Record<string, number>
  dreyfus_scores: Record<string, number>
  big_five_profile: Record<string, number>
  star_completeness: number
  key_insights: string[]
  concerns: string[]
}

// =============================================
// AI SUGGESTIONS / AUTOMATION TYPES
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

export interface OrchestratorProcessRequest {
  user_id: string
  message: string
  conversation_id?: string
  context_type?: 'general' | 'wizard' | 'pipeline' | string  // Context type for routing
  context_id?: string  // ID related to context (e.g., job_id)
  conversation_context?: {
    conversation_id: string
    context_type: string
    context_id?: string
    summary?: string
    recent_messages: Array<{ role: string; content: string; intent?: string }>
  }  // Previous conversation context for memory
}

export interface OrchestratorProcessResponse {
  success: boolean
  conversation_id?: string
  intent?: string
  agent?: string
  confidence?: number
  result?: Record<string, unknown>
  message?: string
  error?: string
  suggested_tool_call?: {
    tool_name: string
    parameters?: Record<string, unknown>
    requires_confirmation?: boolean
    confirmation_message?: string
  }
  action_executed?: boolean
  action_result?: Record<string, unknown>
  action_type?: string
  needs_confirmation?: boolean
  needs_params?: boolean
  pending_action_id?: string
  draft_updates?: Record<string, unknown>
}

// =============================================
// CANDIDATE LIST TYPES
// =============================================

export interface CandidateListParams {
  search?: string
  status?: string
  tags?: string
  seniority?: string
  ids?: string
  limit?: number
  offset?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface CandidatePaginatedResponse {
  candidates: CandidateLocal[]
  total: number
  page: number
  per_page: number
}

export type InterpretMessageAction = 
  | 'advance_stage'
  | 'go_back'
  | 'confirm'
  | 'reject'
  | 'update_field'
  | 'ask_question'
  | 'provide_data'
  | 'help'
  | 'other'

export interface InterpretMessageRequest {
  message: string
  current_stage: string
  context?: Record<string, unknown>
}

export interface InterpretMessageResponse {
  action: InterpretMessageAction
  confidence: number
  extracted_entities?: Record<string, unknown>
  lia_response?: string
  should_advance: boolean
  target_stage?: string
  clarification_needed: boolean
  clarification_question?: string
  reasoning?: string
}
export interface ConversationalRequest {
  message: string
  context?: string
  mode?: string
}

export interface ConversationalResponse {
  response: string
  understood_intent: string
  suggested_action?: string
  can_help: boolean
}
export type WizardOrchestratorAction = 
  | 'respond' 
  | 'advance_stage' 
  | 'update_fields' 
  | 'request_clarification' 
  | 'provide_suggestion' 
  | 'validate_data'

export interface WizardOrchestratorRequest {
  message: string
  current_stage: string
  collected_data: Record<string, unknown>
  conversation_history?: Array<{ role: string; content: string }>
  company_id?: string
  conversation_id?: string
  user_id?: string
}

export interface WizardOrchestratorResponse {
  success: boolean
  lia_message: string
  detected_criteria: Record<string, unknown>
  next_stage?: string
  auto_transition: boolean
  tool_results: Array<Record<string, unknown>>
  confidence: number
  reasoning_steps: string[]
  intent?: string
  error?: string
  awaiting_confirmation?: boolean
  job_vacancy_id?: string
  job_published?: boolean
  action?: WizardOrchestratorAction
  response?: string
  updated_fields?: Record<string, unknown>
  target_stage?: string
  reasoning?: string
  suggestions?: Array<{ field: string; value: Record<string, unknown>; reason: string }>
  validation_errors?: string[]
  action_executed?: boolean
  action_result?: Record<string, unknown>
  action_type?: string
  needs_confirmation?: boolean
  needs_params?: boolean
  pending_action_id?: string
  draft_updates?: Record<string, unknown>
}
export interface ThumbsFeedbackResponse {
  feedback_id: string
  status: string
}

export interface RatingFeedbackResponse {
  feedback_id: string
  status: string
}

export interface CorrectionFeedbackResponse {
  feedback_id: string
  status: string
}

export interface FeedbackMetrics {
  satisfaction_rate: number
  total_feedback: number
  rating_average: number
}
export interface TranscriptionResponse {
  text: string
  confidence: number
  duration: number
}

export interface VoiceChatResponse {
  transcription: string
  response_text: string
  response_audio_base64: string
  session_id: string
  job_draft?: Record<string, unknown>
}

export interface VoiceStatusResponse {
  transcription_available: boolean
  synthesis_available: boolean
}
export interface ImageAnalysisResponse {
  analysis: string
  extracted_text?: string
  confidence: number
}

export interface DocumentAnalysisResponse {
  text_content: string
  structure: Record<string, unknown>
  formatting_quality: number
}

export interface ResumeAnalysisResponse {
  candidate_name: string
  contact_info: Record<string, unknown>
  layout_score: number
  improvement_suggestions: string[]
}

export interface MultimodalStatusResponse {
  image_analysis: boolean
  video_analysis: boolean
  document_analysis: boolean
}
export interface BackgroundJob {
  id: string
  job_type: string
  name: string
  status: string
  progress: number
  created_at: string
}

export interface ProactiveAction {
  id: string
  title: string
  description: string
  priority: string
  suggested_action: Record<string, unknown>
  created_at: string
}

export interface CreateJobResponse {
  job_id: string
  status: string
}

export interface ExecuteJobResponse {
  status: string
  result: Record<string, unknown>
}

export interface ActionResponse {
  status: string
}
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
