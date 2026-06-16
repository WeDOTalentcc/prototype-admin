"use client"

import { useCallback, useEffect, useState } from "react"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { useCompanyLiaInstructions } from "@/hooks/company/use-company-lia-instructions"
import { apiFetch } from "@/lib/api/api-fetch"
import { notifyChatOfSettingsUpdate } from "@/lib/api/settings-notify"
import { useBenefitsData } from "./useBenefitsData"
import { useBenefitsModals } from "./useBenefitsModals"
import type { BenefitTabRecord } from "./benefits-types"

/**
 * useBenefitsTab — thin compositor.
 *
 * Antes: 490 LOC, 20 useState
 * Depois: ~110 LOC, 4 useState (isSaving+error+liaToggles+liaInstructions derivados de sub-hooks)
 *
 * Delegação:
 *   useBenefitsData  → server state + CRUD (Grupo A)
 *   useBenefitsModals → modal/edit UI state (Grupo B)
 *   useCompanyLiaInstructions → lia config (Grupo C, read)
 *   saveLiaFieldToggles (local) → lia write (thin, depende de companyId)
 *
 * API pública permanece idêntica — BenefitsTab.tsx não muda.
 */
export function useBenefitsTab() {
  const { companyId } = useCompanyId()
  const modals = useBenefitsModals()
  const data = useBenefitsData(modals.templateSearch, modals.templateCategoryFilter)
  const { config, refetch: refetchLia } = useCompanyLiaInstructions()

  // Grupo C — LIA toggles/instructions derivados do config canônico
  const [liaToggles, setLiaToggles] = useState<Record<string, boolean>>({})
  const [liaInstructions, setLiaInstructions] = useState<Record<string, string>>({})

  useEffect(() => {
    if (config) {
      setLiaToggles(config.lia_field_toggles || { benefits: true })
      setLiaInstructions(config.lia_instructions || {})
    }
  }, [config])

  // Bootstrap: carregar benefits na montagem
  useEffect(() => {
    if (companyId) {
      data.loadBenefits()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyId])

  // Bootstrap: carregar templates quando o modal abre
  useEffect(() => {
    if (modals.showTemplateModal && data.templates.length === 0) {
      data.loadTemplates().then(() => {
        if (data.templates.length === 0) {
          data.seedTemplates()
        }
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modals.showTemplateModal])

  // LIA write helpers — ficam aqui pois dependem de companyId + liaInstructions locais
  const getCompanyId = useCallback(async (): Promise<string> => {
    if (companyId) return companyId
    try {
      const res = await apiFetch('/api/backend-proxy/company/profile')
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
    async (toggles: Record<string, boolean>, instructions?: Record<string, string>) => {
      try {
        const cid = await getCompanyId()
        const response = await apiFetch(
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

  // Edit mode handlers bridge (useBenefitsModals não faz fetch; useBenefitsData expõe setBenefits)
  const handleEnterEditMode = useCallback(() => {
    modals.handleEnterEditMode(data.benefits)
  }, [modals, data.benefits])

  const handleCancelEdit = useCallback(() => {
    data.setBenefits(modals.getBenefitsBackup())
    modals.handleCancelEditMode()
  }, [data, modals])

  const handleToggleBenefitStatus = useCallback((benefit: BenefitTabRecord) => {
    if (!benefit.id) return
    const updatedBenefit = { ...benefit, is_active: !benefit.is_active }
    data.setBenefits(prev => prev.map(b => (b.id === benefit.id ? updatedBenefit : b)))
    modals.handlePendingChange(updatedBenefit)
  }, [data, modals])

  const handleSaveChanges = useCallback(async () => {
    const entries = Object.values(modals.pendingChanges)
    if (entries.length === 0) {
      modals.resetEditMode()
      return
    }
    // delegate isSaving/error/flash to data layer via handleSaveBenefit loop
    const savePromises = entries.map(benefit => {
      const { company_id: _strip, ...benefitWithoutCompanyId } =
        benefit as BenefitTabRecord & { company_id?: string }
      void _strip
      return apiFetch(`/api/backend-proxy/company/benefits/${benefit.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(benefitWithoutCompanyId),
      })
    })
    try {
      const results = await Promise.all(savePromises)
      const allSuccess = results.every(r => r.ok)
      if (allSuccess) {
        await data.loadBenefits()
        notifyChatOfSettingsUpdate({
          actionId: "bulk_update_benefits",
          section: "benefits",
          field: "bulk",
          value: results.length,
        })
        data.flashSuccess('Alterações salvas com sucesso!')
      } else {
        throw new Error('Algumas alterações não puderam ser salvas')
      }
    } catch {
      data.flashError("Erro ao salvar alterações")
    } finally {
      modals.resetEditMode()
    }
  }, [modals, data])

  // Delegate handleSaveBenefit to close modal after save
  const handleSaveBenefit = useCallback(async (benefit: BenefitTabRecord) => {
    await data.handleSaveBenefit(benefit)
    modals.setShowBenefitModal(false)
    modals.setEditingBenefit(null)
  }, [data, modals])

  return {
    // data
    benefits: data.benefits,
    templates: data.templates,
    isLoading: data.isLoading,
    isLoadingTemplates: data.isLoadingTemplates,
    isSaving: data.isSaving,
    successMessage: data.successMessage,
    error: data.error,
    // modal state
    showBenefitModal: modals.showBenefitModal,
    setShowBenefitModal: modals.setShowBenefitModal,
    editingBenefit: modals.editingBenefit,
    setEditingBenefit: modals.setEditingBenefit,
    showTemplateModal: modals.showTemplateModal,
    setShowTemplateModal: modals.setShowTemplateModal,
    // template filters
    templateSearch: modals.templateSearch,
    setTemplateSearch: modals.setTemplateSearch,
    templateCategoryFilter: modals.templateCategoryFilter,
    setTemplateCategoryFilter: modals.setTemplateCategoryFilter,
    filteredTemplates: data.filteredTemplates,
    // edit mode
    isEditingBenefits: modals.isEditingBenefits,
    handleEnterEditMode,
    handleCancelEdit,
    handleSaveChanges,
    // CRUD
    handleSaveBenefit,
    handleDeleteBenefit: data.handleDeleteBenefit,
    handleToggleBenefitStatus,
    handleSelectTemplate: data.handleSelectTemplate,
    isTemplateAlreadyAdded: data.isTemplateAlreadyAdded,
    // history
    benefitHistory: data.benefitHistory,
    historyLoading: data.historyLoading,
    loadBenefitHistory: data.loadBenefitHistory,
    // LIA
    liaToggles,
    liaInstructions,
    handleLiaToggleChange,
    handleLiaInstructionSave,
  }
}
