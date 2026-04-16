"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import type { CandidateLocal } from "@/services/lia-api"
// liaApi.getCandidates centralises fetch, auth headers, timeout, and retry —
// see fetchWithRetry in services/lia-api/base.ts.
import { liaApi } from "@/services/lia-api"

const PER_PAGE = 20
const SEARCH_DEBOUNCE_MS = 300

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

export function useCandidatesList(initialFilters?: CandidatesListFilters): UseCandidatesListReturn {
  const [candidates, setCandidates] = useState<CandidateLocal[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [filters, setFiltersState] = useState<CandidatesListFilters>(initialFilters ?? {})
  const [searchTerm, setSearchTerm] = useState(initialFilters?.search ?? "")
  const [debouncedSearch, setDebouncedSearch] = useState(initialFilters?.search ?? "")
  const [fetchTrigger, setFetchTrigger] = useState(0)
  const requestIdRef = useRef(0)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm)
    }, SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [searchTerm])

  useEffect(() => {
    const thisRequestId = ++requestIdRef.current

    setLoading(true)
    setError(null)

    const params = {
      search: debouncedSearch || undefined,
      status: filters.status,
      tags: filters.tags,
      seniority: filters.seniority,
      sort_by: filters.sort_by,
      sort_order: filters.sort_order,
      limit: PER_PAGE,
      offset: (currentPage - 1) * PER_PAGE,
    }

    liaApi.getCandidates(params)
      .then(data => {
        if (requestIdRef.current !== thisRequestId) return
        setCandidates(data.candidates as CandidateLocal[])
        setTotal(data.total ?? 0)
        setLoading(false)
      })
      .catch(err => {
        if (requestIdRef.current !== thisRequestId) return
        console.error("[useCandidatesList] fetch error:", err)
        setError("Erro ao carregar candidatos. Tente novamente.")
        setCandidates([])
        setLoading(false)
      })
  }, [filters.status, filters.tags, filters.seniority, filters.sort_by, filters.sort_order, debouncedSearch, currentPage, fetchTrigger])

  const setFilters = useCallback(
    (newFilters: CandidatesListFilters) => {
      const { search, ...rest } = newFilters
      setFiltersState(rest)
      // Always replace searchTerm so `setFilters({})` clears an active search.
      setSearchTerm(search ?? "")
      setCurrentPage(1)
    },
    []
  )

  const updateFilter = useCallback(
    <K extends keyof CandidatesListFilters>(key: K, value: CandidatesListFilters[K]) => {
      if (key === "search") {
        setSearchTerm((value as string) ?? "")
        setCurrentPage(1)
      } else {
        setFiltersState(prev => ({ ...prev, [key]: value }))
        setCurrentPage(1)
      }
    },
    []
  )

  const goToPage = useCallback(
    (page: number) => {
      setCurrentPage(page)
    },
    []
  )

  const refresh = useCallback(() => {
    setFetchTrigger(prev => prev + 1)
  }, [])

  useEffect(() => {
    const onFocus = () => {
      if (error) {
        setFetchTrigger(prev => prev + 1)
      }
    }
    window.addEventListener("focus", onFocus)
    return () => window.removeEventListener("focus", onFocus)
  }, [error])

  const totalPages = Math.max(1, Math.ceil(total / PER_PAGE))

  const exposedFilters: CandidatesListFilters = { ...filters, search: searchTerm }

  return {
    candidates,
    loading,
    error,
    total,
    currentPage,
    totalPages,
    perPage: PER_PAGE,
    filters: exposedFilters,
    setFilters,
    updateFilter,
    goToPage,
    refresh,
  }
}
