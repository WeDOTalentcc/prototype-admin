"use client"

import {
  type ParsedEntities,
  type SearchMode,
  type SearchMetadata,
  type ArchetypeVacancy,
  type AutocompleteItem,
  type SearchAnalysis,
  type SearchSource,
} from "./smartSearchConstants"
import { useSearchParsing, type UseSearchParsingParams } from "./useSearchParsing"
import { useSearchAutocomplete, type UseSearchAutocompleteParams } from "./useSearchAutocomplete"
import { useArchetypeCallbacks, type UseArchetypeCallbacksParams } from "./useArchetypeCallbacks"
import { useSimilarSearchCallbacks, type UseSimilarSearchCallbacksParams } from "./useSimilarSearchCallbacks"

interface UseSmartSearchCallbacksParams {
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
  setPromptEnhancement: React.Dispatch<React.SetStateAction<any>>
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

export function useSmartSearchCallbacks(params: UseSmartSearchCallbacksParams) {
  const {
    value,
    onChange,
    onSubmit,
    onSearchSourceChange,
    isLoading,
    mode,
    entities,
    booleanError,
    jdContent,
    similarUrls,
    similarCvFiles,
    combinedSuggestions,
    selectedArchetype,
    archetypeSearchPrompt,
    similarSearchPrompt,
    jdSearchPrompt,
    booleanFinalPrompt,
  } = params

  const parsingCallbacks = useSearchParsing({
    value: params.value,
    onChange: params.onChange,
    promptEnhancement: params.promptEnhancement,
    promptEnhancementDismissed: params.promptEnhancementDismissed,
    dismissedQueryRef: params.dismissedQueryRef,
    textareaRef: params.textareaRef,
    setEntities: params.setEntities,
    setIsParsingEntities: params.setIsParsingEntities,
    setSearchAnalysis: params.setSearchAnalysis,
    setIsAnalyzing: params.setIsAnalyzing,
    setPromptEnhancement: params.setPromptEnhancement,
    setIsEnhancingPrompt: params.setIsEnhancingPrompt,
    setPromptEnhancementDismissed: params.setPromptEnhancementDismissed,
  })

  const autocompleteCallbacks = useSearchAutocomplete({
    value: params.value,
    onChange: params.onChange,
    onSearchSourceChange: params.onSearchSourceChange,
    showAutocomplete: params.showAutocomplete,
    autocompleteItems: params.autocompleteItems,
    selectedAutocompleteIndex: params.selectedAutocompleteIndex,
    usedAutocompleteTerms: params.usedAutocompleteTerms,
    autocompleteCache: params.autocompleteCache,
    autocompleteAbortRef: params.autocompleteAbortRef,
    textareaRef: params.textareaRef,
    setBooleanError: params.setBooleanError,
    setAutocompleteItems: params.setAutocompleteItems,
    setShowAutocomplete: params.setShowAutocomplete,
    setSelectedAutocompleteIndex: params.setSelectedAutocompleteIndex,
    setUsedAutocompleteTerms: params.setUsedAutocompleteTerms,
    setPendingSourceChange: params.setPendingSourceChange,
    setShowSourceChangeModal: params.setShowSourceChangeModal,
    pendingSourceChange: params.pendingSourceChange,
  })

  const archetypeCallbacks = useArchetypeCallbacks({
    selectedArchetype: params.selectedArchetype,
    editingArchetype: params.editingArchetype,
    editArchetypeName: params.editArchetypeName,
    editArchetypeQuery: params.editArchetypeQuery,
    editArchetypeDescription: params.editArchetypeDescription,
    editArchetypeEmoji: params.editArchetypeEmoji,
    editArchetypeTags: params.editArchetypeTags,
    editArchetypeSkills: params.editArchetypeSkills,
    editArchetypeSeniority: params.editArchetypeSeniority,
    editArchetypeIndustry: params.editArchetypeIndustry,
    editArchetypeExperienceMin: params.editArchetypeExperienceMin,
    editArchetypeLocation: params.editArchetypeLocation,
    editArchetypeWorkModel: params.editArchetypeWorkModel,
    editArchetypeLanguages: params.editArchetypeLanguages,
    editArchetypeEmploymentType: params.editArchetypeEmploymentType,
    setArchetypeVacancies: params.setArchetypeVacancies,
    setIsLoadingArchetypes: params.setIsLoadingArchetypes,
    setClosedJobSuggestions: params.setClosedJobSuggestions,
    setIsLoadingClosedJobs: params.setIsLoadingClosedJobs,
    setJobSearchResults: params.setJobSearchResults,
    setIsSearchingJobs: params.setIsSearchingJobs,
    setIsCreatingArchetype: params.setIsCreatingArchetype,
    setArchetypeTab: params.setArchetypeTab,
    setSelectedArchetype: params.setSelectedArchetype,
    setEditingArchetype: params.setEditingArchetype,
    setEditArchetypeName: params.setEditArchetypeName,
    setEditArchetypeQuery: params.setEditArchetypeQuery,
    setEditArchetypeDescription: params.setEditArchetypeDescription,
    setEditArchetypeEmoji: params.setEditArchetypeEmoji,
    setEditArchetypeTags: params.setEditArchetypeTags,
    setEditArchetypeSkills: params.setEditArchetypeSkills,
    setEditArchetypeSeniority: params.setEditArchetypeSeniority,
    setEditArchetypeIndustry: params.setEditArchetypeIndustry,
    setEditArchetypeExperienceMin: params.setEditArchetypeExperienceMin,
    setEditArchetypeLocation: params.setEditArchetypeLocation,
    setEditArchetypeWorkModel: params.setEditArchetypeWorkModel,
    setEditArchetypeLanguages: params.setEditArchetypeLanguages,
    setEditArchetypeEmploymentType: params.setEditArchetypeEmploymentType,
    setNewLanguageInput: params.setNewLanguageInput,
    setNewTagInput: params.setNewTagInput,
    setNewSkillInput: params.setNewSkillInput,
    setJobSearchQuery: params.setJobSearchQuery,
    setArchetypeDescription: params.setArchetypeDescription,
    setShowArchetypeActions: params.setShowArchetypeActions,
    setIsSavingArchetype: params.setIsSavingArchetype,
    setIsDeletingArchetype: params.setIsDeletingArchetype,
  })

  const similarCallbacks = useSimilarSearchCallbacks({
    similarUrls: params.similarUrls,
    similarCvFiles: params.similarCvFiles,
    combinedSuggestions: params.combinedSuggestions,
    MAX_SIMILAR_URLS: params.MAX_SIMILAR_URLS,
    MAX_CV_FILES: params.MAX_CV_FILES,
    setSimilarUrls: params.setSimilarUrls,
    setSimilarCvFiles: params.setSimilarCvFiles,
    setCombinedSuggestions: params.setCombinedSuggestions,
    setShowCombinedSuggestions: params.setShowCombinedSuggestions,
    setIsAnalyzingProfiles: params.setIsAnalyzingProfiles,
  })

  const handleSubmit = () => {
    if (isLoading) return

    const metadata: SearchMetadata = { mode }

    if (mode === "natural" && value.trim()) {
      onSubmit(value.trim(), entities, mode, metadata)
    } else if (mode === "boolean" && value.trim() && !booleanError) {
      metadata.booleanQuery = value.trim()
      const queryText = booleanFinalPrompt.trim() || `Boolean: ${value.trim()}`
      metadata.searchText = queryText
      onSubmit(queryText, entities, mode, metadata)
    } else if (mode === "jd" && jdContent.trim()) {
      metadata.jobDescription = jdContent.trim()
      const queryText = jdSearchPrompt.trim() || `Job Description Analysis`
      metadata.searchText = queryText
      onSubmit(queryText, {}, mode, metadata)
    } else if (mode === "similar") {
      const validUrls = similarUrls.filter(url => url.trim().length > 0)
      if (validUrls.length === 0 && similarCvFiles.length === 0) return

      metadata.similarProfileUrls = validUrls
      metadata.similarProfileUrl = validUrls[0] || ""

      if (combinedSuggestions.length > 0) {
        metadata.combinedProfile = { keywords: combinedSuggestions }
      }

      const queryText = similarSearchPrompt.trim() || `Similar to: ${validUrls[0] || "CV upload"}`
      metadata.searchText = queryText
      onSubmit(queryText, {}, mode, metadata)
    } else if (mode === "archetypes" && selectedArchetype) {
      metadata.archetypeVacancyId = selectedArchetype.id
      metadata.archetypeCandidateId = selectedArchetype.hired_candidate?.id
      metadata.archetypeProfile = selectedArchetype.hired_candidate
      const queryText = archetypeSearchPrompt.trim() || `Arquétipo: ${selectedArchetype.title}`
      metadata.searchText = queryText
      onSubmit(queryText, {}, mode, metadata)
    }
  }

  return {
    ...parsingCallbacks,
    ...autocompleteCallbacks,
    ...archetypeCallbacks,
    ...similarCallbacks,
    handleSubmit,
  }
}
