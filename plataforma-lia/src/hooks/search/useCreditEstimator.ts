"use client"

import { useState, useCallback, useMemo } from "react"
import { 
  CreditEstimate, 
  CreditEstimateRequest,
  estimateCredits,
  calculateCreditsLocally,
  getCreditBalance,
  CreditBalance
} from "@/lib/api/candidate-search"

export interface CreditEstimatorOptions {
  searchType: "fast"
  limit: number
  highFreshness: boolean
  requireEmails: boolean
  showEmails: boolean
  requirePhoneNumbers: boolean
  showPhoneNumbers: boolean
  requirePhonesOrEmails: boolean
}

export interface CreditEstimatorState {
  estimate: CreditEstimate | null
  balance: CreditBalance | null
  isLoading: boolean
  error: string | null
}

export function useCreditEstimator() {
  const [state, setState] = useState<CreditEstimatorState>({
    estimate: null,
    balance: null,
    isLoading: false,
    error: null
  })

  const calculateLocal = useCallback((options: CreditEstimatorOptions): CreditEstimate => {
    return calculateCreditsLocally({
      searchType: options.searchType,
      limit: options.limit,
      highFreshness: options.highFreshness,
      requireEmails: options.requireEmails,
      showEmails: options.showEmails,
      requirePhoneNumbers: options.requirePhoneNumbers,
      showPhoneNumbers: options.showPhoneNumbers,
      requirePhonesOrEmails: options.requirePhonesOrEmails
    })
  }, [])

  const calculateFromServer = useCallback(async (
    query: string,
    options: CreditEstimatorOptions
  ): Promise<CreditEstimate> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    
    try {
      const request: CreditEstimateRequest = {
        query,
        pearch_type: options.searchType,
        limit: options.limit,
        high_freshness: options.highFreshness,
        require_emails: options.requireEmails,
        show_emails: options.showEmails,
        require_phone_numbers: options.requirePhoneNumbers,
        show_phone_numbers: options.showPhoneNumbers,
        require_phones_or_emails: options.requirePhonesOrEmails
      }
      
      const estimate = await estimateCredits(request)
      setState(prev => ({ ...prev, estimate, isLoading: false }))
      return estimate
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Erro ao calcular creditos"
      setState(prev => ({ ...prev, error: errorMessage, isLoading: false }))
      throw error
    }
  }, [])

  const fetchBalance = useCallback(async (): Promise<CreditBalance> => {
    try {
      const balance = await getCreditBalance()
      setState(prev => ({ ...prev, balance }))
      return balance
    } catch (error) {
      throw error
    }
  }, [])

  const canAfford = useMemo(() => {
    if (!state.estimate || !state.balance) return true
    return state.balance.available_credits >= state.estimate.total_estimated
  }, [state.estimate, state.balance])

  const reset = useCallback(() => {
    setState({
      estimate: null,
      balance: null,
      isLoading: false,
      error: null
    })
  }, [])

  return {
    ...state,
    calculateLocal,
    calculateFromServer,
    fetchBalance,
    canAfford,
    reset
  }
}

export function formatCreditCost(credits: number): string {
  if (credits === 0) return "Gratuito"
  if (credits === 1) return "1 credito"
  return `${credits} creditos`
}

export function getCostLevel(credits: number): "low" | "medium" | "high" | "very-high" {
  if (credits <= 10) return "low"
  if (credits <= 50) return "medium"
  if (credits <= 100) return "high"
  return "very-high"
}

export function getCostColor(level: "low" | "medium" | "high" | "very-high"): string {
  switch (level) {
    case "low": return "text-status-success"
    case "medium": return "text-status-warning"
    case "high": return "text-wedo-orange-text"
    case "very-high": return "text-status-error"
  }
}

export function getCostBgColor(level: "low" | "medium" | "high" | "very-high"): string {
  switch (level) {
    case "low": return "bg-status-success/10"
    case "medium": return "bg-status-warning/10"
    case "high": return "bg-wedo-orange/10"
    case "very-high": return "bg-status-error/10"
  }
}

export const CREDIT_COSTS = {
  searchType: {
    fast: 1,
  },
  insights: 1,
  profileScoring: 1,
  highFreshness: 2,
  apifyEnrichment: 0.01,
} as const

export function describeCostBreakdown(estimate: CreditEstimate): string[] {
  const lines: string[] = []
  
  lines.push(`Base (Busca Rapida): ${estimate.base_cost} creditos`)
  
  if (estimate.insights_cost > 0) {
    lines.push(`Insights + Scoring: +${estimate.insights_cost} creditos`)
  }
  
  if (estimate.freshness_cost > 0) {
    lines.push(`Dados Atualizados: +${estimate.freshness_cost} creditos`)
  }
  
  lines.push(`Enriquecimento Apify: $0.01/candidato (email + telefone)`)
  
  lines.push(`---`)
  lines.push(`Por candidato: ${estimate.cost_per_candidate} creditos + $0.01`)
  lines.push(`Total (${estimate.limit} candidatos): ${estimate.total_estimated} creditos`)
  
  return lines
}
