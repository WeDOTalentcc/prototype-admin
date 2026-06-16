"use client"

import { useState, useCallback } from "react"
import { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import { SearchFilters } from "@/components/search/advanced-filters-modal"

export type SearchFlowState = 
  | "idle"                    // Estado inicial - nenhuma busca ativa
  | "collecting_profile"      // LIA pediu detalhes do perfil, SmartSearch ativo
  | "searching"               // Buscando candidatos (local + preview Pearch)
  | "showing_preview"         // Mostrando preview com estimativa de créditos
  | "awaiting_confirmation"   // Aguardando confirmação para busca híbrida
  | "showing_results"         // Resultados finais exibidos

export interface SearchFlowData {
  query: string
  entities: ParsedEntities
  localCount: number
  pearchEstimate: number
  pearchCredits: number
  threadId?: string
  hasSearched: boolean
  mode: SearchMode
  metadata: SearchMetadata
  filters: SearchFilters
}

export interface SubmitSearchParams {
  query: string
  entities: ParsedEntities
  mode?: SearchMode
  metadata?: SearchMetadata
  filters?: SearchFilters
}

export interface UseSearchFlowReturn {
  flowState: SearchFlowState
  flowData: SearchFlowData
  startProfileCollection: () => void
  submitSearch: (params: SubmitSearchParams) => void
  confirmHybridSearch: () => void
  cancelSearch: () => void
  showResults: () => void
  reset: () => void
  setLocalResults: (count: number) => void
  setPearchPreview: (estimate: number, credits: number, threadId?: string) => void
  updateFilters: (filters: SearchFilters) => void
}

const initialFlowData: SearchFlowData = {
  query: "",
  entities: {},
  localCount: 0,
  pearchEstimate: 0,
  pearchCredits: 0,
  threadId: undefined,
  hasSearched: false,
  mode: "natural",
  metadata: { mode: "natural" },
  filters: {}
}

export function useSearchFlow(): UseSearchFlowReturn {
  const [flowState, setFlowState] = useState<SearchFlowState>("idle")
  const [flowData, setFlowData] = useState<SearchFlowData>(initialFlowData)

  const startProfileCollection = useCallback(() => {
    setFlowState("collecting_profile")
    setFlowData(prev => ({ ...prev, hasSearched: false }))
  }, [])

  const submitSearch = useCallback((params: SubmitSearchParams) => {
    const { query, entities, mode = "natural", metadata, filters = {} } = params
    const finalMetadata: SearchMetadata = metadata || { mode: mode }
    setFlowData(prev => ({
      ...prev,
      query,
      entities,
      mode,
      metadata: finalMetadata,
      filters,
      hasSearched: true
    }))
    setFlowState("searching")
  }, [])

  const updateFilters = useCallback((filters: SearchFilters) => {
    setFlowData(prev => ({ ...prev, filters }))
  }, [])

  const setLocalResults = useCallback((count: number) => {
    setFlowData(prev => ({ ...prev, localCount: count }))
  }, [])

  const setPearchPreview = useCallback((estimate: number, credits: number, threadId?: string) => {
    setFlowData(prev => ({
      ...prev,
      pearchEstimate: estimate,
      pearchCredits: credits,
      threadId
    }))
    setFlowState("showing_preview")
  }, [])

  const confirmHybridSearch = useCallback(() => {
    setFlowState("awaiting_confirmation")
  }, [])

  const showResults = useCallback(() => {
    setFlowState("showing_results")
  }, [])

  const cancelSearch = useCallback(() => {
    setFlowState("idle")
    setFlowData(initialFlowData)
  }, [])

  const reset = useCallback(() => {
    setFlowState("idle")
    setFlowData(initialFlowData)
  }, [])

  return {
    flowState,
    flowData,
    startProfileCollection,
    submitSearch,
    confirmHybridSearch,
    cancelSearch,
    showResults,
    reset,
    setLocalResults,
    setPearchPreview,
    updateFilters
  }
}
