"use client"

import { useState, useEffect, useCallback, useRef } from 'react'

const STORAGE_KEY = 'wedotalent_job_filters'
const SAVED_SEARCHES_KEY = 'wedotalent_job_saved_searches'
const MAX_SAVED_SEARCHES = 10

export interface JobFiltersState {
  selectedStatusFilter: string
  selectedDaysFilter: string
  advancedFilters: { [key: string]: string[] }
  booleanSearch: string
  searchTerm: string
}

export interface SavedSearch {
  id: string
  name: string
  query: string
  filters: JobFiltersState
  createdAt: string
  isShared?: boolean
}

function createDefaultAdvancedFilters(): { [key: string]: string[] } {
  return {
    job_titles: [],
    departments: [],
    locations: [],
    work_models: [],
    job_types: [],
    seniority_levels: [],
    salary_ranges: [],
    status: [],
    stages: [],
    priorities: [],
    managers: [],
    benefits: [],
    requirements: [],
    industries: [],
    budget_ranges: [],
    urgency_levels: [],
    contract_duration: [],
    team_size: []
  }
}

function createDefaultFiltersState(): JobFiltersState {
  return {
    selectedStatusFilter: 'todas',
    selectedDaysFilter: 'todas',
    advancedFilters: createDefaultAdvancedFilters(),
    booleanSearch: '',
    searchTerm: ''
  }
}

export function useJobFiltersPersistence() {
  const [filtersState, setFiltersState] = useState<JobFiltersState>(createDefaultFiltersState)
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([])
  const [isLoaded, setIsLoaded] = useState(false)
  const isInitialized = useRef(false)

  useEffect(() => {
    if (typeof window === 'undefined' || isInitialized.current) return
    isInitialized.current = true

    try {
      const storedFilters = localStorage.getItem(STORAGE_KEY)
      if (storedFilters) {
        const parsed = JSON.parse(storedFilters)
        setFiltersState({
          ...createDefaultFiltersState(),
          ...parsed,
          advancedFilters: {
            ...createDefaultAdvancedFilters(),
            ...(parsed.advancedFilters || {})
          }
        })
      }

      const storedSearches = localStorage.getItem(SAVED_SEARCHES_KEY)
      if (storedSearches) {
        const parsed = JSON.parse(storedSearches)
        setSavedSearches(Array.isArray(parsed) ? parsed.slice(0, MAX_SAVED_SEARCHES) : [])
      }
    } catch (error) {
      console.error('Error loading job filters from localStorage:', error)
    }

    setIsLoaded(true)
  }, [])

  useEffect(() => {
    if (!isLoaded || typeof window === 'undefined') return

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filtersState))
    } catch (error) {
      console.error('Error saving job filters to localStorage:', error)
    }
  }, [filtersState, isLoaded])

  useEffect(() => {
    if (!isLoaded || typeof window === 'undefined') return

    try {
      localStorage.setItem(SAVED_SEARCHES_KEY, JSON.stringify(savedSearches.slice(0, MAX_SAVED_SEARCHES)))
    } catch (error) {
      console.error('Error saving searches to localStorage:', error)
    }
  }, [savedSearches, isLoaded])

  const updateFilter = useCallback(<K extends keyof JobFiltersState>(
    key: K,
    value: JobFiltersState[K]
  ) => {
    setFiltersState(prev => ({
      ...prev,
      [key]: value
    }))
  }, [])

  const updateAdvancedFilter = useCallback((key: string, value: string[]) => {
    setFiltersState(prev => ({
      ...prev,
      advancedFilters: {
        ...prev.advancedFilters,
        [key]: [...value]
      }
    }))
  }, [])

  const clearAllFilters = useCallback(() => {
    setFiltersState(createDefaultFiltersState())
  }, [])

  const saveCurrentSearch = useCallback((name: string) => {
    const newSearch: SavedSearch = {
      id: `search_${Date.now()}`,
      name,
      query: filtersState.searchTerm,
      filters: {
        ...filtersState,
        advancedFilters: { ...filtersState.advancedFilters }
      },
      createdAt: new Date().toISOString(),
      isShared: false
    }
    setSavedSearches(prev => [newSearch, ...prev].slice(0, MAX_SAVED_SEARCHES))
    return newSearch
  }, [filtersState])

  const applySavedSearch = useCallback((searchId: string) => {
    const search = savedSearches.find(s => s.id === searchId)
    if (search) {
      setFiltersState({
        selectedStatusFilter: search.filters.selectedStatusFilter || 'todas',
        selectedDaysFilter: search.filters.selectedDaysFilter || 'todas',
        booleanSearch: search.filters.booleanSearch || '',
        searchTerm: search.filters.searchTerm || search.query || '',
        advancedFilters: {
          ...createDefaultAdvancedFilters(),
          ...(search.filters.advancedFilters || {})
        }
      })
      return true
    }
    return false
  }, [savedSearches])

  const deleteSavedSearch = useCallback((searchId: string) => {
    setSavedSearches(prev => prev.filter(s => s.id !== searchId))
  }, [])

  const renameSavedSearch = useCallback((searchId: string, newName: string) => {
    setSavedSearches(prev => prev.map(s => 
      s.id === searchId ? { ...s, name: newName } : s
    ))
  }, [])

  const toggleSearchSharing = useCallback((searchId: string) => {
    setSavedSearches(prev => prev.map(s =>
      s.id === searchId ? { ...s, isShared: !s.isShared } : s
    ))
  }, [])

  const getActiveFiltersCount = useCallback(() => {
    let count = 0
    if (filtersState.selectedStatusFilter !== 'todas') count++
    if (filtersState.selectedDaysFilter !== 'todas') count++
    if (filtersState.booleanSearch.trim()) count++
    if (filtersState.searchTerm.trim()) count++
    
    Object.values(filtersState.advancedFilters).forEach(arr => {
      if (arr.length > 0) count++
    })
    
    return count
  }, [filtersState])

  const hasActiveFilters = useCallback(() => {
    return getActiveFiltersCount() > 0
  }, [getActiveFiltersCount])

  return {
    filtersState,
    setFiltersState,
    updateFilter,
    updateAdvancedFilter,
    clearAllFilters,
    savedSearches,
    setSavedSearches,
    saveCurrentSearch,
    applySavedSearch,
    deleteSavedSearch,
    renameSavedSearch,
    toggleSearchSharing,
    getActiveFiltersCount,
    hasActiveFilters,
    isLoaded
  }
}
