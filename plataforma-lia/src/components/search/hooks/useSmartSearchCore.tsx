"use client"

import {
  type ParsedEntities,
  type SearchSource,
  type SmartSearchInputProps,
  type SearchMode,
  type ArchetypeCandidate,
  type ArchetypeVacancy,
  type SearchMetadata,
  type CombinedProfileSuggestion,
  MAX_SIMILAR_URLS,
  MAX_CV_FILES,
} from "./smartSearchConstants"
import { useSearchState } from "./useSearchState"
import { useSearchAPI } from "./useSearchAPI"
import { useSearchResults } from "./useSearchResults"

export type { ParsedEntities, SearchSource, SmartSearchInputProps, SearchMode, ArchetypeCandidate, ArchetypeVacancy, SearchMetadata, CombinedProfileSuggestion }

export function useSmartSearchCore(props: SmartSearchInputProps) {
  const state = useSearchState(props)
  const api = useSearchAPI(state)
  const results = useSearchResults(state, api)

  const {
    value, onChange, onSubmit, onCancel, onOpenFilters, onGoToResults,
    isLoading, placeholder, className, activeFiltersCount,
    searchSource, onSearchSourceChange, requireEmails, onRequireEmailsChange,
    requirePhoneNumbers, onRequirePhoneNumbersChange, showGlobalSearchOptions,
    mode, setMode, entities, isParsingEntities,
    booleanError, jdContent, setJdContent,
    searchAnalysis, isAnalyzing,
    autocompleteItems, showAutocomplete, setShowAutocomplete,
    selectedAutocompleteIndex, setSelectedAutocompleteIndex,
    autocompleteEnabled, setAutocompleteEnabled, setAutocompleteItems,
    promptEnhancement, isEnhancingPrompt,
    showSourceChangeModal, setShowSourceChangeModal,
    pendingSourceChange, setPendingSourceChange,
    jdVacancySearch, setJdVacancySearch, jdVacancyResults,
    isSearchingVacancies, selectedVacancy, setSelectedVacancy,
    jdSearchPrompt, setJdSearchPrompt, booleanFinalPrompt,
    panelWidth, textareaRef, ghostOverlayRef,
    fileInputRef, cvFileInputRef, containerRef,
    archetypes, similar, tags, filledCount, modes,
  } = state

  const {
    archetypeVacancies, selectedArchetype, isLoadingArchetypes, archetypeSearch,
    archetypeTab, archetypeCreateMode, closedJobSuggestions, isLoadingClosedJobs,
    jobSearchQuery, jobSearchResults, isSearchingJobs, archetypeDescription,
    isCreatingArchetype, editingArchetype, editArchetypeName, editArchetypeQuery,
    editArchetypeDescription, editArchetypeEmoji, editArchetypeTags, editArchetypeSkills,
    editArchetypeSeniority, editArchetypeIndustry, editArchetypeExperienceMin,
    editArchetypeLocation, editArchetypeWorkModel, editArchetypeLanguages,
    editArchetypeEmploymentType, newLanguageInput, newTagInput, newSkillInput,
    isSavingArchetype, isDeletingArchetype, showArchetypeActions, expandedArchetypeId,
    skillSuggestions, isLoadingSkillSuggestions, isFindingSimilarSkills, tagSuggestions,
    isLoadingTagSuggestions, isFindingSimilarTags, aiSuggestedSkills, selectedAiSkills,
    showSkillSuggestions, aiSuggestedTags, selectedAiTags, showTagSuggestions,
    industrySearchQuery, isIndustryDropdownOpen, archetypeSearchPrompt,
    setArchetypeVacancies, setSelectedArchetype, setArchetypeSearch, setArchetypeTab,
    setArchetypeCreateMode, setArchetypeDescription, setJobSearchQuery,
    setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeDescription,
    setEditArchetypeEmoji, setEditArchetypeTags, setEditArchetypeSkills,
    setEditArchetypeSeniority, setEditArchetypeIndustry, setEditArchetypeExperienceMin,
    setEditArchetypeLocation, setEditArchetypeWorkModel, setEditArchetypeLanguages,
    setEditArchetypeEmploymentType, setNewLanguageInput, setNewTagInput, setNewSkillInput,
    setShowArchetypeActions, setExpandedArchetypeId, setAiSuggestedSkills, setSelectedAiSkills,
    setShowSkillSuggestions, setAiSuggestedTags, setSelectedAiTags, setShowTagSuggestions,
    setIndustrySearchQuery, setIsIndustryDropdownOpen, setArchetypeSearchPrompt,
    setIsFindingSimilarSkills, setIsFindingSimilarTags,
    loadArchetypes, loadClosedJobSuggestions, searchJobsForArchetype, openArchetypeFromJob,
    createArchetypeFromJob, createArchetypeFromDescription, openEditArchetype, closeEditArchetype,
    saveArchetype, deleteArchetype, buildArchetypePrompt,
  } = archetypes

  const {
    similarUrl, similarUrls, similarCvFiles, combinedSuggestions, isAnalyzingProfiles,
    showCombinedSuggestions, similarSearchPrompt,
    setSimilarUrl, setSimilarUrls, setSimilarCvFiles, setCombinedSuggestions,
    setShowCombinedSuggestions, setSimilarSearchPrompt,
    addSimilarUrl, removeSimilarUrl, updateSimilarUrl, handleCvUpload, removeCvFile,
    removeSuggestion, addSuggestion, analyzeProfiles, hasMultipleSources,
  } = similar

  const {
    handleAutocompleteSelect, handleFileUpload, formatDate,
    handleSelectVacancy,
  } = api

  const {
    renderHighlightedText, handleSubmit, ghostTextInfo, ghostTextSuffix,
    handleAcceptEnhancement, handleDismissEnhancement,
    handleSourceChange, confirmSourceChange, handleKeyDown,
    clearSelectedVacancy, canSubmit, getPlaceholder, filteredArchetypes,
    scopeControlsProps, SearchScopeControls,
  } = results

  return {
    modes, value, MAX_CV_FILES, MAX_SIMILAR_URLS, SearchScopeControls, scopeControlsProps,
    activeFiltersCount, addSimilarUrl, aiSuggestedSkills, aiSuggestedTags, analyzeProfiles,
    archetypeCreateMode, archetypeDescription, archetypeSearch, archetypeSearchPrompt,
    archetypeTab, archetypeVacancies, autocompleteEnabled, autocompleteItems, booleanError,
    buildArchetypePrompt, canSubmit, className, clearSelectedVacancy, closeEditArchetype,
    combinedSuggestions, confirmSourceChange, containerRef, createArchetypeFromDescription,
    cvFileInputRef, deleteArchetype, editArchetypeDescription, editArchetypeEmoji,
    editArchetypeEmploymentType, editArchetypeExperienceMin, editArchetypeIndustry,
    editArchetypeLanguages, editArchetypeLocation, editArchetypeName, editArchetypeQuery,
    editArchetypeSeniority, editArchetypeSkills, editArchetypeTags, editArchetypeWorkModel,
    editingArchetype, entities, expandedArchetypeId, fileInputRef, filledCount,
    filteredArchetypes, formatDate, getPlaceholder, ghostOverlayRef, ghostTextInfo,
    ghostTextSuffix, handleAcceptEnhancement, handleAutocompleteSelect, handleCvUpload,
    handleDismissEnhancement, handleFileUpload, handleKeyDown, handleSelectVacancy,
    handleSourceChange, handleSubmit, hasMultipleSources, industrySearchQuery,
    isAnalyzingProfiles, isCreatingArchetype, isDeletingArchetype, isFindingSimilarSkills,
    isFindingSimilarTags, isIndustryDropdownOpen, isLoading, isLoadingArchetypes,
    isParsingEntities, isSavingArchetype, isSearchingJobs, isSearchingVacancies,
    jdContent, jdSearchPrompt, jdVacancyResults, jdVacancySearch, jobSearchQuery,
    jobSearchResults, mode, newLanguageInput, newSkillInput, newTagInput,
    onChange, onGoToResults, onOpenFilters, onRequireEmailsChange, onRequirePhoneNumbersChange,
    onSearchSourceChange, onSubmit, openArchetypeFromJob, openEditArchetype, panelWidth,
    pendingSourceChange, placeholder, removeCvFile, removeSimilarUrl, removeSuggestion,
    requireEmails, requirePhoneNumbers, saveArchetype, searchAnalysis, searchJobsForArchetype,
    searchSource, selectedAiSkills, selectedAiTags, selectedArchetype, selectedAutocompleteIndex,
    selectedVacancy, setAiSuggestedSkills, setAiSuggestedTags, setArchetypeCreateMode,
    setArchetypeDescription, setArchetypeSearch, setArchetypeSearchPrompt, setArchetypeTab,
    setAutocompleteEnabled, setAutocompleteItems, setEditArchetypeDescription,
    setEditArchetypeEmoji, setEditArchetypeEmploymentType, setEditArchetypeExperienceMin,
    setEditArchetypeIndustry, setEditArchetypeLanguages, setEditArchetypeLocation,
    setEditArchetypeName, setEditArchetypeQuery, setEditArchetypeSeniority,
    setEditArchetypeSkills, setEditArchetypeTags, setEditArchetypeWorkModel,
    setExpandedArchetypeId, setIndustrySearchQuery, setIsFindingSimilarSkills,
    setIsFindingSimilarTags, setIsIndustryDropdownOpen, setJdContent, setJdSearchPrompt,
    setJdVacancySearch, setJobSearchQuery, setMode, setNewLanguageInput, setNewSkillInput,
    setNewTagInput, setPendingSourceChange, setSelectedAiSkills, setSelectedAiTags,
    setSelectedArchetype, setSelectedAutocompleteIndex, setSelectedVacancy,
    setShowAutocomplete, setShowSkillSuggestions, setShowSourceChangeModal,
    setShowTagSuggestions, setSimilarSearchPrompt, showAutocomplete, showCombinedSuggestions,
    showGlobalSearchOptions, showSkillSuggestions, showSourceChangeModal, showTagSuggestions,
    showVacancyResults: state.showVacancyResults, similarCvFiles, similarSearchPrompt, similarUrls, tags,
    textareaRef, updateSimilarUrl,
  }
}
