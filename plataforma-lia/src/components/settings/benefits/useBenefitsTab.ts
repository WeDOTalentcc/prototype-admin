"use client"

import { useCallback, useEffect, useState } from "react"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { useCompanyLiaInstructions } from "@/hooks/company/use-company-lia-instructions"
import type { BenefitTabRecord, BenefitTemplate } from "./benefits-types"
import { defaultBenefit } from "./benefits-types"

const normalizeBenefit = (benefit: Record<string, unknown>): BenefitTabRecord => {
  const seniorityRaw = benefit.seniority_levels
  const seniority_levels = Array.isArray(seniorityRaw)
    ? (seniorityRaw as string[])
    : seniorityRaw
    ? [String(seniorityRaw)]
    : ["all"]
  return {
    id: typeof benefit.id === "string" ? benefit.id : undefined,
    name: String(benefit.name || ""),
    category: String(benefit.category || "other"),
    description: String(benefit.description || ""),
    value_type: String(benefit.value_type || "informative"),
    value: typeof benefit.value === "number" ? benefit.value : undefined,
    percentage_value:
      typeof benefit.percentage_value === "number"
        ? benefit.percentage_value
        : undefined,
    value_details:
      typeof benefit.value_details === "string" ? benefit.value_details : "",
    seniority_levels,
    waiting_period_days: Number(benefit.waiting_period_days ?? 0),
    is_mandatory: Boolean(benefit.is_mandatory ?? false),
    is_active: Boolean(benefit.is_active ?? true),
    is_highlighted: Boolean(benefit.is_highlighted ?? false),
    is_discount: Boolean(benefit.is_discount ?? false),
    provider: typeof benefit.provider === "string" ? benefit.provider : "",
  }
}

export function useBenefitsTab() {
  const { companyId } = useCompanyId()
  const [benefits, setBenefits] = useState<BenefitTabRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [showBenefitModal, setShowBenefitModal] = useState(false)
  const [editingBenefit, setEditingBenefit] = useState<BenefitTabRecord | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [templates, setTemplates] = useState<BenefitTemplate[]>([])
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false)
  const [templateSearch, setTemplateSearch] = useState("")
  const [templateCategoryFilter, setTemplateCategoryFilter] = useState<string>("all")
  const [isEditingBenefits, setIsEditingBenefits] = useState(false)
  const [benefitsBackup, setBenefitsBackup] = useState<BenefitTabRecord[]>([])
  const [pendingChanges, setPendingChanges] = useState<Map<string, BenefitTabRecord>>(
    new Map()
  )

  const { config, refetch: refetchLia } = useCompanyLiaInstructions()
  const [liaToggles, setLiaToggles] = useState<Record<string, boolean>>({})
  const [liaInstructions, setLiaInstructions] = useState<Record<string, string>>({})

  useEffect(() => {
    if (config) {
      setLiaToggles(config.lia_field_toggles || { benefits: true })
      setLiaInstructions(config.lia_instructions || {})
    }
  }, [config])

  const flashSuccess = (msg: string) => {
    setSuccessMessage(msg)
    setTimeout(() => setSuccessMessage(null), 3000)
  }
  const flashError = (msg: string) => {
    setError(msg)
    setTimeout(() => setError(null), 3000)
  }

  const getCompanyId = useCallback(async (): Promise<string> => {
    if (companyId) return companyId
    try {
      const res = await fetch('/api/backend-proxy/company/profile')
      if (res.ok) {
        const company = await res.json()
        return company.id || ''
      }
    } catch {
      // fall through
    }
    return ''
  }, [companyId])

  const saveLiaFieldToggles = useCallback(
    async (
      toggles: Record<string, boolean>,
      instructions?: Record<string, string>
    ) => {
      try {
        const cid = await getCompanyId()
        const response = await fetch(
          `/api/backend-proxy/company/culture-profile/${encodeURIComponent(cid)}`,
          {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              lia_field_toggles: toggles,
              lia_instructions: instructions || liaInstructions,
            }),
          }
        )
        if (response.ok) {
          await refetchLia()
        }
      } catch {
        // silent
      }
    },
    [getCompanyId, liaInstructions, refetchLia]
  )

  const handleLiaToggleChange = useCallback(
    (fieldKey: string, isActive: boolean) => {
      const updatedToggles = { ...liaToggles, [fieldKey]: isActive }
      setLiaToggles(updatedToggles)
      saveLiaFieldToggles(updatedToggles)
    },
    [liaToggles, saveLiaFieldToggles]
  )

  const handleLiaInstructionSave = useCallback(
    async (fieldKey: string, instruction: string) => {
      const updatedInstructions = { ...liaInstructions, [fieldKey]: instruction }
      setLiaInstructions(updatedInstructions)
      await saveLiaFieldToggles(liaToggles, updatedInstructions)
    },
    [liaInstructions, liaToggles, saveLiaFieldToggles]
  )

  const loadBenefits = useCallback(async () => {
    setIsLoading(true)
    try {
      const cid = companyId || ''
      const response = await fetch(
        `/api/backend-proxy/company/benefits/?company_id=${encodeURIComponent(cid)}`
      )
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
  }, [companyId])

  useEffect(() => {
    loadBenefits()
  }, [loadBenefits])

  const loadTemplates = useCallback(async () => {
    setIsLoadingTemplates(true)
    try {
      const response = await fetch('/api/backend-proxy/benefits/templates')
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
      await fetch('/api/backend-proxy/benefits/templates', { method: 'POST' })
      await loadTemplates()
    } catch {
      // silent
    }
  }, [loadTemplates])

  useEffect(() => {
    if (showTemplateModal && templates.length === 0) {
      loadTemplates().then(() => {
        if (templates.length === 0) {
          seedTemplates()
        }
      })
    }
  }, [showTemplateModal, templates.length, loadTemplates, seedTemplates])

  const handleAddTemplateDirectly = async (template: BenefitTemplate) => {
    const newBenefit: BenefitTabRecord = {
      ...defaultBenefit,
      name: template.name,
      description: template.description || "",
      category: template.category,
      value_type: "informative",
      is_highlighted: template.is_popular,
    }
    try {
      const response = await fetch(
        `/api/backend-proxy/company/benefits/?company_id=${encodeURIComponent(companyId || '')}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newBenefit),
        }
      )
      if (response.ok) {
        await loadBenefits()
        flashSuccess(`Benefício"${template.name}" adicionado com sucesso!`)
      } else {
        throw new Error('Falha ao adicionar benefício')
      }
    } catch {
      flashError("Erro ao adicionar benefício")
    }
  }

  const handleSelectTemplate = (template: BenefitTemplate) => {
    handleAddTemplateDirectly(template)
  }

  const isTemplateAlreadyAdded = (templateName: string) =>
    benefits.some(b => b.name.toLowerCase() === templateName.toLowerCase())

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

  const handleSaveBenefit = async (benefit: BenefitTabRecord) => {
    setIsSaving(true)
    setError(null)
    try {
      const cid = encodeURIComponent(companyId || '')
      const url = benefit.id
        ? `/api/backend-proxy/company/benefits/${benefit.id}?company_id=${cid}`
        : `/api/backend-proxy/company/benefits/?company_id=${cid}`
      const response = await fetch(url, {
        method: benefit.id ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(benefit),
      })
      if (response.ok) {
        await loadBenefits()
        setShowBenefitModal(false)
        setEditingBenefit(null)
        flashSuccess(
          benefit.id
            ? 'Benefício atualizado com sucesso!'
            : 'Benefício criado com sucesso!'
        )
      } else {
        throw new Error('Falha ao salvar benefício')
      }
    } catch {
      flashError("Erro ao salvar benefício")
    } finally {
      setIsSaving(false)
    }
  }

  const handleDeleteBenefit = async (benefitId: string) => {
    if (typeof window !== 'undefined' && !window.confirm("Tem certeza que deseja excluir este benefício?"))
      return
    try {
      const response = await fetch(
        `/api/backend-proxy/company/benefits/${benefitId}?company_id=${encodeURIComponent(companyId || '')}`,
        { method: 'DELETE' }
      )
      if (response.ok) {
        await loadBenefits()
        flashSuccess('Benefício excluído com sucesso!')
      }
    } catch {
      flashError("Erro ao excluir benefício")
    }
  }

  const handleToggleBenefitStatus = (benefit: BenefitTabRecord) => {
    if (!benefit.id) return
    const benefitId = benefit.id
    const updatedBenefit = { ...benefit, is_active: !benefit.is_active }
    setBenefits(prev => prev.map(b => (b.id === benefitId ? updatedBenefit : b)))
    setPendingChanges(prev => {
      const next = new Map(prev)
      next.set(benefitId, updatedBenefit)
      return next
    })
  }

  const handleEnterEditMode = () => {
    setBenefitsBackup([...benefits])
    setPendingChanges(new Map())
    setIsEditingBenefits(true)
  }

  const handleCancelEdit = () => {
    setBenefits(benefitsBackup)
    setPendingChanges(new Map())
    setIsEditingBenefits(false)
  }

  const handleSaveChanges = async () => {
    if (pendingChanges.size === 0) {
      setIsEditingBenefits(false)
      return
    }
    setIsSaving(true)
    setError(null)
    try {
      const cid = encodeURIComponent(companyId || '')
      const savePromises = Array.from(pendingChanges.values()).map(benefit =>
        fetch(
          `/api/backend-proxy/company/benefits/${benefit.id}?company_id=${cid}`,
          {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(benefit),
          }
        )
      )
      const results = await Promise.all(savePromises)
      const allSuccess = results.every(r => r.ok)
      if (allSuccess) {
        await loadBenefits()
        flashSuccess('Alterações salvas com sucesso!')
      } else {
        throw new Error('Algumas alterações não puderam ser salvas')
      }
    } catch {
      flashError("Erro ao salvar alterações")
    } finally {
      setIsSaving(false)
      setPendingChanges(new Map())
      setIsEditingBenefits(false)
    }
  }

  return {
    // data
    benefits,
    templates,
    isLoading,
    isLoadingTemplates,
    isSaving,
    successMessage,
    error,
    // modal state
    showBenefitModal,
    setShowBenefitModal,
    editingBenefit,
    setEditingBenefit,
    showTemplateModal,
    setShowTemplateModal,
    // template filters
    templateSearch,
    setTemplateSearch,
    templateCategoryFilter,
    setTemplateCategoryFilter,
    filteredTemplates,
    // edit mode
    isEditingBenefits,
    handleEnterEditMode,
    handleCancelEdit,
    handleSaveChanges,
    // CRUD
    handleSaveBenefit,
    handleDeleteBenefit,
    handleToggleBenefitStatus,
    handleSelectTemplate,
    isTemplateAlreadyAdded,
    // LIA
    liaToggles,
    liaInstructions,
    handleLiaToggleChange,
    handleLiaInstructionSave,
  }
}
