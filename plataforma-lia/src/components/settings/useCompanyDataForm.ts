import type React from "react"
export type { CompanyData } from "./companyTeamHub.types"
import type { CompanyData } from "./companyTeamHub.types"

export interface CompanyDataSectionProps {
  companyData: CompanyData
  setCompanyData: React.Dispatch<React.SetStateAction<CompanyData>>
  isEditingCompanyData: boolean
  setIsEditingCompanyData: (value: boolean) => void
  companyDataBackup: CompanyData | null
  setCompanyDataBackup: (data: CompanyData | null) => void
  saveCompanyData: () => Promise<void>
  saving: boolean
  loading: boolean
  successMessage: string | null
  error: string | null
  updateLiaToggle: (fieldKey: string, isActive: boolean) => void
  updateLiaInstruction: (fieldKey: string, instruction: string) => void
  isLiaAnalyzing: boolean
  liaAnalysisProgress: number
  liaAnalysisStep: string | null
  handleLiaAnalysis: () => void
  handleSaveCultureFields: () => Promise<void>
  techStackByCategory: Record<string, string[]>
  expandedCategories: Record<string, boolean>
  setExpandedCategories: (fn: (prev: Record<string, boolean>) => Record<string, boolean>) => void
  addTechToCategory: (category: string, tech: string) => void
  removeTechFromCategory: (category: string, tech: string) => void
  TECH_STACK_CATEGORIES: readonly string[]
}

export const inputClass = (disabled: boolean) =>
  `w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg dark:focus:ring-lia-border-subtle/10 dark:focus:border-lia-border-subtle transition-colors ${disabled ? 'opacity-60 cursor-not-allowed bg-lia-bg-secondary dark:bg-lia-bg-primary' : ''}`

export const textareaClass = (disabled: boolean) =>
  `w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg dark:focus:ring-lia-border-subtle/10 dark:focus:border-lia-border-subtle transition-colors resize-none ${disabled ? 'opacity-60 cursor-not-allowed bg-lia-bg-secondary dark:bg-lia-bg-primary' : ''}`

export const selectClass = (disabled: boolean) =>
  `w-full px-3 py-2 text-xs font-['Open_Sans',sans-serif] border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-primary focus:ring-2 focus:ring-lia-btn-primary-bg/10 focus:border-lia-btn-primary-bg dark:focus:ring-lia-border-subtle/10 dark:focus:border-lia-border-subtle transition-colors ${disabled ? 'opacity-60 cursor-not-allowed bg-lia-bg-secondary dark:bg-lia-bg-primary' : ''}`
