"use client"

import { useState, useCallback, useEffect } from "react"
import type { CandidateLocal } from "@/services/lia-api"

const BACKEND_URL = '/api/backend-proxy'
const PER_PAGE = 20

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
  const [fetchTrigger, setFetchTrigger] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function doFetch() {
      setLoading(true)
      setError(null)

      const query = new URLSearchParams()
      if (filters.search) query.set('search', filters.search)
      if (filters.status) query.set('status', filters.status)
      if (filters.tags) query.set('tags', filters.tags)
      if (filters.seniority) query.set('seniority', filters.seniority)
      if (filters.sort_by) query.set('sort_by', filters.sort_by)
      if (filters.sort_order) query.set('sort_order', filters.sort_order)
      query.set('limit', String(PER_PAGE))
      query.set('offset', String((currentPage - 1) * PER_PAGE))

      const qs = query.toString()
      const url = `${BACKEND_URL}/candidates${qs ? `?${qs}` : ''}`
      const maxRetries = 2
      const baseDelay = 1500

      for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
          const response = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
          })

          if (!response.ok) {
            throw new Error(`Backend retornou ${response.status}`)
          }

          const data = await response.json()

          if (!cancelled) {
            setCandidates(data.candidates || data.items || [])
            setTotal(data.total ?? 0)
            setLoading(false)
          }
          return
        } catch (err) {
          if (cancelled) return
          if (attempt < maxRetries) {
            await new Promise(r => setTimeout(r, baseDelay * (attempt + 1)))
          } else {
            setError("Erro ao carregar candidatos. Tente novamente.")
            setLoading(false)
          }
        }
      }
    }

    doFetch()
    return () => { cancelled = true }
  }, [filters, currentPage, fetchTrigger])

  const setFilters = useCallback(
    (newFilters: CandidatesListFilters) => {
      setFiltersState(newFilters)
      setCurrentPage(1)
    },
    []
  )

  const updateFilter = useCallback(
    <K extends keyof CandidatesListFilters>(key: K, value: CandidatesListFilters[K]) => {
      setFiltersState(prev => ({ ...prev, [key]: value }))
      setCurrentPage(1)
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
