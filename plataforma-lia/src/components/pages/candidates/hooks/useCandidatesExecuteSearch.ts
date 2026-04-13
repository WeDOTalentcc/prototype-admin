"use client"

import { liaApi, CandidateLocal } from "@/services/lia-api"
import {
  searchCandidates as searchCandidatesHybrid,
} from "@/lib/api/candidate-search"
import { isGlobalSource } from "@/lib/utils/source-detection"
import type { Candidate } from "@/components/pages/candidates/types"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { ChatMessage } from "./candidates-core"

export type SearchSource = 'local' | 'global' | 'hybrid'

interface PearchSearchOptions {
  searchType: 'fast'
  limit: number
  showEmails: boolean
  showPhoneNumbers: boolean
  highFreshness: boolean
  requireEmails: boolean
  requirePhoneNumbers: boolean
}

interface SearchResults {
  local: Candidate[]
  global: Candidate[]
  localCount: number
  globalCount: number
  query: string
  isLoading: boolean
  showGlobalResults: boolean
  globalDismissed: boolean
  isEnrichingContacts: boolean
}

interface ExecuteSearchDeps {
  searchSource: SearchSource
  pearchSearchOptions: PearchSearchOptions
  searchThreadId: string | undefined
  setSearchThreadId: (id: string | undefined) => void
  hideViewedCandidatesFilter: (candidates: Candidate[]) => Candidate[]
  talentFunnel: { addToHistory: (entry: Record<string, unknown>) => void }
  setCandidates: (c: Candidate[]) => void
  setSearchResults: (v: SearchResults | ((prev: SearchResults) => SearchResults)) => void
  setHasSearchResults: (v: boolean) => void
  setSearchResultsCount: (v: number) => void
  setLocalResultsCount: (v: number) => void
  setPearchResultsCount: (v: number) => void
  setCreditsUsedInSearch: (v: number) => void
  setCreditsRemaining: (fn: (prev: number) => number) => void
  setShowSearchResults: (v: boolean) => void
  setDisplayedResultsCount: (v: number) => void
  setCurrentSearchSource: (s: string) => void
  setHasSearched: (v: boolean) => void
  setLastSearchEntities: (e: ParsedEntities | null) => void
  setLastSearchMetadata: (m: SearchMetadata | undefined) => void
  setLastSearchUsedPearch: (v: boolean) => void
  setSearchExecutionId: (fn: number | ((prev: number) => number)) => void
  setShowExpandGlobalOption: (v: boolean) => void
  setShowExpandedLIA: (v: boolean) => void
  setUserCollapsedLIA: (v: boolean) => void
  setLastSuccessfulQuery: (q: string) => void
  setChatMessages: (fn: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void
  setIsLoading: (v: boolean) => void
  setIsSearchActive: (v: boolean) => void
}

export function mapCandidateToInternal(c: Record<string, unknown>): Candidate {
  const candidateSource = (c.source || 'pearch') as string
  return {
    id: (c.id as string) || `search-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    candidateId: ((c.id as string)?.substring(0, 8).toUpperCase()) || 'CAND',
    name: (c.name as string) || 'Nome não disponível',
    email: (c.email as string) || '',
    phone: (c.phone as string) || '',
    mobile_phone: c.phone as string | undefined,
    current_title: (c.headline as string) || (c.current_title as string) || '',
    current_company: (c.current_company as string) || '',
    current_salary: undefined,
    desired_salary_min: undefined,
    desired_salary_max: undefined,
    location: (c.location as string) || '',
    location_city: (c.location as string)?.split(',')[0]?.trim(),
    location_state: (c.location as string)?.split(',')[1]?.trim(),
    linkedin_url: c.linkedin_url as string | undefined,
    avatar_url: (c.avatar_url as string) || (c.picture_url as string),
    technical_skills: (c.skills as string[]) || [],
    skills: (c.skills as string[]) || [],
    seniority_level: c.seniority_level as string | undefined,
    years_of_experience: (c.years_experience as number) || (c.total_experience_years as number),
    experience: (c.years_experience as number) || (c.total_experience_years as number) || 0,
    position: (c.headline as string) || (c.current_title as string) || '',
    monthlySalary: 0,
    workModel: 'remoto' as const,
    score: c.match_score ? Math.round((c.match_score as number) * 25) : ((c.score as number) || 75),
    contractType: 'CLT' as const,
    linkedin: (c.linkedin_url as string) || '',
    avatar: (c.avatar_url as string) || (c.picture_url as string),
    experiences: (c.experiences as unknown[]) || (c.work_history as unknown[]) || [],
    workHistory: ((c.experiences as Record<string, unknown>[]) || (c.work_history as Record<string, unknown>[]) || []).map((exp: Record<string, unknown>) => ({
      company: (exp.company_info as Record<string, unknown>)?.name as string || (exp.company as string) || '',
      title: (exp.company_roles as Record<string, unknown>[])?.[0]?.title as string || (exp.title as string) || '',
      startDate: (exp.company_roles as Record<string, unknown>[])?.[0]?.start_date as string || (exp.start_date as string) || '',
      endDate: (exp.company_roles as Record<string, unknown>[])?.[0]?.end_date as string || (exp.end_date as string) || '',
      duration: (exp.duration as string) || '',
      location: (exp.company_info as Record<string, unknown>)?.location as string || (exp.location as string) || '',
      description: (exp.company_roles as Record<string, unknown>[])?.[0]?.description as string || (exp.description as string) || '',
    })),
    education: ((c.education as Record<string, unknown>[]) || (c.educations as Record<string, unknown>[]) || []).map((edu: Record<string, unknown>) => ({
      school: (edu.school as string) || '',
      degree: (edu.degree as string) || '',
      field_of_study: (edu.field_of_study as string) || '',
      fieldOfStudy: (edu.field_of_study as string) || '',
      startDate: (edu.start_date as string) || '',
      endDate: (edu.end_date as string) || '',
    })),
    liaAnalysis: {
      score: c.match_score ? Math.round((c.match_score as number) * 25) : ((c.score as number) || 75),
      strengths: c.match_reasoning ? [c.match_reasoning as string] : [],
      concerns: [],
      recommendation: (c.match_reasoning as string) || (c.match_summary as string) || '',
    },
    source: candidateSource,
    contact_source: (c.contact_source as string) || null,
    enrichment_source: (c.enrichment_source as string) || null,
    is_enriching: (c.is_enriching as boolean) || false,
    pearch_profile_id: c.pearch_profile_id as string | undefined,
    has_email: (c.has_email as boolean) ?? true,
    has_phone: (c.has_phone as boolean) ?? true,
    is_opentowork: c.is_opentowork as boolean | undefined,
    is_decision_maker: c.is_decision_maker as boolean | undefined,
    is_top_universities: c.is_top_universities as boolean | undefined,
    is_startup: (c.is_startup as boolean) || ((c.company_info as Record<string, unknown>)?.is_startup as boolean),
    expertise: c.expertise as string | undefined,
    outreach_message: c.outreach_message as string | undefined,
  } as unknown as Candidate
}

export function useCandidatesExecuteSearch(deps: ExecuteSearchDeps) {
  const {
    searchSource, pearchSearchOptions, searchThreadId, setSearchThreadId,
    hideViewedCandidatesFilter, talentFunnel,
    setCandidates, setSearchResults, setHasSearchResults, setSearchResultsCount,
    setLocalResultsCount, setPearchResultsCount, setCreditsUsedInSearch, setCreditsRemaining,
    setShowSearchResults, setDisplayedResultsCount, setCurrentSearchSource, setHasSearched,
    setLastSearchEntities, setLastSearchMetadata, setLastSearchUsedPearch, setSearchExecutionId,
    setShowExpandGlobalOption, setShowExpandedLIA, setUserCollapsedLIA, setLastSuccessfulQuery,
    setChatMessages, setIsLoading, setIsSearchActive,
  } = deps

  const executeSearch = async (
    query: string,
    entities?: ParsedEntities,
    mode?: SearchMode,
    metadata?: SearchMetadata,
    usePearch: boolean = false
  ) => {
    setIsLoading(true)
    setIsSearchActive(true)
    setSearchResults(prev => ({ ...prev, isLoading: true, query }))

    try {
      let mappedCandidates: Candidate[] = []
      let totalCount = 0
      let creditsUsed: number | undefined
      const shouldUsePearch = usePearch || searchSource === 'global'
      const shouldUseHybrid = searchSource === 'hybrid'
      let localCount = 0
      let pearchCount = 0
      let isEnrichingContacts = false

      if (mode === 'similar' && metadata) {
        const similarUrl = metadata.similarProfileUrl || metadata.similarProfileUrls?.[0]
        if (similarUrl) {
          const response = await fetch('/api/backend-proxy/search/candidates/similar', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ linkedin_url: similarUrl, limit: 20, search_pearch: shouldUsePearch || shouldUseHybrid, pearch_type: pearchSearchOptions.searchType })
          })
          if (response.ok) {
            const data = await response.json()
            totalCount = data.total_count || 0; localCount = data.local_count || 0; pearchCount = data.pearch_count || 0; creditsUsed = data.credits_used
            if (data.is_enriching_contacts) isEnrichingContacts = true
            if (data.credits_remaining !== undefined) setCreditsRemaining(() => data.credits_remaining)
            if (data.candidates?.length > 0) mappedCandidates = data.candidates.map((c: Record<string, unknown>) => mapCandidateToInternal(c))
          }
        }
      } else if (mode === 'jd' && metadata?.jobDescription) {
        const response = await fetch('/api/backend-proxy/search/candidates/by-job-description', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ job_description: metadata.jobDescription, limit: 20, search_pearch: shouldUsePearch || shouldUseHybrid, pearch_type: pearchSearchOptions.searchType })
        })
        if (response.ok) {
          const data = await response.json()
          totalCount = data.total_count || 0; localCount = data.local_count || 0; pearchCount = data.pearch_count || 0; creditsUsed = data.credits_used
          if (data.is_enriching_contacts) isEnrichingContacts = true
          if (data.credits_remaining !== undefined) setCreditsRemaining(() => data.credits_remaining)
          if (data.candidates?.length > 0) mappedCandidates = data.candidates.map((c: Record<string, unknown>) => mapCandidateToInternal(c))
        }
      } else if (mode === 'archetypes' && metadata?.archetypeVacancyId) {
        const response = await fetch(`/api/backend-proxy/search/archetypes/${metadata.archetypeVacancyId}/search`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ limit: 20, search_pearch: shouldUsePearch || shouldUseHybrid, pearch_type: pearchSearchOptions.searchType })
        })
        if (response.ok) {
          const data = await response.json()
          totalCount = data.total_count || 0; localCount = data.local_count || 0; pearchCount = data.pearch_count || 0; creditsUsed = data.credits_used
          if (data.is_enriching_contacts) isEnrichingContacts = true
          if (data.credits_remaining !== undefined) setCreditsRemaining(() => data.credits_remaining)
          if (data.candidates?.length > 0) mappedCandidates = data.candidates.map((c: Record<string, unknown>) => mapCandidateToInternal(c))
        }
      } else {
        const searchSpec = entities ? {
          location: entities.location, job_title: entities.job_title, seniority: entities.seniority,
          years_experience: entities.years_experience, skills: entities.skills || [],
          industry: entities.industry, company: entities.company
        } : undefined
        const searchResponse = await searchCandidatesHybrid({
          query, thread_id: searchThreadId, search_spec: searchSpec,
          search_local: true, search_pearch: shouldUsePearch || shouldUseHybrid,
          pearch_type: pearchSearchOptions.searchType, local_limit: 50,
          pearch_limit: shouldUsePearch || shouldUseHybrid ? pearchSearchOptions.limit : 0,
          show_emails: pearchSearchOptions.showEmails,
          show_phone_numbers: pearchSearchOptions.showPhoneNumbers, high_freshness: pearchSearchOptions.highFreshness,
          require_emails: pearchSearchOptions.requireEmails, require_phone_numbers: pearchSearchOptions.requirePhoneNumbers
        })
        if (searchResponse.thread_id) setSearchThreadId(searchResponse.thread_id)
        creditsUsed = searchResponse.credits_used
        if (searchResponse.is_enriching_contacts) isEnrichingContacts = true
        totalCount = searchResponse.total_count || 0; localCount = searchResponse.local_count || 0; pearchCount = searchResponse.pearch_count || 0
        if (searchResponse.credits_remaining !== undefined && searchResponse.credits_remaining !== null) {
          setCreditsRemaining(() => searchResponse.credits_remaining as number)
        }
        if (searchResponse.candidates?.length > 0) {
          mappedCandidates = searchResponse.candidates.map((c) => mapCandidateToInternal(c as unknown as Record<string, unknown>))
        }
      }

      setHasSearched(true)
      setLastSearchEntities(entities || null)
      setLastSearchMetadata(metadata)
      setLastSearchUsedPearch(usePearch || searchSource === 'global' || searchSource === 'hybrid')
      setSearchExecutionId(prev => prev + 1)

      const shouldUsePearchForSource = usePearch || searchSource === 'global'
      const shouldUseHybridForSource = searchSource === 'hybrid'
      if (shouldUsePearchForSource) setCurrentSearchSource('global')
      else if (shouldUseHybridForSource) setCurrentSearchSource('hybrid')
      else setCurrentSearchSource('local')

      talentFunnel.addToHistory({ query, mode: mode || 'natural', source: searchSource, entities, metadata, resultsCount: mappedCandidates.length })

      const localCandidates = mappedCandidates.filter(c => !isGlobalSource(c.source, Boolean(c.pearch_profile_id)))
      const globalCandidates = mappedCandidates.filter(c => isGlobalSource(c.source, Boolean(c.pearch_profile_id)))
      const shouldAutoShowGlobal = shouldUsePearch || shouldUseHybrid
      const candidatesBeforeFilter = shouldAutoShowGlobal ? mappedCandidates : localCandidates
      const candidatesForTable = hideViewedCandidatesFilter(candidatesBeforeFilter)
      const hiddenCandidates = candidatesBeforeFilter.filter(c => !candidatesForTable.some(v => v.id === c.id))
      const hiddenLocalCount = hiddenCandidates.filter(c => !isGlobalSource(c.source, Boolean(c.pearch_profile_id))).length
      const hiddenGlobalCount = hiddenCandidates.filter(c => isGlobalSource(c.source, Boolean(c.pearch_profile_id))).length
      const totalHiddenCount = hiddenLocalCount + hiddenGlobalCount

      setCandidates(candidatesForTable)
      setHasSearchResults(true)
      setSearchResultsCount((totalCount || mappedCandidates.length) - totalHiddenCount)
      setLocalResultsCount(Math.max(0, (localCount > 0 ? localCount : localCandidates.length) - hiddenLocalCount))
      setPearchResultsCount(Math.max(0, (pearchCount > 0 ? pearchCount : globalCandidates.length) - hiddenGlobalCount))
      setCreditsUsedInSearch(creditsUsed || 0)
      setShowSearchResults(true)
      setDisplayedResultsCount(10)

      setSearchResults(prev => ({
        ...prev,
        local: localCandidates, global: globalCandidates,
        localCount: localCount > 0 ? localCount : localCandidates.length,
        globalCount: pearchCount > 0 ? pearchCount : globalCandidates.length,
        query, isLoading: false, showGlobalResults: shouldAutoShowGlobal,
        globalDismissed: prev.globalDismissed,
        isEnrichingContacts,
      }))

      setShowExpandedLIA(true)
      setUserCollapsedLIA(false)
      setLastSuccessfulQuery(query)
      setShowExpandGlobalOption(!shouldUsePearch && !shouldUseHybrid)

      if (mappedCandidates.length > 0) {
        try {
          const analyzeResponse = await fetch('/api/backend-proxy/search/analyze', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query,
              candidates: mappedCandidates.slice(0, 50).map(c => ({
                id: c.id, name: c.name, current_title: c.current_title || c.position,
                current_company: c.current_company, location: c.location || c.location_city,
                skills: c.skills || c.technical_skills, years_experience: c.experience || c.years_of_experience,
                lia_score: c.liaAnalysis?.score || c.score, seniority_level: c.seniority_level,
                work_model: c.workModel, email: c.email, phone: c.phone || c.mobile_phone,
                linkedin_url: c.linkedin_url, source: c.source,
              })),
              local_count: localCount, global_count: pearchCount,
            })
          })
          if (analyzeResponse.ok) {
            const analyticsData = await analyzeResponse.json()
            setChatMessages(prev => [...prev, {
              id: `proactive-insight-${Date.now()}`, type: 'proactive_insight',
              content: '', timestamp: new Date(), analytics: analyticsData,
            }])
          }
        } catch {}
      }
    } catch {
      setSearchResults(prev => ({ ...prev, isLoading: false, query: '' }))
    } finally {
      setIsLoading(false)
      setIsSearchActive(false)
    }
  }

  return { executeSearch, mapCandidateToInternal }
}
