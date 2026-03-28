"use client"

import React from "react"
import type { Candidate } from "../types"

export interface CandidatesActionsContext {
  candidates: Candidate[]
  setCandidates: React.Dispatch<React.SetStateAction<Candidate[]>>
  activeTab: string
  setActiveTab: React.Dispatch<React.SetStateAction<string>>
  viewingList: { id: string; name: string; color?: string } | null
  setViewingList: React.Dispatch<React.SetStateAction<{ id: string; name: string; color?: string } | null>>
  candidateListsForModal: Array<{ id: string; name: string; color?: string }>
  selectedCandidatesForBatch: Set<string>
  setSelectedCandidatesForBatch: React.Dispatch<React.SetStateAction<Set<string>>>
  isSavingToBase: boolean
  setIsSavingToBase: React.Dispatch<React.SetStateAction<boolean>>
  isAddingToList: boolean
  setIsAddingToList: React.Dispatch<React.SetStateAction<boolean>>
  showAddToListModal: boolean
  setShowAddToListModal: React.Dispatch<React.SetStateAction<boolean>>
  addToListCandidateIds: string[]
  setAddToListCandidateIds: React.Dispatch<React.SetStateAction<string[]>>
  addToListCandidateNames: string[]
  setAddToListCandidateNames: React.Dispatch<React.SetStateAction<string[]>>
  showUnsavedWarningModal: boolean
  setShowUnsavedWarningModal: React.Dispatch<React.SetStateAction<boolean>>
  pendingTabChange: string | null
  setPendingTabChange: React.Dispatch<React.SetStateAction<string | null>>
  hasUnsavedPearchCandidates: boolean
  unsavedPearchCandidates: Candidate[]
  showSearchResults: boolean
  setShowSearchResults: React.Dispatch<React.SetStateAction<boolean>>
  lastSearchQuery: string
  deselectAllCandidates: () => void
  toast: (opts: { title: string; description?: string; variant?: "destructive" | "default" }) => void
  user: any
}

export function useCandidatesActions(ctx: CandidatesActionsContext) {
  const {
    candidates,
    setCandidates,
    activeTab,
    setActiveTab,
    selectedCandidatesForBatch,
    setIsSavingToBase,
    setIsAddingToList,
    setShowAddToListModal,
    setAddToListCandidateIds,
    setAddToListCandidateNames,
    setShowUnsavedWarningModal,
    setPendingTabChange,
    hasUnsavedPearchCandidates,
    unsavedPearchCandidates,
    setShowSearchResults,
    lastSearchQuery,
    deselectAllCandidates,
    toast,
  } = ctx

  // Salvar candidatos Pearch selecionados na base local
  const handleSaveToLocalBase = async () => {
    const selectedPearchCandidates = candidates.filter(
      c => selectedCandidatesForBatch.has(c.id) && c.source === 'pearch'
    )

    if (selectedPearchCandidates.length === 0) {
      toast({
        title: "Nenhum candidato Pearch selecionado",
        description: "Selecione candidatos de busca global para salvar na base.",
        variant: "destructive"
      })
      return
    }

    setIsSavingToBase(true)

    try {
      const importPayload = {
        candidates: selectedPearchCandidates.map(c => ({
          pearch_id: c.id,
          name: c.name,
          first_name: c.name?.split(' ')[0] || null,
          last_name: c.name?.split(' ').slice(1).join(' ') || null,
          middle_name: c.middle_name || null,
          email: c.email || null,
          phone: c.phone || null,
          linkedin_url: c.linkedin_url || null,
          avatar_url: c.avatar_url || null,
          current_title: c.current_title || null,
          current_company: c.current_company || null,
          headline: c.headline || null,
          summary: c.summary || null,
          location: c.location || null,
          years_of_experience: c.years_of_experience || null,
          skills: c.skills || [],
          expertise: c.expertise || [],
          languages: c.languages || [],
          education: c.education || [],
          experiences: (c.experiences || []).map((exp: any) => ({
            company_name: exp.company || exp.company_name || 'Empresa não informada',
            company_linkedin_url: exp.company_linkedin_url || null,
            company_domain: exp.company_domain || null,
            title: exp.title || null,
            start_date: exp.start_date || null,
            end_date: exp.end_date || null,
            duration_years: exp.duration_years || null,
            is_current: exp.current || false,
            description: exp.description || null,
            location: exp.location || null,
            industries: exp.industries || [],
            company_size: exp.company_size || null,
            company_size_range: exp.company_size_range || null,
            technologies: exp.technologies || [],
            is_startup: exp.is_startup || null,
            company_founded_year: null,
            company_annual_revenue: null,
            company_followers_count: exp.company_followers_count || exp.company_info?.followers_count || null,
            company_keywords: exp.company_keywords || exp.company_info?.keywords || []
          })),
          is_open_to_work: c.is_open_to_work || null,
          is_decision_maker: c.is_decision_maker || null,
          is_top_universities: c.is_top_universities || null,
          is_hiring: c.is_hiring || null,
          best_personal_email: c.best_personal_email || null,
          best_business_email: c.best_business_email || null,
          personal_emails: c.personal_emails || [],
          business_emails: c.business_emails || [],
          phone_types: c.phone_types || null,
          estimated_age: c.estimated_age || null,
          linkedin_followers_count: c.linkedin_followers_count || c.followers_count || null,
          linkedin_connections_count: c.linkedin_connections_count || c.connections_count || null,
          insights: c.pearch_insights || c.insights || null,
          outreach_message: c.outreach_message || null
        })),
        source_search_query: lastSearchQuery || undefined
      }

      const response = await fetch('/api/backend-proxy/search/candidates/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(importPayload)
      })

      if (!response.ok) {
        throw new Error('Falha ao importar candidatos')
      }

      const result = await response.json()

      toast({
        title: "Candidatos salvos na base!",
        description: result.message,
      })

      // Limpar seleção após salvar
      deselectAllCandidates()

    } catch (error) {
      toast({
        title: "Erro ao salvar candidatos",
        description: "Tente novamente em alguns instantes.",
        variant: "destructive"
      })
    } finally {
      setIsSavingToBase(false)
    }
  }

  // Handler para adicionar candidatos à lista (importando Pearch candidates primeiro)
  const handleAddToList = async () => {
    const selectedIds = Array.from(selectedCandidatesForBatch)
    const selectedCandidates = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
    const selectedNames = selectedCandidates.map(c => c.name)

    // Separar candidatos locais e Pearch
    const localCandidates = selectedCandidates.filter(c => c.source !== 'pearch')
    const pearchCandidates = selectedCandidates.filter(c => c.source === 'pearch')

    // Se não há candidatos Pearch, abrir modal diretamente
    if (pearchCandidates.length === 0) {
      setAddToListCandidateIds(selectedIds)
      setAddToListCandidateNames(selectedNames)
      setShowAddToListModal(true)
      return
    }

    // Importar candidatos Pearch primeiro
    setIsAddingToList(true)

    try {
      const importPayload = {
        candidates: pearchCandidates.map(c => ({
          pearch_id: c.pearch_profile_id || c.id,
          name: c.name,
          first_name: c.name?.split(' ')[0] || null,
          last_name: c.name?.split(' ').slice(1).join(' ') || null,
          middle_name: c.middle_name || null,
          email: c.email || null,
          phone: c.phone || null,
          linkedin_url: c.linkedin_url || null,
          avatar_url: c.avatar_url || null,
          current_title: c.current_title || null,
          current_company: c.current_company || null,
          headline: c.headline || null,
          summary: c.summary || null,
          location: c.location || null,
          years_of_experience: c.years_of_experience || null,
          skills: c.skills || [],
          expertise: c.expertise || [],
          languages: c.languages || [],
          education: c.education || [],
          experiences: (c.experiences || []).map((exp: any) => ({
            company_name: exp.company || exp.company_name || 'Empresa não informada',
            company_linkedin_url: exp.company_linkedin_url || null,
            company_domain: exp.company_domain || null,
            title: exp.title || null,
            start_date: exp.start_date || null,
            end_date: exp.end_date || null,
            duration_years: exp.duration_years || null,
            is_current: exp.current || false,
            description: exp.description || null,
            location: exp.location || null,
            industries: exp.industries || [],
            company_size: exp.company_size || null,
            company_size_range: exp.company_size_range || null,
            technologies: exp.technologies || [],
            is_startup: exp.is_startup || null,
            company_founded_year: null,
            company_annual_revenue: null,
            company_followers_count: exp.company_followers_count || exp.company_info?.followers_count || null,
            company_keywords: exp.company_keywords || exp.company_info?.keywords || []
          })),
          is_open_to_work: c.is_open_to_work || null,
          is_decision_maker: c.is_decision_maker || null,
          is_top_universities: c.is_top_universities || null,
          is_hiring: c.is_hiring || null,
          best_personal_email: c.best_personal_email || null,
          best_business_email: c.best_business_email || null,
          personal_emails: c.personal_emails || [],
          business_emails: c.business_emails || [],
          phone_types: c.phone_types || null,
          estimated_age: c.estimated_age || null,
          linkedin_followers_count: c.linkedin_followers_count || c.followers_count || null,
          linkedin_connections_count: c.linkedin_connections_count || c.connections_count || null,
          insights: c.pearch_insights || c.insights || null,
          outreach_message: c.outreach_message || null
        })),
        source_search_query: lastSearchQuery || undefined
      }

      const response = await fetch('/api/backend-proxy/search/candidates/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(importPayload)
      })

      if (!response.ok) {
        throw new Error('Falha ao importar candidatos Pearch')
      }

      const result = await response.json()

      // Criar mapeamento de pearch_id → local_id
      const idMapping = new Map<string, string>()
      if (result.mapping && Array.isArray(result.mapping)) {
        result.mapping.forEach((m: { pearch_id: string; local_id: string }) => {
          idMapping.set(m.pearch_id, m.local_id)
        })
      }

      // Substituir IDs Pearch pelos IDs locais
      const localIds: string[] = []

      // Adicionar IDs dos candidatos locais
      localCandidates.forEach(c => {
        localIds.push(c.id)
      })

      // Adicionar IDs mapeados dos candidatos Pearch
      pearchCandidates.forEach(c => {
        const pearchId = c.pearch_profile_id || c.id
        const localId = idMapping.get(pearchId)
        if (localId) {
          localIds.push(localId)
        } else {
          // Fallback: usar ID original se não encontrar mapeamento
          localIds.push(c.id)
        }
      })

      // Abrir modal com IDs locais
      setAddToListCandidateIds(localIds)
      setAddToListCandidateNames(selectedNames)
      setShowAddToListModal(true)

      // Mostrar toast informativo
      if (result.imported_count > 0 || result.updated_count > 0) {
        toast({
          title: "Candidatos importados",
          description: `${result.imported_count || 0} novo(s), ${result.updated_count || 0} atualizado(s)`,
        })
      }

    } catch (error) {
      toast({
        title: "Erro ao importar candidatos",
        description: "Não foi possível salvar candidatos Pearch na base. Tente novamente.",
        variant: "destructive"
      })
    } finally {
      setIsAddingToList(false)
    }
  }

  // Handler para mudança de aba com verificação de candidatos não salvos
  const handleTabChangeWithWarning = (newTab: string) => {
    // Se está na aba de busca com resultados Pearch e quer mudar para outra aba
    if (activeTab === 'search' && hasUnsavedPearchCandidates && newTab !== 'search') {
      setPendingTabChange(newTab)
      setShowUnsavedWarningModal(true)
    } else {
      setActiveTab(newTab)
    }
  }

  // Handler para salvar todos os candidatos Pearch e sair
  const handleSaveAllAndExit = async () => {
    setIsSavingToBase(true)

    try {
      const importPayload = {
        candidates: unsavedPearchCandidates.map(c => ({
          pearch_id: c.pearch_profile_id || c.id,
          name: c.name,
          first_name: c.name?.split(' ')[0] || null,
          last_name: c.name?.split(' ').slice(1).join(' ') || null,
          middle_name: c.middle_name || null,
          email: c.email || null,
          phone: c.phone || null,
          linkedin_url: c.linkedin_url || null,
          avatar_url: c.avatar_url || null,
          current_title: c.current_title || null,
          current_company: c.current_company || null,
          headline: c.headline || null,
          summary: c.summary || null,
          location: c.location || null,
          years_of_experience: c.years_of_experience || null,
          skills: c.skills || [],
          expertise: c.expertise || [],
          languages: c.languages || [],
          education: c.education || [],
          experiences: (c.experiences || []).map((exp: any) => ({
            company_name: exp.company || exp.company_name || 'Empresa não informada',
            company_linkedin_url: exp.company_linkedin_url || null,
            company_domain: exp.company_domain || null,
            title: exp.title || null,
            start_date: exp.start_date || null,
            end_date: exp.end_date || null,
            duration_years: exp.duration_years || null,
            is_current: exp.current || false,
            description: exp.description || null,
            location: exp.location || null,
            industries: exp.industries || [],
            company_size: exp.company_size || null,
            company_size_range: exp.company_size_range || null,
            technologies: exp.technologies || [],
            is_startup: exp.is_startup || null,
            company_founded_year: null,
            company_annual_revenue: null,
            company_followers_count: exp.company_followers_count || exp.company_info?.followers_count || null,
            company_keywords: exp.company_keywords || exp.company_info?.keywords || []
          })),
          is_open_to_work: c.is_open_to_work || null,
          is_decision_maker: c.is_decision_maker || null,
          is_top_universities: c.is_top_universities || null,
          is_hiring: c.is_hiring || null,
          best_personal_email: c.best_personal_email || null,
          best_business_email: c.best_business_email || null,
          personal_emails: c.personal_emails || [],
          business_emails: c.business_emails || [],
          phone_types: c.phone_types || null,
          estimated_age: c.estimated_age || null,
          linkedin_followers_count: c.linkedin_followers_count || c.followers_count || null,
          linkedin_connections_count: c.linkedin_connections_count || c.connections_count || null,
          insights: c.pearch_insights || c.insights || null,
          outreach_message: c.outreach_message || null
        })),
        source_search_query: lastSearchQuery || undefined
      }

      const response = await fetch('/api/backend-proxy/search/candidates/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(importPayload)
      })

      if (!response.ok) {
        throw new Error('Falha ao importar candidatos')
      }

      const result = await response.json()

      toast({
        title: "Candidatos salvos!",
        description: result.message,
      })

      // Limpar resultados de busca e mudar para a aba pendente
      setCandidates([])
      setShowSearchResults(false)
      setShowUnsavedWarningModal(false)
      if (ctx.pendingTabChange) {
        setActiveTab(ctx.pendingTabChange!)
        setPendingTabChange(null)
      }

    } catch (error: any) {
      const errorMessage = error?.message || 'Erro desconhecido ao salvar candidatos'
      toast({
        title: "Erro ao salvar",
        description: errorMessage,
        variant: "destructive"
      })
    } finally {
      setIsSavingToBase(false)
    }
  }

  // Handler para sair sem salvar
  const handleExitWithoutSaving = () => {
    setCandidates([])
    setShowSearchResults(false)
    setShowUnsavedWarningModal(false)
    if (ctx.pendingTabChange) {
      setActiveTab(ctx.pendingTabChange!)
      setPendingTabChange(null)
    }
  }

  return {
    handleSaveToLocalBase,
    handleAddToList,
    handleTabChangeWithWarning,
    handleSaveAllAndExit,
    handleExitWithoutSaving,
  }
}
