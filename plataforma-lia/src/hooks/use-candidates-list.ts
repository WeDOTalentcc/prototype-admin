"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { liaApi } from "@/services/lia-api"
import type { CandidateLocal, CandidateListParams, CandidatePaginatedResponse } from "@/services/lia-api"

export interface CandidatesListFilters {
  search?: string
  status?: string
  tags?: string
  seniority?: string
  sort_by?: string
  sort_order?: "asc" | "desc"
}

export interface UseCandidatesListReturn {
  candidates: CandidateLocal[]
  loading: boolean
  error: string | null
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

const PER_PAGE = 20

export function useCandidatesList(initialFilters?: CandidatesListFilters): UseCandidatesListReturn {
  const [candidates, setCandidates] = useState<CandidateLocal[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [filters, setFiltersState] = useState<CandidatesListFilters>(initialFilters ?? {})

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const fetchCandidates = useCallback(
    async (f: CandidatesListFilters, page: number) => {
      // Cancel previous in-flight request
      if (abortRef.current) {
        abortRef.current.abort()
      }
      abortRef.current = new AbortController()

      setLoading(true)
      setError(null)

      const params: CandidateListParams = {
        limit: PER_PAGE,
        offset: (page - 1) * PER_PAGE,
        ...(f.search ? { search: f.search } : {}),
        ...(f.status ? { status: f.status } : {}),
        ...(f.tags ? { tags: f.tags } : {}),
        ...(f.seniority ? { seniority: f.seniority } : {}),
        ...(f.sort_by ? { sort_by: f.sort_by } : {}),
        ...(f.sort_order ? { sort_order: f.sort_order } : {}),
      }

      try {
        const result = await liaApi.getCandidates(params)
        setCandidates(result.candidates || (result as any).items || [])
        setTotal(result.total ?? 0)
      } catch (err) {
        if ((err as Error)?.name !== "AbortError") {
          setError("Erro ao carregar candidatos. Tente novamente.")
        }
      } finally {
        setLoading(false)
      }
    },
    []
  )

  // Debounce search, immediate for other filter changes
  const scheduleSearch = useCallback(
    (f: CandidatesListFilters, page: number, isTextSearch: boolean) => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      const delay = isTextSearch ? 300 : 0
      debounceRef.current = setTimeout(() => fetchCandidates(f, page), delay)
    },
    [fetchCandidates]
  )

  // Initial load
  useEffect(() => {
    fetchCandidates(filters, 1)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const setFilters = useCallback(
    (newFilters: CandidatesListFilters) => {
      setFiltersState(newFilters)
      setCurrentPage(1)
      const isTextSearch = newFilters.search !== filters.search
      scheduleSearch(newFilters, 1, isTextSearch)
    },
    [filters.search, scheduleSearch]
  )

  const updateFilter = useCallback(
    <K extends keyof CandidatesListFilters>(key: K, value: CandidatesListFilters[K]) => {
      setFiltersState(prev => {
        const updated = { ...prev, [key]: value }
        setCurrentPage(1)
        const isTextSearch = key === "search"
        scheduleSearch(updated, 1, isTextSearch)
        return updated
      })
    },
    [scheduleSearch]
  )

  const goToPage = useCallback(
    (page: number) => {
      setCurrentPage(page)
      fetchCandidates(filters, page)
    },
    [filters, fetchCandidates]
  )

  const refresh = useCallback(() => {
    fetchCandidates(filters, currentPage)
  }, [filters, currentPage, fetchCandidates])

  const totalPages = Math.max(1, Math.ceil(total / PER_PAGE))

  return {
    candidates,
    loading,
    error,
    total,
    currentPage,
    totalPages,
    perPage: PER_PAGE,
    filters,
    setFilters,
    updateFilter,
    goToPage,
    refresh,
  }
}
