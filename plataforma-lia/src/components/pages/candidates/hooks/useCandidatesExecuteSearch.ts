import { type Dispatch, type SetStateAction } from "react"
import { liaApi, CandidateLocal } from "@/services/lia-api"
import {
  searchCandidates as searchCandidatesHybrid,
} from "@/lib/api/candidate-search"
import { isGlobalSource } from "@/lib/utils/source-detection"
import type { Candidate } from "../types"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { SearchAnalytics } from "@/components/proactive-insight-card"
import type { useTalentFunnel } from "@/hooks/use-talent-funnel"
import type { useHideViewedCandidates } from "@/hooks/useHideViewedCandidates"

type SearchSource = 'local' | 'global' | 'hybrid'

interface ChatMessage {
  id: string
  type: 'user' | 'lia' | 'proactive_insight' | 'calibration'
  content: string
  timestamp: Date
  searchResults?: {
    localCount: number
    globalCount: number
    query: string
  }
  analytics?: SearchAnalytics
  candidates?: Record<string, unknown>[]
  metadata?: {
    action_executed?: boolean
    action_result?: Record<string, unknown>
    action_type?: string
    needs_confirmation?: boolean
    needs_params?: boolean
    pending_action_id?: string
    conversation_id?: string
  }
}

interface SearchResultsState {
  local: Candidate[]
  global: Candidate[]
  localCount: number
  globalCount: number
  query: string
  isLoading: boolean
  showGlobalResults: boolean
  globalDismissed: boolean
}

export interface UseCandidatesExecuteSearchParams {
  setIsLoading: Dispatch<SetStateAction<boolean>>
  setIsSearchActive: Dispatch<SetStateAction<boolean>>
  searchSource: SearchSource
  pearchSearchOptions: {
    searchType: 'fast' | 'pro'
    limit: number
    showEmails: boolean
    showPhoneNumbers: boolean
    highFreshness: boolean
    requireEmails: boolean
    requirePhoneNumbers: boolean
  }
  searchThreadId: string | undefined
  setSearchThreadId: Dispatch<SetStateAction<string | undefined>>
  setCreditsRemaining: Dispatch<SetStateAction<number | undefined>>
  setCandidates: Dispatch<SetStateAction<Candidate[]>>
  setHasSearched: Dispatch<SetStateAction<boolean>>
  setLastSearchEntities: Dispatch<SetStateAction<ParsedEntities | null>>
  setLastSearchMetadata: Dispatch<SetStateAction<SearchMetadata | undefined>>
  setLastSearchUsedPearch: Dispatch<SetStateAction<boolean>>
  setSearchExecutionId: Dispatch<SetStateAction<number>>
  setCurrentSearchSource: Dispatch<SetStateAction<SearchSource>>
  setHasSearchResults: Dispatch<SetStateAction<boolean>>
  setSearchResultsCount: Dispatch<SetStateAction<number>>
  setLocalResultsCount: Dispatch<SetStateAction<number>>
  setPearchResultsCount: Dispatch<SetStateAction<number>>
  setCreditsUsedInSearch: Dispatch<SetStateAction<number>>
  setShowSearchResults: Dispatch<SetStateAction<boolean>>
  setDisplayedResultsCount: Dispatch<SetStateAction<number>>
  setSearchResults: Dispatch<SetStateAction<SearchResultsState>>
  setShowExpandedLIA: Dispatch<SetStateAction<boolean>>
  setUserCollapsedLIA: Dispatch<SetStateAction<boolean>>
  setLastSuccessfulQuery: Dispatch<SetStateAction<string>>
  setShowExpandGlobalOption: Dispatch<SetStateAction<boolean>>
  setChatMessages: Dispatch<SetStateAction<ChatMessage[]>>
  talentFunnel: ReturnType<typeof useTalentFunnel>
  hideViewedCandidates: ReturnType<typeof useHideViewedCandidates>
}

interface WorkHistoryEntry {
  company_info?: { name?: string; location?: string }
  company_roles?: Array<{ title?: string; start_date?: string; end_date?: string; description?: string }>
  company?: string
  title?: string
  start_date?: string
  end_date?: string
  duration?: string
  location?: string
  description?: string
}

interface EducationEntry {
  school?: string
  degree?: string
  field_of_study?: string
  start_date?: string
  end_date?: string
}

export function mapCandidateToInternal(c: Record<string, unknown>): Candidate {
  const cAny = c as Record<string, unknown>
  const candidateSource = (cAny.source as string) || 'pearch'
  const experiences = (cAny.experiences || cAny.work_history || []) as WorkHistoryEntry[]
  const educations = (cAny.education || cAny.educations || []) as EducationEntry[]
  const companyInfo = cAny.company_info as Record<string, unknown> | undefined

  return {
    id: (cAny.id as string) || `search-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    candidateId: (cAny.id as string)?.substring(0, 8).toUpperCase() || 'CAND',
    name: (cAny.name as string) || 'Nome não disponível',
    email: (cAny.email as string) || '',
    phone: (cAny.phone as string) || '',
    mobile_phone: cAny.phone as string | undefined,
    current_title: (cAny.headline as string) || (cAny.current_title as string) || '',
    current_company: (cAny.current_company as string) || '',
    current_salary: undefined,
    desired_salary_min: undefined,
    desired_salary_max: undefined,
    location: (cAny.location as string) || '',
    location_city: (cAny.location as string)?.split(',')[0]?.trim(),
    location_state: (cAny.location as string)?.split(',')[1]?.trim(),
    linkedin_url: cAny.linkedin_url as string | undefined,
    avatar_url: (cAny.avatar_url as string) || (cAny.picture_url as string),
    technical_skills: (cAny.skills as string[]) || [],
    skills: (cAny.skills as string[]) || [],
    seniority_level: cAny.seniority_level as string | undefined,
    years_of_experience: (cAny.years_experience as number) || (cAny.total_experience_years as number),
    experience: (cAny.years_experience as number) || (cAny.total_experience_years as number) || 0,
    position: (cAny.headline as string) || (cAny.current_title as string) || '',
    monthlySalary: 0,
    workModel: 'remoto' as const,
    score: (cAny.match_score as number) ? Math.round((cAny.match_score as number) * 25) : ((cAny.score as number) || 75),
    contractType: 'CLT' as const,
    linkedin: (cAny.linkedin_url as string) || '',
    avatar: (cAny.avatar_url as string) || (cAny.picture_url as string),
    experiences: experiences,
    workHistory: experiences.map((exp) => ({
      company: exp.company_info?.name || exp.company || '',
      title: exp.company_roles?.[0]?.title || exp.title || '',
      startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
      endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
      duration: exp.duration || '',
      location: exp.company_info?.location || exp.location || '',
      description: exp.company_roles?.[0]?.description || exp.description || ''
    })),
    education: educations.map((edu) => ({
      school: edu.school || '',
      degree: edu.degree || '',
      field_of_study: edu.field_of_study || '',
      fieldOfStudy: edu.field_of_study || '',
      startDate: edu.start_date || '',
      endDate: edu.end_date || ''
    })),
    liaAnalysis: {
      score: (cAny.match_score as number) ? Math.round((cAny.match_score as number) * 25) : ((cAny.score as number) || 75),
      strengths: (cAny.match_reasoning as string) ? [(cAny.match_reasoning as string)] : [],
      concerns: [],
      recommendation: (cAny.match_reasoning as string) || (cAny.match_summary as string) || ''
    },
    source: candidateSource,
    pearch_profile_id: cAny.pearch_profile_id as string | undefined,
    has_email: (cAny.has_email as boolean) ?? true,
    has_phone: (cAny.has_phone as boolean) ?? true,
    is_opentowork: cAny.is_opentowork as boolean | undefined,
    is_decision_maker: cAny.is_decision_maker as boolean | undefined,
    is_top_universities: cAny.is_top_universities as boolean | undefined,
    is_startup: (cAny.is_startup as boolean) || (companyInfo?.is_startup as boolean),
    expertise: cAny.expertise as string | undefined,
    outreach_message: cAny.outreach_message as string | undefined
  }
}

export function useCandidatesExecuteSearch(params: UseCandidatesExecuteSearchParams) {
  const {
    setIsLoading, setIsSearchActive, searchSource, pearchSearchOptions,
    searchThreadId, setSearchThreadId, setCreditsRemaining,
    setCandidates, setHasSearched, setLastSearchEntities,
    setLastSearchMetadata, setLastSearchUsedPearch, setSearchExecutionId,
    setCurrentSearchSource, setHasSearchResults, setSearchResultsCount,
    setLocalResultsCount, setPearchResultsCount, setCreditsUsedInSearch,
    setShowSearchResults, setDisplayedResultsCount, setSearchResults,
    setShowExpandedLIA, setUserCollapsedLIA, setLastSuccessfulQuery,
    setShowExpandGlobalOption, setChatMessages, talentFunnel,
    hideViewedCandidates,
  } = params

  const executeSearch = async (
    query: string,
    entities?: ParsedEntities,
    mode?: SearchMode,
    metadata?: SearchMetadata,
    usePearch: boolean = false
  ) => {
    setIsLoading(true)
    setIsSearchActive(true)
    setSearchResults(prev => ({ ...prev, isLoading: true, query: query }))

    try {
      let mappedCandidates: Candidate[] = []
      let totalCount = 0
      let creditsUsed: number | undefined
      const shouldUsePearch = usePearch || searchSource === 'global'
      const shouldUseHybrid = searchSource === 'hybrid'
      let localCount = 0
      let pearchCount = 0

      if (mode === 'similar' && metadata) {
        const similarUrl = metadata.similarProfileUrl || (metadata.similarProfileUrls?.[0])
        if (similarUrl) {
          const response = await fetch('/api/backend-proxy/search/candidates/similar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              linkedin_url: similarUrl, limit: 20,
              search_pearch: shouldUsePearch || shouldUseHybrid,
              pearch_type: pearchSearchOptions.searchType
            })
          })
          if (response.ok) {
            const data = await response.json()
            totalCount = data.total_count || 0
            localCount = data.local_count || 0
            pearchCount = data.pearch_count || 0
            creditsUsed = data.credits_used
            if (data.credits_remaining !== undefined) setCreditsRemaining(data.credits_remaining)
            if (data.candidates?.length > 0) {
              mappedCandidates = data.candidates.map((c: Record<string, unknown>) => mapCandidateToInternal(c))
            }
          }
        }
      } else if (mode === 'jd' && metadata?.jobDescription) {
        const response = await fetch('/api/backend-proxy/search/candidates/by-job-description', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            job_description: metadata.jobDescription, limit: 20,
            search_pearch: shouldUsePearch || shouldUseHybrid,
            pearch_type: pearchSearchOptions.searchType
          })
        })
        if (response.ok) {
          const data = await response.json()
          totalCount = data.total_count || 0
          localCount = data.local_count || 0
          pearchCount = data.pearch_count || 0
          creditsUsed = data.credits_used
          if (data.credits_remaining !== undefined) setCreditsRemaining(data.credits_remaining)
          if (data.candidates?.length > 0) {
            mappedCandidates = data.candidates.map((c: Record<string, unknown>) => mapCandidateToInternal(c))
          }
        }
      } else if (mode === 'archetypes' && metadata?.archetypeVacancyId) {
        const archetypeId = metadata.archetypeVacancyId
        const response = await fetch(`/api/backend-proxy/search/archetypes/${archetypeId}/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            limit: 20,
            search_pearch: shouldUsePearch || shouldUseHybrid,
            pearch_type: pearchSearchOptions.searchType
          })
        })
        if (response.ok) {
          const data = await response.json()
          totalCount = data.total_count || 0
          localCount = data.local_count || 0
          pearchCount = data.pearch_count || 0
          creditsUsed = data.credits_used
          if (data.credits_remaining !== undefined) setCreditsRemaining(data.credits_remaining)
          if (data.candidates?.length > 0) {
            mappedCandidates = data.candidates.map((c: Record<string, unknown>) => mapCandidateToInternal(c))
          }
        }
      } else if (shouldUsePearch || shouldUseHybrid) {
        const searchSpec = entities ? {
          location: entities.location,
          job_title: entities.job_title,
          seniority: entities.seniority,
          years_experience: entities.years_experience,
          skills: entities.skills || [],
          industry: entities.industry,
          company: entities.company
        } : undefined

        const searchResponse = await searchCandidatesHybrid({
          query,
          thread_id: searchThreadId,
          search_spec: searchSpec,
          search_local: shouldUseHybrid,
          search_pearch: true,
          pearch_type: pearchSearchOptions.searchType,
          local_limit: shouldUseHybrid ? 20 : 1,
          pearch_limit: pearchSearchOptions.limit,
          show_emails: pearchSearchOptions.showEmails,
          show_phone_numbers: pearchSearchOptions.showPhoneNumbers,
          high_freshness: pearchSearchOptions.highFreshness,
          require_emails: pearchSearchOptions.requireEmails,
          require_phone_numbers: pearchSearchOptions.requirePhoneNumbers
        })

        if (searchResponse.thread_id) setSearchThreadId(searchResponse.thread_id)
        creditsUsed = searchResponse.credits_used
        totalCount = searchResponse.total_count || 0
        localCount = searchResponse.local_count || 0
        pearchCount = searchResponse.pearch_count || 0
        if (searchResponse.credits_remaining !== undefined && searchResponse.credits_remaining !== null) {
          setCreditsRemaining(searchResponse.credits_remaining)
        }

        if (searchResponse.candidates?.length > 0) {
          mappedCandidates = searchResponse.candidates.map((c) => {
            const candidateSource = c.source || 'pearch'
            const experiences = (c.experiences || c.work_history || []) as WorkHistoryEntry[]
            const educations = (c.education || c.educations || []) as EducationEntry[]
            const companyInfo = c.company_info as Record<string, unknown> | undefined

            return {
              id: c.id || `pearch-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              candidateId: c.id?.substring(0, 8).toUpperCase() || 'PEARCH',
              name: c.name || 'Nome não disponível',
              email: c.email || '',
              phone: c.phone || '',
              mobile_phone: c.phone,
              current_title: c.headline || c.current_title || '',
              current_company: c.current_company || '',
              current_salary: undefined,
              desired_salary_min: undefined,
              desired_salary_max: undefined,
              location: c.location || '',
              location_city: c.location?.split(',')[0]?.trim(),
              location_state: c.location?.split(',')[1]?.trim(),
              linkedin_url: c.linkedin_url,
              avatar_url: c.avatar_url || c.picture_url,
              technical_skills: c.skills || [],
              skills: c.skills || [],
              seniority_level: c.seniority_level,
              years_of_experience: c.years_experience || c.total_experience_years,
              experience: c.years_experience || c.total_experience_years || 0,
              position: c.headline || c.current_title || '',
              monthlySalary: 0,
              workModel: 'remoto' as const,
              score: c.match_score ? Math.round(c.match_score * 25) : 75,
              contractType: 'CLT' as const,
              linkedin: c.linkedin_url || '',
              avatar: c.avatar_url,
              experiences: experiences,
              workHistory: experiences.map((exp) => ({
                company: exp.company_info?.name || exp.company || '',
                title: exp.company_roles?.[0]?.title || exp.title || '',
                startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
                endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
                duration: exp.duration || '',
                location: exp.company_info?.location || exp.location || '',
                description: exp.company_roles?.[0]?.description || exp.description || ''
              })),
              education: educations.map((edu) => ({
                school: edu.school || '',
                degree: edu.degree || '',
                field_of_study: edu.field_of_study || '',
                fieldOfStudy: edu.field_of_study || '',
                startDate: edu.start_date || '',
                endDate: edu.end_date || ''
              })),
              liaAnalysis: {
                score: c.match_score ? Math.round(c.match_score * 25) : 75,
                strengths: c.match_reasoning ? [c.match_reasoning] : [],
                concerns: [],
                recommendation: c.match_reasoning || ''
              },
              source: candidateSource,
              pearch_profile_id: c.pearch_profile_id,
              has_email: c.has_email ?? true,
              has_phone: c.has_phone ?? true,
              is_opentowork: c.is_opentowork,
              is_decision_maker: c.is_decision_maker,
              is_top_universities: c.is_top_universities,
              is_startup: c.is_startup || (companyInfo?.is_startup as boolean),
              expertise: c.expertise,
              outreach_message: c.outreach_message
            }
          })
        }
      } else {
        const response = await liaApi.listCandidates(query, undefined, 0, 50)
        if (response.items?.length > 0) {
          const searchLower = query.toLowerCase()
          const filtered = response.items.filter((c: CandidateLocal) => {
            return (
              c.name?.toLowerCase().includes(searchLower) ||
              c.current_title?.toLowerCase().includes(searchLower) ||
              c.current_company?.toLowerCase().includes(searchLower) ||
              c.location_city?.toLowerCase().includes(searchLower) ||
              c.location_state?.toLowerCase().includes(searchLower) ||
              c.technical_skills?.some((s: string) => s.toLowerCase().includes(searchLower))
            )
          })
          totalCount = filtered.length
          localCount = filtered.length
          pearchCount = 0
          mappedCandidates = filtered.map((c: CandidateLocal) => ({
            id: c.id,
            candidateId: c.id.substring(0, 8).toUpperCase(),
            name: c.name || 'Sem nome',
            email: c.email || '',
            phone: c.phone || '',
            mobile_phone: c.mobile_phone,
            current_title: c.current_title || '',
            current_company: c.current_company || '',
            current_salary: c.current_salary,
            desired_salary_min: c.desired_salary_min,
            desired_salary_max: c.desired_salary_max,
            location: [c.location_city, c.location_state].filter(Boolean).join(', '),
            location_city: c.location_city,
            location_state: c.location_state,
            linkedin_url: c.linkedin_url,
            avatar_url: c.avatar_url || c.picture_url,
            technical_skills: c.technical_skills || [],
            skills: c.technical_skills || [],
            seniority_level: c.seniority_level,
            years_of_experience: c.years_of_experience,
            experience: c.years_of_experience || 0,
            position: c.current_title || '',
            monthlySalary: c.current_salary || 0,
            workModel: (c.work_model_preference || 'remoto') as 'remoto' | 'híbrido' | 'presencial',
            score: c.lia_score || 75,
            contractType: (c.contract_type_preference?.toUpperCase() || 'CLT') as 'CLT' | 'PJ' | 'Freelancer',
            linkedin: c.linkedin_url || '',
            education: c.education || c.educations || [],
            avatar: c.avatar_url || c.picture_url,
            liaAnalysis: {
              score: c.lia_score || 75,
              strengths: c.lia_insights?.strengths || [],
              concerns: c.lia_insights?.concerns || [],
              recommendation: c.lia_insights?.recommendation || ''
            },
            source: 'local',
            tags: c.tags || [],
            notes: c.notes,
            has_email: true,
            has_phone: true,
            is_opentowork: c.is_opentowork,
            is_decision_maker: c.is_decision_maker,
            is_top_universities: c.is_top_universities,
            is_startup: c.is_startup || c.company_info?.is_startup,
            expertise: c.expertise,
            outreach_message: c.outreach_message
          }))
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

      talentFunnel.addToHistory({
        query,
        mode: (mode || 'natural') as 'natural' | 'boolean' | 'similar' | 'jd' | 'archetypes' | 'ai-natural',
        source: searchSource,
        entities,
        metadata,
        resultsCount: mappedCandidates.length
      })

      const localCandidates = mappedCandidates.filter(c => {
        const hasPearchId = Boolean(c.pearch_profile_id)
        return !isGlobalSource(c.source, hasPearchId)
      })
      const globalCandidates = mappedCandidates.filter(c => {
        const hasPearchId = Boolean(c.pearch_profile_id)
        return isGlobalSource(c.source, hasPearchId)
      })

      const shouldAutoShowGlobal = shouldUsePearch || shouldUseHybrid
      const candidatesBeforeFilter = shouldAutoShowGlobal ? mappedCandidates : localCandidates
      const candidatesForTable = hideViewedCandidates.filterCandidates(candidatesBeforeFilter)

      const hiddenCandidates = candidatesBeforeFilter.filter(c => !candidatesForTable.some(visible => visible.id === c.id))
      const hiddenLocalCount = hiddenCandidates.filter(c => !isGlobalSource(c.source, Boolean(c.pearch_profile_id))).length
      const hiddenGlobalCount = hiddenCandidates.filter(c => isGlobalSource(c.source, Boolean(c.pearch_profile_id))).length
      const totalHiddenCount = hiddenLocalCount + hiddenGlobalCount

      setCandidates(candidatesForTable)
      setHasSearchResults(true)
      const baseLocalCount = localCount > 0 ? localCount : localCandidates.length
      const baseGlobalCount = pearchCount > 0 ? pearchCount : globalCandidates.length
      setSearchResultsCount((totalCount || mappedCandidates.length) - totalHiddenCount)
      setLocalResultsCount(Math.max(0, baseLocalCount - hiddenLocalCount))
      setPearchResultsCount(Math.max(0, baseGlobalCount - hiddenGlobalCount))
      setCreditsUsedInSearch(creditsUsed || 0)
      setShowSearchResults(true)
      setDisplayedResultsCount(10)

      setSearchResults(prev => ({
        local: localCandidates,
        global: globalCandidates,
        localCount: localCount > 0 ? localCount : localCandidates.length,
        globalCount: pearchCount > 0 ? pearchCount : globalCandidates.length,
        query: query,
        isLoading: false,
        showGlobalResults: shouldAutoShowGlobal,
        globalDismissed: prev.globalDismissed
      }))

      setShowExpandedLIA(true)
      setUserCollapsedLIA(false)

      const shouldShowLocationTip = !usePearch && !shouldUsePearch && !shouldUseHybrid && globalCandidates.length > 0
      if (shouldShowLocationTip) {
        const hasLocationInQuery = /brasil|brazil|são paulo|sp\b|rio|rj\b|minas|mg\b|curitiba|porto alegre|belo horizonte|recife|salvador|fortaleza|brasília/i.test(query)
        const internationalCountries = [
          'india', 'united states', 'usa', 'uk', 'united kingdom', 'canada', 'germany',
          'france', 'spain', 'portugal', 'australia', 'netherlands', 'italy', 'mexico',
          'argentina', 'colombia', 'chile', 'peru', 'philippines', 'pakistan', 'nigeria'
        ]
        const internationalCandidates = globalCandidates.filter(c => {
          const location = (c.location || c.location_city || '').toLowerCase()
          return internationalCountries.some(country => location.includes(country))
        })
        if (internationalCandidates.length >= 3 && !hasLocationInQuery) {
          const liaMessage: ChatMessage = {
            id: `lia-location-tip-${Date.now()}`,
            type: 'lia',
            content: `💡 **Dica de Localização**\n\nEncontrei candidatos de outros países nos resultados globais.\n\nSe você busca apenas profissionais no **Brasil**, pode refinar a busca adicionando a localização, por exemplo:\n\n• "*${query} em São Paulo*"\n• "*${query} Brasil*"\n\nOu use os **filtros de localização** no painel de busca avançada.`,
            timestamp: new Date()
          }
          setChatMessages(prev => [...prev, liaMessage])
        }
      }

      setLastSuccessfulQuery(query)

      if (!shouldUsePearch && !shouldUseHybrid) setShowExpandGlobalOption(true)
      else setShowExpandGlobalOption(false)

      if (mappedCandidates.length > 0) {
        try {
          const analyzeResponse = await fetch('/api/backend-proxy/search/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query,
              candidates: mappedCandidates.slice(0, 50).map(c => ({
                id: c.id, name: c.name,
                current_title: c.current_title || c.position,
                current_company: c.current_company,
                location: c.location || c.location_city,
                skills: c.skills || c.technical_skills,
                years_experience: c.experience || c.years_of_experience,
                lia_score: c.liaAnalysis?.score || c.score,
                seniority_level: c.seniority_level,
                work_model: c.workModel || c.work_model_preference,
                email: c.email, phone: c.phone || c.mobile_phone,
                linkedin_url: c.linkedin_url, source: c.source
              })),
              local_count: localCount, global_count: pearchCount
            })
          })
          if (analyzeResponse.ok) {
            const analyticsData: SearchAnalytics = await analyzeResponse.json()
            const insightMessage: ChatMessage = {
              id: `lia-insight-${Date.now()}`,
              type: 'proactive_insight',
              content: analyticsData.summary || '',
              timestamp: new Date(),
              analytics: analyticsData
            }
            setChatMessages(prev => [...prev, insightMessage])
          }
        } catch {
          // Analytics is best-effort
        }
      }
    } catch {
      setSearchResults(prev => ({ ...prev, isLoading: false }))
    } finally {
      setIsLoading(false)
      setIsSearchActive(false)
    }
  }

  const handleBulkActionComplete = () => {
    setIsLoading(true)
    liaApi.listCandidates(undefined, undefined, 0, 100)
      .then(response => {
        if (response.items?.length > 0) {
          const backendCandidates: Candidate[] = response.items.map((c: CandidateLocal) => ({
            id: c.id,
            candidateId: c.id.substring(0, 5).toUpperCase(),
            name: c.name || 'Sem nome',
            email: c.email || '',
            phone: c.phone || '',
            position: c.current_title || 'Não informado',
            location: [c.location_city, c.location_state].filter(Boolean).join(', ') || 'Não informado',
            workModel: (c.work_model_preference || 'remoto') as 'remoto' | 'híbrido' | 'presencial',
            score: c.lia_score || 75,
            status: (c.status || 'active') as 'active' | 'prospect' | 'interview' | 'hired',
            currentSalary: c.desired_salary_min ? `R$ ${c.desired_salary_min.toLocaleString('pt-BR')}` : undefined,
            expectedSalary: c.desired_salary_max ? `R$ ${c.desired_salary_max.toLocaleString('pt-BR')}` : undefined,
            contractType: (c.contract_type_preference?.toUpperCase() || 'CLT') as 'CLT' | 'PJ' | 'Freelancer',
            tags: c.tags || [],
            linkedin: c.linkedin_url || '',
            skills: c.technical_skills || [],
            experience: c.years_of_experience || 0,
            education: c.education || c.educations || [],
            notes: c.notes,
            avatar: c.avatar_url || c.picture_url,
            liaAnalysis: {
              score: c.lia_score || 75,
              strengths: c.lia_insights?.strengths || ['Perfil técnico sólido'],
              concerns: c.lia_insights?.concerns || [],
              recommendation: c.lia_insights?.recommendation || 'Avaliar com atenção'
            },
            source: 'local',
            has_email: true,
            has_phone: true
          }))
          setCandidates(backendCandidates)
        }
        setIsLoading(false)
      })
      .catch(() => { setIsLoading(false) })
  }

  return { executeSearch, handleBulkActionComplete }
}
