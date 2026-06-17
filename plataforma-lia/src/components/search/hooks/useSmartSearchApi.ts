"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import type {
  ParsedEntities,
  SearchMode,
  AutocompleteItem,
  AutocompleteResponse,
  SearchAnalysis,
} from "./smartSearchConstants"
import { API_BASE } from "./smartSearchConstants"

interface UseSmartSearchApiParams {
  value: string
  mode: SearchMode
  searchSource: string
  onChange: (value: string) => void
  textareaRef: React.MutableRefObject<HTMLTextAreaElement | null>
}

export function useSmartSearchApi(params: UseSmartSearchApiParams) {
  const { value, mode, searchSource, onChange, textareaRef } = params

  const [entities, setEntities] = useState<ParsedEntities>({})
  const [isParsingEntities, setIsParsingEntities] = useState(false)
  const [searchAnalysis, setSearchAnalysis] = useState<SearchAnalysis | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [booleanError, setBooleanError] = useState<string | null>(null)
  const [autocompleteItems, setAutocompleteItems] = useState<AutocompleteItem[]>([])
  const [showAutocomplete, setShowAutocomplete] = useState(false)
  const [selectedAutocompleteIndex, setSelectedAutocompleteIndex] = useState(-1)
  const [usedAutocompleteTerms, setUsedAutocompleteTerms] = useState<Set<string>>(new Set())
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
  const parseTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const analyzeTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const autocompleteTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const enhanceTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const autocompleteAbortRef = useRef<AbortController | null>(null)
  const autocompleteCache = useRef<Map<string, AutocompleteItem[]>>(new Map())

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
  }, [])

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
  }, [])

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
  }, [promptEnhancementDismissed])

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

  const fetchAutocomplete = useCallback(async (query: string) => {
    if (!query || query.length < 2) {
      setAutocompleteItems([])
      setShowAutocomplete(false)
      return
    }
    const lastWord = query.split(" ").pop()?.toLowerCase() || ""
    const cacheKey = lastWord.slice(0, 4)
    if (autocompleteCache.current.has(cacheKey)) {
      const cached = autocompleteCache.current.get(cacheKey)!
      const filtered = cached.filter(item =>
        (item.text.toLowerCase().includes(lastWord) ||
        item.insert_text.toLowerCase().includes(lastWord)) &&
        !usedAutocompleteTerms.has(item.insert_text.toLowerCase())
      )
      if (filtered.length > 0) {
        setAutocompleteItems(filtered.slice(0, 8))
        setShowAutocomplete(true)
        setSelectedAutocompleteIndex(-1)
        return
      }
    }
    if (autocompleteAbortRef.current) {
      autocompleteAbortRef.current.abort()
    }
    autocompleteAbortRef.current = new AbortController()
    try {
      const response = await fetch(
        `${API_BASE}/api/backend-proxy/search-assistant/autocomplete?query=${encodeURIComponent(query)}`,
        { signal: autocompleteAbortRef.current.signal }
      )
      if (response.ok) {
        const data: AutocompleteResponse = await response.json()
        const allItems = data.items || []
        const items = allItems.filter(item => !usedAutocompleteTerms.has(item.insert_text.toLowerCase()))
        setAutocompleteItems(items)
        setShowAutocomplete(items.length > 0)
        setSelectedAutocompleteIndex(-1)
        if (allItems.length > 0 && cacheKey.length >= 2) {
          autocompleteCache.current.set(cacheKey, allItems)
          if (autocompleteCache.current.size > 50) {
            const firstKey = autocompleteCache.current.keys().next().value
            if (firstKey) autocompleteCache.current.delete(firstKey)
          }
        }
      }
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
      }
      setShowAutocomplete(false)
    }
  }, [usedAutocompleteTerms])

  const handleAutocompleteSelect = useCallback((item: AutocompleteItem) => {
    const trimmedValue = value.trimEnd()
    const lastSpaceIndex = trimmedValue.lastIndexOf(" ")
    const beforeLastWord = lastSpaceIndex >= 0 ? trimmedValue.substring(0, lastSpaceIndex + 1) : ""
    const newValue = beforeLastWord + item.insert_text + " "
    onChange(newValue)
    setUsedAutocompleteTerms(prev => new Set(prev).add(item.insert_text.toLowerCase()))
    setShowAutocomplete(false)
    setAutocompleteItems([])
    textareaRef.current?.focus()
  }, [value, onChange, setUsedAutocompleteTerms, setShowAutocomplete, setAutocompleteItems, textareaRef])

  const validateBoolean = useCallback((query: string) => {
    if (!query.trim()) {
      setBooleanError(null)
      return true
    }
    const openParens = (query.match(/\(/g) || []).length
    const closeParens = (query.match(/\)/g) || []).length
    if (openParens !== closeParens) {
      setBooleanError("Parênteses não balanceados")
      return false
    }
    const hasOperators = /\b(AND|OR|NOT)\b/i.test(query)
    if (query.length > 10 && !hasOperators) {
      setBooleanError("Use operadores AND, OR, NOT para combinar termos")
      return false
    }
    setBooleanError(null)
    return true
  }, [])

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
  }, [value, mode, parseQuery, validateBoolean])

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
  }, [entities, value, mode, analyzeSearch])

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
  }, [value, mode, fetchAutocomplete, autocompleteEnabled])

  useEffect(() => {
    if (!value || value.trim().length === 0) {
      setUsedAutocompleteTerms(new Set())
    }
  }, [value])

  useEffect(() => {
    setUsedAutocompleteTerms(new Set())
  }, [mode])

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
  }, [value, mode, searchSource, fetchPromptEnhancement, promptEnhancementDismissed])

  return {
    entities, setEntities, isParsingEntities, searchAnalysis, setSearchAnalysis,
    isAnalyzing, booleanError, setBooleanError, autocompleteItems, setAutocompleteItems,
    showAutocomplete, setShowAutocomplete, selectedAutocompleteIndex, setSelectedAutocompleteIndex,
    usedAutocompleteTerms, autocompleteEnabled, setAutocompleteEnabled,
    promptEnhancement, setPromptEnhancement, isEnhancingPrompt, promptEnhancementDismissed,
    parseQuery, analyzeSearch, fetchPromptEnhancement,
    handleAcceptEnhancement, handleEditEnhancement, handleDismissEnhancement, handleApplySuggestion,
    fetchAutocomplete, handleAutocompleteSelect, validateBoolean,
  }
}
