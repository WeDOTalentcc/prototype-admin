"use client"

import { useCallback, useState } from "react"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import type { BenefitTabRecord, BenefitTemplate, BenefitHistoryEntry } from "./benefits-types"
import { defaultBenefit } from "./benefits-types"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"

const toStringArray = (raw: unknown, fallback: string[]): string[] => {
  if (Array.isArray(raw)) return raw.map((x) => String(x))
  if (raw === undefined || raw === null) return fallback
  return [String(raw)]
}

const toRecord = (raw: unknown): Record<string, unknown> => {
  if (raw && typeof raw === "object" && !Array.isArray(raw)) {
    return raw as Record<string, unknown>
  }
  return {}
}

export const normalizeBenefit = (benefit: Record<string, unknown>): BenefitTabRecord => ({
  id: typeof benefit.id === "string" ? benefit.id : undefined,
  name: String(benefit.name || ""),
  category: String(benefit.category || "other"),
  description: String(benefit.description || ""),
  icon:
    typeof benefit.icon === "string" && benefit.icon.length > 0
      ? benefit.icon
      : undefined,
  value_type: String(benefit.value_type || "informative"),
  value: typeof benefit.value === "number" ? benefit.value : undefined,
  percentage_value:
    typeof benefit.percentage_value === "number" ? benefit.percentage_value : undefined,
  value_details:
    typeof benefit.value_details === "string" ? benefit.value_details : "",
  applicable_to: toStringArray(benefit.applicable_to, ["all"]),
  seniority_levels: toStringArray(benefit.seniority_levels, ["all"]),
  contract_types: toStringArray(benefit.contract_types, []),
  departments: toRecord(benefit.departments),
  waiting_period_days: Number(benefit.waiting_period_days ?? 0),
  is_mandatory: Boolean(benefit.is_mandatory ?? false),
  is_active: Boolean(benefit.is_active ?? true),
  is_highlighted: Boolean(benefit.is_highlighted ?? false),
  is_discount: Boolean(benefit.is_discount ?? false),
  order: Number(benefit.order ?? 0),
  provider: typeof benefit.provider === "string" ? benefit.provider : "",
  provider_contact:
    typeof benefit.provider_contact === "string" ? benefit.provider_contact : "",
  subsidiaries: Array.isArray(benefit.subsidiaries)
    ? (benefit.subsidiaries as Array<{ name: string; cnpj?: string | null }>)
    : [],
  valid_from: typeof benefit.valid_from === "string" ? benefit.valid_from : null,
  valid_until: typeof benefit.valid_until === "string" ? benefit.valid_until : null,
  review_frequency_months:
    typeof benefit.review_frequency_months === "number"
      ? benefit.review_frequency_months
      : null,
  next_review_date:
    typeof benefit.next_review_date === "string" ? benefit.next_review_date : null,
  provider_cnpj:
    typeof benefit.provider_cnpj === "string" ? benefit.provider_cnpj : null,
})

export interface BenefitsDataApi {
  // data
  benefits: BenefitTabRecord[]
  setBenefits: React.Dispatch<React.SetStateAction<BenefitTabRecord[]>>
  templates: BenefitTemplate[]
  isLoading: boolean
  isLoadingTemplates: boolean
  isSaving: boolean
  successMessage: string | null
  error: string | null
  benefitHistory: BenefitHistoryEntry[]
  historyLoading: boolean
  filteredTemplates: BenefitTemplate[]
  // actions
  loadBenefits: () => Promise<void>
  loadTemplates: () => Promise<void>
  seedTemplates: () => Promise<void>
  handleSaveBenefit: (benefit: BenefitTabRecord) => Promise<void>
  handleDeleteBenefit: (benefitId: string) => Promise<void>
  handleAddTemplateDirectly: (template: BenefitTemplate) => Promise<void>
  handleSelectTemplate: (template: BenefitTemplate) => void
  isTemplateAlreadyAdded: (templateName: string) => boolean
  loadBenefitHistory: (benefitId: string) => Promise<void>
  flashSuccess: (msg: string) => void
  flashError: (msg: string) => void
}

/**
 * useBenefitsData — Grupo A: server state (benefits, templates, history) + CRUD handlers.
 * NÃO contém modal/UI state nem LIA toggles.
 * templateSearch e templateCategoryFilter são passados como parâmetros para filteredTemplates.
 */
export function useBenefitsData(
  templateSearch: string,
  templateCategoryFilter: string
): BenefitsDataApi {
  const { companyId } = useCompanyId()

  const [benefits, setBenefits] = useState<BenefitTabRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [benefitHistory, setBenefitHistory] = useState<BenefitHistoryEntry[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [templates, setTemplates] = useState<BenefitTemplate[]>([])
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false)

  const flashSuccess = useCallback((msg: string) => {
    setSuccessMessage(msg)
    setTimeout(() => setSuccessMessage(null), 3000)
  }, [])

  const flashError = useCallback((msg: string) => {
    setError(msg)
    setTimeout(() => setError(null), 3000)
  }, [])

  const loadBenefits = useCallback(async () => {
    if (!companyId) return
    setIsLoading(true)
    try {
      const response = await apiFetch(`/api/backend-proxy/company/benefits/`)
      if (response.ok) {
        const data = await response.json()
        const rawBenefits = Array.isArray(data) ? data : data.items || []
        setBenefits((rawBenefits as Record<string, unknown>[]).map(normalizeBenefit))
      }
    } catch {
      flashError("Erro ao carregar benefícios")
    } finally {
      setIsLoading(false)
    }
  }, [companyId, flashError])

  const loadTemplates = useCallback(async () => {
    setIsLoadingTemplates(true)
    try {
      const response = await apiFetch('/api/backend-proxy/benefits/templates')
      if (response.ok) {
        const data = await response.json()
        setTemplates(data.items || [])
      }
    } catch {
      // silent
    } finally {
      setIsLoadingTemplates(false)
    }
  }, [])

  const seedTemplates = useCallback(async () => {
    try {
      await apiFetch('/api/backend-proxy/benefits/templates', { method: 'POST' })
      await loadTemplates()
      notifyChatOfSettingsUpdate({ actionId: "seed_benefit_templates", section: "benefits" })
    } catch {
      // silent
    }
  }, [loadTemplates])

  const handleAddTemplateDirectly = useCallback(async (template: BenefitTemplate) => {
    const newBenefit: BenefitTabRecord = {
      ...defaultBenefit,
      name: template.name,
      description: template.description || "",
      category: template.category,
      value_type: "informative",
      is_highlighted: template.is_popular,
    }
    try {
      const response = await apiFetch(`/api/backend-proxy/company/benefits/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newBenefit),
      })
      if (response.ok) {
        await loadBenefits()
        notifyChatOfSettingsUpdate({
          actionId: "add_benefit_from_template",
          section: "benefits",
          field: template.name,
          value: template.category,
        })
        flashSuccess(`Benefício "${template.name}" adicionado com sucesso!`)
      } else {
        throw new Error('Falha ao adicionar benefício')
      }
    } catch {
      flashError("Erro ao adicionar benefício")
    }
  }, [loadBenefits, flashSuccess, flashError])

  const handleSelectTemplate = useCallback(
    (template: BenefitTemplate) => { handleAddTemplateDirectly(template) },
    [handleAddTemplateDirectly]
  )

  const isTemplateAlreadyAdded = useCallback(
    (templateName: string) =>
      benefits.some(b => b.name.toLowerCase() === templateName.toLowerCase()),
    [benefits]
  )

  const handleSaveBenefit = useCallback(async (benefit: BenefitTabRecord) => {
    setIsSaving(true)
    setError(null)
    try {
      const url = benefit.id
        ? `/api/backend-proxy/company/benefits/${benefit.id}`
        : `/api/backend-proxy/company/benefits/`
      // REGRA 2 canonical: NUNCA enviar company_id no body — backend rejeita.
      const { company_id: _strip, ...benefitWithoutCompanyId } =
        benefit as BenefitTabRecord & { company_id?: string }
      void _strip
      const response = await apiFetch(url, {
        method: benefit.id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(benefitWithoutCompanyId),
      })
      if (response.ok) {
        await loadBenefits()
        flashSuccess(benefit.id ? 'Benefício atualizado com sucesso!' : 'Benefício criado com sucesso!')
      } else {
        throw new Error('Falha ao salvar benefício')
      }
    } catch {
      flashError("Erro ao salvar benefício")
    } finally {
      setIsSaving(false)
    }
  }, [loadBenefits, flashSuccess, flashError])

  const handleDeleteBenefit = useCallback(async (benefitId: string) => {
    if (typeof window !== 'undefined' && !window.confirm("Tem certeza que deseja excluir este benefício?"))
      return
    try {
      const response = await apiFetch(
        `/api/backend-proxy/company/benefits/${benefitId}`,
        { method: 'DELETE' }
      )
      if (response.ok) {
        await loadBenefits()
        notifyChatOfSettingsUpdate({ actionId: "delete_benefit", section: "benefits", field: benefitId })
        flashSuccess('Benefício excluído com sucesso!')
      }
    } catch {
      flashError("Erro ao excluir benefício")
    }
  }, [loadBenefits, flashSuccess, flashError])

  const loadBenefitHistory = useCallback(async (benefitId: string) => {
    setHistoryLoading(true)
    setBenefitHistory([])
    try {
      const response = await apiFetch(
        `/api/backend-proxy/company/benefits/${benefitId}/history`,
        { headers: { "Content-Type": "application/json" } }
      )
      if (response.ok) {
        const data = await response.json()
        setBenefitHistory(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error("[benefitHistory]", err)
    } finally {
      setHistoryLoading(false)
    }
  }, [])

  const filteredTemplates = templates.filter(template => {
    const search = templateSearch.trim().toLowerCase()
    const matchesSearch =
      search === "" ||
      template.name.toLowerCase().includes(search) ||
      (template.description && template.description.toLowerCase().includes(search))
    const matchesCategory =
      templateCategoryFilter === "all" || template.category === templateCategoryFilter
    return matchesSearch && matchesCategory
  })

  return {
    benefits,
    setBenefits,
    templates,
    isLoading,
    isLoadingTemplates,
    isSaving,
    successMessage,
    error,
    benefitHistory,
    historyLoading,
    filteredTemplates,
    loadBenefits,
    loadTemplates,
    seedTemplates,
    handleSaveBenefit,
    handleDeleteBenefit,
    handleAddTemplateDirectly,
    handleSelectTemplate,
    isTemplateAlreadyAdded,
    loadBenefitHistory,
    flashSuccess,
    flashError,
  }
}
