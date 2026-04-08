// useCandidatesData.ts
// Data-fetching sub-hook: initial candidate load, bulk data requests,
// viewed-candidate tracking, and ancillary list/vacancy loading.
// Pure React — no Next.js router/navigation dependencies.

import { useState, useEffect } from "react"
import { liaApi, CandidateLocal } from "@/services/lia-api"
import { useCandidatesListMapped } from "@/hooks/use-candidates-list-mapped"
import { useBulkCandidateDataRequests } from "@/hooks/use-candidate-data-requests"
import { mapCandidateToInternal as _mapCandidateToInternal } from "@/components/pages/candidates/hooks/useCandidatesExecuteSearch"
import type { Candidate } from "@/components/pages/candidates/types"
import type { JobVacancy, EmailTemplate } from "@/services/lia-api"

interface UseCandidatesDataOptions {
  /** Propagate the new Set of viewed candidate IDs upward */
  onViewedIdsChange: (updater: (prev: Set<string>) => Set<string>) => void
  /** Sync candidates into the parent state (overridden by search results) */
  onCandidatesChange: (candidates: Candidate[]) => void
  onLoadingChange: (loading: boolean) => void
  candidateIds: string[]
  candidatesEnabled: boolean
}

export function useCandidatesData({
  onViewedIdsChange,
  onCandidatesChange,
  onLoadingChange,
  candidateIds,
  candidatesEnabled,
}: UseCandidatesDataOptions) {
  // ── Base candidate list (F3 source of truth) ──────────────────────────────
  const candidatesListHook = useCandidatesListMapped()

  useEffect(() => {
    onCandidatesChange(candidatesListHook.candidates)
    onLoadingChange(candidatesListHook.loading)
  }, [candidatesListHook.candidates, candidatesListHook.loading, onCandidatesChange, onLoadingChange])

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

  useEffect(() => {
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
      .catch(() => setCandidateListsForModal([]))

    fetch('/api/backend-proxy/candidates/viewed')
      .then(r => (r.ok ? r.json() : null))
      .then(data => {
        if (data?.candidate_ids) {
          onViewedIdsChange(() => new Set<string>(data.candidate_ids))
        }
      })
      .catch(() => {})
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // intentional: runs once on mount to fetch viewed candidates; onViewedIdsChange is a setState - stable but adding it could cause re-runs

  useEffect(() => {
    liaApi
      .listJobVacancies()
      .then(r =>
        r.items &&
        setBulkJobVacancies(
          r.items.filter((j: JobVacancy) => j.status === 'open' || j.status === 'draft')
        )
      )
      .catch(() => {})
    liaApi
      .listEmailTemplates(undefined, true)
      .then(r => r.items && setBulkEmailTemplates(r.items))
      .catch(() => {})
  }, [])

  // ── Mark a candidate as viewed ────────────────────────────────────────────
  const markCandidateAsViewed = async (candidateId: string, source = 'profile') => {
    try {
      await fetch(`/api/backend-proxy/candidates/${candidateId}/viewed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source }),
      })
      onViewedIdsChange(prev => new Set([...prev, candidateId]))
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
  }
}
