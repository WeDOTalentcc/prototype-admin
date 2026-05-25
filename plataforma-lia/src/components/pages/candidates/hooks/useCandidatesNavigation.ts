"use client"

// useCandidatesNavigation.ts
// Owns all side-effects that react to URL params and
// navigation store tokens. No business logic — pure effect wiring.

import { useEffect } from "react"
import { useSearchParams } from "next/navigation"
import { useNavigationStore } from "@/stores/navigation-store"
import type { Candidate } from "@/components/pages/candidates/types"
import type { ParsedEntities } from "@/components/search/smart-search-input"
import type { TableFilters } from "@/hooks/candidates/use-candidate-filters"
import { getInitialDisplayedResultsCount } from '@/stores/candidates-store'

interface UseCandidatesNavigationParams {
  // View state setters
  setPreviewCandidate: (c: Candidate | null) => void
  setShowCandidatePreview: (v: boolean) => void
  // Search state
  activeTab: string
  lastSearchQuery: string
  searchSource: string
  setSearchSource: (s: 'local' | 'global' | 'hybrid') => void
  searchExecutionId: number
  lastSearchEntities: ParsedEntities | null | undefined
  setTableFilters: (fn: (prev: TableFilters) => TableFilters) => void
  // Candidates list
  candidates: Candidate[]
  // Pending candidate from props
  pendingCandidateOpen?: { candidateId: string } | null
  onCandidateOpened?: () => void
  // Derived
  showGlobalSearchOptions: boolean
  // Search state setters
  setShowSearchResults: (v: boolean) => void
  setDisplayedResultsCount: (v: number) => void
  setActiveTab: (v: 'search' | 'favorites' | 'lists' | 'history' | 'saved-searches' | 'agents') => void
  // Cross-tab filter setters
  setCrossTabFilter: (v: Record<string, unknown> | null) => void
  setShowCrossTabBanner: (v: boolean) => void
  setSearchTerm: (v: string) => void
  setQuickFilters: (v: Set<string>) => void
}

export function useCandidatesNavigation({
  setPreviewCandidate,
  setShowCandidatePreview,
  activeTab,
  lastSearchQuery,
  searchSource,
  setSearchSource,
  searchExecutionId,
  lastSearchEntities,
  setTableFilters,
  candidates,
  pendingCandidateOpen,
  onCandidateOpened,
  showGlobalSearchOptions,
  setShowSearchResults,
  setDisplayedResultsCount,
  setActiveTab,
  setCrossTabFilter,
  setShowCrossTabBanner,
  setSearchTerm,
  setQuickFilters,
}: UseCandidatesNavigationParams) {
  const searchParams = useSearchParams()
  const expandedSearchParam = searchParams.get('expandedSearch')
  const saveTalentFunnelState = useNavigationStore(s => s.saveTalentFunnelState)

  // Persist tab + search query to funnel state
  useEffect(() => {
    if (activeTab === 'search' || activeTab === 'favorites' || activeTab === 'lists') {
      saveTalentFunnelState(activeTab, lastSearchQuery)
    }
  }, [activeTab, lastSearchQuery, saveTalentFunnelState])

  // Restrict search source when global search is disabled
  useEffect(() => {
    if (!showGlobalSearchOptions && (searchSource === 'hybrid' || searchSource === 'global')) {
      setSearchSource('local')
    }
  }, [showGlobalSearchOptions, searchSource, setSearchSource])

  // Honour ?expandedSearch=true URL param
  useEffect(() => {
    if (expandedSearchParam === 'true') {
      setShowSearchResults(true)
      setDisplayedResultsCount(getInitialDisplayedResultsCount())
      setActiveTab('search')
    }
  }, [expandedSearchParam, setShowSearchResults, setDisplayedResultsCount, setActiveTab])

  const consumeNavigateToRecentCandidate = useNavigationStore(s => s.consumeNavigateToRecentCandidate)

  useEffect(() => {
    if (!candidates.length) return
    const nav = consumeNavigateToRecentCandidate()
    if (!nav) return
    const found = nav.candidateId && candidates.find(c => c.id === nav.candidateId)
    if (found) { setPreviewCandidate(found); setShowCandidatePreview(true) }
  }, [candidates, setPreviewCandidate, setShowCandidatePreview, consumeNavigateToRecentCandidate])

  // Open a pending candidate passed via prop
  useEffect(() => {
    if (pendingCandidateOpen && candidates.length > 0) {
      const found = candidates.find(c => c.id === pendingCandidateOpen.candidateId)
      if (found) { setPreviewCandidate(found); setShowCandidatePreview(true) }
      onCandidateOpened?.()
    }
  }, [pendingCandidateOpen, candidates, onCandidateOpened, setPreviewCandidate, setShowCandidatePreview])

  // Auto-populate tableFilters from entities returned by the last search
  useEffect(() => {
    if (searchExecutionId > 0) {
      const e = lastSearchEntities
      const yearsExp = e?.years_experience
      const parsedYears = typeof yearsExp === 'string' ? parseInt(yearsExp, 10) : yearsExp
      setTableFilters(prev => ({
        ...prev,
        locations: e?.location ? [e.location] : [],
        jobTitles: e?.job_title ? [e.job_title] : [],
        skills: e?.skills?.length ? e.skills : [],
        industries: e?.industry ? [e.industry] : [],
        seniorityLevels: e?.seniority ? [e.seniority] : [],
        minExperience: parsedYears !== undefined && !isNaN(parsedYears) ? parsedYears : undefined,
        companies: e?.company ? [e.company] : [],
      }))
    }
  }, [searchExecutionId, lastSearchEntities, setTableFilters])

  const consumeCandidatesFilterData = useNavigationStore(s => s.consumeCandidatesFilterData)

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const tabParam = urlParams.get('tab')
    const filterParam = urlParams.get('filter')
    const companyParam = urlParams.get('name') || urlParams.get('companies')
    const filterData = consumeCandidatesFilterData()

    if (filterData) {
      setCrossTabFilter(filterData as Record<string, unknown>)
      setShowCrossTabBanner(true)
      if (filterData.type === 'company' && filterData.company) {
        setSearchTerm(`empresa:"${filterData.company}"`)
        setQuickFilters(new Set(['company_filter']))
      }
    } else if (tabParam === 'candidates' && filterParam === 'company' && companyParam) {
      const companies = companyParam.split(',')
      setCrossTabFilter({ type: 'company', companies, source: 'url' })
      setShowCrossTabBanner(true)
      setSearchTerm(`empresas:${companies.join(',')}`)
    }
  }, [setCrossTabFilter, setShowCrossTabBanner, setSearchTerm, setQuickFilters, consumeCandidatesFilterData])
}
