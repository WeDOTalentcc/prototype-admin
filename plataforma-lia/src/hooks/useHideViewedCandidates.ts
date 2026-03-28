"use client"

import { useState, useCallback, useMemo } from "react"
import { 
  HideViewedScope, 
  HideViewedPeriod 
} from "@/components/search/advanced-filters-modal"

export interface HideViewedFilter {
  scope: HideViewedScope
  period: HideViewedPeriod
  enabled: boolean
}

export interface ViewedCandidateRecord {
  candidateId: string
  viewedAt: Date
  viewedBy: string
  projectId?: string
  companyId?: string
  isShortlisted?: boolean
}

interface UseHideViewedCandidatesProps {
  userId?: string
  companyId?: string
  projectId?: string
  userEmail?: string
}

interface UseHideViewedCandidatesReturn {
  filter: HideViewedFilter
  setScope: (scope: HideViewedScope) => void
  setPeriod: (period: HideViewedPeriod) => void
  viewedCandidateIds: string[]
  isLoading: boolean
  fetchViewedCandidates: () => Promise<void>
  filterCandidates: <T extends { id: string }>(candidates: T[]) => T[]
  hiddenCount: number
}

function getPeriodStartDate(period: HideViewedPeriod): Date | null {
  const now = new Date()
  
  switch (period) {
    case "all_time":
      return null
    case "last_24h":
      return new Date(now.getTime() - 24 * 60 * 60 * 1000)
    case "last_2_weeks":
      return new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000)
    case "last_3_months":
      return new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)
    case "last_6_months":
      return new Date(now.getTime() - 180 * 24 * 60 * 60 * 1000)
    default:
      return null
  }
}

export function useHideViewedCandidates({
  userId,
  companyId,
  projectId,
  userEmail
}: UseHideViewedCandidatesProps = {}): UseHideViewedCandidatesReturn {
  const [filter, setFilter] = useState<HideViewedFilter>({
    scope: "dont_hide",
    period: "all_time",
    enabled: false
  })
  
  const [viewedCandidateIds, setViewedCandidateIds] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [lastFetchParams, setLastFetchParams] = useState<string>("")

  const setScope = useCallback((scope: HideViewedScope) => {
    setFilter(prev => ({
      ...prev,
      scope,
      enabled: scope !== "dont_hide"
    }))
  }, [])

  const setPeriod = useCallback((period: HideViewedPeriod) => {
    setFilter(prev => ({
      ...prev,
      period
    }))
  }, [])

  const fetchViewedCandidates = useCallback(async () => {
    if (filter.scope === "dont_hide") {
      setViewedCandidateIds([])
      return
    }

    const fetchParams = JSON.stringify({ 
      scope: filter.scope, 
      period: filter.period, 
      userId, 
      companyId, 
      projectId,
      userEmail 
    })
    
    if (fetchParams === lastFetchParams && viewedCandidateIds.length > 0) {
      return
    }

    setIsLoading(true)
    
    try {
      const response = await fetch('/api/backend-proxy/candidates/viewed/filtered', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scope: filter.scope,
          period: filter.period,
          user_id: userId,
          company_id: companyId,
          project_id: projectId,
          user_email: userEmail
        })
      })

      if (response.ok) {
        const data = await response.json()
        setViewedCandidateIds(data.candidate_ids || [])
        setLastFetchParams(fetchParams)
      } else {
        setViewedCandidateIds([])
      }
    } catch (error) {
      setViewedCandidateIds([])
    } finally {
      setIsLoading(false)
    }
  }, [filter.scope, filter.period, userId, companyId, projectId, userEmail, lastFetchParams, viewedCandidateIds.length])

  const filterCandidates = useCallback(<T extends { id: string }>(candidates: T[]): T[] => {
    if (!filter.enabled || viewedCandidateIds.length === 0) {
      return candidates
    }

    const viewedSet = new Set(viewedCandidateIds)
    return candidates.filter(candidate => !viewedSet.has(candidate.id))
  }, [filter.enabled, viewedCandidateIds])

  const hiddenCount = useMemo(() => {
    return viewedCandidateIds.length
  }, [viewedCandidateIds])

  return {
    filter,
    setScope,
    setPeriod,
    viewedCandidateIds,
    isLoading,
    fetchViewedCandidates,
    filterCandidates,
    hiddenCount
  }
}

export default useHideViewedCandidates
