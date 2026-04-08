"use client"

import { useEffect } from "react"
import type { SearchStateReturn } from "./useSearchState"
import type { SearchAPIReturn } from "./useSearchAPI"

export function useSearchEffects(state: SearchStateReturn, api: SearchAPIReturn) {
  const {
    value, onChange, mode,
    searchSource, onSearchSourceChange, showGlobalSearchOptions,
    entities, setEntities, setBooleanError,
    jdContent, setShowAutocomplete, setAutocompleteItems,
    setUsedAutocompleteTerms, autocompleteEnabled,
    promptEnhancement, setPromptEnhancement,
    promptEnhancementDismissed, setPromptEnhancementDismissed,
    jdVacancySearch, setJdVacancyResults, setShowVacancyResults,
    setJdSearchPrompt, setBooleanFinalPrompt,
    dismissedQueryRef, enhanceTimeoutRef, textareaRef,
    parseTimeoutRef, analyzeTimeoutRef, autocompleteTimeoutRef,
    jdVacancySearchTimeoutRef,
    archetypes, similar,
  } = state

  const {
    parseQuery, analyzeSearch, fetchPromptEnhancement, fetchAutocomplete,
    validateBoolean, searchJobVacancies,
  } = api

  const {
    setSelectedArchetype,
    setArchetypeSearchPrompt, loadArchetypes, loadClosedJobSuggestions,
    buildArchetypePrompt, selectedArchetype,
  } = archetypes

  const {
    similarUrls, similarCvFiles, combinedSuggestions,
    showCombinedSuggestions, setSimilarSearchPrompt,
  } = similar

  useEffect(() => {
    if (!showGlobalSearchOptions && (searchSource === 'hybrid' || searchSource === 'global') && onSearchSourceChange) {
      onSearchSourceChange('local')
    }
  }, [showGlobalSearchOptions, searchSource, onSearchSourceChange])

  useEffect(() => {
    if (mode === "natural") {
      if (parseTimeoutRef.current) {
        clearTimeout(parseTimeoutRef.current)
      }
      parseTimeoutRef.current = setTimeout(() => {
        parseQuery(value)
      }, 300)
      return () => {
        if (parseTimeoutRef.current) {
          clearTimeout(parseTimeoutRef.current)
        }
      }
    } else if (mode === "boolean") {
      validateBoolean(value)
    }
  }, [value, mode, parseQuery, validateBoolean, parseTimeoutRef])

  useEffect(() => {
    if (mode === "natural" && value && Object.keys(entities).length > 0) {
      if (analyzeTimeoutRef.current) {
        clearTimeout(analyzeTimeoutRef.current)
      }
      analyzeTimeoutRef.current = setTimeout(() => {
        analyzeSearch(value, entities)
      }, 500)
      return () => {
        if (analyzeTimeoutRef.current) {
          clearTimeout(analyzeTimeoutRef.current)
        }
      }
    }
  }, [entities, value, mode, analyzeSearch, analyzeTimeoutRef])

  useEffect(() => {
    if (mode === "natural" && value && autocompleteEnabled) {
      if (autocompleteTimeoutRef.current) {
        clearTimeout(autocompleteTimeoutRef.current)
      }
      autocompleteTimeoutRef.current = setTimeout(() => {
        fetchAutocomplete(value)
      }, 80)
      return () => {
        if (autocompleteTimeoutRef.current) {
          clearTimeout(autocompleteTimeoutRef.current)
        }
      }
    } else {
      setShowAutocomplete(false)
      setAutocompleteItems([])
    }
  }, [value, mode, fetchAutocomplete, autocompleteEnabled, autocompleteTimeoutRef, setShowAutocomplete, setAutocompleteItems])

  useEffect(() => {
    if (!value || value.trim().length === 0) {
      setUsedAutocompleteTerms(new Set())
    }
  }, [value, setUsedAutocompleteTerms])

  useEffect(() => {
    setUsedAutocompleteTerms(new Set())
  }, [mode, setUsedAutocompleteTerms])

  useEffect(() => {
    if (promptEnhancementDismissed && dismissedQueryRef.current) {
      const dismissedPrefix = dismissedQueryRef.current.toLowerCase().slice(0, 15)
      const currentPrefix = value.toLowerCase().slice(0, 15)
      const prefixChanged = currentPrefix !== dismissedPrefix
      const lengthChanged = Math.abs(value.length - dismissedQueryRef.current.length) > 10
      if (prefixChanged || lengthChanged) {
        setPromptEnhancementDismissed(false)
        dismissedQueryRef.current = ""
      }
    }

    if (mode === "natural" && value && value.length >= 10 && !promptEnhancementDismissed) {
      if (enhanceTimeoutRef.current) {
        clearTimeout(enhanceTimeoutRef.current)
      }
      enhanceTimeoutRef.current = setTimeout(() => {
        fetchPromptEnhancement(value)
      }, 1200)
      return () => {
        if (enhanceTimeoutRef.current) {
          clearTimeout(enhanceTimeoutRef.current)
        }
      }
    } else if (!promptEnhancementDismissed) {
      setPromptEnhancement(null)
    }
  }, [value, mode, searchSource, fetchPromptEnhancement, promptEnhancementDismissed, dismissedQueryRef, enhanceTimeoutRef, setPromptEnhancement, setPromptEnhancementDismissed])

  useEffect(() => {
    textareaRef.current?.focus()
  // eslint-disable-next-line react-hooks/exhaustive-deps -- textareaRef is a stable ref, run only on mount
  }, [])

  useEffect(() => {
    setEntities({})
    setBooleanError(null)
    setSelectedArchetype(null)
    setSimilarSearchPrompt("")
    setJdSearchPrompt("")
    setBooleanFinalPrompt("")
    setArchetypeSearchPrompt("")
    if (mode === "jd") {
      onChange("")
    }
    if (mode === "archetypes") {
      loadArchetypes()
      loadClosedJobSuggestions()
    }
  }, [mode, loadArchetypes, loadClosedJobSuggestions, onChange, setEntities, setBooleanError, setSelectedArchetype, setSimilarSearchPrompt, setJdSearchPrompt, setBooleanFinalPrompt, setArchetypeSearchPrompt])

  useEffect(() => {
    if (combinedSuggestions.length > 0 && showCombinedSuggestions) {
      const validUrls = similarUrls.filter(url => url.trim().length > 0)
      const sourceCount = validUrls.length + similarCvFiles.length
      const prompt = sourceCount > 1
        ? `Buscar candidatos similares aos ${sourceCount} perfis analisados. Características combinadas: ${combinedSuggestions.join(", ")}`
        : `Buscar candidatos similares ao perfil: ${combinedSuggestions.join(", ")}`
      setSimilarSearchPrompt(prompt)
    }
  }, [combinedSuggestions, showCombinedSuggestions, similarUrls, similarCvFiles, setSimilarSearchPrompt])

  useEffect(() => {
    if (jdContent.trim().length > 0) {
      const preview = jdContent.length > 200
        ? `Analisar descrição da vaga e encontrar candidatos compatíveis:\n\n${jdContent.slice(0, 200)}...`
        : `Analisar descrição da vaga e encontrar candidatos compatíveis:\n\n${jdContent}`
      setJdSearchPrompt(preview)
    } else {
      setJdSearchPrompt("")
    }
  }, [jdContent, setJdSearchPrompt])

  useEffect(() => {
    if (value.trim() && mode === "boolean") {
      setBooleanFinalPrompt(`Busca booleana: ${value.trim()}`)
    } else {
      setBooleanFinalPrompt("")
    }
  }, [value, mode, setBooleanFinalPrompt])

  useEffect(() => {
    if (selectedArchetype) {
      const prompt = buildArchetypePrompt(selectedArchetype as any)
      setArchetypeSearchPrompt(prompt)
    } else {
      setArchetypeSearchPrompt("")
    }
  }, [selectedArchetype, buildArchetypePrompt, setArchetypeSearchPrompt])

  useEffect(() => {
    if (jdVacancySearchTimeoutRef.current) {
      clearTimeout(jdVacancySearchTimeoutRef.current)
    }
    if (jdVacancySearch.length >= 2) {
      jdVacancySearchTimeoutRef.current = setTimeout(() => {
        searchJobVacancies(jdVacancySearch)
      }, 300)
    } else {
      setJdVacancyResults([])
      setShowVacancyResults(false)
    }
    return () => {
      if (jdVacancySearchTimeoutRef.current) {
        clearTimeout(jdVacancySearchTimeoutRef.current)
      }
    }
  }, [jdVacancySearch, searchJobVacancies, jdVacancySearchTimeoutRef, setJdVacancyResults, setShowVacancyResults])
}
