'use client'

import { useState, useEffect, useCallback } from 'react'
import { useUIPreferencesStore } from '@/stores/ui-preferences-store'

export interface KanbanFiltersPersisted {
  searchQuery: string
  stageFilter: string[]
  scoreMin: number | null
  statusFilter: string | null
  workModelFilter: string | null
  sortColumn: string
  sortDirection: 'asc' | 'desc'
}

export interface UseFiltersPersistenceOptions {
  storageKey?: string
  jobId?: string
  enabled?: boolean
}

export interface UseFiltersPersistenceReturn {
  filters: KanbanFiltersPersisted
  setFilters: (filters: Partial<KanbanFiltersPersisted>) => void
  setSearchQuery: (query: string) => void
  setStageFilter: (stages: string[]) => void
  setScoreMin: (score: number | null) => void
  setStatusFilter: (status: string | null) => void
  setWorkModelFilter: (workModel: string | null) => void
  setSortColumn: (column: string) => void
  setSortDirection: (direction: 'asc' | 'desc') => void
  resetFilters: () => void
  hasActiveFilters: boolean
}

const DEFAULT_FILTERS: KanbanFiltersPersisted = {
  searchQuery: '',
  stageFilter: [],
  scoreMin: null,
  statusFilter: null,
  workModelFilter: null,
  sortColumn: 'notaLiaGeral',
  sortDirection: 'desc'
}

export function useFiltersPersistence(
  options: UseFiltersPersistenceOptions = {}
): UseFiltersPersistenceReturn {
  const { 
    storageKey = 'kanban-filters',
    jobId,
    enabled = true
  } = options

  const fullStorageKey = jobId ? `${storageKey}-${jobId}` : storageKey

  const [filters, setFiltersState] = useState<KanbanFiltersPersisted>(DEFAULT_FILTERS)

  const { getKanbanFilters, setKanbanFilters, removeKanbanFilters } = useUIPreferencesStore()

  useEffect(() => {
    if (!enabled) return

    const saved = getKanbanFilters(fullStorageKey)
    if (saved) {
      setFiltersState(prev => ({ ...prev, ...saved as Partial<KanbanFiltersPersisted> }))
    }
  }, [fullStorageKey, enabled, getKanbanFilters])

  const saveFilters = useCallback((newFilters: KanbanFiltersPersisted) => {
    if (!enabled) return
    setKanbanFilters(fullStorageKey, newFilters as unknown as Record<string, unknown>)
  }, [fullStorageKey, enabled, setKanbanFilters])

  const setFilters = useCallback((partial: Partial<KanbanFiltersPersisted>) => {
    setFiltersState(prev => {
      const newFilters = { ...prev, ...partial }
      saveFilters(newFilters)
      return newFilters
    })
  }, [saveFilters])

  const setSearchQuery = useCallback((query: string) => {
    setFilters({ searchQuery: query })
  }, [setFilters])

  const setStageFilter = useCallback((stages: string[]) => {
    setFilters({ stageFilter: stages })
  }, [setFilters])

  const setScoreMin = useCallback((score: number | null) => {
    setFilters({ scoreMin: score })
  }, [setFilters])

  const setStatusFilter = useCallback((status: string | null) => {
    setFilters({ statusFilter: status })
  }, [setFilters])

  const setWorkModelFilter = useCallback((workModel: string | null) => {
    setFilters({ workModelFilter: workModel })
  }, [setFilters])

  const setSortColumn = useCallback((column: string) => {
    setFilters({ sortColumn: column })
  }, [setFilters])

  const setSortDirection = useCallback((direction: 'asc' | 'desc') => {
    setFilters({ sortDirection: direction })
  }, [setFilters])

  const resetFilters = useCallback(() => {
    setFiltersState(DEFAULT_FILTERS)
    if (enabled) {
      removeKanbanFilters(fullStorageKey)
    }
  }, [fullStorageKey, enabled, removeKanbanFilters])

  const hasActiveFilters = 
    filters.searchQuery !== '' ||
    filters.stageFilter.length > 0 ||
    filters.scoreMin !== null ||
    filters.statusFilter !== null ||
    filters.workModelFilter !== null

  return {
    filters,
    setFilters,
    setSearchQuery,
    setStageFilter,
    setScoreMin,
    setStatusFilter,
    setWorkModelFilter,
    setSortColumn,
    setSortDirection,
    resetFilters,
    hasActiveFilters
  }
}
