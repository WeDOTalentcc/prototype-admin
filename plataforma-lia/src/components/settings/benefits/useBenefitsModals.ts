"use client"

import { useCallback, useState } from "react"
import type { BenefitTabRecord } from "./benefits-types"

export interface BenefitsModalsApi {
  // modal state
  showBenefitModal: boolean
  setShowBenefitModal: React.Dispatch<React.SetStateAction<boolean>>
  editingBenefit: BenefitTabRecord | null
  setEditingBenefit: React.Dispatch<React.SetStateAction<BenefitTabRecord | null>>
  showTemplateModal: boolean
  setShowTemplateModal: React.Dispatch<React.SetStateAction<boolean>>
  // template filters
  templateSearch: string
  setTemplateSearch: React.Dispatch<React.SetStateAction<string>>
  templateCategoryFilter: string
  setTemplateCategoryFilter: React.Dispatch<React.SetStateAction<string>>
  // inline edit mode
  isEditingBenefits: boolean
  // pendingChanges as Record (no Map — React identity comparison works correctly with plain objects)
  pendingChanges: Record<string, BenefitTabRecord>
  // handlers
  handleEnterEditMode: (benefits: BenefitTabRecord[]) => void
  handleCancelEditMode: () => void
  handlePendingChange: (benefit: BenefitTabRecord) => void
  resetEditMode: () => void
  getBenefitsBackup: () => BenefitTabRecord[]
}

/**
 * useBenefitsModals — Grupo B: modal open/close state, template filters, inline edit mode.
 * Thin (~60 LOC). NÃO faz fetch nem chama APIs.
 *
 * Fix: pendingChanges usa Record<string, BenefitTabRecord> em vez de Map —
 * React detecta mudanças por identity comparison em objetos planos, não em Maps.
 */
export function useBenefitsModals(): BenefitsModalsApi {
  const [showBenefitModal, setShowBenefitModal] = useState(false)
  const [editingBenefit, setEditingBenefit] = useState<BenefitTabRecord | null>(null)
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [templateSearch, setTemplateSearch] = useState("")
  const [templateCategoryFilter, setTemplateCategoryFilter] = useState<string>("all")
  const [isEditingBenefits, setIsEditingBenefits] = useState(false)
  const [benefitsBackup, setBenefitsBackup] = useState<BenefitTabRecord[]>([])
  // ✅ Record em vez de Map — React identity comparison funciona corretamente
  const [pendingChanges, setPendingChanges] = useState<Record<string, BenefitTabRecord>>({})

  const handleEnterEditMode = useCallback((benefits: BenefitTabRecord[]) => {
    setBenefitsBackup([...benefits])
    setPendingChanges({})
    setIsEditingBenefits(true)
  }, [])

  const handleCancelEditMode = useCallback(() => {
    setPendingChanges({})
    setIsEditingBenefits(false)
  }, [])

  const handlePendingChange = useCallback((benefit: BenefitTabRecord) => {
    if (!benefit.id) return
    setPendingChanges(prev => ({ ...prev, [benefit.id!]: benefit }))
  }, [])

  const resetEditMode = useCallback(() => {
    setPendingChanges({})
    setIsEditingBenefits(false)
  }, [])

  const getBenefitsBackup = useCallback(() => benefitsBackup, [benefitsBackup])

  return {
    showBenefitModal,
    setShowBenefitModal,
    editingBenefit,
    setEditingBenefit,
    showTemplateModal,
    setShowTemplateModal,
    templateSearch,
    setTemplateSearch,
    templateCategoryFilter,
    setTemplateCategoryFilter,
    isEditingBenefits,
    pendingChanges,
    handleEnterEditMode,
    handleCancelEditMode,
    handlePendingChange,
    resetEditMode,
    getBenefitsBackup,
  }
}
