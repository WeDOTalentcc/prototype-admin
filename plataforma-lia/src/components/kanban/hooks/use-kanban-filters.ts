import { useState, useCallback, useMemo } from 'react'
import type { KanbanCandidate } from '../types'
import { filterKanbanCandidates, type KanbanFilterCriteria } from '../utils/filter-utils'

export interface KanbanFiltersState {
  searchQuery: string
  kanbanScoreMin: number | null
  kanbanStatusFilter: string | null
  kanbanWorkModelFilter: string | null
}

export interface UseKanbanFiltersReturn {
  searchQuery: string
  kanbanScoreMin: number | null
  kanbanStatusFilter: string | null
  kanbanWorkModelFilter: string | null
  setSearchQuery: (query: string) => void
  setKanbanScoreMin: (score: number | null) => void
  setKanbanStatusFilter: (status: string | null) => void
  setKanbanWorkModelFilter: (workModel: string | null) => void
  applyFilters: (filters: Partial<KanbanFiltersState>) => void
  clearFilters: () => void
  filterCandidates: (candidates: KanbanCandidate[]) => KanbanCandidate[]
  hasActiveFilters: boolean
}

const initialState: KanbanFiltersState = {
  searchQuery: '',
  kanbanScoreMin: null,
  kanbanStatusFilter: null,
  kanbanWorkModelFilter: null
}

export function useKanbanFilters(): UseKanbanFiltersReturn {
  const [filters, setFilters] = useState<KanbanFiltersState>(initialState)

  const setSearchQuery = useCallback((query: string) => {
    setFilters(prev => ({ ...prev, searchQuery: query }))
  }, [])

  const setKanbanScoreMin = useCallback((score: number | null) => {
    setFilters(prev => ({ ...prev, kanbanScoreMin: score }))
  }, [])

  const setKanbanStatusFilter = useCallback((status: string | null) => {
    setFilters(prev => ({ ...prev, kanbanStatusFilter: status }))
  }, [])

  const setKanbanWorkModelFilter = useCallback((workModel: string | null) => {
    setFilters(prev => ({ ...prev, kanbanWorkModelFilter: workModel }))
  }, [])

  const applyFilters = useCallback((newFilters: Partial<KanbanFiltersState>) => {
    setFilters(prev => ({ ...prev, ...newFilters }))
  }, [])

  const clearFilters = useCallback(() => {
    setFilters(initialState)
  }, [])

  const filterCandidates = useCallback((candidates: KanbanCandidate[]): KanbanCandidate[] => {
    return filterKanbanCandidates(candidates, filters)
  }, [filters])

  const hasActiveFilters = useMemo(() => {
    return (
      filters.searchQuery !== '' ||
      filters.kanbanScoreMin !== null ||
      filters.kanbanStatusFilter !== null ||
      filters.kanbanWorkModelFilter !== null
    )
  }, [filters])

  return {
    searchQuery: filters.searchQuery,
    kanbanScoreMin: filters.kanbanScoreMin,
    kanbanStatusFilter: filters.kanbanStatusFilter,
    kanbanWorkModelFilter: filters.kanbanWorkModelFilter,
    setSearchQuery,
    setKanbanScoreMin,
    setKanbanStatusFilter,
    setKanbanWorkModelFilter,
    applyFilters,
    clearFilters,
    filterCandidates,
    hasActiveFilters
  }
}
