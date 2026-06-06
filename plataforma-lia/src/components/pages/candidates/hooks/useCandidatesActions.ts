"use client"

import React from "react"
import type { Candidate } from "../types"
import { toast } from "sonner"
import { isGlobalSource } from "@/lib/utils/source-detection"
import { useNavGuardStore } from "@/stores/nav-guard-store"
import type { RevealedContacts } from "@/stores/candidates-store"

interface CandidateExperience {
  company?: string
  company_name?: string
  company_linkedin_url?: string
  company_domain?: string
  title?: string
  start_date?: string
  end_date?: string
  duration_years?: number
  current?: boolean
  description?: string
  location?: string
  industries?: string[]
  company_size?: string
  company_size_range?: string
  technologies?: string[]
  is_startup?: boolean
  company_followers_count?: number
  company_keywords?: string[]
  company_info?: { followers_count?: number; keywords?: string[] }
}

export interface CandidatesActionsContext {
  candidates: Candidate[]
  revealedContacts: RevealedContacts
  setCandidates: (v: Candidate[]) => void
  activeTab: string
  setActiveTab: (v: string) => void
  viewingList: { id: string; name: string; color?: string } | null
  setViewingList: (v: { id: string; name: string; color?: string } | null) => void
  candidateListsForModal: Array<{ id: string; name: string; color?: string }>
  selectedCandidatesForBatch: Set<string>
  setSelectedCandidatesForBatch: React.Dispatch<React.SetStateAction<Set<string>>>
  isSavingToBase: boolean
  setIsSavingToBase: (v: boolean) => void
  isAddingToList: boolean
  setIsAddingToList: (v: boolean) => void
  showAddToListModal: boolean
  setShowAddToListModal: (v: boolean) => void
  addToListCandidateIds: string[]
  setAddToListCandidateIds: (v: string[]) => void
  addToListCandidateNames: string[]
  setAddToListCandidateNames: (v: string[]) => void
  showUnsavedWarningModal: boolean
  setShowUnsavedWarningModal: (v: boolean) => void
  pendingTabChange: string | null
  setPendingTabChange: (v: string | null) => void
  hasUnsavedPearchCandidates: boolean
  unsavedPearchCandidates: Candidate[]
  showSearchResults: boolean
  setShowSearchResults: (v: boolean) => void
  lastSearchQuery: string
  deselectAllCandidates: () => void
  user: { id?: string; name?: string; email?: string; [key: string]: unknown } | null
}

export function useCandidatesActions(ctx: CandidatesActionsContext) {
  const {
    candidates,
    revealedContacts,
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
  } = ctx

  // Salvar candidatos Pearch selecionados na base local
  const handleSaveToLocalBase = async () => {
    const selectedPearchCandidates = candidates.filter(
      c => selectedCandidatesForBatch.has(c.id) && isGlobalSource(c.source, !!c.pearch_profile_id)
    )

    if (selectedPearchCandidates.length === 0) {
      toast.error("Nenhum candidato Pearch selecionado", { description: "Selecione candidatos de busca global para salvar na base." })
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
          email: revealedContacts[c.id]?.email ?? c.email ?? null,
          phone: revealedContacts[c.id]?.phone ?? c.phone ?? null,
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
          experiences: (c.experiences || []).map((exp: CandidateExperience) => ({
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

      // Optimistic rastro: flip saved rows to local so the "Fonte" column shows
      // the Home icon (Base Local, no credit cost) instead of the Globe. The
      // recruiter can now see exactly which candidates were saved; the row stays
      // even though the selection clears. Mirrors server state after import.
      const savedIds = new Set(selectedPearchCandidates.map(c => c.id))
      setCandidates(
        candidates.map(c =>
          savedIds.has(c.id) ? { ...c, source: 'local', enrichment_source: 'local', email: revealedContacts[c.id]?.email ?? c.email, phone: revealedContacts[c.id]?.phone ?? c.phone } : c
        )
      )

      toast.success("Candidatos salvos na base!", {
        description:
          result.message ||
          `${selectedPearchCandidates.length} candidato(s) agora na sua base — veja o ícone de casa na coluna Fonte.`,
      })

      // Limpar seleção após salvar
      deselectAllCandidates()

    } catch (error) {
      toast.error("Erro ao salvar candidatos", { description: "Tente novamente em alguns instantes." })
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
          email: revealedContacts[c.id]?.email ?? c.email ?? null,
          phone: revealedContacts[c.id]?.phone ?? c.phone ?? null,
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
          experiences: (c.experiences || []).map((exp: CandidateExperience) => ({
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
        toast.success("Candidatos importados", { description: `${result.imported_count || 0} novo(s), ${result.updated_count || 0} atualizado(s)` })
      }

    } catch (error) {
      toast.error("Erro ao importar candidatos", { description: "Não foi possível salvar candidatos Pearch na base. Tente novamente." })
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
          email: revealedContacts[c.id]?.email ?? c.email ?? null,
          phone: revealedContacts[c.id]?.phone ?? c.phone ?? null,
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
          experiences: (c.experiences || []).map((exp: CandidateExperience) => ({
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

      toast.success("Candidatos salvos!", { description: result.message })

      // Limpar resultados de busca e mudar para a aba pendente
      setCandidates([])
      setShowSearchResults(false)
      setShowUnsavedWarningModal(false)
      {
        const pp = useNavGuardStore.getState().pendingProceed
        if (pp) { useNavGuardStore.getState().clear(); pp() }
      }
      if (ctx.pendingTabChange) {
        setActiveTab(ctx.pendingTabChange!)
        setPendingTabChange(null)
      }

    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido ao salvar candidatos'
      toast.error("Erro ao salvar", { description: errorMessage })
    } finally {
      setIsSavingToBase(false)
    }
  }

  // Handler para sair sem salvar
  const handleExitWithoutSaving = () => {
    setCandidates([])
    setShowSearchResults(false)
    setShowUnsavedWarningModal(false)
    {
      const pp = useNavGuardStore.getState().pendingProceed
      if (pp) { useNavGuardStore.getState().clear(); pp() }
    }
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
