"use client"

import { useCallback } from "react"
import {
  type ParsedEntities,
  type AutocompleteItem,
  type AutocompleteResponse,
  API_BASE,
} from "./smartSearchConstants"
import type { SearchStateReturn, VacancyResult } from "./useSearchState"

export function useSearchAPI(state: SearchStateReturn) {
  const {
    setEntities, setSearchAnalysis, setIsParsingEntities, setIsAnalyzing,
    setPromptEnhancement, setIsEnhancingPrompt, promptEnhancementDismissed,
    setAutocompleteItems, setShowAutocomplete, setSelectedAutocompleteIndex,
    usedAutocompleteTerms, autocompleteAbortRef, autocompleteCache,
    setBooleanError, setJdVacancyResults, setIsSearchingVacancies,
    setShowVacancyResults, setSelectedVacancy, setJdContent,
    setUsedAutocompleteTerms, value, onChange, textareaRef,
  } = state

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
  }, [usedAutocompleteTerms, autocompleteAbortRef, autocompleteCache, setAutocompleteItems, setShowAutocomplete, setSelectedAutocompleteIndex])

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
  }, [setBooleanError])

  const searchJobVacancies = useCallback(async (searchTerm: string) => {
    if (searchTerm.length < 2) {
      setJdVacancyResults([])
      setShowVacancyResults(false)
      return
    }

    setIsSearchingVacancies(true)
    try {
      const response = await fetch(`/api/backend-proxy/job-vacancies/search?query=${encodeURIComponent(searchTerm)}&page_size=5`)
      if (response.ok) {
        const data = await response.json()
        setJdVacancyResults(data.items || [])
        setShowVacancyResults(true)
      }
    } catch (error) {
      setJdVacancyResults([])
    } finally {
      setIsSearchingVacancies(false)
    }
  }, [setJdVacancyResults, setShowVacancyResults, setIsSearchingVacancies])

  const handleSelectVacancy = async (vacancy: VacancyResult) => {
    setSelectedVacancy({
      id: vacancy.id,
      title: vacancy.title,
      job_id: vacancy.job_id
    })
    setShowVacancyResults(false)
    state.setJdVacancySearch("")

    try {
      const response = await fetch(`/api/backend-proxy/job-vacancies/${vacancy.id}`)
      if (response.ok) {
        const fullVacancy = await response.json()
        if (fullVacancy.description) {
          setJdContent(fullVacancy.description)
        } else {
          const parts: string[] = []
          if (fullVacancy.title) parts.push(`Cargo: ${fullVacancy.title}`)
          if (fullVacancy.department) parts.push(`Departamento: ${fullVacancy.department}`)
          if (fullVacancy.location) parts.push(`Localização: ${fullVacancy.location}`)
          if (fullVacancy.seniority_level) parts.push(`Senioridade: ${fullVacancy.seniority_level}`)
          if (fullVacancy.requirements?.length) parts.push(`Requisitos: ${fullVacancy.requirements.join(', ')}`)
          setJdContent(parts.join('\n\n'))
        }
      }
    } catch (error) {
      if (vacancy.description_preview) {
        setJdContent(vacancy.description_preview.replace('...', ''))
      }
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      const text = await file.text()
      setJdContent(text)
      setSelectedVacancy(null)
    } catch (error) {
    }
  }

  const formatDate = (dateStr: string) => {
    if (!dateStr) return ""
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      })
    } catch {
      return dateStr
    }
  }

  return {
    parseQuery,
    analyzeSearch,
    fetchPromptEnhancement,
    fetchAutocomplete,
    handleAutocompleteSelect,
    validateBoolean,
    searchJobVacancies,
    handleSelectVacancy,
    handleFileUpload,
    formatDate,
  }
}

export type SearchAPIReturn = ReturnType<typeof useSearchAPI>
