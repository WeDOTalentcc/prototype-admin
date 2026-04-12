"use client"

/**
 * useSearchSource — Controle de fonte de busca (local/hybrid/global) + créditos Pearch.
 *
 * Extraído de ExpandableAIPrompt (P1-E).
 * Gerencia: searchSource, modal de confirmação de mudança, tipo Pearch, limite de candidatos,
 * filtros de contato e integração com useCreditEstimator.
 *
 * Portabilidade Vue: mapeia para composable useSearchSource().
 */

import { useState, useEffect } from "react"
import { useCreditEstimator } from "@/hooks/search/useCreditEstimator"
import { useGlobalSearchSettings } from "@/hooks/search/useGlobalSearchSettings"
import type { SearchSource } from "@/components/search/expandable-ai-prompt.types"

export interface UseSearchSourceResult {
  searchSource: SearchSource
  setSearchSource: (s: SearchSource) => void
  showSourceChangeModal: boolean
  setShowSourceChangeModal: (v: boolean) => void
  pendingSourceChange: 'hybrid' | 'global' | null
  pearchSearchType: 'fast'
  setPearchSearchType: (t: 'fast') => void
  candidateLimit: number
  setCandidateLimit: (n: number) => void
  requireEmails: boolean
  setRequireEmails: (v: boolean) => void
  requirePhoneNumbers: boolean
  setRequirePhoneNumbers: (v: boolean) => void
  showGlobalSearchOptions: boolean
  creditEstimator: ReturnType<typeof useCreditEstimator>
  handleSourceChange: (newSource: SearchSource) => void
  confirmSourceChange: () => void
}

export function useSearchSource(): UseSearchSourceResult {
  const { settings: globalSettings, loading: globalSettingsLoading } = useGlobalSearchSettings()
  const creditEstimator = useCreditEstimator()

  const showGlobalSearchOptions = !globalSettingsLoading && globalSettings.globalSearchEnabled

  const [searchSource, setSearchSource] = useState<SearchSource>('local')
  const [showSourceChangeModal, setShowSourceChangeModal] = useState(false)
  const [pendingSourceChange, setPendingSourceChange] = useState<'hybrid' | 'global' | null>(null)
  const [pearchSearchType, setPearchSearchType] = useState<'fast'>('fast')
  const [candidateLimit, setCandidateLimit] = useState(15)
  const [requireEmails, setRequireEmails] = useState(false)
  const [requirePhoneNumbers, setRequirePhoneNumbers] = useState(false)

  // Reset para local se global search for desabilitado
  useEffect(() => {
    if (!showGlobalSearchOptions && (searchSource === 'hybrid' || searchSource === 'global')) {
      setSearchSource('local')
    }
  }, [showGlobalSearchOptions, searchSource])

  // Carrega saldo de créditos quando fonte muda para global/hybrid
  useEffect(() => {
    if (searchSource !== 'local') {
      creditEstimator.fetchBalance().catch(() => { /* TODO: integrar com Sentry */ })
    }
  }, [searchSource]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSourceChange = (newSource: SearchSource) => {
    if (newSource === 'local') {
      setSearchSource('local')
    } else {
      setPendingSourceChange(newSource)
      setShowSourceChangeModal(true)
    }
  }

  const confirmSourceChange = () => {
    if (pendingSourceChange) {
      setSearchSource(pendingSourceChange)
      setPendingSourceChange(null)
      setShowSourceChangeModal(false)
    }
  }

  return {
    searchSource,
    setSearchSource,
    showSourceChangeModal,
    setShowSourceChangeModal,
    pendingSourceChange,
    pearchSearchType,
    setPearchSearchType,
    candidateLimit,
    setCandidateLimit,
    requireEmails,
    setRequireEmails,
    requirePhoneNumbers,
    setRequirePhoneNumbers,
    showGlobalSearchOptions,
    creditEstimator,
    handleSourceChange,
    confirmSourceChange,
  }
}
