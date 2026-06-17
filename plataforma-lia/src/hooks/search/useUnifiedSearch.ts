"use client"

import { useState, useCallback, useMemo } from "react"
import { ParsedEntities, SearchMode, SearchMetadata, SearchSource } from "@/components/search/smart-search-input"
import { SearchFilters } from "@/components/search/advanced-filters-modal"

export interface UnifiedSearchState {
  query: string
  entities: ParsedEntities | null
  mode: SearchMode
  metadata: SearchMetadata | null
  filters: SearchFilters
  searchSource: SearchSource
  hasSearched: boolean
  lastSuccessfulQuery: string
}

export interface PearchSearchOptions {
  requireEmails: boolean
  requirePhoneNumbers: boolean
  showEmails: boolean
  showPhoneNumbers: boolean
}

export interface UseUnifiedSearchReturn {
  searchState: UnifiedSearchState
  pearchOptions: PearchSearchOptions
  setQuery: (query: string) => void
  setEntities: (entities: ParsedEntities | null) => void
  setMode: (mode: SearchMode) => void
  setMetadata: (metadata: SearchMetadata | null) => void
  setFilters: (filters: SearchFilters) => void
  setSearchSource: (source: SearchSource) => void
  setPearchOptions: (options: Partial<PearchSearchOptions>) => void
  updateSearch: (params: Partial<UnifiedSearchState>) => void
  markSearched: (query: string) => void
  reset: () => void
  getActiveFiltersCount: () => number
}

const initialSearchState: UnifiedSearchState = {
  query: "",
  entities: null,
  mode: "natural",
  metadata: null,
  filters: {},
  searchSource: "local",
  hasSearched: false,
  lastSuccessfulQuery: ""
}

const initialPearchOptions: PearchSearchOptions = {
  requireEmails: false,
  requirePhoneNumbers: false,
  showEmails: false,
  showPhoneNumbers: false
}

export function useUnifiedSearch(): UseUnifiedSearchReturn {
  const [searchState, setSearchState] = useState<UnifiedSearchState>(initialSearchState)
  const [pearchOptions, setPearchOptionsState] = useState<PearchSearchOptions>(initialPearchOptions)

  const setQuery = useCallback((query: string) => {
    setSearchState(prev => ({ ...prev, query }))
  }, [])

  const setEntities = useCallback((entities: ParsedEntities | null) => {
    setSearchState(prev => ({ ...prev, entities }))
  }, [])

  const setMode = useCallback((mode: SearchMode) => {
    setSearchState(prev => ({ ...prev, mode }))
  }, [])

  const setMetadata = useCallback((metadata: SearchMetadata | null) => {
    setSearchState(prev => ({ ...prev, metadata }))
  }, [])

  const setFilters = useCallback((filters: SearchFilters) => {
    setSearchState(prev => ({ ...prev, filters }))
  }, [])

  const setSearchSource = useCallback((searchSource: SearchSource) => {
    setSearchState(prev => ({ ...prev, searchSource }))
  }, [])

  const setPearchOptions = useCallback((options: Partial<PearchSearchOptions>) => {
    setPearchOptionsState(prev => ({ ...prev, ...options }))
  }, [])

  const updateSearch = useCallback((params: Partial<UnifiedSearchState>) => {
    setSearchState(prev => ({ ...prev, ...params }))
  }, [])

  const markSearched = useCallback((query: string) => {
    setSearchState(prev => ({
      ...prev,
      hasSearched: true,
      lastSuccessfulQuery: query
    }))
  }, [])

  const reset = useCallback(() => {
    setSearchState(initialSearchState)
    setPearchOptionsState(initialPearchOptions)
  }, [])

  const getActiveFiltersCount = useCallback(() => {
    let count = 0
    const filters = searchState.filters
    Object.values(filters).forEach(category => {
      if (category) {
        Object.values(category).forEach(value => {
          if (value !== undefined && value !== null && value !== "" && value !== false &&
              !(Array.isArray(value) && value.length === 0)) {
            count++
          }
        })
      }
    })
    return count
  }, [searchState.filters])

  return {
    searchState,
    pearchOptions,
    setQuery,
    setEntities,
    setMode,
    setMetadata,
    setFilters,
    setSearchSource,
    setPearchOptions,
    updateSearch,
    markSearched,
    reset,
    getActiveFiltersCount
  }
}
