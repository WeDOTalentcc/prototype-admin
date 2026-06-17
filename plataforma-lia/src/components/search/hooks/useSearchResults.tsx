"use client"

import { useCallback } from "react"
import { buildHighlightedText } from "./renderHighlightedText"
import { SearchScopeControls } from "./SearchScopeControls"
import {
  type SearchSource,
  type SearchMetadata,
} from "./smartSearchConstants"
import type { SearchStateReturn } from "./useSearchState"
import type { SearchAPIReturn } from "./useSearchAPI"
import { useSearchEffects } from "./useSearchEffects"

export function useSearchResults(state: SearchStateReturn, api: SearchAPIReturn) {
  const {
    value, onChange, onSubmit, onCancel, isLoading, placeholder,
    searchSource, onSearchSourceChange, requireEmails, onRequireEmailsChange,
    requirePhoneNumbers, onRequirePhoneNumbersChange, showGlobalSearchOptions,
    mode, entities, booleanError,
    jdContent, setJdContent,
    showAutocomplete, setShowAutocomplete, autocompleteItems,
    selectedAutocompleteIndex, setSelectedAutocompleteIndex,
    promptEnhancement, setPromptEnhancement, isEnhancingPrompt,
    setPromptEnhancementDismissed,
    setShowSourceChangeModal, setPendingSourceChange,
    setJdVacancySearch, setSelectedVacancy,
    jdSearchPrompt, booleanFinalPrompt,
    dismissedQueryRef, textareaRef, filledCount,
    archetypes, similar,
  } = state

  const { handleAutocompleteSelect } = api

  const {
    archetypeVacancies, archetypeSearch,
    selectedArchetype, archetypeSearchPrompt,
  } = archetypes

  const {
    similarUrls, similarCvFiles, combinedSuggestions,
    similarSearchPrompt,
  } = similar

  useSearchEffects(state, api)

  const renderHighlightedText = useCallback(() => {
    return buildHighlightedText(value, entities, filledCount)
  }, [value, entities, filledCount])

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
        metadata.combinedProfile = {
          keywords: combinedSuggestions
        }
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

  const getGhostTextInfo = useCallback((): { suffix: string | null; showFallbackCard: boolean; fullEnhancement: string | null } => {
    if (!promptEnhancement || showAutocomplete || isEnhancingPrompt) {
      return { suffix: null, showFallbackCard: false, fullEnhancement: null }
    }
    const enhanced = promptEnhancement.enhanced_query
    const userText = value
    if (enhanced.toLowerCase().startsWith(userText.toLowerCase())) {
      return { suffix: enhanced.slice(userText.length), showFallbackCard: false, fullEnhancement: null }
    }
    return { suffix: null, showFallbackCard: true, fullEnhancement: enhanced }
  }, [promptEnhancement, value, showAutocomplete, isEnhancingPrompt])

  const ghostTextInfo = getGhostTextInfo()
  const ghostTextSuffix = ghostTextInfo.suffix

  const handleAcceptEnhancement = useCallback(() => {
    if (promptEnhancement) {
      onChange(promptEnhancement.enhanced_query)
      setPromptEnhancement(null)
    }
  }, [promptEnhancement, onChange, setPromptEnhancement])

  const handleEditEnhancement = useCallback(() => {
    if (promptEnhancement) {
      onChange(promptEnhancement.enhanced_query)
      setPromptEnhancement(null)
      textareaRef.current?.focus()
    }
  }, [promptEnhancement, onChange, setPromptEnhancement, textareaRef])

  const handleDismissEnhancement = useCallback(() => {
    setPromptEnhancement(null)
    setPromptEnhancementDismissed(true)
    dismissedQueryRef.current = value
  }, [value, setPromptEnhancement, setPromptEnhancementDismissed, dismissedQueryRef])

  const handleApplySuggestion = useCallback((suggestionValue: string) => {
    const currentValue = value.trim()
    const newValue = currentValue ? `${currentValue}, ${suggestionValue}` : suggestionValue
    onChange(newValue)
    textareaRef.current?.focus()
  }, [value, onChange, textareaRef])

  const handleSourceChange = (newSource: SearchSource) => {
    if (newSource === 'local') {
      onSearchSourceChange?.(newSource)
    } else {
      setPendingSourceChange(newSource)
      setShowSourceChangeModal(true)
    }
  }

  const confirmSourceChange = () => {
    if (state.pendingSourceChange && onSearchSourceChange) {
      onSearchSourceChange(state.pendingSourceChange)
      setPendingSourceChange(null)
      setShowSourceChangeModal(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    const visibleItems = Math.min(autocompleteItems.length, 5)
    if (showAutocomplete && visibleItems > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault()
        setSelectedAutocompleteIndex(prev =>
          prev < visibleItems - 1 ? prev + 1 : 0
        )
        return
      }
      if (e.key === "ArrowUp") {
        e.preventDefault()
        setSelectedAutocompleteIndex(prev =>
          prev > 0 ? prev - 1 : visibleItems - 1
        )
        return
      }
      if ((e.key === "Tab" || e.key === "Enter") && selectedAutocompleteIndex >= 0) {
        e.preventDefault()
        handleAutocompleteSelect(autocompleteItems[selectedAutocompleteIndex])
        return
      }
      if (e.key === "Escape") {
        e.preventDefault()
        setShowAutocomplete(false)
        return
      }
    }

    if (e.key === "Tab" && !e.shiftKey && (ghostTextSuffix || ghostTextInfo.showFallbackCard) && !showAutocomplete) {
      e.preventDefault()
      handleAcceptEnhancement()
      return
    }

    if (e.key === "Escape" && promptEnhancement) {
      e.preventDefault()
      handleDismissEnhancement()
      return
    }

    if (e.key === "Enter" && !e.shiftKey && mode !== "jd") {
      e.preventDefault()
      handleSubmit()
    }
    if (e.key === "Escape") {
      onCancel()
    }
  }

  const clearSelectedVacancy = () => {
    setSelectedVacancy(null)
    setJdContent("")
    setJdVacancySearch("")
  }

  const canSubmit = () => {
    if (isLoading) return false
    switch (mode) {
      case "natural":
        return value.trim().length > 0
      case "boolean":
        if (value.trim().length > 0 && booleanFinalPrompt.trim().length === 0) {
          return false
        }
        return value.trim().length > 0 && !booleanError
      case "jd":
        return jdContent.trim().length > 0
      case "similar":
        const validUrls = similarUrls.filter(url => url.trim().length > 0)
        return validUrls.length > 0 || similarCvFiles.length > 0
      case "archetypes":
        return selectedArchetype !== null
      default:
        return false
    }
  }

  const getPlaceholder = () => {
    switch (mode) {
      case "natural":
        return placeholder
      case "similar":
        return "Cole a URL do LinkedIn ou ID do candidato..."
      case "jd":
        return "Cole a descrição da vaga aqui..."
      case "boolean":
        return "(software OR engineer) AND (python OR java) AND NOT junior"
      case "archetypes":
        return "Buscar vagas concluídas..."
      default:
        return placeholder
    }
  }

  const filteredArchetypes = archetypeVacancies.filter(v => {
    const searchLower = archetypeSearch.toLowerCase()
    const title = v.title || ''
    const hiredName = v.hired_candidate?.name || ''
    const department = v.department || ''
    return title.toLowerCase().includes(searchLower) ||
      hiredName.toLowerCase().includes(searchLower) ||
      department.toLowerCase().includes(searchLower)
  })

  const scopeControlsProps = {
    searchSource,
    onSearchSourceChange,
    handleSourceChange,
    showGlobalSearchOptions,
    onRequireEmailsChange,
    onRequirePhoneNumbersChange,
    requireEmails,
    requirePhoneNumbers,
    canSubmit,
    isLoading: isLoading || false,
  }

  return {
    renderHighlightedText,
    handleSubmit,
    getGhostTextInfo,
    ghostTextInfo,
    ghostTextSuffix,
    handleAcceptEnhancement,
    handleEditEnhancement,
    handleDismissEnhancement,
    handleApplySuggestion,
    handleSourceChange,
    confirmSourceChange,
    handleKeyDown,
    clearSelectedVacancy,
    canSubmit,
    getPlaceholder,
    filteredArchetypes,
    scopeControlsProps,
    SearchScopeControls,
  }
}

export type SearchResultsReturn = ReturnType<typeof useSearchResults>
