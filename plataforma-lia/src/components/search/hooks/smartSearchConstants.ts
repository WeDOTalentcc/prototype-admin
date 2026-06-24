import type React from "react"

export interface ParsedEntities {
  location?: string
  job_title?: string
  years_experience?: string
  industry?: string
  skills?: string[]
  seniority?: string
  company?: string
}

export type SearchSource = "local" | "global" | "hybrid"

export interface SmartSearchInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit: (query: string, entities: ParsedEntities, mode?: SearchMode, metadata?: SearchMetadata) => void
  onCancel: () => void
  onOpenFilters?: () => void
  onGoToResults?: () => void
  isLoading?: boolean
  placeholder?: string
  className?: string
  activeFiltersCount?: number
  searchSource?: SearchSource
  onSearchSourceChange?: (source: SearchSource) => void
  requireEmails?: boolean
  onRequireEmailsChange?: (value: boolean) => void
  requirePhoneNumbers?: boolean
  onRequirePhoneNumbersChange?: (value: boolean) => void
  initialJdContent?: string
}

export type SearchMode = "natural" | "similar" | "jd" | "boolean" | "archetypes"

export interface ArchetypeCandidate {
  id: string
  name: string
  current_title?: string
  years_experience?: number
  skills?: string[]
  hired_at?: string
}

export interface ArchetypeVacancy {
  id: string
  title: string
  department?: string
  closed_at?: string
  hired_candidate?: ArchetypeCandidate
}

export interface SearchMetadata {
  mode: SearchMode
  booleanQuery?: string
  jobDescription?: string
  similarProfileUrl?: string
  similarProfileUrls?: string[]
  combinedProfile?: CombinedProfileSuggestion
  archetypeVacancyId?: string
  archetypeCandidateId?: string
  archetypeProfile?: ArchetypeCandidate
  filters?: Record<string, unknown>
  searchText?: string
}

export interface CombinedProfileSuggestion {
  keywords: string[]
  title?: string
  seniority?: string
  skills_technical?: string[]
  skills_soft?: string[]
  industries?: string[]
  location?: string
  summary?: string
}

export interface SearchTag {
  key: keyof ParsedEntities
  label: string
  icon: React.ElementType
  filled: boolean
  value?: string
}

export interface SearchAlert {
  type: string
  severity: "info" | "warning" | "error"
  message: string
  suggestion?: string
  action_label?: string
  action_value?: string
}

export interface SearchAnalysis {
  completeness_score: number
  filled_criteria: string[]
  missing_criteria: string[]
  alerts: SearchAlert[]
  enrichment_suggestions: Record<string, string[]>
  next_recommended_action?: string
}

export interface AutocompleteItem {
  text: string
  category: string
  icon: string
  description?: string
  insert_text: string
}

export interface AutocompleteResponse {
  items: AutocompleteItem[]
  context_hint?: string
}

export const API_BASE = ""

export const SEARCH_SUGGESTIONS = [
  'Backend Sênior em São Paulo, 5+ anos em fintechs, Node.js e Python',
  'Product Manager Pleno remoto, experiência em B2B SaaS, metodologias ágeis'
]

export const MAX_SIMILAR_URLS = 3
export const MAX_CV_FILES = 2
