"use client"

/**
 * useCandidatesListMapped — Sprint G4.
 *
 * Wraps useCandidatesList and applies mapCandidateLocalToCandidate transform,
 * returning Candidate[] (FE display type) instead of CandidateLocal[] (API type).
 *
 * Portabilidade Vue: composable com computed(() => candidates.value.map(...))
 */
import { useMemo } from "react"
import { useCandidatesList, type CandidatesListFilters, type CandidatesErrorKind } from "./use-candidates-list"
import { mapCandidateLocalToCandidate } from "@/lib/transforms/candidate-transforms"
import type { Candidate } from "@/components/pages/candidates/types"

export interface UseCandidatesListMappedReturn {
  candidates: Candidate[]
  loading: boolean
  error: string | null
  errorKind: CandidatesErrorKind | null
  total: number
  currentPage: number
  totalPages: number
  perPage: number
  filters: CandidatesListFilters
  setFilters: (filters: CandidatesListFilters) => void
  updateFilter: <K extends keyof CandidatesListFilters>(key: K, value: CandidatesListFilters[K]) => void
  goToPage: (page: number) => void
  refresh: () => void
}

export function useCandidatesListMapped(
  initialFilters?: CandidatesListFilters
): UseCandidatesListMappedReturn {
  const list = useCandidatesList(initialFilters)

  const candidates = useMemo<Candidate[]>(
    () => list.candidates.map((c, idx) => mapCandidateLocalToCandidate(c, idx)),
    [list.candidates]
  )

  return {
    candidates,
    loading: list.loading,
    error: list.error,
    errorKind: list.errorKind,
    total: list.total,
    currentPage: list.currentPage,
    totalPages: list.totalPages,
    perPage: list.perPage,
    filters: list.filters,
    setFilters: list.setFilters,
    updateFilter: list.updateFilter,
    goToPage: list.goToPage,
    refresh: list.refresh,
  }
}
