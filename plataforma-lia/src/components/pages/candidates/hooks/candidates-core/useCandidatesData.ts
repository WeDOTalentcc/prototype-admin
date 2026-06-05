// useCandidatesData.ts
// Data-fetching sub-hook: initial candidate load, bulk data requests,
// viewed-candidate tracking, and ancillary list/vacancy loading.
// Pure React — no Next.js router/navigation dependencies.

import { useState, useEffect, useRef, useCallback } from "react"
import { liaApi, CandidateLocal } from "@/services/lia-api"
import { useCandidatesListMapped } from "@/hooks/candidates/use-candidates-list-mapped"
import { useBulkCandidateDataRequests } from "@/hooks/candidates/use-candidate-data-requests"
import { mapCandidateToInternal as _mapCandidateToInternal } from "@/components/pages/candidates/hooks/useCandidatesExecuteSearch"
import type { Candidate } from "@/components/pages/candidates/types"
import type { JobVacancy, EmailTemplate } from "@/services/lia-api"
import { fetchWithRetry, isTransientNetworkError } from "@/services/lia-api/base"

interface UseCandidatesDataOptions {
  /** Propagate the new Set of viewed candidate IDs upward */
  onViewedIdsChange: (updater: (prev: Set<string>) => Set<string>) => void
  /** Sync candidates into the parent state (overridden by search results) */
  onCandidatesChange: (candidates: Candidate[]) => void
  onLoadingChange: (loading: boolean) => void
  /** Propagate fetch error upward so the page can show an error state */
  onErrorChange?: (error: string | null) => void
  candidateIds: string[]
  candidatesEnabled: boolean
}

export function useCandidatesData({
  onViewedIdsChange,
  onCandidatesChange,
  onLoadingChange,
  onErrorChange,
  candidateIds,
  candidatesEnabled,
}: UseCandidatesDataOptions) {
  // ── Base candidate list (F3 source of truth) ──────────────────────────────
  const candidatesListHook = useCandidatesListMapped()

  useEffect(() => {
    onCandidatesChange(candidatesListHook.candidates)
    onLoadingChange(candidatesListHook.loading)
    onErrorChange?.(candidatesListHook.error)
  }, [candidatesListHook.candidates, candidatesListHook.loading, candidatesListHook.error, onCandidatesChange, onLoadingChange, onErrorChange])

  // ── Bulk data requests for visible candidates ─────────────────────────────
  const { dataRequestsMap, getDataRequestForCandidate } = useBulkCandidateDataRequests({
    candidateIds,
    enabled: candidatesEnabled,
  })

  // ── Candidate lists for modal ─────────────────────────────────────────────
  const [candidateListsForModal, setCandidateListsForModal] = useState<
    Array<{ id: string; name: string; color?: string }>
  >([])

  // ── Job vacancies and email templates for bulk actions ────────────────────
  const [bulkJobVacancies, setBulkJobVacancies] = useState<JobVacancy[]>([])
  const [bulkEmailTemplates, setBulkEmailTemplates] = useState<EmailTemplate[]>([])
  const secondaryFetchFailedRef = useRef(false)

  const loadSecondaryData = useCallback(() => {
    secondaryFetchFailedRef.current = false

    liaApi
      .getCandidateLists({ limit: 50 })
      .then(r =>
        r?.items &&
        setCandidateListsForModal(
          r.items.map((l) => ({
            id: l.id,
            name: l.name,
            color: l.color ?? undefined,
          }))
        )
      )
      .catch(() => { setCandidateListsForModal([]); secondaryFetchFailedRef.current = true })

    // Task #728: silence cold-start network failures — they are recoverable
    // on focus re-fetch (see useEffect below) and do NOT need a console.warn
    // that surfaces in the Next.js dev overlay. Real (non-transient) errors
    // are still logged so we don't mask backend regressions.
    const handleSecondaryFailure = (label: string, err: unknown) => {
      secondaryFetchFailedRef.current = true
      if (isTransientNetworkError(err)) return
      const message = err instanceof Error ? err.message : String(err)
      console.warn(`[useCandidatesData] ${label} fetch failed`, message)
    }

    fetchWithRetry('/api/backend-proxy/candidates/viewed')
      .then(async r => {
        if (!r.ok) throw new Error(`viewed ${r.status}`)
        const data = await r.json()
        if (data?.candidate_ids) {
          onViewedIdsChange(() => new Set<string>(data.candidate_ids))
        }
      })
      .catch((err) => handleSecondaryFailure('viewed-candidates', err))

    liaApi.listJobVacancies()
      .then(r =>
        r.items &&
        setBulkJobVacancies(
          r.items.filter((j: JobVacancy) => j.status === 'open' || j.status === 'draft')
        )
      )
      .catch((err) => handleSecondaryFailure('listJobVacancies', err))

    liaApi.listEmailTemplates(undefined, true)
      .then(r => r.items && setBulkEmailTemplates(r.items))
      .catch((err) => handleSecondaryFailure('listEmailTemplates', err))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    loadSecondaryData()
  }, [loadSecondaryData])

  useEffect(() => {
    const onFocus = () => {
      if (secondaryFetchFailedRef.current) {
        loadSecondaryData()
      }
    }
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [loadSecondaryData])

  // ── Mark a candidate as viewed ────────────────────────────────────────────
  const markCandidateAsViewed = async (candidateId: string, source = 'profile') => {
    // Optimistic local mark FIRST: the eye indicator must not depend on the
    // server POST, which 404s for global-sourced (Pearch) candidates not yet in
    // the local DB. Persisting viewed-state server-side is best-effort.
    onViewedIdsChange(prev => new Set([...prev, candidateId]))
    try {
      await fetch(`/api/backend-proxy/candidates/${candidateId}/viewed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source }),
      })
    } catch {}
  }

  // ── Refresh candidates after bulk mutations ───────────────────────────────
  const refreshCandidates = () => {
    onLoadingChange(true)
    liaApi
      .listCandidates(undefined, undefined, 0, 100)
      .then(response => {
        if (response.items?.length > 0) {
          onCandidatesChange(
            response.items.map((c: CandidateLocal) =>
              _mapCandidateToInternal(c as unknown as Record<string, unknown>)
            )
          )
        }
        onLoadingChange(false)
      })
      .catch(() => onLoadingChange(false))
  }

  return {
    candidateListsForModal,
    setCandidateListsForModal,
    bulkJobVacancies,
    bulkEmailTemplates,
    dataRequestsMap,
    getDataRequestForCandidate,
    markCandidateAsViewed,
    refreshCandidates,
    refreshCandidatesList: candidatesListHook.refresh,
  }
}
