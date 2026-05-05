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
//     a string de `errorKind` via i18n (ver candidates-page.tsx canônico).
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
  /** Task #801 (C1): true enquanto o hook está auto-retentando após erro
   *  transiente de rede; consumidores podem renderizar um banner discreto
   *  de "reconectando…" sem esconder a lista preservada. */
  isTransientRetrying: boolean
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
  // Task #801 (C1): contador de tentativa transparente para o consumidor.
  // Não dispara re-render adicional além do triggered pelo backoff (setTimeout
  // → setFetchTrigger). Persiste entre fetches para que possamos exibir
  // "reconectando…" enquanto preservamos a lista atual.
  const transientRetryRef = useRef(0)
  const TRANSIENT_BACKOFFS_MS = [1000, 3000, 8000] as const
  const [isTransientRetrying, setIsTransientRetrying] = useState(false)

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
        setIsTransientRetrying(false)
        transientRetryRef.current = 0
      })
      .catch((err: Error & { status?: number; transientNetworkError?: boolean }) => {
        if (requestIdRef.current !== thisRequestId) return
        // [Task #801 C1] erros de rede transientes NÃO devem poluir
        // console.error — eles são esperados em cold-start/HMR e tratados
        // com auto-retry abaixo. Apenas erros determinísticos (auth, 5xx
        // persistente) sobem como `error` para o operador.
        // Só classifica; a UI traduz via i18n. `error` fica com mensagem crua
        // como fallback para consumers legados.
        const status = typeof err?.status === "number" ? err.status : undefined
        const isTransient =
          err?.transientNetworkError === true ||
          (status === 0) ||
          (status === undefined && /network|failed to fetch|load failed/i.test(err?.message ?? ""))
        if (!isTransient) {
          console.error("[useCandidatesList] fetch error:", err)
        }
        const kind: CandidatesErrorKind =
          status === 401 ? "unauthorized" :
          status === 403 ? "forbidden" :
          (status !== undefined && status >= 500) ? "server" :
          "network"

        // Task #801 (C1): em erro transiente de rede (cold-start, HMR, DNS)
        // **NÃO** zeramos a lista. O dev overlay e o usuário continuam vendo
        // o último snapshot enquanto auto-retentamos com backoff. Só limpamos
        // em erro definitivo (401/403/500+) onde mostrar dados stale seria
        // enganoso.
        if (isTransient) {
          // Erro transiente: preserva snapshot SEMPRE (mesmo após esgotar
          // budget de auto-retry). A regra invariante (CLAUDE.md §
          // HMR-resilience) é "nunca zerar lista em transient". O usuário
          // pode disparar refresh manual; sob mudança de filtro/página o
          // budget é resetado pelo effect abaixo.
          setError(err?.message || "candidates_fetch_failed")
          setErrorKind("network")
          setLoading(false)
          if (transientRetryRef.current < TRANSIENT_BACKOFFS_MS.length) {
            const delay = TRANSIENT_BACKOFFS_MS[transientRetryRef.current]
            transientRetryRef.current += 1
            setIsTransientRetrying(true)
            setTimeout(() => {
              if (requestIdRef.current === thisRequestId) {
                setFetchTrigger(prev => prev + 1)
              }
            }, delay)
          } else {
            // Budget esgotado: para de auto-retentar mas mantém snapshot e
            // banner discreto desligado para a UI mostrar `error` clássico
            // (com botão "Tentar novamente").
            setIsTransientRetrying(false)
          }
          return
        }

        setError(err?.message || "candidates_fetch_failed")
        setErrorKind(kind)
        setCandidates([])
        // Reseta total para evitar paginação stale sob estado de erro
        // (ex.: banner 401/500 mostrado com "Página 1 de 3" de listagem antiga).
        setTotal(0)
        setLoading(false)
        setIsTransientRetrying(false)
        transientRetryRef.current = 0
      })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.status, filters.tags, filters.seniority, filters.sort_by, filters.sort_order, debouncedSearch, currentPage, fetchTrigger])

  // Cancela retry transiente quando filtros/página mudam — o próximo fetch
  // recomeça do zero com a janela de backoff resetada.
  useEffect(() => {
    transientRetryRef.current = 0
    setIsTransientRetrying(false)
  }, [filters.status, filters.tags, filters.seniority, filters.sort_by, filters.sort_order, debouncedSearch, currentPage])

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
    isTransientRetrying,
  }
}
