"use client"

import { useState, useCallback, useEffect, useRef, useMemo } from "react"
import { toast } from "sonner"
import { useCreditEstimator, getCostLevel } from "@/hooks/search/useCreditEstimator"
import type { CreditEstimate } from "@/lib/api/candidate-search"
import type { SearchSource, ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import { isGlobalSource } from "@/lib/utils/source-detection"

// ---------------------------------------------------------------------------
// Exported types
// ---------------------------------------------------------------------------

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

export type RevealedContacts = Record<string, { email?: string; phone?: string }>

export interface CreditEstimateWithLevel extends CreditEstimate {
  cost_level: "low" | "medium" | "high" | "very-high"
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useVacancySearch(vacancyId: string, enrichedJD: string, onCandidatesAdded?: () => void) {
  // ---- core state ----
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

  // ---- reveal contacts (item 5) ----
  const [revealedContacts, setRevealedContacts] = useState<RevealedContacts>({})
  const [isRevealing, setIsRevealing] = useState(false)

  // ---- credit estimator (feature 1) ----
  const { calculateLocal } = useCreditEstimator()
  const [creditEstimate, setCreditEstimate] = useState<CreditEstimateWithLevel | null>(null)

  useEffect(() => {
    const limit = mode === "auto" ? autoConfig.maxCandidates : 15
    const raw = calculateLocal({
      searchType: "fast",
      limit,
      highFreshness: false,
      requireEmails,
      showEmails: requireEmails,
      requirePhoneNumbers,
      showPhoneNumbers: requirePhoneNumbers,
      requirePhonesOrEmails: requireEmails || requirePhoneNumbers,
    })
    setCreditEstimate({
      ...raw,
      cost_level: getCostLevel(raw.total_estimated),
    })
  }, [searchSource, requireEmails, requirePhoneNumbers, mode, autoConfig.maxCandidates, calculateLocal])

  // ---- search fingerprint (feature 3) ----
  const [searchFingerprint, setSearchFingerprint] = useState<string | null>(null)

  useEffect(() => {
    if (!searchFingerprint || !vacancyId) return
    let cancelled = false
    const rehydrate = async () => {
      try {
        const res = await fetch(
          `/api/backend-proxy/search/feedback/by-search?fingerprint=${encodeURIComponent(searchFingerprint)}&job_id=${encodeURIComponent(vacancyId)}`,
        )
        if (!res.ok || cancelled) return
        const data = await res.json()
        const feedbacks: Record<string, "like" | "dislike"> = {}
        const items = data?.data?.feedbacks || data?.feedbacks || []
        for (const fb of items) {
          if (fb.candidate_id && fb.feedback_type) {
            feedbacks[String(fb.candidate_id)] = fb.feedback_type as "like" | "dislike"
          }
        }
        if (!cancelled) setSearchFeedbacks(feedbacks)
      } catch {
        // best-effort re-hydration
      }
    }
    rehydrate()
    return () => { cancelled = true }
  }, [searchFingerprint, vacancyId])

  // ---- auto confirmation flow (feature 4) ----
  const [showAutoConfirm, setShowAutoConfirm] = useState(false)

  // ---- search progress simulation (feature 5) ----
  const [searchProgress, setSearchProgress] = useState(0)
  const progressIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const startProgressSimulation = useCallback(() => {
    setSearchProgress(20)
    if (progressIntervalRef.current) clearInterval(progressIntervalRef.current)
    progressIntervalRef.current = setInterval(() => {
      setSearchProgress(prev => {
        if (prev >= 55) return prev // cap during search phase
        return prev + Math.floor(Math.random() * 5) + 1
      })
    }, 400)
  }, [])

  const advanceProgressToResponse = useCallback(() => {
    if (progressIntervalRef.current) clearInterval(progressIntervalRef.current)
    setSearchProgress(60)
    progressIntervalRef.current = setInterval(() => {
      setSearchProgress(prev => {
        if (prev >= 90) return prev // cap during parsing phase
        return prev + Math.floor(Math.random() * 8) + 2
      })
    }, 200)
  }, [])

  const completeProgress = useCallback(() => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current)
      progressIntervalRef.current = null
    }
    setSearchProgress(100)
  }, [])

  const resetProgress = useCallback(() => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current)
      progressIntervalRef.current = null
    }
    setSearchProgress(0)
  }, [])

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current)
    }
  }, [])

  // ---- modal helpers ----
  const openModal = useCallback(() => setShowModal(true), [])
  const closeModal = useCallback(() => setShowModal(false), [])
  const closeResults = useCallback(() => {
    setShowResults(false)
    setSelectedIds(new Set())
    setShowAutoConfirm(false)
  }, [])

  // ---- determine search endpoint (feature 2) ----
  const buildSearchPayload = useCallback((
    query: string,
    metadata: SearchMetadata,
    limit: number,
  ): { url: string; body: Record<string, unknown> } => {
    const useJDEndpoint =
      (metadata.mode === "jd" || !!metadata.jobDescription) && !!enrichedJD

    if (useJDEndpoint) {
      return {
        url: "/api/backend-proxy/search/candidates/by-job-description",
        body: {
          job_description: enrichedJD,
          search_source: searchSource,
          require_emails: requireEmails,
          limit,
        },
      }
    }

    return {
      url: "/api/backend-proxy/search/candidates",
      body: {
        query: query.trim(),
        search_source: searchSource,
        require_emails: requireEmails,
        require_phone_numbers: requirePhoneNumbers,
        limit,
        ...(metadata.jobDescription ? { job_description: metadata.jobDescription } : {}),
        ...(metadata.booleanQuery ? { boolean_query: metadata.booleanQuery } : {}),
        ...(metadata.filters ? { filters: metadata.filters } : {}),
      },
    }
  }, [enrichedJD, searchSource, requireEmails, requirePhoneNumbers])

  // ---- main search submit ----
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
    setSearchFingerprint(null)
    setShowAutoConfirm(false)
    setRevealedContacts({})
    startProgressSimulation()

    const limit = mode === "auto" ? autoConfig.maxCandidates : 15
    const { url, body } = buildSearchPayload(query, metadata, limit)

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })

      advanceProgressToResponse()

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}))
        if (errBody?.error === "fairness_blocked" || errBody?.fairness_blocked) {
          toast.error(errBody.educational_message || "Busca bloqueada")
          resetProgress()
          setIsSearching(false)
          setShowResults(false)
          return
        }
        throw new Error(errBody?.message || `Search failed: ${res.status}`)
      }

      const data = await res.json()
      const candidates = data?.data?.candidates || data?.candidates || data?.data || []

      // Store search fingerprint (feature 3)
      const fp = data?.data?.search_fingerprint || data?.search_fingerprint || null
      setSearchFingerprint(fp)

      setSearchResults(candidates)
      setTotalResults(data?.data?.total || data?.total || candidates.length)
      setThreadId(data?.data?.thread_id || data?.thread_id)
      completeProgress()

      // Auto confirmation flow (feature 4)
      if (mode === "auto") {
        setShowAutoConfirm(true)
      }
    } catch (err) {
      toast.error("Erro na busca", { description: (err as Error).message })
      resetProgress()
      setShowResults(false)
    } finally {
      setIsSearching(false)
    }
  }, [
    searchSource, requireEmails, requirePhoneNumbers, mode, autoConfig,
    buildSearchPayload, startProgressSimulation, advanceProgressToResponse,
    completeProgress, resetProgress,
  ])

  // ---- load more ----
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
    } catch {
      // silent
    } finally {
      setIsSearching(false)
    }
  }, [threadId, lastSearchParams, searchFeedbacks, searchResults])

  // ---- feedback (feature 3 — includes fingerprint) ----
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
          ...(searchFingerprint ? { search_fingerprint: searchFingerprint } : {}),
        }),
      })
    } catch {
      // best-effort
    }
  }, [vacancyId, searchFingerprint])

  // ---- reveal contact (item 5) ----
  const handleRevealContact = useCallback(async (candidateId: string, candidateName: string, type: "email" | "phone", linkedinUrl?: string) => {
    setIsRevealing(true)
    try {
      const linkedinSlug = linkedinUrl?.split("/in/")?.[1]?.replace("/", "") || null
      const res = await fetch("/api/backend-proxy/search/reveal/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: candidateId,
          candidate_name: candidateName,
          reveal_type: type,
          linkedin_slug: linkedinSlug,
        }),
      })
      const data = await res.json()
      if (data.success) {
        const value = type === "email" ? data.email : data.phone
        setRevealedContacts(prev => ({
          ...prev,
          [candidateId]: { ...prev[candidateId], [type]: value },
        }))
        toast.success(type === "email" ? "Email revelado" : "Telefone revelado", {
          description: value || "Contato revelado",
          duration: 5000,
        })
        // Auto-persist for pearch candidates
        const candidate = searchResults.find(c => String(c.id) === candidateId)
        const source = (candidate?.source_type || candidate?.source || "") as string
        if (isGlobalSource(source, Boolean(candidate?.pearch_profile_id))) {
          fetch("/api/backend-proxy/search/candidates/persist-revealed", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              pearch_id: candidate?.pearch_profile_id || candidateId,
              candidate_name: candidateName,
              email: type === "email" ? value : null,
              phone: type === "phone" ? value : null,
              linkedin_url: linkedinUrl || null,
              current_title: candidate?.current_title || null,
              current_company: candidate?.current_company || null,
              avatar_url: candidate?.avatar_url || null,
            }),
          }).catch(() => {})
        }
      } else {
        toast.error("Contato não disponível", { description: data.message || "Não foi possível revelar" })
      }
    } catch {
      toast.error("Erro ao revelar contato")
    } finally {
      setIsRevealing(false)
    }
  }, [searchResults])

  // ---- selection ----
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

  // ---- add selected to vacancy ----
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
      setShowAutoConfirm(false)
      onCandidatesAdded?.()
    } catch (err) {
      toast.error("Erro ao adicionar", { description: (err as Error).message })
    }
  }, [selectedIds, vacancyId, searchSource, onCandidatesAdded])

  // ---- auto add (used after confirmation — feature 4) ----
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
      setShowAutoConfirm(false)
      onCandidatesAdded?.()
    } catch (err) {
      toast.error("Erro ao adicionar", { description: (err as Error).message })
    }
  }, [searchResults, autoConfig, searchSource, vacancyId, onCandidatesAdded])

  // ---- auto confirmation actions (feature 4) ----
  const confirmAutoAdd = useCallback(() => {
    setShowAutoConfirm(false)
    addAutoCandidates()
  }, [addAutoCandidates])

  const cancelAutoAdd = useCallback(() => {
    setShowAutoConfirm(false)
  }, [])

  // ---- edit search ----
  const handleEditSearch = useCallback(() => {
    setShowResults(false)
    setShowModal(true)
    setShowAutoConfirm(false)
  }, [])

  // ---- return ----
  const autoQualifyingPreview = useMemo(() => {
    if (mode !== "auto") return []
    return searchResults.filter(c => {
      const score = Number(c.lia_score || c.score || c.match_percentage || 0)
      return score >= autoConfig.minScore
    }).slice(0, autoConfig.maxCandidates)
  }, [searchResults, autoConfig, mode])

  return {
    // core state
    mode, setMode,
    showModal, openModal, closeModal,
    showResults, closeResults,
    searchSource, setSearchSource,
    requireEmails, setRequireEmails,
    requirePhoneNumbers, setRequirePhoneNumbers,
    autoConfig, setAutoConfig,
    // search actions
    handleSearchSubmit,
    handleLoadMore,
    handleFeedback,
    // selection
    selectedIds, toggleSelect, selectAll, clearSelection,
    // add actions
    addSelectedToVacancy,
    addAutoCandidates,
    // edit
    handleEditSearch,
    // search state
    lastSearchParams,
    isSearching,
    searchResults,
    totalResults,
    searchFeedbacks,
    // credit estimate (feature 1)
    creditEstimate,
    // search fingerprint (feature 3)
    searchFingerprint,
    // auto confirmation (feature 4)
    showAutoConfirm,
    autoQualifyingPreview,
    confirmAutoAdd,
    cancelAutoAdd,
    // progress (feature 5)
    searchProgress,
    // reveal contacts (item 5)
    revealedContacts,
    isRevealing,
    handleRevealContact,
  }
}
