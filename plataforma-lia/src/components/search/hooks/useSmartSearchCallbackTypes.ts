import type React from "react"
import type {
  ParsedEntities,
  SearchMode,
  SearchMetadata,
  ArchetypeVacancy,
  AutocompleteItem,
  SearchAnalysis,
  SearchSource,
} from "./smartSearchConstants"

export interface UseSmartSearchCallbacksParams {
  value: string
  onChange: (value: string) => void
  onSubmit: (query: string, entities: ParsedEntities, mode?: SearchMode, metadata?: SearchMetadata) => void
  onCancel: () => void
  onSearchSourceChange?: (source: SearchSource) => void
  isLoading: boolean
  mode: SearchMode
  entities: ParsedEntities
  booleanError: string | null
  jdContent: string
  similarUrls: string[]
  similarCvFiles: File[]
  combinedSuggestions: string[]
  showCombinedSuggestions: boolean
  selectedArchetype: ArchetypeVacancy | null
  archetypeSearchPrompt: string
  similarSearchPrompt: string
  jdSearchPrompt: string
  booleanFinalPrompt: string
  promptEnhancement: {
    enhanced_query: string
    explanation: string
    confidence: number
    suggestions?: Array<{ label: string; value: string; category: string }>
  } | null
  promptEnhancementDismissed: boolean
  showAutocomplete: boolean
  autocompleteItems: AutocompleteItem[]
  selectedAutocompleteIndex: number
  usedAutocompleteTerms: Set<string>
  autocompleteCache: React.MutableRefObject<Map<string, AutocompleteItem[]>>
  autocompleteAbortRef: React.MutableRefObject<AbortController | null>
  dismissedQueryRef: React.MutableRefObject<string>
  textareaRef: React.MutableRefObject<HTMLTextAreaElement | null>
  setEntities: React.Dispatch<React.SetStateAction<ParsedEntities>>
  setIsParsingEntities: React.Dispatch<React.SetStateAction<boolean>>
  setSearchAnalysis: React.Dispatch<React.SetStateAction<SearchAnalysis | null>>
  setIsAnalyzing: React.Dispatch<React.SetStateAction<boolean>>
  setPromptEnhancement: React.Dispatch<React.SetStateAction<{
    enhanced_query: string
    explanation: string
    confidence: number
    suggestions?: Array<{ label: string; value: string; category: string }>
  } | null>>
  setIsEnhancingPrompt: React.Dispatch<React.SetStateAction<boolean>>
  setPromptEnhancementDismissed: React.Dispatch<React.SetStateAction<boolean>>
  setBooleanError: React.Dispatch<React.SetStateAction<string | null>>
  setAutocompleteItems: React.Dispatch<React.SetStateAction<AutocompleteItem[]>>
  setShowAutocomplete: React.Dispatch<React.SetStateAction<boolean>>
  setSelectedAutocompleteIndex: React.Dispatch<React.SetStateAction<number>>
  setUsedAutocompleteTerms: React.Dispatch<React.SetStateAction<Set<string>>>
  setArchetypeVacancies: React.Dispatch<React.SetStateAction<ArchetypeVacancy[]>>
  setIsLoadingArchetypes: React.Dispatch<React.SetStateAction<boolean>>
  setClosedJobSuggestions: React.Dispatch<React.SetStateAction<Array<Record<string, unknown>>>>
  setIsLoadingClosedJobs: React.Dispatch<React.SetStateAction<boolean>>
  setJobSearchResults: React.Dispatch<React.SetStateAction<Array<{
    id: string
    title: string
    department: string | null
    seniority_level: string | null
    status: string
    created_at: string
    description: string | null
    technical_requirements: Array<Record<string, unknown>> | null
  }>>>
  setIsSearchingJobs: React.Dispatch<React.SetStateAction<boolean>>
  setIsCreatingArchetype: React.Dispatch<React.SetStateAction<boolean>>
  setArchetypeTab: React.Dispatch<React.SetStateAction<"list" | "create">>
  setSelectedArchetype: React.Dispatch<React.SetStateAction<ArchetypeVacancy | null>>
  setEditingArchetype: React.Dispatch<React.SetStateAction<Record<string, unknown> | null>>
  setEditArchetypeName: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeQuery: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeDescription: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeEmoji: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeTags: React.Dispatch<React.SetStateAction<string[]>>
  setEditArchetypeSkills: React.Dispatch<React.SetStateAction<string[]>>
  setEditArchetypeSeniority: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeIndustry: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeExperienceMin: React.Dispatch<React.SetStateAction<number | null>>
  setEditArchetypeLocation: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeWorkModel: React.Dispatch<React.SetStateAction<string>>
  setEditArchetypeLanguages: React.Dispatch<React.SetStateAction<string[]>>
  setEditArchetypeEmploymentType: React.Dispatch<React.SetStateAction<string>>
  setNewLanguageInput: React.Dispatch<React.SetStateAction<string>>
  setNewTagInput: React.Dispatch<React.SetStateAction<string>>
  setNewSkillInput: React.Dispatch<React.SetStateAction<string>>
  setJobSearchQuery: React.Dispatch<React.SetStateAction<string>>
  setArchetypeDescription: React.Dispatch<React.SetStateAction<string>>
  setShowArchetypeActions: React.Dispatch<React.SetStateAction<string | null>>
  setIsSavingArchetype: React.Dispatch<React.SetStateAction<boolean>>
  setIsDeletingArchetype: React.Dispatch<React.SetStateAction<string | null>>
  setSimilarUrls: React.Dispatch<React.SetStateAction<string[]>>
  setSimilarCvFiles: React.Dispatch<React.SetStateAction<File[]>>
  setCombinedSuggestions: React.Dispatch<React.SetStateAction<string[]>>
  setShowCombinedSuggestions: React.Dispatch<React.SetStateAction<boolean>>
  setIsAnalyzingProfiles: React.Dispatch<React.SetStateAction<boolean>>
  setPendingSourceChange: React.Dispatch<React.SetStateAction<'hybrid' | 'global' | null>>
  setShowSourceChangeModal: React.Dispatch<React.SetStateAction<boolean>>
  pendingSourceChange: 'hybrid' | 'global' | null
  editingArchetype: Record<string, unknown> | null
  editArchetypeName: string
  editArchetypeQuery: string
  editArchetypeDescription: string
  editArchetypeEmoji: string
  editArchetypeTags: string[]
  editArchetypeSkills: string[]
  editArchetypeSeniority: string
  editArchetypeIndustry: string
  editArchetypeExperienceMin: number | null
  editArchetypeLocation: string
  editArchetypeWorkModel: string
  editArchetypeLanguages: string[]
  editArchetypeEmploymentType: string
  MAX_SIMILAR_URLS: number
  MAX_CV_FILES: number
}
