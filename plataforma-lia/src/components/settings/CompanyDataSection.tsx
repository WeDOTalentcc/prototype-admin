'use client'

import React from 'react'
import { Button } from "@/components/ui/button"
import {
  Building,
  Edit,
  Save,
  CheckCircle,
  AlertCircle,
  Loader2,
} from "lucide-react"
import { textStyles } from '@/lib/design-tokens'
import type { CompanyData, CompanyDataSectionProps } from './useCompanyDataForm'
import {
  GeneralInfoSection,
  ContactPresenceSection,
  CultureIdentitySection,
  CorporateInfoSection,
  WorkModelSection,
  SocialResponsibilitySection,
  BigFiveSection,
  LiaAnalysisCard,
} from './company'

export type { CompanyData, CompanyDataSectionProps }

export function CompanyDataSection({
  companyData,
  setCompanyData,
  isEditingCompanyData,
  setIsEditingCompanyData,
  companyDataBackup,
  setCompanyDataBackup,
  saveCompanyData,
  saving,
  loading,
  successMessage,
  error,
  updateLiaToggle,
  updateLiaInstruction,
  isLiaAnalyzing,
  liaAnalysisProgress,
  liaAnalysisStep,
  handleLiaAnalysis,
  handleSaveCultureFields,
  techStackByCategory,
  expandedCategories,
  setExpandedCategories,
  addTechToCategory,
  removeTechFromCategory,
  TECH_STACK_CATEGORIES,
}: CompanyDataSectionProps) {

  const countActiveFields = () => {
    const toggles = companyData.lia_field_toggles || {}
    return Object.values(toggles).filter(Boolean).length
  }

  const totalFields = Object.keys(companyData.lia_field_toggles || {}).length || 34

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse motion-reduce:animate-none">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 bg-lia-bg-tertiary rounded-md" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {successMessage && (
        <div className="bg-status-success/10 border border-status-success/30 text-status-success dark:bg-status-success/20 dark:border-status-success/30 dark:text-status-success px-3 py-2 rounded-md flex items-center gap-2 text-xs font-['Open_Sans',sans-serif]">
          <CheckCircle className="w-3.5 h-3.5" />
          {successMessage}
        </div>
      )}
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error dark:bg-status-error/20 dark:border-status-error/30 dark:text-status-error px-3 py-2 rounded-md flex items-center gap-2 text-xs font-['Open_Sans',sans-serif]">
          <AlertCircle className="w-3.5 h-3.5" />
          {error}
        </div>
      )}

      <div className="flex items-center justify-between bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-btn-primary-bg">
            <Building className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className={textStyles.h3}>
              Dados da Empresa
            </h2>
            <p className={textStyles.description}>
              Configure os dados institucionais e preferências da LIA
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-elevated font-['Open_Sans',sans-serif]">
            {countActiveFields()} de {totalFields} campos ativos
          </span>
          {!isEditingCompanyData ? (
            <Button
              onClick={() => {
                setCompanyDataBackup({ ...companyData })
                setIsEditingCompanyData(true)
              }}
              variant="outline"
              size="sm"
              className="gap-1.5 text-xs rounded-md"
            >
              <Edit className="w-3.5 h-3.5" />
              Editar
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <Button
                onClick={() => {
                  if (companyDataBackup) {
                    setCompanyData(() => companyDataBackup)
                  }
                  setIsEditingCompanyData(false)
                  setCompanyDataBackup(null as unknown as CompanyData)
                }}
                disabled={saving}
                variant="outline"
                size="sm"
                className="text-xs rounded-md"
              >
                Cancelar
              </Button>
              <Button
                onClick={async () => {
                  await saveCompanyData()
                  setIsEditingCompanyData(false)
                  setCompanyDataBackup(null as unknown as CompanyData)
                }}
                disabled={saving}
                size="sm"
                className="gap-1.5 text-xs rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                    Salvando...
                  </>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    Salvar
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      </div>

      <GeneralInfoSection
        companyData={companyData}
        setCompanyData={setCompanyData as React.Dispatch<React.SetStateAction<Record<string, any>>>}
        isEditing={isEditingCompanyData}
        updateLiaToggle={updateLiaToggle}
        updateLiaInstruction={updateLiaInstruction}
      />

      <ContactPresenceSection
        companyData={companyData}
        setCompanyData={setCompanyData}
        isEditing={isEditingCompanyData}
        updateLiaToggle={updateLiaToggle}
        updateLiaInstruction={updateLiaInstruction}
      />

      <LiaAnalysisCard
        isEditing={isEditingCompanyData}
        website={companyData.website}
        isLiaAnalyzing={isLiaAnalyzing}
        liaAnalysisProgress={liaAnalysisProgress}
        liaAnalysisStep={liaAnalysisStep}
        handleLiaAnalysis={handleLiaAnalysis}
      />

      <CultureIdentitySection
        companyData={companyData}
        setCompanyData={setCompanyData}
        isEditing={isEditingCompanyData}
        updateLiaToggle={updateLiaToggle}
        updateLiaInstruction={updateLiaInstruction}
      />

      <CorporateInfoSection
        companyData={companyData}
        setCompanyData={setCompanyData}
        isEditing={isEditingCompanyData}
      />

      <WorkModelSection
        companyData={companyData}
        setCompanyData={setCompanyData}
        isEditing={isEditingCompanyData}
        updateLiaToggle={updateLiaToggle}
        updateLiaInstruction={updateLiaInstruction}
      />

      <SocialResponsibilitySection
        companyData={companyData}
        setCompanyData={setCompanyData}
        isEditing={isEditingCompanyData}
        updateLiaToggle={updateLiaToggle}
        updateLiaInstruction={updateLiaInstruction}
      />

      <BigFiveSection
        companyData={companyData}
        setCompanyData={setCompanyData}
        isEditing={isEditingCompanyData}
        saving={saving}
        updateLiaToggle={updateLiaToggle}
        updateLiaInstruction={updateLiaInstruction}
        handleSaveCultureFields={handleSaveCultureFields}
      />
    </div>
  )
}
