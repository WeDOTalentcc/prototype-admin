"use client"

/**
 * useEligibilityTemplates — canonical hook para o catalogo dinamico per-tenant.
 *
 * Audit 2026-05-20 Sprint 1 F4: substitui o catalogo hardcoded
 * `src/components/settings/eligibility-questions-bank.ts` por fetch dinamico
 * via API endpoints F2 (POST /api/backend-proxy/eligibility-question-templates).
 *
 * Decisões Paulo 2026-05-20:
 * - A1: customize cria cópia total no DB (não override por field)
 * - B1: customize é snapshot canonical (não sincroniza com master após)
 * - C: admin tudo, recrutador create-novos OK mas não delete/update-de-outros
 * - Snapshot na vaga: vaga.eligibility_questions JSONB = cópia das perguntas
 *   selecionadas no momento do save (não link dinâmico).
 *
 * Pattern canonical: useState + fetch direto (sem React Query — projeto não
 * usa). Cache em-memory + invalidate manual via refetch().
 */

import { useCallback, useEffect, useState } from "react"

export type QuestionType = "text" | "yes_no" | "scale" | "multiple"

export type QuestionCategory =
  | "general"
  | "eligibility"
  | "availability"
  | "education"
  | "experience"
  | "languages"
  | "compensation"
  | "work_model"
  | "compliance"
  | "system_default"

export interface TriggerCondition {
  field: string
  operator: "equals" | "contains" | "greater_than"
  value: string | number | boolean
}

export interface EligibilityQuestionData {
  question: string
  type: QuestionType
  category: QuestionCategory
  contextHint?: string
  options?: string[]
  triggerCondition?: TriggerCondition
  linkedField?: string
  isSystemDefault?: boolean
  eliminatory?: boolean
  eliminatoryAnswer?: string | boolean
  legacy_id?: string
}

export interface EligibilityQuestionTemplate {
  id: string
  company_id: string | null
  is_master_template: boolean
  parent_template_id: string | null
  data: EligibilityQuestionData
  created_at: string
  updated_at: string
  created_by: string | null
  deleted_at: string | null
}

export interface ListResponse {
  items: EligibilityQuestionTemplate[]
  total: number
  master_count: number
  custom_count: number
}

interface UseEligibilityTemplatesResult {
  templates: EligibilityQuestionTemplate[]
  masterCount: number
  customCount: number
  total: number
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  createCustom: (data: EligibilityQuestionData) => Promise<EligibilityQuestionTemplate | null>
  updateTemplate: (
    id: string,
    data: EligibilityQuestionData,
  ) => Promise<EligibilityQuestionTemplate | null>
  deleteTemplate: (id: string) => Promise<boolean>
  customizeMaster: (
    masterId: string,
    overrides?: EligibilityQuestionData,
  ) => Promise<EligibilityQuestionTemplate | null>
}

export function useEligibilityTemplates(
  options: { includeMaster?: boolean } = {},
): UseEligibilityTemplatesResult {
  const { includeMaster = true } = options
  const [templates, setTemplates] = useState<EligibilityQuestionTemplate[]>([])
  const [masterCount, setMasterCount] = useState(0)
  const [customCount, setCustomCount] = useState(0)
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAll = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const qs = new URLSearchParams({
        include_master: String(includeMaster),
      }).toString()
      const res = await fetch(
        `/api/backend-proxy/eligibility-question-templates?${qs}`,
      )
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      const data: ListResponse = await res.json()
      setTemplates(data.items || [])
      setMasterCount(data.master_count ?? 0)
      setCustomCount(data.custom_count ?? 0)
      setTotal(data.total ?? 0)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar templates")
    } finally {
      setIsLoading(false)
    }
  }, [includeMaster])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  const createCustom = useCallback(
    async (data: EligibilityQuestionData) => {
      try {
        const res = await fetch(
          "/api/backend-proxy/eligibility-question-templates",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data }),
          },
        )
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        const created: EligibilityQuestionTemplate = await res.json()
        await fetchAll()
        return created
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao criar template")
        return null
      }
    },
    [fetchAll],
  )

  const updateTemplate = useCallback(
    async (id: string, data: EligibilityQuestionData) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/eligibility-question-templates/${encodeURIComponent(id)}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data }),
          },
        )
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        const updated: EligibilityQuestionTemplate = await res.json()
        await fetchAll()
        return updated
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao atualizar template")
        return null
      }
    },
    [fetchAll],
  )

  const deleteTemplate = useCallback(
    async (id: string) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/eligibility-question-templates/${encodeURIComponent(id)}`,
          { method: "DELETE" },
        )
        if (!res.ok && res.status !== 204) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        await fetchAll()
        return true
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao deletar template")
        return false
      }
    },
    [fetchAll],
  )

  const customizeMaster = useCallback(
    async (masterId: string, overrides?: EligibilityQuestionData) => {
      try {
        const res = await fetch(
          `/api/backend-proxy/eligibility-question-templates/${encodeURIComponent(masterId)}/customize`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(overrides ? { overrides } : {}),
          },
        )
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || err.error || `HTTP ${res.status}`)
        }
        const custom: EligibilityQuestionTemplate = await res.json()
        await fetchAll()
        return custom
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro ao customizar master")
        return null
      }
    },
    [fetchAll],
  )

  return {
    templates,
    masterCount,
    customCount,
    total,
    isLoading,
    error,
    refetch: fetchAll,
    createCustom,
    updateTemplate,
    deleteTemplate,
    customizeMaster,
  }
}



/**
 * Flat-shape canonical compatível com o antigo ELIGIBILITY_QUESTIONS_BANK.
 * Permite migração incremental de componentes consumindo o catalogo
 * hardcoded sem reescrever shape de props.
 *
 * server template: { id, data: { question, category, ... }, is_master_template, ... }
 * flat shape:      { id, question, category, ..., _isMaster, _legacyId }
 */
export interface FlatEligibilityQuestion {
  id: string  // serverId UUID
  question: string
  type: QuestionType
  category: QuestionCategory
  contextHint?: string
  options?: string[]
  triggerCondition?: TriggerCondition
  linkedField?: string
  isSystemDefault?: boolean
  eliminatory?: boolean
  eliminatoryAnswer?: string | boolean
  _isMaster: boolean
  _serverId: string
  _legacyId?: string
}

export function flattenTemplate(t: EligibilityQuestionTemplate): FlatEligibilityQuestion {
  return {
    ...t.data,
    id: t.id,
    _isMaster: t.is_master_template,
    _serverId: t.id,
    _legacyId: t.data.legacy_id,
  } as FlatEligibilityQuestion
}

export function flattenTemplates(items: EligibilityQuestionTemplate[]): FlatEligibilityQuestion[] {
  return items.map(flattenTemplate)
}

/**
 * QUESTION_CATEGORIES canonical (movido de eligibility-questions-bank.ts).
 * Mantém compatibilidade com componentes que importam essa estrutura.
 */
export const QUESTION_CATEGORIES: Record<
  QuestionCategory,
  { label: string; icon: string; color: string }
> = {
  general: { label: "Gerais", icon: "📋", color: "bg-lia-bg-tertiary text-lia-text-primary" },
  eligibility: { label: "Elegibilidade e Requisitos Legais", icon: "📋", color: "bg-wedo-cyan/15 text-wedo-cyan-dark" },
  availability: { label: "Disponibilidade e Mobilidade", icon: "✈️", color: "bg-status-success/15 text-status-success" },
  education: { label: "Formação e Certificações", icon: "🎓", color: "bg-wedo-purple/15 text-wedo-purple" },
  experience: { label: "Experiência Específica", icon: "💼", color: "bg-wedo-orange/15 text-wedo-orange" },
  languages: { label: "Idiomas", icon: "🌍", color: "bg-wedo-cyan/20 text-wedo-cyan-dark" },
  compensation: { label: "Remuneração e Contrato", icon: "💰", color: "bg-status-warning/15 text-status-warning" },
  work_model: { label: "Modelo de Trabalho", icon: "🏠", color: "bg-wedo-purple/15 text-wedo-purple" },
  compliance: { label: "Compliance e Conflito de Interesses", icon: "⚠️", color: "bg-status-error/15 text-status-error" },
  system_default: { label: "Perguntas Padrão do Sistema", icon: "⚙️", color: "bg-lia-bg-tertiary text-lia-text-primary" },
}
