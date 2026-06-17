"use client"

import { useCallback } from "react"
import {
  type ParsedEntities,
  type SearchAnalysis,
  type AutocompleteItem,
  API_BASE,
} from "./smartSearchConstants"

export interface UseSearchParsingParams {
  value: string
  onChange: (value: string) => void
  promptEnhancement: {
    enhanced_query: string
    explanation: string
    confidence: number
    suggestions?: Array<{ label: string; value: string; category: string }>
  } | null
  promptEnhancementDismissed: boolean
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
}

export function useSearchParsing(params: UseSearchParsingParams) {
  const {
    value,
    onChange,
    promptEnhancement,
    promptEnhancementDismissed,
    dismissedQueryRef,
    textareaRef,
    setEntities,
    setIsParsingEntities,
    setSearchAnalysis,
    setIsAnalyzing,
    setPromptEnhancement,
    setIsEnhancingPrompt,
    setPromptEnhancementDismissed,
  } = params

  const parseQuery = useCallback(async (query: string) => {
    if (!query || query.length < 5) {
      setEntities({})
      setSearchAnalysis(null)
      return
    }

    setIsParsingEntities(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/search/parse-query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      })

      if (response.ok) {
        const data = await response.json()
        setEntities(data.entities || {})
      }
    } catch (error) {
    } finally {
      setIsParsingEntities(false)
    }
  }, [setEntities, setSearchAnalysis, setIsParsingEntities])

  const analyzeSearch = useCallback(async (query: string, currentEntities: ParsedEntities) => {
    if (!query || query.length < 5) {
      setSearchAnalysis(null)
      return
    }

    setIsAnalyzing(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/search-assistant/analyze/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, entities: currentEntities })
      })

      if (response.ok) {
        const data = await response.json()
        setSearchAnalysis(data)
      }
    } catch (error) {
    } finally {
      setIsAnalyzing(false)
    }
  }, [setSearchAnalysis, setIsAnalyzing])

  const fetchPromptEnhancement = useCallback(async (query: string) => {
    if (!query || query.length < 10 || promptEnhancementDismissed) {
      setPromptEnhancement(null)
      return
    }

    setIsEnhancingPrompt(true)
    try {
      const response = await fetch(`${API_BASE}/api/backend-proxy/enhance-prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      })

      if (response.ok) {
        const data = await response.json()
        if (data.enhanced_query && data.enhanced_query !== query && data.confidence >= 0.6) {
          setPromptEnhancement({
            enhanced_query: data.enhanced_query,
            explanation: data.explanation,
            confidence: data.confidence,
            suggestions: data.suggestions || []
          })
        } else {
          setPromptEnhancement(null)
        }
      }
    } catch (error) {
      setPromptEnhancement(null)
    } finally {
      setIsEnhancingPrompt(false)
    }
  }, [promptEnhancementDismissed, setPromptEnhancement, setIsEnhancingPrompt])

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

  return {
    parseQuery,
    analyzeSearch,
    fetchPromptEnhancement,
    handleAcceptEnhancement,
    handleEditEnhancement,
    handleDismissEnhancement,
    handleApplySuggestion,
  }
}
