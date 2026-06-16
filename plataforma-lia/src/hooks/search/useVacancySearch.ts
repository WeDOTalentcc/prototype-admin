"use client"

import { useState, useCallback } from "react"
import { toast } from "sonner"
import type { SearchSource, ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"

export type VacancySearchMode = "manual" | "auto"

export interface VacancySearchParams {
  query: string
  entities: ParsedEntities
  searchSource: SearchSource
  searchMode: SearchMode
  metadata: SearchMetadata
  requireEmails: boolean
  requirePhoneNumbers: boolean
}

export interface AutoConfig {
  maxCandidates: number
  minScore: number
}

export function useVacancySearch(vacancyId: string) {
  const [mode, setMode] = useState<VacancySearchMode>("auto")
  const [showModal, setShowModal] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [searchSource, setSearchSource] = useState<SearchSource>("hybrid")
  const [requireEmails, setRequireEmails] = useState(true)
  const [requirePhoneNumbers, setRequirePhoneNumbers] = useState(false)
  const [lastSearchParams, setLastSearchParams] = useState<VacancySearchParams | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [autoConfig, setAutoConfig] = useState<AutoConfig>({ maxCandidates: 30, minScore: 70 })
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<Record<string, unknown>[]>([])
  const [totalResults, setTotalResults] = useState(0)
  const [threadId, setThreadId] = useState<string | undefined>()
  const [searchFeedbacks, setSearchFeedbacks] = useState<Record<string, "like" | "dislike">>({})

  const openModal = useCallback(() => setShowModal(true), [])
  const closeModal = useCallback(() => setShowModal(false), [])
  const closeResults = useCallback(() => {
    setShowResults(false)
    setSelectedIds(new Set())
  }, [])

  const handleSearchSubmit = useCallback(async (
    query: string,
    entities: ParsedEntities,
    searchMode: SearchMode,
    metadata: SearchMetadata,
  ) => {
    const params: VacancySearchParams = {
      query, entities, searchSource, searchMode, metadata,
      requireEmails, requirePhoneNumbers,
    }
    setLastSearchParams(params)
    setShowModal(false)
    setShowResults(true)
    setIsSearching(true)
    setSearchResults([])
    setSelectedIds(new Set())

    try {
      const res = await fetch("/api/backend-proxy/search/candidates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.trim(),
          search_source: searchSource,
          require_emails: requireEmails,
          require_phone_numbers: requirePhoneNumbers,
          limit: mode === "auto" ? autoConfig.maxCandidates : 15,
          ...(metadata.jobDescription ? { job_description: metadata.jobDescription } : {}),
          ...(metadata.booleanQuery ? { boolean_query: metadata.booleanQuery } : {}),
          ...(metadata.filters ? { filters: metadata.filters } : {}),
        }),
      })

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        if (errBody?.error === "fairness_blocked" || errBody?.fairness_blocked) {
          toast.error(errBody.educational_message || "Busca bloqueada")
          setIsSearching(false)
          setShowResults(false)
          return
        }
        throw new Error(errBody?.message || `Search failed: ${res.status}`)
      }

      const data = await res.json()
      const candidates = data?.data?.candidates || data?.candidates || data?.data || []
      setSearchResults(candidates)
      setTotalResults(data?.data?.total || data?.total || candidates.length)
      setThreadId(data?.data?.thread_id || data?.thread_id)
    } catch (err) {
      toast.error("Erro na busca", { description: (err as Error).message })
      setShowResults(false)
    } finally {
      setIsSearching(false)
    }
  }, [searchSource, requireEmails, requirePhoneNumbers, mode, autoConfig])

  const handleLoadMore = useCallback(async () => {
    if (!threadId || !lastSearchParams) return
    setIsSearching(true)
    try {
      const dislikedEmails = Object.entries(searchFeedbacks)
        .filter(([, fb]) => fb === "dislike")
        .map(([id]) => {
          const c = searchResults.find(r => String(r.id) === id)
          return (c?.email as string) || ""
        })
        .filter(Boolean)

      const res = await fetch("/api/backend-proxy/search/candidates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: lastSearchParams.query,
          search_source: lastSearchParams.searchSource,
          require_emails: lastSearchParams.requireEmails,
          thread_id: threadId,
          excluded_emails: dislikedEmails,
          offset: searchResults.length,
          limit: 15,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        const more = data?.data?.candidates || data?.candidates || data?.data || []
        setSearchResults(prev => [...prev, ...more])
        setTotalResults(data?.data?.total || data?.total || searchResults.length + more.length)
      }
    } catch { /* silent */ } finally {
      setIsSearching(false)
    }
  }, [threadId, lastSearchParams, searchFeedbacks, searchResults])

  const handleFeedback = useCallback(async (candidateId: string, type: "like" | "dislike") => {
    setSearchFeedbacks(prev => ({ ...prev, [candidateId]: type }))
    try {
      await fetch("/api/backend-proxy/search/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: candidateId,
          feedback_type: type,
          job_id: vacancyId,
        }),
      })
    } catch { /* best-effort */ }
  }, [vacancyId])

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const selectAll = useCallback(() => {
    setSelectedIds(new Set(searchResults.map(c => String(c.id))))
  }, [searchResults])

  const clearSelection = useCallback(() => setSelectedIds(new Set()), [])

  const addSelectedToVacancy = useCallback(async () => {
    if (selectedIds.size === 0) return
    const sourceLabel = searchSource === "local" ? "local" : searchSource === "hybrid" ? "hybrid" : "pearch"
    try {
      const res = await fetch(`/api/backend-proxy/search/vacancy/${vacancyId}/add-candidates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_ids: Array.from(selectedIds),
          source: sourceLabel,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        if (err?.detail?.error === "calibration_required") {
          toast.error("Calibração necessária", { description: err.detail.message })
          return
        }
        throw new Error(err?.message || `Failed: ${res.status}`)
      }
      const data = await res.json()
      toast.success(`${data.added_count} candidatos adicionados`, {
        description: data.skipped_count > 0 ? `${data.skipped_count} já estavam na vaga` : undefined,
      })
      setShowResults(false)
      setSelectedIds(new Set())
    } catch (err) {
      toast.error("Erro ao adicionar", { description: (err as Error).message })
    }
  }, [selectedIds, vacancyId, searchSource])

  const addAutoCandidates = useCallback(async () => {
    const qualifying = searchResults.filter(c => {
      const score = Number(c.lia_score || c.score || c.match_percentage || 0)
      return score >= autoConfig.minScore
    }).slice(0, autoConfig.maxCandidates)

    if (qualifying.length === 0) {
      toast.error("Nenhum candidato atingiu o score mínimo")
      return
    }

    const ids = qualifying.map(c => String(c.id))
    setSelectedIds(new Set(ids))
    const sourceLabel = searchSource === "local" ? "local" : searchSource === "hybrid" ? "hybrid" : "pearch"
    try {
      const res = await fetch(`/api/backend-proxy/search/vacancy/${vacancyId}/add-candidates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate_ids: ids, source: sourceLabel }),
      })
      if (!res.ok) throw new Error(`Failed: ${res.status}`)
      const data = await res.json()
      toast.success(`${data.added_count} candidatos adicionados automaticamente`)
      setShowResults(false)
      setSelectedIds(new Set())
    } catch (err) {
      toast.error("Erro ao adicionar", { description: (err as Error).message })
    }
  }, [searchResults, autoConfig, searchSource, vacancyId])

  const handleEditSearch = useCallback(() => {
    setShowResults(false)
    setShowModal(true)
  }, [])

  return {
    mode, setMode,
    showModal, openModal, closeModal,
    showResults, closeResults,
    searchSource, setSearchSource,
    requireEmails, setRequireEmails,
    requirePhoneNumbers, setRequirePhoneNumbers,
    autoConfig, setAutoConfig,
    handleSearchSubmit,
    handleLoadMore,
    handleFeedback,
    selectedIds, toggleSelect, selectAll, clearSelection,
    addSelectedToVacancy,
    addAutoCandidates,
    handleEditSearch,
    lastSearchParams,
    isSearching,
    searchResults,
    totalResults,
    searchFeedbacks,
  }
}
