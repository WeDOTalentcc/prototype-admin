import React from "react"

export interface Candidate {
  id: string
  candidateId: string
  name: string
  email: string
  secondary_email?: string
  phone: string
  mobile_phone?: string
  secondary_phone?: string
  linkedin_url?: string
  github_url?: string
  portfolio_url?: string
  avatar_url?: string
  
  date_of_birth?: string
  gender?: string
  nationality?: string
  marital_status?: string
  cpf?: string
  
  current_title?: string
  current_company?: string
  seniority_level?: string
  years_of_experience?: number
  self_introduction?: string
  
  technical_skills?: string[]
  soft_skills?: string[]
  languages?: Record<string, string>
  certifications?: string[]
  interests?: string[]
  
  location_city?: string
  location_state?: string
  location_country?: string
  address_street?: string
  address_number?: string
  address_district?: string
  address_zip?: string
  address_complement?: string
  
  is_remote?: boolean
  willing_to_relocate?: boolean
  mobility?: boolean
  work_model_preference?: string
  contract_type_preference?: string
  
  current_salary?: number
  salary_currency?: string
  desired_salary_min?: number
  desired_salary_max?: number
  salary_expectation_clt?: number
  salary_expectation_pj?: number
  salary_expectation_freelance?: number
  
  resume_url?: string
  resume_text?: string
  cover_letter?: string
  
  source?: string
  ats_source_name?: string
  ats_candidate_id?: string
  pearch_profile_id?: string
  
  lia_score?: number
  lia_insights?: {
    strengths?: string[]
    concerns?: string[]
    recommendation?: string
    overall_summary?: string
  }
  skills_match_percentage?: number
  
  status?: string
  is_active?: boolean
  is_blacklisted?: boolean
  blacklist_reason?: string
  
  preferred_contact_method?: string
  best_time_to_contact?: string
  communication_consent?: boolean
  
  completed_register?: boolean
  accept_terms?: boolean
  
  tags?: string[]
  notes?: string
  additional_data?: Record<string, unknown>
  
  created_at?: string
  updated_at?: string
  last_contacted_at?: string
  last_activity_at?: string
  
  position: string
  monthlySalary: number
  location: string
  workModel: 'remoto' | 'híbrido' | 'presencial'
  score: number
  currentSalary?: string
  expectedSalary?: string
  contractType: 'CLT' | 'PJ' | 'Freelancer'
  benefits?: string[]
  linkedin: string

  // UI / display fields
  role?: string
  matchPercentage?: number
  avatar?: string
  lastUpdated?: Date

  // Extended profile
  skills: string[]
  experience: number
  education: string | Array<{
    school?: string
    degree?: string
    field_of_study?: string
    fieldOfStudy?: string
    startDate?: string
    endDate?: string
  }>
  experiences?: Record<string, unknown>[]
  workHistory?: Array<{
    company: string
    title?: string
    role?: string
    position?: string
    period?: string
    startDate?: string
    endDate?: string
    duration?: string
    location?: string
    description?: string
  }>
  salary?: {
    current: number
    expected: number
  }

  // LIA analysis
  liaAnalysis?: {
    score: number
    strengths: string[]
    concerns: string[]
    recommendation: string
  }

  // Big Five personality
  bigFive?: {
    openness: number
    conscientiousness: number
    extraversion: number
    agreeableness: number
    neuroticism: number
  }

  // Contact enrichment fields
  contact_source?: string | null
  enrichment_source?: string | null
  is_enriching?: boolean

  // Pearch / contact reveal fields
  has_email?: boolean
  has_phone?: boolean
  is_opentowork?: boolean
  is_open_to_work?: boolean
  is_decision_maker?: boolean
  is_top_universities?: boolean
  is_startup?: boolean
  is_hiring?: boolean
  expertise?: string[]
  outreach_message?: string
  headline?: string
  linkedin_followers_count?: number
  linkedin_connections_count?: number
  pearch_insights?: {
    overall_summary?: string
    match_reasoning?: string
    query_insights?: Array<{
      subquery?: string
      match_level?: string
      short_rationale?: string
      short_quotes?: string[]
    }>
  }
  best_personal_email?: string
  phone_types?: Record<string, boolean>
  estimated_age?: number
  middle_name?: string
  best_business_email?: string
  personal_emails?: string[]
  business_emails?: string[]
  company_followers_count?: number
  company_keywords?: string[]
  summary?: string
  followers_count?: number
  connections_count?: number
  insights?: Record<string, unknown> | null
  industry?: string
  company_segment?: string
  title?: string
  company?: string
}

export interface CandidatesPageState {
  candidates: Candidate[]
  selectedCandidates: Set<string>
  isLoading: boolean
  searchQuery: string
  currentTab: 'search' | 'favorites' | 'history' | 'saved' | 'lists'
  sortConfig: SortConfig
  filters: CandidateFilters
}

export interface SortConfig {
  column: string
  direction: 'asc' | 'desc'
}

export interface CandidateFilters {
  skills?: string[]
  location?: string[]
  seniority?: string[]
  workModel?: string[]
  salaryMin?: number
  salaryMax?: number
  source?: string[]
  tags?: string[]
}

export interface CandidateAction {
  type: 'contact' | 'schedule' | 'compare' | 'add_to_vacancy' | 'add_to_list' | 'download_cv'
  candidateIds: string[]
}

export interface SearchMetadata {
  query: string
  totalResults: number
  source: 'local' | 'global' | 'hybrid'
  creditsUsed?: number
  searchTime: number
}

// ─── Types ───────────────────────────────────────────────────────────────────

export interface TableFilters {
  statuses: string[]
  tags: string[]
  seniorityLevels: string[]
  workModels: string[]
  contractTypes: string[]
  minExperience?: number
  maxExperience?: number
  minScore?: number
  maxScore?: number
  minSalary?: number
  maxSalary?: number
  locations: string[]
  remoteOnly: boolean
  hasEmail: boolean
  hasPhone: boolean
  hasLinkedin: boolean
  sources: string[]
  jobTitles: string[]
  skills: string[]
  companies: string[]
  industries: string[]
  companySizes: string[]
  universities: string[]
  degrees: string[]
  fieldsOfStudy: string[]
  languages: string[]
  isOpenToWork: boolean
  isDecisionMaker: boolean
  isTopUniversities: boolean
  isStartup: boolean
  hasGithub: boolean
  hasPortfolio: boolean
  softSkills: string[]
  certifications: string[]
  willingToRelocate: boolean | null
  mobility: boolean | null
  updatedAtFrom?: string
  updatedAtTo?: string
  lastContactedFrom?: string
  lastContactedTo?: string
  availabilityWindow?: "immediate" | "15_days" | "30_days" | "60_days"
  shortlistedDateFrom?: string
  shortlistedDateTo?: string
  shortlistedVacancyOrigin?: string
  placementDateFrom?: string
  placementDateTo?: string
  placementVacancyDestination?: string
  placementClientCompany?: string
  specificVacancyId?: string
  registrationDateFrom?: string
  registrationDateTo?: string
}

export interface FilterSectionBaseProps {
  tableFilters: TableFilters
  setTableFilters: React.Dispatch<React.SetStateAction<TableFilters>>
}

export interface FilterSectionBasicProps extends FilterSectionBaseProps {
  searchSortBy: string
  onSortChange: (value: string) => void
}

export interface FilterSectionProfileProps extends FilterSectionBaseProps {
  onToggleFilter: (category: keyof TableFilters, value: string) => void
}

export interface FilterSectionAdvancedProps extends FilterSectionBaseProps {
  onToggleFilter: (category: keyof TableFilters, value: string) => void
  newSoftSkillFilter: string
  setNewSoftSkillFilter: (value: string) => void
  newCertificationFilter: string
  setNewCertificationFilter: (value: string) => void
  onClearAll: () => void
}

export interface CandidatesFilterPanelProps {
  onReSearchWithFilters?: () => void
  tableFilters: TableFilters
  setTableFilters: React.Dispatch<React.SetStateAction<TableFilters>>
  searchSortBy: string
  onSortChange: (value: string) => void
  newSoftSkillFilter: string
  setNewSoftSkillFilter: (value: string) => void
  newCertificationFilter: string
  setNewCertificationFilter: (value: string) => void
  activeFiltersCount: number
  onToggleFilter: (category: keyof TableFilters, value: string) => void
  onClearAll: () => void
  onClose: () => void
}

