"use client"

import { useCallback } from 'react'
import { useJobFiltersStore } from '@/stores/job-filters-store'
import type { JobFiltersState, SavedSearch } from '@/stores/job-filters-store'

export type { JobFiltersState }
export type { SavedSearch as JobSavedSearch } from '@/stores/job-filters-store'

export function useJobFiltersPersistence() {
  const filtersState = useJobFiltersStore(s => s.filtersState)
  const setFiltersState = useJobFiltersStore(s => s.setFiltersState)
  const storeUpdateFilter = useJobFiltersStore(s => s.updateFilter)
  const storeUpdateAdvancedFilter = useJobFiltersStore(s => s.updateAdvancedFilter)
  const storeClearAllFilters = useJobFiltersStore(s => s.clearAllFilters)
  const savedSearches = useJobFiltersStore(s => s.savedSearches)
  const storeSaveCurrentSearch = useJobFiltersStore(s => s.saveCurrentSearch)
  const storeApplySavedSearch = useJobFiltersStore(s => s.applySavedSearch)
  const storeDeleteSavedSearch = useJobFiltersStore(s => s.deleteSavedSearch)
  const storeRenameSavedSearch = useJobFiltersStore(s => s.renameSavedSearch)
  const storeToggleSearchSharing = useJobFiltersStore(s => s.toggleSearchSharing)
  const storeGetActiveFiltersCount = useJobFiltersStore(s => s.getActiveFiltersCount)
  const storeHasActiveFilters = useJobFiltersStore(s => s.hasActiveFilters)

  const updateFilter = useCallback(<K extends keyof JobFiltersState>(
    key: K,
    value: JobFiltersState[K]
  ) => {
    storeUpdateFilter(key, value)
  }, [storeUpdateFilter])

  const updateAdvancedFilter = useCallback((key: string, value: string[]) => {
    storeUpdateAdvancedFilter(key, value)
  }, [storeUpdateAdvancedFilter])

  const clearAllFilters = useCallback(() => {
    storeClearAllFilters()
  }, [storeClearAllFilters])

  const saveCurrentSearch = useCallback((name: string) => {
    return storeSaveCurrentSearch(name)
  }, [storeSaveCurrentSearch])

  const applySavedSearch = useCallback((searchId: string) => {
    return storeApplySavedSearch(searchId)
  }, [storeApplySavedSearch])

  const deleteSavedSearch = useCallback((searchId: string) => {
    storeDeleteSavedSearch(searchId)
  }, [storeDeleteSavedSearch])

  const renameSavedSearch = useCallback((searchId: string, newName: string) => {
    storeRenameSavedSearch(searchId, newName)
  }, [storeRenameSavedSearch])

  const toggleSearchSharing = useCallback((searchId: string) => {
    storeToggleSearchSharing(searchId)
  }, [storeToggleSearchSharing])

  const getActiveFiltersCount = useCallback(() => {
    return storeGetActiveFiltersCount()
  }, [storeGetActiveFiltersCount])

  const hasActiveFilters = useCallback(() => {
    return storeHasActiveFilters()
  }, [storeHasActiveFilters])

  return {
    filtersState,
    setFiltersState,
    updateFilter,
    updateAdvancedFilter,
    clearAllFilters,
    savedSearches,
    setSavedSearches: useJobFiltersStore(s => s.setSavedSearches),
    saveCurrentSearch,
    applySavedSearch,
    deleteSavedSearch,
    renameSavedSearch,
    toggleSearchSharing,
    getActiveFiltersCount,
    hasActiveFilters,
    isLoaded: true
  }
}
