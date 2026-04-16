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

// Classificação do erro de fetch. "unauthorized"/"forbidden" exigem relogin;
// "server"/"network" são retriáveis.
//
// Contrato para consumidores:
//   - `errorKind` é a fonte de verdade para roteamento de UX.
//   - `error` passou a carregar a mensagem crua (err.message) em vez do texto
//     pt-BR anterior. Consumidores que queiram copy localizado devem derivar
//     a string de `errorKind` via i18n (ver FunilDeTalentosClient).
export type CandidatesErrorKind = "unauthorized" | "forbidden" | "server" | "network"

export interface UseCandidatesListReturn {
  candidates: CandidateLocal[]
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

export function useCandidatesList(initialFilters?: CandidatesListFilters): UseCandidatesListReturn {
  const [candidates, setCandidates] = useState<CandidateLocal[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [errorKind, setErrorKind] = useState<CandidatesErrorKind | null>(null)
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
    setErrorKind(null)

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
      .catch((err: Error & { status?: number }) => {
        if (requestIdRef.current !== thisRequestId) return
        console.error("[useCandidatesList] fetch error:", err)
        // Só classifica; a UI traduz via i18n. `error` fica com mensagem crua
        // como fallback para consumers legados.
        const status = typeof err?.status === "number" ? err.status : undefined
        const kind: CandidatesErrorKind =
          status === 401 ? "unauthorized" :
          status === 403 ? "forbidden" :
          (status !== undefined && status >= 500) ? "server" :
          "network"
        setError(err?.message || "candidates_fetch_failed")
        setErrorKind(kind)
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
    errorKind,
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
