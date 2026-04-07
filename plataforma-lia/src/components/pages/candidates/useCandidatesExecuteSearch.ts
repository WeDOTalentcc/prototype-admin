import { liaApi, CandidateLocal } from "@/services/lia-api"
import {
  searchCandidates as searchCandidatesHybrid,
} from "@/lib/api/candidate-search"
import { isGlobalSource } from "@/lib/utils/source-detection"
import type { Candidate } from "./types"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { SearchAnalytics } from "@/components/proactive-insight-card"

type SearchSource = 'local' | 'global' | 'hybrid'

type RawExperience = {
  company_info?: { name?: string; location?: string; is_startup?: boolean }
  company_roles?: Array<{ title?: string; start_date?: string; end_date?: string; description?: string }>
  company?: string
  title?: string
  start_date?: string
  end_date?: string
  duration?: string
  location?: string
  description?: string
}

type RawEducation = {
  school?: string
  degree?: string
  field_of_study?: string
  start_date?: string
  end_date?: string
}

type RawCandidate = {
  id?: string
  name?: string
  email?: string
  phone?: string
  mobile_phone?: string
  headline?: string
  current_title?: string
  current_company?: string
  location?: string
  location_city?: string
  skills?: string[]
  seniority_level?: string
  years_experience?: number
  total_experience_years?: number
  avatar_url?: string
  picture_url?: string
  linkedin_url?: string
  match_score?: number
  match_reasoning?: string
  match_summary?: string
  score?: number
  experiences?: RawExperience[]
  work_history?: RawExperience[]
  education?: RawEducation[]
  educations?: RawEducation[]
  source?: string
  pearch_profile_id?: string
  has_email?: boolean
  has_phone?: boolean
  is_opentowork?: boolean
  is_decision_maker?: boolean
  is_top_universities?: boolean
  is_startup?: boolean
  company_info?: { is_startup?: boolean }
  expertise?: string[]
  outreach_message?: string
}

type ChatMessage = {
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
  candidates?: Candidate[]
  metadata?: Record<string, unknown>
}

export function mapCandidateToInternal(c: RawCandidate): Candidate {
  const candidateSource = c.source || 'pearch'
  return {
    id: c.id || `search-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    candidateId: c.id?.substring(0, 8).toUpperCase() || 'CAND',
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
    score: c.match_score ? Math.round(c.match_score * 25) : (c.score || 75),
    contractType: 'CLT' as const,
    linkedin: c.linkedin_url || '',
    avatar: c.avatar_url || c.picture_url,
    experiences: c.experiences || c.work_history || [],
    workHistory: (c.experiences || c.work_history || []).map((exp: RawExperience) => ({
      company: exp.company_info?.name || exp.company || '',
      title: exp.company_roles?.[0]?.title || exp.title || '',
      startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
      endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
      duration: exp.duration || '',
      location: exp.company_info?.location || exp.location || '',
      description: exp.company_roles?.[0]?.description || exp.description || ''
    })),
    education: (c.education || c.educations || []).map((edu: RawEducation) => ({
      school: edu.school || '',
      degree: edu.degree || '',
      field_of_study: edu.field_of_study || '',
      fieldOfStudy: edu.field_of_study || '',
      startDate: edu.start_date || '',
      endDate: edu.end_date || ''
    })),
    liaAnalysis: {
      score: c.match_score ? Math.round(c.match_score * 25) : (c.score || 75),
      strengths: c.match_reasoning ? [c.match_reasoning] : [],
      concerns: [],
      recommendation: c.match_reasoning || c.match_summary || ''
    },
    source: candidateSource,
    pearch_profile_id: c.pearch_profile_id,
    has_email: c.has_email ?? true,
    has_phone: c.has_phone ?? true,
    is_opentowork: c.is_opentowork,
    is_decision_maker: c.is_decision_maker,
    is_top_universities: c.is_top_universities,
    is_startup: c.is_startup || c.company_info?.is_startup,
    expertise: c.expertise,
    outreach_message: c.outreach_message
  }
}

export interface ExecuteSearchDeps {
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
  hideViewedCandidates: { filterCandidates: (candidates: Candidate[]) => Candidate[] }
  talentFunnel: { addToHistory: (item: Record<string, unknown>) => void }
  setIsLoading: (v: boolean) => void
  setIsSearchActive: (v: boolean) => void
  setSearchResults: (fn: (prev: Record<string, unknown>) => Record<string, unknown>) => void
  setCreditsRemaining: (v: number) => void
  setCandidates: (v: Candidate[]) => void
  setHasSearchResults: (v: boolean) => void
  setSearchResultsCount: (v: number) => void
  setLocalResultsCount: (v: number) => void
  setPearchResultsCount: (v: number) => void
  setCreditsUsedInSearch: (v: number) => void
  setShowSearchResults: (v: boolean) => void
  setDisplayedResultsCount: (v: number) => void
  setLastSearchEntities: (v: ParsedEntities | null | undefined) => void
  setLastSearchMetadata: (v: SearchMetadata | undefined) => void
  setLastSearchUsedPearch: (v: boolean) => void
  setSearchExecutionId: (fn: (prev: number) => number) => void
  setCurrentSearchSource: (v: string) => void
  setShowExpandGlobalOption: (v: boolean) => void
  setHasSearched: (v: boolean) => void
  setLastSuccessfulQuery: (v: string) => void
  setChatMessages: (fn: (prev: ChatMessage[]) => ChatMessage[]) => void
  setShowExpandedLIA: (v: boolean) => void
  setUserCollapsedLIA: (v: boolean) => void
  setSearchThreadId: (v: string | undefined) => void
}

export function createExecuteSearch(deps: ExecuteSearchDeps) {
  return async function executeSearch(
    query: string,
    entities?: ParsedEntities | null,
    mode?: SearchMode,
    metadata?: SearchMetadata,
    usePearch: boolean = false
  ) {
    deps.setIsLoading(true)
    deps.setIsSearchActive(true)

    deps.setSearchResults((prev) => ({
      ...prev,
      isLoading: true,
      query: query
    }))

    try {
      let mappedCandidates: Candidate[] = []
      let totalCount = 0
      let creditsUsed: number | undefined

      const shouldUsePearch = usePearch || deps.searchSource === 'global'
      const shouldUseHybrid = deps.searchSource === 'hybrid'

      let localCount = 0
      let pearchCount = 0

      if (mode === 'similar' && metadata) {
        const similarUrl = metadata.similarProfileUrl || (metadata.similarProfileUrls?.[0])
        if (similarUrl) {
          const response = await fetch('/api/backend-proxy/search/candidates/similar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              linkedin_url: similarUrl,
              limit: 20,
              search_pearch: shouldUsePearch || shouldUseHybrid,
              pearch_type: deps.pearchSearchOptions.searchType
            })
          })
          if (response.ok) {
            const data = await response.json()
            totalCount = data.total_count || 0
            localCount = data.local_count || 0
            pearchCount = data.pearch_count || 0
            creditsUsed = data.credits_used
            if (data.credits_remaining !== undefined) deps.setCreditsRemaining(data.credits_remaining)
            if (data.candidates?.length > 0) {
              mappedCandidates = data.candidates.map((c: RawCandidate) => mapCandidateToInternal(c))
            }
          }
        }
      } else if (mode === 'jd' && metadata?.jobDescription) {
        const response = await fetch('/api/backend-proxy/search/candidates/by-job-description', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            job_description: metadata.jobDescription,
            limit: 20,
            search_pearch: shouldUsePearch || shouldUseHybrid,
            pearch_type: deps.pearchSearchOptions.searchType
          })
        })
        if (response.ok) {
          const data = await response.json()
          totalCount = data.total_count || 0
          localCount = data.local_count || 0
          pearchCount = data.pearch_count || 0
          creditsUsed = data.credits_used
          if (data.credits_remaining !== undefined) deps.setCreditsRemaining(data.credits_remaining)
          if (data.candidates?.length > 0) {
            mappedCandidates = data.candidates.map((c: RawCandidate) => mapCandidateToInternal(c))
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
            pearch_type: deps.pearchSearchOptions.searchType
          })
        })
        if (response.ok) {
          const data = await response.json()
          totalCount = data.total_count || 0
          localCount = data.local_count || 0
          pearchCount = data.pearch_count || 0
          creditsUsed = data.credits_used
          if (data.credits_remaining !== undefined) deps.setCreditsRemaining(data.credits_remaining)
          if (data.candidates?.length > 0) {
            mappedCandidates = data.candidates.map((c: RawCandidate) => mapCandidateToInternal(c))
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
          thread_id: deps.searchThreadId,
          search_spec: searchSpec,
          search_local: shouldUseHybrid,
          search_pearch: true,
          pearch_type: deps.pearchSearchOptions.searchType,
          local_limit: shouldUseHybrid ? 20 : 1,
          pearch_limit: deps.pearchSearchOptions.limit,
          show_emails: deps.pearchSearchOptions.showEmails,
          show_phone_numbers: deps.pearchSearchOptions.showPhoneNumbers,
          high_freshness: deps.pearchSearchOptions.highFreshness,
          require_emails: deps.pearchSearchOptions.requireEmails,
          require_phone_numbers: deps.pearchSearchOptions.requirePhoneNumbers
        })

        if (searchResponse.thread_id) deps.setSearchThreadId(searchResponse.thread_id)

        creditsUsed = searchResponse.credits_used
        totalCount = searchResponse.total_count || 0
        localCount = searchResponse.local_count || 0
        pearchCount = searchResponse.pearch_count || 0

        if (searchResponse.credits_remaining !== undefined && searchResponse.credits_remaining !== null) {
          deps.setCreditsRemaining(searchResponse.credits_remaining)
        }

        if (searchResponse.candidates?.length > 0) {
          mappedCandidates = searchResponse.candidates.map((c: RawCandidate) => {
            const candidateSource = c.source || 'pearch'
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
              experiences: c.experiences || c.work_history || [],
              workHistory: (c.experiences || c.work_history || []).map((exp: RawExperience) => ({
                company: exp.company_info?.name || exp.company || '',
                title: exp.company_roles?.[0]?.title || exp.title || '',
                startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
                endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
                duration: exp.duration || '',
                location: exp.company_info?.location || exp.location || '',
                description: exp.company_roles?.[0]?.description || exp.description || ''
              })),
              education: (c.education || c.educations || []).map((edu: RawEducation) => ({
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
              is_startup: c.is_startup || c.company_info?.is_startup,
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
            mobile_phone: c.mobile_phone ?? undefined,
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

      deps.setHasSearched(true)
      deps.setLastSearchEntities(entities || null)
      deps.setLastSearchMetadata(metadata)
      deps.setLastSearchUsedPearch(usePearch || deps.searchSource === 'global' || deps.searchSource === 'hybrid')
      deps.setSearchExecutionId(prev => prev + 1)

      const shouldUsePearchForSource = usePearch || deps.searchSource === 'global'
      const shouldUseHybridForSource = deps.searchSource === 'hybrid'
      if (shouldUsePearchForSource) {
        deps.setCurrentSearchSource('global')
      } else if (shouldUseHybridForSource) {
        deps.setCurrentSearchSource('hybrid')
      } else {
        deps.setCurrentSearchSource('local')
      }

      deps.talentFunnel.addToHistory({
        query,
        mode: (mode || 'natural') as SearchMode,
        source: deps.searchSource,
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

      const candidatesBeforeFilter = shouldAutoShowGlobal
        ? mappedCandidates
        : localCandidates

      const candidatesForTable = deps.hideViewedCandidates.filterCandidates(candidatesBeforeFilter)

      const hiddenCandidates = candidatesBeforeFilter.filter(c => !candidatesForTable.some(visible => visible.id === c.id))
      const hiddenLocalCount = hiddenCandidates.filter(c => {
        const hasPearchId = Boolean(c.pearch_profile_id)
        return !isGlobalSource(c.source, hasPearchId)
      }).length
      const hiddenGlobalCount = hiddenCandidates.filter(c => {
        const hasPearchId = Boolean(c.pearch_profile_id)
        return isGlobalSource(c.source, hasPearchId)
      }).length
      const totalHiddenCount = hiddenLocalCount + hiddenGlobalCount

      deps.setCandidates(candidatesForTable)
      deps.setHasSearchResults(true)
      const baseLocalCount = localCount > 0 ? localCount : localCandidates.length
      const baseGlobalCount = pearchCount > 0 ? pearchCount : globalCandidates.length
      deps.setSearchResultsCount((totalCount || mappedCandidates.length) - totalHiddenCount)
      deps.setLocalResultsCount(Math.max(0, baseLocalCount - hiddenLocalCount))
      deps.setPearchResultsCount(Math.max(0, baseGlobalCount - hiddenGlobalCount))
      deps.setCreditsUsedInSearch(creditsUsed || 0)
      deps.setShowSearchResults(true)
      deps.setDisplayedResultsCount(10)

      deps.setSearchResults((prev) => ({
        local: localCandidates,
        global: globalCandidates,
        localCount: localCount > 0 ? localCount : localCandidates.length,
        globalCount: pearchCount > 0 ? pearchCount : globalCandidates.length,
        query: query,
        isLoading: false,
        showGlobalResults: shouldAutoShowGlobal,
        globalDismissed: prev.globalDismissed
      }))

      deps.setShowExpandedLIA(true)
      deps.setUserCollapsedLIA(false)

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
          deps.setChatMessages(prev => [...prev, liaMessage])
        }
      }

      deps.setLastSuccessfulQuery(query)

      if (!shouldUsePearch && !shouldUseHybrid) {
        deps.setShowExpandGlobalOption(true)
      } else {
        deps.setShowExpandGlobalOption(false)
      }

      if (mappedCandidates.length > 0) {
        try {
          const analyzeResponse = await fetch('/api/backend-proxy/search/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query,
              candidates: mappedCandidates.slice(0, 50).map(c => ({
                id: c.id,
                name: c.name,
                current_title: c.current_title || c.position,
                current_company: c.current_company,
                location: c.location || c.location_city,
                skills: c.skills || c.technical_skills,
                years_experience: c.experience || c.years_of_experience,
                lia_score: c.liaAnalysis?.score || c.score,
                seniority_level: c.seniority_level,
                work_model: c.workModel || c.work_model_preference,
                email: c.email,
                phone: c.phone || c.mobile_phone,
                linkedin_url: c.linkedin_url,
                source: c.source
              })),
              local_count: localCount,
              global_count: pearchCount
            })
          })

          if (analyzeResponse.ok) {
            const analyticsData: SearchAnalytics = await analyzeResponse.json()

            const insightMessage: ChatMessage = {
              id: `proactive-insight-${Date.now()}`,
              type: 'proactive_insight',
              content: '',
              timestamp: new Date(),
              analytics: analyticsData
            }
            deps.setChatMessages(prev => [...prev, insightMessage])
          }
        } catch (analyzeError) {
        }
      }
    } catch (error) {
      deps.setSearchResults((prev) => ({
        ...prev,
        isLoading: false,
        query: ''
      }))
    } finally {
      deps.setIsLoading(false)
      deps.setIsSearchActive(false)
    }
  }
}
