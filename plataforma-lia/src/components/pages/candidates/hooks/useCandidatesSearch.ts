"use client"

import type React from "react"
import {
  searchCandidates as searchCandidatesHybrid,
} from "@/lib/api/candidate-search"
import { isGlobalSource } from "@/lib/utils/source-detection"
import type { Candidate } from "../types"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { SearchAnalytics } from "@/components/proactive-insight-card"
import { toast } from "sonner"
import { LOAD_MORE_STEP } from '@/stores/candidates-store'

export type PendingSearchRequest = {
  query: string
  entities?: ParsedEntities
  mode?: SearchMode
  metadata?: SearchMetadata
} | null

export interface CandidatesSearchContext {
  candidates: Candidate[]
  setCandidates: (v: Candidate[] | ((prev: Candidate[]) => Candidate[])) => void
  searchResults: {
    local: Candidate[]
    global: Candidate[]
    localCount: number
    globalCount: number
    query: string
    isLoading: boolean
    showGlobalResults: boolean
    globalDismissed: boolean
    isEnrichingContacts: boolean
    filteredNoContact: number
    enrichmentAttempted: number
  }
  setSearchResults: (v: CandidatesSearchContext['searchResults'] | ((prev: CandidatesSearchContext['searchResults']) => CandidatesSearchContext['searchResults'])) => void
  searchTerm: string
  lastSearchQuery: string
  lastSearchEntities: ParsedEntities | null
  lastSearchMode: string
  lastSearchMetadata: SearchMetadata | undefined
  lastSearchUsedPearch: boolean
  searchSource: 'local' | 'hybrid' | 'global'
  setSearchSource: (v: 'local' | 'hybrid' | 'global') => void
  currentSearchSource: 'local' | 'global' | 'hybrid'
  setCurrentSearchSource: (v: 'local' | 'global' | 'hybrid') => void
  openCreditModals: { hybrid: boolean; global: boolean; email: boolean; phone: boolean }
  setOpenCreditModals: (v: CandidatesSearchContext['openCreditModals'] | ((prev: CandidatesSearchContext['openCreditModals']) => CandidatesSearchContext['openCreditModals'])) => void
  pearchSearchOptions: {
    searchType: 'fast'
    limit: number
    showEmails: boolean
    showPhoneNumbers: boolean
    highFreshness: boolean
    requireEmails: boolean
    requirePhoneNumbers: boolean
  }
  setPearchSearchOptions: (v: CandidatesSearchContext['pearchSearchOptions'] | ((prev: CandidatesSearchContext['pearchSearchOptions']) => CandidatesSearchContext['pearchSearchOptions'])) => void
  creditsRemaining: number | null
  setCreditsRemaining: (v: number | null) => void
  creditsUsedInSearch: number
  setCreditsUsedInSearch: (v: number) => void
  pearchResultsCount: number
  setPearchResultsCount: (v: number) => void
  localResultsCount: number
  setLocalResultsCount: (v: number) => void
  searchResultsCount: number
  setSearchResultsCount: (v: number) => void
  showSearchResults: boolean
  setShowSearchResults: (v: boolean) => void
  hasSearchResults: boolean
  setHasSearchResults: (v: boolean) => void
  showGlobalExpansionConfirm: boolean
  setShowGlobalExpansionConfirm: (v: boolean) => void
  isExpandingToGlobal: boolean
  setIsExpandingToGlobal: (v: boolean) => void
  displayedResultsCount: number
  setDisplayedResultsCount: (v: number | ((prev: number) => number)) => void
  isLoadingMore: boolean
  setIsLoadingMore: (v: boolean) => void
  searchFeedbacks: Record<string, 'like' | 'dislike'>
  setSearchFeedbacks: (v: Record<string, 'like' | 'dislike'> | ((prev: Record<string, 'like' | 'dislike'>) => Record<string, 'like' | 'dislike'>)) => void
  hasSearched: boolean
  lastSuccessfulQuery: string
  setSearchThreadId: (id: string | undefined) => void
  setSearchFingerprint: (fp: string | undefined) => void
  searchThreadId: string | undefined
  showExpandGlobalOption: boolean
  setShowExpandGlobalOption: (v: boolean) => void
  setChatMessages: (v: unknown[] | ((prev: unknown[]) => unknown[])) => void
  showSourceChangeModal: boolean
  setShowSourceChangeModal: (v: boolean) => void
  pendingSourceChange: 'hybrid' | 'global' | null
  setPendingSourceChange: (v: 'hybrid' | 'global' | null) => void
  showContactFilterModal: boolean
  setShowContactFilterModal: (v: boolean) => void
  pendingContactFilter: 'email' | 'phone' | null
  setPendingContactFilter: (v: 'email' | 'phone' | null) => void
  showCreditConfirmation: boolean
  setShowCreditConfirmation: (v: boolean) => void
  pendingSearchRequest: PendingSearchRequest
  setPendingSearchRequest: (v: PendingSearchRequest | ((prev: PendingSearchRequest) => PendingSearchRequest)) => void
  activeSearchFilters: SearchFilters
  setActiveSearchFilters: (v: SearchFilters | ((prev: SearchFilters) => SearchFilters)) => void
  setSelectedTemplate: (v: string) => void
  executeSearch: (
    query: string,
    entities?: ParsedEntities | null,
    mode?: SearchMode,
    metadata?: SearchMetadata,
    usePearch?: boolean
  ) => Promise<void>
  user: { id?: string; email?: string; name?: string; [key: string]: unknown } | null
}

export function useCandidatesSearch(ctx: CandidatesSearchContext) {
  const {
    candidates,
    setCandidates,
    searchResults,
    setSearchResults,
    lastSearchQuery,
    lastSearchEntities,
    lastSearchMode,
    lastSearchMetadata,
    lastSearchUsedPearch,
    searchSource,
    setSearchSource,
    setCurrentSearchSource,
    setPearchSearchOptions,
    setCreditsRemaining,
    setCreditsUsedInSearch,
    setPearchResultsCount,
    setLocalResultsCount,
    setSearchResultsCount,
    setShowSearchResults,
    setHasSearchResults,
    setShowGlobalExpansionConfirm,
    setIsExpandingToGlobal,
    setDisplayedResultsCount,
    setIsLoadingMore,
    setSearchFeedbacks,
    hasSearched,
    lastSuccessfulQuery,
    setSearchThreadId,
    setSearchFingerprint,
    searchThreadId,
    setShowExpandGlobalOption,
    setChatMessages,
    setShowSourceChangeModal,
    setPendingSourceChange,
    setShowContactFilterModal,
    setPendingContactFilter,
    setShowCreditConfirmation,
    setPendingSearchRequest,
    setActiveSearchFilters,
    setSelectedTemplate,
    pearchSearchOptions,
    executeSearch,
  } = ctx

  // Handler para confirmar busca com Pearch (após modal de créditos)
  const handleConfirmPearchSearch = async () => {
    setShowCreditConfirmation(false)

    if (ctx.pendingSearchRequest) {
      await executeSearch(
        ctx.pendingSearchRequest.query,
        ctx.pendingSearchRequest.entities,
        ctx.pendingSearchRequest.mode,
        ctx.pendingSearchRequest.metadata,
        true // usePearch = true
      )
      setPendingSearchRequest(null)
    }
  }

  // Handler para mudança de fonte de busca com confirmação de créditos
  const handleSourceChange = (newSource: 'local' | 'hybrid' | 'global') => {
    if (newSource === 'local') {
      // Local é gratuito - muda direto
      setSearchSource('local')
    } else {
      // Híbrido ou Global - mostrar modal de confirmação
      setPendingSourceChange(newSource)
      setShowSourceChangeModal(true)
    }
  }

  // Confirmar mudança de fonte após aceitar modal
  const confirmSourceChange = () => {
    if (ctx.pendingSourceChange) {
      const newSource = ctx.pendingSourceChange

      setSearchSource(newSource)
      setPendingSourceChange(null)
      setShowSourceChangeModal(false)

      // Now execute search with updated state
      if (lastSearchQuery && hasSearched) {
        // Use the new source to determine Pearch usage, but also respect previous search context
        const shouldUsePearch = newSource === 'global' || newSource === 'hybrid' || lastSearchUsedPearch
        executeSearch(
          lastSearchQuery,
          lastSearchEntities,
          lastSearchMode as SearchMode,
          lastSearchMetadata,
          shouldUsePearch
        )
      }

      toast.success(newSource === 'hybrid' ? 'Busca Híbrida ativada' : 'Busca Global ativada', { description: 'Atualizando resultados com a nova configuração...' })
    } else {
      setShowSourceChangeModal(false)
    }
  }

  // Handler para mudança de filtro de contato com confirmação
  const handleContactFilterChange = (filterType: 'email' | 'phone') => {
    const isCurrentlyActive = filterType === 'email'
      ? pearchSearchOptions.requireEmails
      : pearchSearchOptions.requirePhoneNumbers

    if (isCurrentlyActive) {
      // Desativar filtro - não precisa confirmação
      if (filterType === 'email') {
        setPearchSearchOptions(prev => ({ ...prev, requireEmails: false }))
      } else {
        setPearchSearchOptions(prev => ({ ...prev, requirePhoneNumbers: false }))
      }
    } else {
      // Ativar filtro - mostrar modal de confirmação (enriquecimento via Apify $0.01/candidato)
      setPendingContactFilter(filterType)
      setShowContactFilterModal(true)
    }
  }

  // Confirmar ativação de filtro de contato após aceitar modal
  const confirmContactFilterChange = () => {
    const filterType = ctx.pendingContactFilter

    if (filterType === 'email') {
      setPearchSearchOptions(prev => ({ ...prev, requireEmails: true }))
    } else if (filterType === 'phone') {
      setPearchSearchOptions(prev => ({ ...prev, requirePhoneNumbers: true }))
    }
    setPendingContactFilter(null)
    setShowContactFilterModal(false)

    // Now execute search with updated state - respect previous Pearch usage
    if (lastSearchQuery && hasSearched) {
      const shouldUsePearch = searchSource === 'global' || searchSource === 'hybrid' || lastSearchUsedPearch
      executeSearch(
        lastSearchQuery,
        lastSearchEntities,
        lastSearchMode as SearchMode,
        lastSearchMetadata,
        shouldUsePearch
      )
    }

    toast.success(filterType === 'email' ? 'Filtro de Email ativado' : 'Filtro de Telefone ativado', { description: 'Atualizando resultados com o novo filtro...' })
  }

  const handleSearchFeedbackChange = (candidateId: string, feedback: 'like' | 'dislike' | null) => {
    setSearchFeedbacks(prev => {
      const updated = { ...prev }
      if (feedback === null) {
        delete updated[candidateId]
      } else {
        updated[candidateId] = feedback
      }
      return updated
    })
  }

  const handleLoadMore = async () => {
    setIsLoadingMore(true)
    await new Promise(resolve => setTimeout(resolve, 300))
    setDisplayedResultsCount(prev => prev + LOAD_MORE_STEP)
    setIsLoadingMore(false)
  }

  // Handler para expandir busca para global (Pearch AI)
  const handleExpandToGlobal = async () => {
    setShowGlobalExpansionConfirm(false)
    setIsExpandingToGlobal(true)

    try {
      // Reusar a última query bem-sucedida
      const queryToUse = lastSuccessfulQuery || lastSearchQuery

      if (!queryToUse) {
        toast.error("Nenhuma busca ativa", { description: "Execute uma busca local primeiro para poder expandir para busca global." })
        return
      }

      // Construir SearchSpec a partir das entities salvas
      const searchSpec = lastSearchEntities ? {
        location: lastSearchEntities.location,
        job_title: lastSearchEntities.job_title,
        seniority: lastSearchEntities.seniority,
        years_experience: lastSearchEntities.years_experience,
        skills: lastSearchEntities.skills || [],
        industry: lastSearchEntities.industry,
        company: lastSearchEntities.company
      } : undefined

      // Executar busca global (Pearch AI)
      const searchResponse = await searchCandidatesHybrid({
        query: queryToUse,
        thread_id: searchThreadId,
        search_spec: searchSpec,
        search_local: true, // Manter local para híbrido
        search_pearch: true, // Adicionar busca global
        pearch_type: pearchSearchOptions.searchType,
        local_limit: 20,
        pearch_limit: pearchSearchOptions.limit,
        show_emails: pearchSearchOptions.showEmails,
        show_phone_numbers: pearchSearchOptions.showPhoneNumbers,
        high_freshness: pearchSearchOptions.highFreshness,
        require_emails: pearchSearchOptions.requireEmails,
        require_phone_numbers: pearchSearchOptions.requirePhoneNumbers
      })

      // Atualizar thread_id
      if (searchResponse.thread_id) {
        setSearchThreadId(searchResponse.thread_id)
      }

      // Atualizar saldo de créditos
      if (searchResponse.credits_remaining !== undefined && searchResponse.credits_remaining !== null) {
        setCreditsRemaining(searchResponse.credits_remaining)
      }

      // Mapear candidatos do Pearch para formato interno
      if (searchResponse.candidates && searchResponse.candidates.length > 0) {
        const mappedCandidates = searchResponse.candidates.map((c) => {
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
            avatar: c.avatar_url || c.picture_url,
            // Mapeamento de experiências profissionais da Pearch
            experiences: (c as unknown as Record<string, unknown>).experiences as unknown[] || [],
            workHistory: ((c as unknown as Record<string, unknown>).experiences as Array<Record<string, unknown>> || []).map((exp: {
              company_info?: { name?: string; location?: string }
              company?: string
              company_roles?: Array<{ title?: string; start_date?: string; end_date?: string; description?: string }>
              title?: string
              start_date?: string
              end_date?: string
              duration?: string
              location?: string
              description?: string
            }) => ({
              company: exp.company_info?.name || exp.company || '',
              title: exp.company_roles?.[0]?.title || exp.title || '',
              startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
              endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
              duration: exp.duration || '',
              location: exp.company_info?.location || exp.location || '',
              description: exp.company_roles?.[0]?.description || exp.description || ''
            })),
            // Mapeamento de formação acadêmica da Pearch
            education: ((c as unknown as Record<string, unknown>).education as Array<Record<string, unknown>> || []).map((edu: {
              school?: string
              degree?: string
              field_of_study?: string
              start_date?: string
              end_date?: string
            }) => ({
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
            contact_source: (c as unknown as Record<string, unknown>).contact_source as string || null,
            enrichment_source: (c as unknown as Record<string, unknown>).enrichment_source as string || null,
            is_enriching: (c as unknown as Record<string, unknown>).is_enriching as boolean || false,
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

        // Separar candidatos locais e globais
        const localCandidates = mappedCandidates.filter(c => !isGlobalSource(c.source, Boolean(c.pearch_profile_id)))
        const globalCandidates = mappedCandidates.filter(c => isGlobalSource(c.source, Boolean(c.pearch_profile_id)))

        // Atualizar estados
        setCandidates(mappedCandidates as unknown as Candidate[])
        // Fase 2: re-hidrata feedback persistido para os criterios desta busca
        // (fingerprint). Restaura o tier-sort like/dislike ao recarregar/resgatar a busca.
        setSearchFingerprint(searchResponse.search_fingerprint)
        if (searchResponse.search_fingerprint) {
          try {
            const _fbResp = await fetch(
              `/api/backend-proxy/search/feedback/by-search?fingerprint=${encodeURIComponent(searchResponse.search_fingerprint)}`
            )
            if (_fbResp.ok) {
              const _fbData = await _fbResp.json()
              if (_fbData?.feedbacks && Object.keys(_fbData.feedbacks).length > 0) {
                setSearchFeedbacks(_fbData.feedbacks as Record<string, 'like' | 'dislike'>)
              }
            }
          } catch (_e) {
            console.warn('[search] re-hidratacao de feedback falhou (best-effort):', _e)
          }
        }
        setCurrentSearchSource('hybrid')
        setSearchResultsCount(searchResponse.total_count || mappedCandidates.length)
        setLocalResultsCount(searchResponse.local_count || localCandidates.length)
        setPearchResultsCount(searchResponse.pearch_count || globalCandidates.length)
        setCreditsUsedInSearch(searchResponse.credits_used || 0)

        // Atualizar searchResults para exibição no painel LIA
        setSearchResults((prev) => ({
          ...prev,
          local: localCandidates as unknown as typeof prev.local,
          global: globalCandidates as unknown as typeof prev.global,
          localCount: searchResponse.local_count || localCandidates.length,
          globalCount: searchResponse.pearch_count || globalCandidates.length,
          showGlobalResults: globalCandidates.length > 0
        }))

        if (globalCandidates.length > 0) {
          toast.success("Busca expandida com sucesso!", { description: `Encontrados ${globalCandidates.length} candidatos adicionais na base global.` })

          const liaMessage = {
            id: `lia-expand-global-${Date.now()}`,
            type: 'lia',
            content: `🌐 **Busca expandida para base global**\n\nEncontrei mais **${globalCandidates.length} candidatos** na Busca Global!\n\nAgora você tem acesso a um pool ampliado de talentos para sua vaga.`,
            timestamp: new Date()
          }
          setChatMessages(prev => [...prev, liaMessage])

          try {
            const analyzeResponse = await fetch('/api/backend-proxy/search/analyze', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                query: queryToUse,
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
                  work_model: c.workModel || 'remoto',
                  email: c.email,
                  phone: c.phone || c.mobile_phone,
                  linkedin_url: c.linkedin_url,
                  source: c.source
                })),
                local_count: localCandidates.length,
                global_count: globalCandidates.length
              })
            })

            if (analyzeResponse.ok) {
              const analyticsData: SearchAnalytics = await analyzeResponse.json()

              const insightMessage = {
                id: `proactive-insight-global-${Date.now()}`,
                type: 'proactive_insight',
                content: '',
                timestamp: new Date(),
                analytics: analyticsData
              }
              setChatMessages(prev => [...prev, insightMessage])
            }
          } catch (analyzeError) {
          }
        } else {
          toast.info("Busca global indisponível", {
            description: "O serviço de busca global (Pearch AI) não está configurado no momento. Os resultados da base local foram mantidos."
          })
          const liaMessage = {
            id: `lia-expand-unavailable-${Date.now()}`,
            type: 'lia' as const,
            content: `A busca global não está disponível no momento. Os resultados da base local foram mantidos.\n\nPara habilitar a busca global, configure a integração com Pearch AI nas configurações da plataforma.`,
            timestamp: new Date()
          }
          setChatMessages(prev => [...prev, liaMessage])
        }
      } else {
        toast.info("Busca global indisponível", {
          description: "O serviço de busca global (Pearch AI) não está configurado no momento. Os resultados da base local foram mantidos."
        })
        const liaMessage = {
          id: `lia-expand-unavailable-${Date.now()}`,
          type: 'lia' as const,
          content: `A busca global não está disponível no momento. Os resultados da base local foram mantidos.\n\nPara habilitar a busca global, configure a integração com Pearch AI nas configurações da plataforma.`,
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, liaMessage])
      }

      setShowExpandGlobalOption(false)

    } catch (error) {
      toast.error("Erro ao expandir busca", { description: "Não foi possível expandir para busca global. Tente novamente." })
    } finally {
      setIsExpandingToGlobal(false)
    }
  }

  // Handler para aplicar filtros avançados (agora usado pelo painel lateral)
  const handleApplyAdvancedFilters = (filters: SearchFilters) => {
    setActiveSearchFilters(filters)

    // Aplicar filtros na busca
    const query = buildQueryFromFilters(filters)
    if (query) {
      executeSearch(query, {}, 'natural', undefined, false)
    }
  }

  // Função auxiliar para construir query a partir de filtros
  const buildQueryFromFilters = (filters: SearchFilters): string => {
    const parts: string[] = []

    if ((filters.skills as Record<string, unknown>)?.skills && ((filters.skills as Record<string, unknown>).skills as string[]).length > 0) {
      parts.push(`skills: ${((filters.skills as Record<string, unknown>).skills as string[]).join(', ')}`)
    }
    if (((filters as unknown as Record<string, unknown>)?.locations as Record<string, unknown> | undefined)?.locations && (((((filters as unknown as Record<string, unknown>)?.locations as Record<string, unknown> | undefined)?.locations) as string[] | undefined)?.length ?? 0) > 0) {
      parts.push(`localização: ${((((filters as unknown as Record<string, unknown>).locations as Record<string, unknown>)?.locations as string[] | undefined)?.join(', ') ?? '')}`)
    }
    if (filters.general?.minExperience || filters.general?.maxExperience) {
      const min = filters.general.minExperience || 0
      const max = filters.general.maxExperience || 10
      parts.push(`experiência: ${min}-${max} anos`)
    }
    if (filters.job?.levels && filters.job.levels.length > 0) {
      parts.push(`senioridade: ${filters.job.levels.join(', ')}`)
    }
    if (filters.job?.titles && filters.job.titles.length > 0) {
      parts.push(`cargo: ${filters.job.titles.join(', ')}`)
    }
    if (filters.languages?.languages && filters.languages.languages.length > 0) {
      parts.push(`idiomas: ${filters.languages.languages.join(', ')}`)
    }
    if (filters.company?.industries && filters.company.industries.length > 0) {
      parts.push(`indústrias: ${filters.company.industries.join(', ')}`)
    }
    if (filters.education?.degrees && filters.education.degrees.length > 0) {
      parts.push(`formação: ${filters.education.degrees.join(', ')}`)
    }

    return parts.join(', ')
  }

  // Handlers para templates e busca
  const handleTemplateSelection = (template: string) => {
    setSelectedTemplate(template)
    // Implementar lógica de aplicação do template
  }

  return {
    handleConfirmPearchSearch,
    handleSourceChange,
    confirmSourceChange,
    handleContactFilterChange,
    confirmContactFilterChange,
    handleSearchFeedbackChange,
    handleLoadMore,
    handleExpandToGlobal,
    handleApplyAdvancedFilters,
    buildQueryFromFilters,
    handleTemplateSelection,
  }
}
