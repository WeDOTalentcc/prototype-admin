"use client"

import React from "react"
import { flushSync } from "react-dom"
import {
  searchCandidates as searchCandidatesHybrid,
} from "@/lib/api/candidate-search"
import { isGlobalSource } from "@/lib/utils/source-detection"
import type { Candidate } from "../types"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { SearchAnalytics } from "@/components/proactive-insight-card"

export interface CandidatesSearchContext {
  candidates: Candidate[]
  setCandidates: React.Dispatch<React.SetStateAction<Candidate[]>>
  searchResults: {
    local: Candidate[]
    global: Candidate[]
    localCount: number
    globalCount: number
    query: string
    isLoading: boolean
    showGlobalResults: boolean
    globalDismissed: boolean
  }
  setSearchResults: React.Dispatch<React.SetStateAction<CandidatesSearchContext['searchResults']>>
  searchTerm: string
  lastSearchQuery: string
  lastSearchEntities: ParsedEntities | null
  lastSearchMode: string
  lastSearchMetadata: SearchMetadata | undefined
  lastSearchUsedPearch: boolean
  searchSource: 'local' | 'hybrid' | 'global'
  setSearchSource: React.Dispatch<React.SetStateAction<'local' | 'hybrid' | 'global'>>
  currentSearchSource: 'local' | 'global' | 'hybrid'
  setCurrentSearchSource: React.Dispatch<React.SetStateAction<'local' | 'global' | 'hybrid'>>
  openCreditModals: { hybrid: boolean; global: boolean; email: boolean; phone: boolean }
  setOpenCreditModals: React.Dispatch<React.SetStateAction<CandidatesSearchContext['openCreditModals']>>
  pearchSearchOptions: {
    searchType: 'fast' | 'pro'
    limit: number
    showEmails: boolean
    showPhoneNumbers: boolean
    highFreshness: boolean
    requireEmails: boolean
    requirePhoneNumbers: boolean
  }
  setPearchSearchOptions: React.Dispatch<React.SetStateAction<CandidatesSearchContext['pearchSearchOptions']>>
  creditsRemaining: number | null
  setCreditsRemaining: React.Dispatch<React.SetStateAction<number | null>>
  creditsUsedInSearch: number
  setCreditsUsedInSearch: React.Dispatch<React.SetStateAction<number>>
  pearchResultsCount: number
  setPearchResultsCount: React.Dispatch<React.SetStateAction<number>>
  localResultsCount: number
  setLocalResultsCount: React.Dispatch<React.SetStateAction<number>>
  searchResultsCount: number
  setSearchResultsCount: React.Dispatch<React.SetStateAction<number>>
  showSearchResults: boolean
  setShowSearchResults: React.Dispatch<React.SetStateAction<boolean>>
  hasSearchResults: boolean
  setHasSearchResults: React.Dispatch<React.SetStateAction<boolean>>
  showGlobalExpansionConfirm: boolean
  setShowGlobalExpansionConfirm: React.Dispatch<React.SetStateAction<boolean>>
  isExpandingToGlobal: boolean
  setIsExpandingToGlobal: React.Dispatch<React.SetStateAction<boolean>>
  displayedResultsCount: number
  setDisplayedResultsCount: React.Dispatch<React.SetStateAction<number>>
  isLoadingMore: boolean
  setIsLoadingMore: React.Dispatch<React.SetStateAction<boolean>>
  searchFeedbacks: Record<string, 'like' | 'dislike'>
  setSearchFeedbacks: React.Dispatch<React.SetStateAction<Record<string, 'like' | 'dislike'>>>
  hasSearched: boolean
  lastSuccessfulQuery: string
  setSearchThreadId: React.Dispatch<React.SetStateAction<string | undefined>>
  searchThreadId: string | undefined
  showExpandGlobalOption: boolean
  setShowExpandGlobalOption: React.Dispatch<React.SetStateAction<boolean>>
  setChatMessages: React.Dispatch<React.SetStateAction<any[]>>
  showSourceChangeModal: boolean
  setShowSourceChangeModal: React.Dispatch<React.SetStateAction<boolean>>
  pendingSourceChange: 'hybrid' | 'global' | null
  setPendingSourceChange: React.Dispatch<React.SetStateAction<'hybrid' | 'global' | null>>
  showContactFilterModal: boolean
  setShowContactFilterModal: React.Dispatch<React.SetStateAction<boolean>>
  pendingContactFilter: 'email' | 'phone' | null
  setPendingContactFilter: React.Dispatch<React.SetStateAction<'email' | 'phone' | null>>
  showCreditConfirmation: boolean
  setShowCreditConfirmation: React.Dispatch<React.SetStateAction<boolean>>
  pendingSearchRequest: {
    query: string
    entities?: ParsedEntities
    mode?: SearchMode
    metadata?: SearchMetadata
  } | null
  setPendingSearchRequest: React.Dispatch<React.SetStateAction<CandidatesSearchContext['pendingSearchRequest']>>
  activeSearchFilters: SearchFilters
  setActiveSearchFilters: React.Dispatch<React.SetStateAction<SearchFilters>>
  setSelectedTemplate: React.Dispatch<React.SetStateAction<string>>
  executeSearch: (
    query: string,
    entities?: ParsedEntities | null,
    mode?: SearchMode,
    metadata?: SearchMetadata,
    usePearch?: boolean
  ) => Promise<void>
  toast: (opts: { title: string; description?: string; variant?: "destructive" | "default" }) => void
  user: any
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
    toast,
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
      // Híbrido ou Global consome créditos - mostrar modal de confirmação
      setPendingSourceChange(newSource)
      setShowSourceChangeModal(true)
    }
  }

  // Confirmar mudança de fonte após aceitar modal
  const confirmSourceChange = () => {
    if (ctx.pendingSourceChange) {
      const newSource = ctx.pendingSourceChange

      // Use flushSync to ensure state is committed before executing search
      flushSync(() => {
        setSearchSource(newSource)
        setPendingSourceChange(null)
        setShowSourceChangeModal(false)
      })

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

      toast({
        title: newSource === 'hybrid' ? 'Busca Híbrida ativada' : 'Busca Global ativada',
        description: 'Atualizando resultados com a nova configuração...',
      })
    } else {
      setShowSourceChangeModal(false)
    }
  }

  // Handler para mudança de filtro de contato com confirmação de créditos
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
      // Ativar filtro - mostrar modal de confirmação (consome créditos extras)
      setPendingContactFilter(filterType)
      setShowContactFilterModal(true)
    }
  }

  // Confirmar ativação de filtro de contato após aceitar modal
  const confirmContactFilterChange = () => {
    const filterType = ctx.pendingContactFilter

    // Use flushSync to ensure state is committed before executing search
    flushSync(() => {
      if (filterType === 'email') {
        setPearchSearchOptions(prev => ({ ...prev, requireEmails: true }))
      } else if (filterType === 'phone') {
        setPearchSearchOptions(prev => ({ ...prev, requirePhoneNumbers: true }))
      }
      setPendingContactFilter(null)
      setShowContactFilterModal(false)
    })

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

    toast({
      title: filterType === 'email' ? 'Filtro de Email ativado' : 'Filtro de Telefone ativado',
      description: 'Atualizando resultados com o novo filtro...',
    })
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
    setDisplayedResultsCount(prev => prev + 10)
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
        toast({
          title: "Nenhuma busca ativa",
          description: "Execute uma busca local primeiro para poder expandir para busca global.",
          variant: "destructive"
        })
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
            experiences: c.experiences || [],
            workHistory: (c.experiences || []).map((exp: any) => ({
              company: exp.company_info?.name || exp.company || '',
              title: exp.company_roles?.[0]?.title || exp.title || '',
              startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
              endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
              duration: exp.duration || '',
              location: exp.company_info?.location || exp.location || '',
              description: exp.company_roles?.[0]?.description || exp.description || ''
            })),
            // Mapeamento de formação acadêmica da Pearch
            education: (c.education || []).map((edu: any) => ({
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

        // Separar candidatos locais e globais
        const localCandidates = mappedCandidates.filter(c => !isGlobalSource(c.source, Boolean(c.pearch_profile_id)))
        const globalCandidates = mappedCandidates.filter(c => isGlobalSource(c.source, Boolean(c.pearch_profile_id)))

        // Atualizar estados
        setCandidates(mappedCandidates)
        setCurrentSearchSource('hybrid')
        setSearchResultsCount(searchResponse.total_count || mappedCandidates.length)
        setLocalResultsCount(searchResponse.local_count || localCandidates.length)
        setPearchResultsCount(searchResponse.pearch_count || globalCandidates.length)
        setCreditsUsedInSearch(searchResponse.credits_used || 0)

        // Atualizar searchResults para exibição no painel LIA
        setSearchResults(prev => ({
          ...prev,
          local: localCandidates,
          global: globalCandidates,
          localCount: searchResponse.local_count || localCandidates.length,
          globalCount: searchResponse.pearch_count || globalCandidates.length,
          showGlobalResults: true
        }))

        // Notificar usuário
        toast({
          title: "Busca expandida com sucesso!",
          description: `Encontrados ${globalCandidates.length} candidatos adicionais na base global.`
        })

        // Adicionar mensagem no chat
        const liaMessage = {
          id: `lia-expand-global-${Date.now()}`,
          type: 'lia',
          content: `🌐 **Busca expandida para base global**\n\nEncontrei mais **${globalCandidates.length} candidatos** na Busca Global!\n\nAgora você tem acesso a um pool ampliado de talentos para sua vaga.`,
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, liaMessage])

        // 🎯 Chamar análise proativa após expansão para busca global
        if (mappedCandidates.length > 0) {
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

              // Inserir card de insights proativos no chat
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
            console.warn('Erro ao analisar resultados da busca global:', analyzeError)
          }
        }
      }

      setShowExpandGlobalOption(false)

    } catch (error) {
      console.error('Erro ao expandir busca para global:', error)
      toast({
        title: "Erro ao expandir busca",
        description: "Não foi possível expandir para busca global. Tente novamente.",
        variant: "destructive"
      })
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

    if (filters.skills?.skills && filters.skills.skills.length > 0) {
      parts.push(`skills: ${filters.skills.skills.join(', ')}`)
    }
    if (filters.locations?.locations && filters.locations.locations.length > 0) {
      parts.push(`localização: ${filters.locations.locations.join(', ')}`)
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
