import React from "react"

export interface BackendEntities {
  location?: string
  job_title?: string
  years_experience?: string
  industry?: string
  skills?: string[]
  seniority?: string
  company?: string
}

export const ENTITY_LABELS: Record<string, string> = {
  job_title: 'Cargo',
  location: 'Localização',
  years_experience: 'Experiência',
  industry: 'Setor',
  skills: 'Habilidades',
  seniority: 'Senioridade',
  company: 'Empresa'
}

export const CRITERIA_TYPE_MAP: Record<string, string> = {
  'Cargo': 'job_title',
  'Localização': 'location',
  'Experiência': 'years_experience',
  'Setor': 'industry',
  'Habilidades': 'skills',
  'Habilidade': 'skills',
  'Senioridade': 'seniority',
  'Empresa': 'company'
}

export interface SearchCriterion {
  id: string
  type: 'location' | 'job_title' | 'experience' | 'years_experience' | 'industry' | 'skills' | 'seniority' | 'company' | 'education' | 'language'
  label: string
  value: string
  active: boolean
}

export interface SearchAnalysis {
  completeness_score: number
  criteria_found: { type: string; value: string; label: string }[]
  criteria_missing: { type: string; label: string; importance: string }[]
  alerts: { severity: string; message: string; suggestion?: string; action_value?: string }[]
  suggestions: string[]
  enrichment_suggestions?: Record<string, string[]>
  next_recommended_action?: string
}

export interface AutocompleteSuggestion {
  text: string
  category: string
  icon?: string
  description?: string
  insert_text?: string
}

export interface ArchetypeData {
  id: string
  name: string
  description?: string
  department?: string
  hired_candidate?: { name: string }
  criteria?: Record<string, unknown>
}

export interface SimilarProfile {
  url: string
  type: 'linkedin' | 'cv'
  filename?: string
}

export interface SearchFilters {
  ppiOptions: Record<string, unknown>
  general: Record<string, unknown>
  locations: Record<string, unknown>
  job: Record<string, unknown>
  company: Record<string, unknown>
  skills: Record<string, unknown>
  education: Record<string, unknown>
  languages: Record<string, unknown>
}

export type PromptEnhancement = {
  enhanced_query: string
  explanation: string
  confidence: number
  suggestions?: Array<{ label: string; value: string; category: string }>
} | null

export interface UseEAPCallbacksParams {
  parseEntitiesFromQuery: (query: string) => Promise<void>
  parsedEntities: BackendEntities
  advancedFilters: SearchFilters
  naturalSearchValue: string
  promptEnhancement: PromptEnhancement
  promptEnhancementDismissed: boolean
  dismissedQueryRef: React.MutableRefObject<string>
  autocompleteCache: React.MutableRefObject<Map<string, AutocompleteSuggestion[]>>
  similarProfiles: SimilarProfile[]
  similarUrls: string[]
  similarCvFiles: File[]
  editingArchetype: ArchetypeData | null
  editArchetypeName: string
  editArchetypeQuery: string
  editArchetypeDescription: string
  editArchetypeEmoji: string
  editArchetypeTags: string[]
  archetypeToDelete: { id: string; name: string } | null
  showAutocomplete: boolean
  autocompleteSuggestions: AutocompleteSuggestion[]
  selectedAutocompleteIndex: number
  extractedCriteria: SearchCriterion[]
  onCommand: (command: string, action: string) => void
  selectedCandidates: Record<string, unknown>[]
  candidateContext: Record<string, unknown> | null
  savedTemplates: Record<string, unknown>[]
  filteredCount: number
  totalCount: number
  inputValue: string
  isProcessing: boolean
  isExpanded: boolean
  templateSuggestions: Record<string, unknown>
  suggestionQueue: Record<string, unknown>
  setNaturalSearchValue: React.Dispatch<React.SetStateAction<string>>
  setShowPremiumAutocomplete: React.Dispatch<React.SetStateAction<boolean>>
  setPromptEnhancement: React.Dispatch<React.SetStateAction<PromptEnhancement>>
  setPromptEnhancementDismissed: React.Dispatch<React.SetStateAction<boolean>>
  setAutocompleteSuggestions: React.Dispatch<React.SetStateAction<AutocompleteSuggestion[]>>
  setShowAutocomplete: React.Dispatch<React.SetStateAction<boolean>>
  setSelectedAutocompleteIndex: React.Dispatch<React.SetStateAction<number>>
  setSimilarProfiles: React.Dispatch<React.SetStateAction<SimilarProfile[]>>
  setSimilarUrls: React.Dispatch<React.SetStateAction<string[]>>
  setSimilarCvFiles: React.Dispatch<React.SetStateAction<File[]>>
  setCombinedSuggestions: React.Dispatch<React.SetStateAction<string[]>>
  setShowCombinedSuggestions: React.Dispatch<React.SetStateAction<boolean>>
  setCombinedProfileKeywords: React.Dispatch<React.SetStateAction<string[]>>
  setIsAnalyzingProfiles: React.Dispatch<React.SetStateAction<boolean>>
  setArchetypes: React.Dispatch<React.SetStateAction<ArchetypeData[]>>
  setIsCreatingArchetype: React.Dispatch<React.SetStateAction<boolean>>
  setSelectedJobForArchetype: React.Dispatch<React.SetStateAction<string | null>>
  setEditingArchetype: React.Dispatch<React.SetStateAction<ArchetypeData | null>>
  setEditArchetypeName: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeQuery: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeDescription: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeEmoji: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeTags: React.Dispatch<React.SetStateAction<string[]>>
  setNewTagInput: React.Dispatch<React.SetStateAction<string>>
  setIsSavingArchetype: React.Dispatch<React.SetStateAction<boolean>>
  setIsDeletingArchetype: React.Dispatch<React.SetStateAction<string | null>>
  setShowDeleteArchetypeDialog: React.Dispatch<React.SetStateAction<boolean>>
  setArchetypeToDelete: React.Dispatch<React.SetStateAction<{ id: string; name: string } | null>>
  setIsCreatingFromSearch: React.Dispatch<React.SetStateAction<boolean>>
  setNewArchetypeDescription: React.Dispatch<React.SetStateAction<string>>
  setSearchSource: React.Dispatch<React.SetStateAction<'local' | 'global' | 'hybrid'>>
  setPendingSourceChange: React.Dispatch<React.SetStateAction<'hybrid' | 'global' | null>>
  setShowSourceChangeModal: React.Dispatch<React.SetStateAction<boolean>>
  setExtractedCriteria: React.Dispatch<React.SetStateAction<SearchCriterion[]>>
  setSearchAnalysis: React.Dispatch<React.SetStateAction<SearchAnalysis | null>>
  setParsedEntities: React.Dispatch<React.SetStateAction<BackendEntities>>
  setIsParsingEntities: React.Dispatch<React.SetStateAction<boolean>>
  setIsEnhancingPrompt: React.Dispatch<React.SetStateAction<boolean>>
  setIsProcessing: React.Dispatch<React.SetStateAction<boolean>>
  setLastCommand: React.Dispatch<React.SetStateAction<string>>
  setCommandHistory: React.Dispatch<React.SetStateAction<string[]>>
  setInputValue: React.Dispatch<React.SetStateAction<string>>
  setIsExpanded: React.Dispatch<React.SetStateAction<boolean>>
  setShowHistory: React.Dispatch<React.SetStateAction<boolean>>
  MAX_SIMILAR_URLS: number
  MAX_CV_FILES: number
  pendingSourceChange: 'hybrid' | 'global' | null
}
