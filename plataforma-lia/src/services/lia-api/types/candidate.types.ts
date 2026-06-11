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

export interface CandidateLocal {
  id: string
  vc_id?: string
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
  is_hired?: boolean
  hired_at?: string | null
  hired_job_id?: string | null
  hired_job_title?: string | null
  is_blacklisted?: boolean
  blacklisted_by?: string | null
  blacklisted_at?: string | null
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
  items?: CandidateLocal[]
  total: number
  page: number
  per_page: number
  skip?: number
  limit?: number
  source?: string
}
