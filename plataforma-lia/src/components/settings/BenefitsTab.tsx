"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import {
  Library,
  Plus,
  Pencil,
  Loader2,
  CheckCircle,
  AlertCircle,
} from "lucide-react"
import {
  textStyles,
  badgeStyles,
  actionButtonStyles,
} from "@/lib/design-tokens"
import { BenefitFormModal } from "./benefits/BenefitFormModal"
import { BenefitTemplateModal } from "./benefits/BenefitTemplateModal"
import { BenefitsList } from "./benefits/BenefitsList"
import { useBenefitsTab } from "./benefits/useBenefitsTab"
import { defaultBenefit } from "./benefits/benefits-types"
import type { BenefitTemplate } from "./benefits/benefits-types"
import { HubHeader } from "./_shared"

export function BenefitsTab() {
  const t = useTranslations("settings.benefits")
  const hub = useBenefitsTab()

  const templatesByCategory = hub.filteredTemplates.reduce<Record<string, BenefitTemplate[]>>(
    (acc, template) => {
      const cat = template.category || "other"
      if (!acc[cat]) acc[cat] = []
      acc[cat].push(template)
      return acc
    },
    {}
  )

  if (hub.isLoading) {
    return (
      <div className="space-y-3" role="status" aria-live="polite" aria-label={t("loading")}>
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mx-auto mb-2 text-lia-text-secondary" />
            <p className={textStyles.description}>{t("loading")}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {hub.successMessage && (
        <div className={`${badgeStyles.success} px-2 py-1.5 rounded-md flex items-center gap-2`}>
          <CheckCircle className="w-4 h-4" />
          {hub.successMessage}
        </div>
      )}

      {hub.error && (
        <div className={`${badgeStyles.error} px-2 py-1.5 rounded-md flex items-center gap-2`}>
          <AlertCircle className="w-4 h-4" />
          {hub.error}
        </div>
      )}

      <HubHeader title={t("title")} description={t("description")}>
          {!hub.isEditingBenefits ? (
            <button onClick={hub.handleEnterEditMode} className={actionButtonStyles.smOutline}>
              <Pencil className={actionButtonStyles.icon} />
              {t("edit")}
            </button>
          ) : (
            <>
              <button
                onClick={hub.handleCancelEdit}
                className={actionButtonStyles.smSecondary}
                disabled={hub.isSaving}
              >
                {t("cancel")}
              </button>
              <button
                onClick={hub.handleSaveChanges}
                disabled={hub.isSaving}
                className={actionButtonStyles.smPrimary}
              >
                {hub.isSaving ? (
                  <>
                    <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
                    {t("savingBtn")}
                  </>
                ) : (
                  t("saveChanges")
                )}
              </button>
            </>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => hub.setShowTemplateModal(true)}
            disabled={!hub.isEditingBenefits}
            className="gap-1.5 rounded-xl text-xs border-lia-border-default text-lia-text-primary dark:border-lia-border-default hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover"
          >
            <Library className="w-3.5 h-3.5" />
            {t("addFromList")}
          </Button>
          <Button
            size="sm"
            onClick={() => {
              hub.setEditingBenefit({ ...defaultBenefit })
              hub.setShowBenefitModal(true)
            }}
            disabled={!hub.isEditingBenefits}
            className="gap-1.5 rounded-md text-xs bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
          >
            <Plus className="w-3.5 h-3.5" />
            {t("newBenefit")}
          </Button>
        </div>
      </HubHeader>

      <BenefitsList
        benefits={hub.benefits}
        isEditingBenefits={hub.isEditingBenefits}
        onToggleStatus={hub.handleToggleBenefitStatus}
        onEditBenefit={(b) => {
          hub.setEditingBenefit(b)
          hub.setShowBenefitModal(true)
          if (b.id) hub.loadBenefitHistory(b.id)
        }}
        onCreateBenefitInCategory={(categoryId) => {
          hub.setEditingBenefit({ ...defaultBenefit, category: categoryId })
          hub.setShowBenefitModal(true)
        }}
        onDelete={hub.handleDeleteBenefit}
      />

      <BenefitFormModal
        open={hub.showBenefitModal}
        onOpenChange={hub.setShowBenefitModal}
        editingBenefit={hub.editingBenefit}
        setEditingBenefit={hub.setEditingBenefit}
        isSaving={hub.isSaving}
        onSave={hub.handleSaveBenefit}
        history={hub.benefitHistory}
        historyLoading={hub.historyLoading}
      />

      <BenefitTemplateModal
        open={hub.showTemplateModal}
        onOpenChange={hub.setShowTemplateModal}
        templates={hub.templates}
        isLoadingTemplates={hub.isLoadingTemplates}
        templateSearch={hub.templateSearch}
        setTemplateSearch={hub.setTemplateSearch}
        templateCategoryFilter={hub.templateCategoryFilter}
        setTemplateCategoryFilter={hub.setTemplateCategoryFilter}
        filteredTemplates={hub.filteredTemplates}
        templatesByCategory={templatesByCategory}
        isTemplateAlreadyAdded={hub.isTemplateAlreadyAdded}
        onSelectTemplate={hub.handleSelectTemplate}
        onOpenBenefitModal={() => {
          hub.setEditingBenefit({ ...defaultBenefit })
          hub.setShowBenefitModal(true)
        }}
      />
    </div>
  )
}

export default BenefitsTab
