export interface LanguageEntry {
  language: string
  proficiency: string
}

export interface OpinionEntry {
  opinion_type?: string
  wsi_score?: number | null
  score?: number | null
  archetype?: string
  summary?: string
  created_at?: string
}

export interface OpinionsData {
  current_general_opinion?: OpinionEntry | null
  vacancy_opinions?: OpinionEntry[]
  total_opinions?: number
}

export type CandidateData = {
  name: string
  id?: string
  candidateId?: string
  pearch_id?: string
  avatar_url?: string
  avatar?: string
  photo_url?: string
  photoUrl?: string
  email?: string
  phone?: string
  position?: string
  title?: string
  location?: string
  seniority_level?: string
  seniorityLevel?: string
  years_of_experience?: number | null
  yearsOfExperience?: number | null
  linkedin?: string
  linkedin_url?: string
  github?: string
  github_url?: string
  stackoverflow?: string
  stackoverflow_url?: string
  twitter?: string
  twitter_url?: string
  x_url?: string
  behance?: string
  behance_url?: string
  portfolio?: string
  portfolio_url?: string
  current_company?: string
  company?: string
  company_segment?: string
  industry?: string
  communication_consent?: boolean
  communicationConsent?: boolean
  last_contacted_at?: string | Date
  lastContactedAt?: string | Date
  updated_at?: string | Date
  updatedAt?: string | Date
  created_at?: string | Date
  createdAt?: string | Date
  job_title?: string
  jobTitle?: string
  liaAnalysis?: { score?: number; fitScore?: number }
  lia_analysis?: { score?: number; fit_score?: number }
  workHistory?: Array<Record<string, unknown>>
  education?: Array<Record<string, unknown>>
  skills?: Array<Record<string, unknown>>
  certifications?: Array<Record<string, unknown>>
  projects?: Array<Record<string, unknown>>
  awards?: Array<Record<string, unknown>>
  contact_source?: string | null
  enrichment_source?: string | null
  is_enriching?: boolean
  [key: string]: unknown
}
