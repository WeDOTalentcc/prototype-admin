"use client"

import { useCallback, useEffect, useState } from "react"
import { apiFetch } from "@/lib/api/api-fetch"

/**
 * Taxonomy v2 canonical de beneficios (2026-05-24).
 *
 * Single source of truth: lia-agent-system/app/domains/company/services/benefits_service.py
 *   BENEFIT_CATEGORIES (14)
 *   BENEFIT_VALUE_TYPES (6)
 *   BENEFIT_WAITING_PERIODS (9)
 *
 * Esse hook substitui as constantes hardcoded que existiam em
 * BenefitFormModal.tsx (BENEFIT_CATEGORIES, VALUE_TYPES, WAITING_PERIODS).
 *
 * canonical-fix: consumers herdam via API. NUNCA hardcodar uma segunda lista.
 */

export interface BenefitCategoryItem {
  id: string
  name: string
  icon: string
}

export interface BenefitValueTypeItem {
  id: string
  name: string
  icon: string // lucide-react icon name (DollarSign, Percent, Info, etc.)
}

export interface BenefitWaitingPeriodItem {
  id: number
  label: string
}

export interface BenefitTaxonomy {
  categories: BenefitCategoryItem[]
  valueTypes: BenefitValueTypeItem[]
  waitingPeriods: BenefitWaitingPeriodItem[]
  isLoading: boolean
  error: string | null
  refresh: () => void
}

/**
 * Fallback offline-safe — usado SOMENTE quando o fetch falha de vez
 * (rede caiu, backend down). Mantem UI funcional ao inves de mostrar
 * dropdown vazio. Reflete a taxonomy v2 canonical em snapshot.
 *
 * NAO usar como fonte de dados em codigo de aplicacao — sempre passe
 * pelo hook que vai chamar o endpoint canonical.
 */
const FALLBACK_CATEGORIES: BenefitCategoryItem[] = [
  { id: "health", name: "Saúde", icon: "🏥" },
  { id: "wellness", name: "Bem-estar", icon: "💪" },
  { id: "food", name: "Alimentação", icon: "🍽️" },
  { id: "transport", name: "Transporte", icon: "🚌" },
  { id: "education", name: "Educação & Desenvolvimento", icon: "📚" },
  { id: "financial", name: "Financeiro", icon: "💰" },
  { id: "retirement", name: "Previdência", icon: "🏛️" },
  { id: "family", name: "Família", icon: "👨‍👩‍👧" },
  { id: "parental", name: "Parental estendido", icon: "🤱" },
  { id: "flexibility", name: "Flexibilidade & Tempo", icon: "⏰" },
  { id: "equipment", name: "Equipamento & Home Office", icon: "💻" },
  { id: "culture", name: "Cultura & Lazer", icon: "🎭" },
  { id: "recognition", name: "Reconhecimento", icon: "🏆" },
  { id: "other", name: "Outros", icon: "📦" },
]

const FALLBACK_VALUE_TYPES: BenefitValueTypeItem[] = [
  { id: "monetary", name: "Valor fixo (R$)", icon: "DollarSign" },
  { id: "percentage", name: "Percentual do salário", icon: "Percent" },
  { id: "match", name: "Contrapartida da empresa", icon: "Repeat" },
  { id: "reimbursement", name: "Reembolso até limite", icon: "Receipt" },
  { id: "coverage", name: "Cobertura/franquia", icon: "Shield" },
  { id: "informative", name: "Apenas descrição", icon: "Info" },
]

const FALLBACK_WAITING_PERIODS: BenefitWaitingPeriodItem[] = [
  { id: 0, label: "Imediato" },
  { id: -1, label: "Após período de experiência (90 dias)" },
  { id: 30, label: "30 dias" },
  { id: 60, label: "60 dias" },
  { id: 90, label: "90 dias" },
  { id: 180, label: "180 dias (6 meses)" },
  { id: 365, label: "365 dias (1 ano)" },
  { id: 540, label: "540 dias (18 meses)" },
  { id: 730, label: "730 dias (2 anos)" },
]

export function useBenefitTaxonomy(): BenefitTaxonomy {
  const [categories, setCategories] = useState<BenefitCategoryItem[]>(FALLBACK_CATEGORIES)
  const [valueTypes, setValueTypes] = useState<BenefitValueTypeItem[]>(FALLBACK_VALUE_TYPES)
  const [waitingPeriods, setWaitingPeriods] = useState<BenefitWaitingPeriodItem[]>(
    FALLBACK_WAITING_PERIODS,
  )
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAll = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [catsRes, vtypesRes, periodsRes] = await Promise.all([
        apiFetch("/api/backend-proxy/company/benefits/categories/list"),
        apiFetch("/api/backend-proxy/company/benefits/value-types/list"),
        apiFetch("/api/backend-proxy/company/benefits/waiting-periods/list"),
      ])

      if (Array.isArray(catsRes)) setCategories(catsRes as BenefitCategoryItem[])
      if (Array.isArray(vtypesRes)) setValueTypes(vtypesRes as BenefitValueTypeItem[])
      if (Array.isArray(periodsRes))
        setWaitingPeriods(periodsRes as BenefitWaitingPeriodItem[])
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Erro ao carregar taxonomia de benefícios"
      // NAO silent fallback — sinalizamos erro mas mantemos FALLBACK_* pra UI funcionar.
      // canonical-fix REGRA 4: erro visivel + needs_manual_review pra usuario.
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  return {
    categories,
    valueTypes,
    waitingPeriods,
    isLoading,
    error,
    refresh: fetchAll,
  }
}
