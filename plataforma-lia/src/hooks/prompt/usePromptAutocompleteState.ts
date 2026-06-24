"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import type { AutocompleteSuggestion } from "@/hooks/ui/usePromptState"

export interface UsePromptAutocompleteStateParams {
  naturalSearchValue: string
  activeSearchTab: string
}

export interface UsePromptAutocompleteStateReturn {
  autocompleteSuggestions: AutocompleteSuggestion[]
  setAutocompleteSuggestions: React.Dispatch<React.SetStateAction<AutocompleteSuggestion[]>>
  showAutocomplete: boolean
  setShowAutocomplete: (v: boolean) => void
  selectedAutocompleteIndex: number
  setSelectedAutocompleteIndex: React.Dispatch<React.SetStateAction<number>>
  autocompleteEnabled: boolean
  setAutocompleteEnabled: (v: boolean) => void
  promptEnhancement: {
    enhanced_query: string
    explanation: string
    confidence: number
    suggestions?: Array<{ label: string; value: string; category: string }>
  } | null
  setPromptEnhancement: React.Dispatch<React.SetStateAction<{
    enhanced_query: string
    explanation: string
    confidence: number
    suggestions?: Array<{ label: string; value: string; category: string }>
  } | null>>
  isEnhancingPrompt: boolean
  promptEnhancementDismissed: boolean
  fetchAutocomplete: (query: string) => Promise<void>
  fetchPromptEnhancement: (query: string) => Promise<void>
  handleAcceptEnhancement: (setNaturalSearchValue: React.Dispatch<React.SetStateAction<string>>) => void
  handleDismissEnhancement: () => void
  handleAutocompleteKeyDown: (
    e: React.KeyboardEvent,
    setNaturalSearchValue: React.Dispatch<React.SetStateAction<string>>
  ) => void
}

export function usePromptAutocompleteState({
  naturalSearchValue,
  activeSearchTab,
}: UsePromptAutocompleteStateParams): UsePromptAutocompleteStateReturn {
  const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<AutocompleteSuggestion[]>([])
  const [showAutocomplete, setShowAutocomplete] = useState(false)
  const [selectedAutocompleteIndex, setSelectedAutocompleteIndex] = useState(0)
  const autocompleteCache = useRef<Map<string, AutocompleteSuggestion[]>>(new Map())
  const [autocompleteEnabled, setAutocompleteEnabled] = useState(true)

  const [promptEnhancement, setPromptEnhancement] = useState<{
    enhanced_query: string
    explanation: string
    confidence: number
    suggestions?: Array<{ label: string; value: string; category: string }>
  } | null>(null)
  const [isEnhancingPrompt, setIsEnhancingPrompt] = useState(false)
  const [promptEnhancementDismissed, setPromptEnhancementDismissed] = useState(false)
  const dismissedQueryRef = useRef<string>("")
  const enhanceTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const fetchAutocomplete = useCallback(async (query: string) => {
    if (!query.trim() || query.length < 2) {
      setAutocompleteSuggestions([])
      setShowAutocomplete(false)
      return
    }
    const cacheKey = query.toLowerCase().trim()
    if (autocompleteCache.current.has(cacheKey)) {
      setAutocompleteSuggestions(autocompleteCache.current.get(cacheKey) || [])
      setShowAutocomplete(true)
      return
    }
    try {
      const res = await fetch(`/api/backend-proxy/search-assistant/autocomplete/?query=${encodeURIComponent(query)}`)
      if (res.ok) {
        const data = await res.json()
        const items = data.items || []
        const suggestions: AutocompleteSuggestion[] = items.map((item: Record<string, unknown>) => ({
          text: item.text,
          category: item.category,
          icon: item.icon,
          description: item.description,
          insert_text: item.insert_text || item.text
        }))
        autocompleteCache.current.set(cacheKey, suggestions)
        setAutocompleteSuggestions(suggestions)
        setShowAutocomplete(suggestions.length > 0)
      }
    } catch (error) {
      console.error("[usePromptAutocompleteState] Error:", error)
    }
  }, [])

  const fetchPromptEnhancement = useCallback(async (query: string) => {
    if (!query || query.length < 10 || promptEnhancementDismissed) {
      setPromptEnhancement(null)
      return
    }
    setIsEnhancingPrompt(true)
    try {
      const response = await fetch('/api/backend-proxy/enhance-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })
      if (response.ok) {
        const data = await response.json()
        if (data.enhanced_query && data.enhanced_query !== query) {
          setPromptEnhancement(data)
        }
      }
    } catch {
    } finally {
      setIsEnhancingPrompt(false)
    }
  }, [promptEnhancementDismissed])

  const handleAcceptEnhancement = useCallback((
    setNaturalSearchValue: React.Dispatch<React.SetStateAction<string>>
  ) => {
    if (promptEnhancement) {
      setNaturalSearchValue(promptEnhancement.enhanced_query)
      setPromptEnhancement(null)
    }
  }, [promptEnhancement])

  const handleDismissEnhancement = useCallback(() => {
    dismissedQueryRef.current = naturalSearchValue
    setPromptEnhancementDismissed(true)
    setPromptEnhancement(null)
  }, [naturalSearchValue])

  useEffect(() => {
    if (activeSearchTab !== 'natural' || !naturalSearchValue || naturalSearchValue.length < 10) {
      setPromptEnhancement(null)
      return
    }
    if (promptEnhancementDismissed && dismissedQueryRef.current) {
      const dismissedPrefix = dismissedQueryRef.current.toLowerCase().slice(0, 15)
      const currentPrefix = naturalSearchValue.toLowerCase().slice(0, 15)
      if (dismissedPrefix !== currentPrefix) {
        setPromptEnhancementDismissed(false)
        dismissedQueryRef.current = ""
      }
    }
    if (enhanceTimeoutRef.current) {
      clearTimeout(enhanceTimeoutRef.current)
    }
    enhanceTimeoutRef.current = setTimeout(() => {
      if (!promptEnhancementDismissed) {
        fetchPromptEnhancement(naturalSearchValue)
      }
    }, 1500)
    return () => {
      if (enhanceTimeoutRef.current) {
        clearTimeout(enhanceTimeoutRef.current)
      }
    }
  }, [naturalSearchValue, activeSearchTab, promptEnhancementDismissed, fetchPromptEnhancement])

  const handleAutocompleteKeyDown = useCallback((
    e: React.KeyboardEvent,
    setNaturalSearchValue: React.Dispatch<React.SetStateAction<string>>
  ) => {
    if (!showAutocomplete || autocompleteSuggestions.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedAutocompleteIndex(prev => prev < autocompleteSuggestions.length - 1 ? prev + 1 : 0)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedAutocompleteIndex(prev => prev > 0 ? prev - 1 : autocompleteSuggestions.length - 1)
    } else if (e.key === 'Tab' || e.key === 'Enter') {
      if (autocompleteSuggestions[selectedAutocompleteIndex]) {
        e.preventDefault()
        const selected = autocompleteSuggestions[selectedAutocompleteIndex]
        const insertValue = selected.insert_text || selected.text
        setNaturalSearchValue(prev => {
          const words = prev.split(' ')
          words.pop()
          return [...words, insertValue].join(' ') + ' '
        })
        setShowAutocomplete(false)
      }
    } else if (e.key === 'Escape') {
      setShowAutocomplete(false)
    }
  }, [showAutocomplete, autocompleteSuggestions, selectedAutocompleteIndex])

  return {
    autocompleteSuggestions, setAutocompleteSuggestions,
    showAutocomplete, setShowAutocomplete,
    selectedAutocompleteIndex, setSelectedAutocompleteIndex,
    autocompleteEnabled, setAutocompleteEnabled,
    promptEnhancement, setPromptEnhancement,
    isEnhancingPrompt,
    promptEnhancementDismissed,
    fetchAutocomplete,
    fetchPromptEnhancement,
    handleAcceptEnhancement,
    handleDismissEnhancement,
    handleAutocompleteKeyDown,
  }
}
