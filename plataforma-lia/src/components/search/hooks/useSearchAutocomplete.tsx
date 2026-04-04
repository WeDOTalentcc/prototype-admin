"use client"

import { useCallback } from "react"
import {
  type AutocompleteItem,
  type SearchSource,
  API_BASE,
} from "./smartSearchConstants"

export interface UseSearchAutocompleteParams {
  value: string
  onChange: (value: string) => void
  onSearchSourceChange?: (source: SearchSource) => void
  showAutocomplete: boolean
  autocompleteItems: AutocompleteItem[]
  selectedAutocompleteIndex: number
  usedAutocompleteTerms: Set<string>
  autocompleteCache: React.MutableRefObject<Map<string, AutocompleteItem[]>>
  autocompleteAbortRef: React.MutableRefObject<AbortController | null>
  textareaRef: React.MutableRefObject<HTMLTextAreaElement | null>
  setBooleanError: React.Dispatch<React.SetStateAction<string | null>>
  setAutocompleteItems: React.Dispatch<React.SetStateAction<AutocompleteItem[]>>
  setShowAutocomplete: React.Dispatch<React.SetStateAction<boolean>>
  setSelectedAutocompleteIndex: React.Dispatch<React.SetStateAction<number>>
  setUsedAutocompleteTerms: React.Dispatch<React.SetStateAction<Set<string>>>
  setPendingSourceChange: React.Dispatch<React.SetStateAction<'hybrid' | 'global' | null>>
  setShowSourceChangeModal: React.Dispatch<React.SetStateAction<boolean>>
  pendingSourceChange: 'hybrid' | 'global' | null
}

export function useSearchAutocomplete(params: UseSearchAutocompleteParams) {
  const {
    value,
    onChange,
    onSearchSourceChange,
    usedAutocompleteTerms,
    autocompleteCache,
    autocompleteAbortRef,
    textareaRef,
    setBooleanError,
    setAutocompleteItems,
    setShowAutocomplete,
    setSelectedAutocompleteIndex,
    setUsedAutocompleteTerms,
    setPendingSourceChange,
    setShowSourceChangeModal,
    pendingSourceChange,
  } = params

  const handleSourceChange = (newSource: SearchSource) => {
    if (newSource === 'local') {
      onSearchSourceChange?.(newSource)
    } else {
      setPendingSourceChange(newSource)
      setShowSourceChangeModal(true)
    }
  }

  const confirmSourceChange = () => {
    if (pendingSourceChange && onSearchSourceChange) {
      onSearchSourceChange(pendingSourceChange)
      setPendingSourceChange(null)
      setShowSourceChangeModal(false)
    }
  }

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
        const data = await response.json()
        const allItems = data.items || []
        const items = allItems.filter((item: AutocompleteItem) => !usedAutocompleteTerms.has(item.insert_text.toLowerCase()))
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
  }, [usedAutocompleteTerms, autocompleteCache, autocompleteAbortRef, setAutocompleteItems, setShowAutocomplete, setSelectedAutocompleteIndex])

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

  return {
    handleSourceChange,
    confirmSourceChange,
    fetchAutocomplete,
    handleAutocompleteSelect,
    validateBoolean,
  }
}
