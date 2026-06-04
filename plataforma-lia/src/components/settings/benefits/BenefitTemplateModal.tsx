"use client"

import React from"react"
import { useTranslations } from "next-intl"
import { textStyles } from"@/lib/design-tokens"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { Chip } from "@/components/ui/chip"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"
import {
  Dialog,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DraggableDialogContent,
} from"@/components/ui/dialog"
import {
  Gift,
  Plus,
  Search,
  Star,
  Check,
  Loader2,
  Stethoscope,
  Utensils,
  Car,
  GraduationCap,
  Wallet,
  Home,
  Baby,
  Shield,
  Clock,
  Library,
} from"lucide-react"

interface BenefitTemplate {
  id: string
  name: string
  description: string
  category: string
  is_popular: boolean
  is_active: boolean
  order: number
}

interface BenefitTemplateModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  templates: BenefitTemplate[]
  isLoadingTemplates: boolean
  templateSearch: string
  setTemplateSearch: (s: string) => void
  templateCategoryFilter: string
  setTemplateCategoryFilter: (c: string) => void
  filteredTemplates: BenefitTemplate[]
  templatesByCategory: Record<string, BenefitTemplate[]>
  isTemplateAlreadyAdded: (name: string) => boolean
  onSelectTemplate: (template: BenefitTemplate) => void
  onOpenBenefitModal: () => void
}

export function BenefitTemplateModal({
  open,
  onOpenChange,
  isLoadingTemplates,
  templateSearch,
  setTemplateSearch,
  templateCategoryFilter,
  setTemplateCategoryFilter,
  filteredTemplates,
  templatesByCategory,
  isTemplateAlreadyAdded,
  onSelectTemplate,
  onOpenBenefitModal,
}: BenefitTemplateModalProps) {
  const t = useTranslations("settings.benefits")

  const BENEFIT_CATEGORIES = [
    { id:"health", name: t("categoryHealth"), icon: Stethoscope, color:"text-status-error", bgColor:"bg-status-error/10 dark:bg-status-error/20" },
    { id:"food", name: t("categoryFood"), icon: Utensils, color:"text-wedo-orange", bgColor:"bg-wedo-orange/10 dark:bg-wedo-orange/20" },
    { id:"transport", name: t("categoryTransport"), icon: Car, color:"text-lia-text-primary", bgColor:"bg-lia-bg-tertiary dark:bg-lia-bg-secondary" },
    { id:"education", name: t("categoryEducation"), icon: GraduationCap, color:"text-wedo-purple", bgColor:"bg-wedo-purple/10 dark:bg-wedo-purple/20" },
    { id:"wellness", name: t("categoryHealth"), icon: Stethoscope, color:"text-wedo-cyan", bgColor:"bg-wedo-cyan/10 dark:bg-wedo-cyan/20" },
    { id:"financial", name: t("categoryFinancial"), icon: Wallet, color:"text-status-success", bgColor:"bg-status-success/10 dark:bg-status-success/20" },
    { id:"quality_life", name: t("categoryQualityLife"), icon: Home, color:"text-lia-text-secondary", bgColor:"bg-lia-bg-tertiary dark:bg-lia-bg-secondary" },
    { id:"family", name: t("categoryFamily"), icon: Baby, color:"text-wedo-magenta", bgColor:"bg-wedo-magenta/10 dark:bg-wedo-magenta/20" },
    { id:"flexibility", name: t("categoryQualityLife"), icon: Clock, color:"text-wedo-purple", bgColor:"bg-wedo-purple/10 dark:bg-wedo-purple/20" },
    { id:"security", name: t("categorySecurity"), icon: Shield, color:"text-lia-text-primary", bgColor:"bg-lia-bg-secondary dark:bg-lia-bg-secondary/50" },
    { id:"other", name: t("noDescription"), icon: Gift, color:"text-lia-text-secondary", bgColor:"bg-lia-bg-tertiary dark:bg-lia-bg-secondary" },
  ]

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DraggableDialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-hidden flex flex-col p-3">
        <DialogHeader className="flex-shrink-0 pb-2">
          <DialogTitle className={`flex items-center gap-2 ${textStyles.h3}`}>
            <Library className="w-4 h-4 text-lia-text-primary" />
            {t("libraryTitle")}
          </DialogTitle>
          <DialogDescription className={`${textStyles.description}`}>
            {t("libraryDescription")}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-shrink-0 space-y-2 py-1.5">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 text-lia-text-secondary" />
              <Input
                placeholder={t("searchBenefit")}
                value={templateSearch}
                onChange={(e) => setTemplateSearch(e.target.value)}
                className="pl-8 h-8 text-xs rounded-full py-1.5 px-2"
              />
            </div>
            <Select value={templateCategoryFilter} onValueChange={setTemplateCategoryFilter}>
              <SelectTrigger className="w-[180px] h-8 text-xs rounded-md">
                <SelectValue placeholder={t("allCategoriesFilter")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all" className="text-xs">{t("allCategoriesFilter")}</SelectItem>
                {BENEFIT_CATEGORIES.map((cat) => {
                  const Icon = cat.icon
                  return (
                    <SelectItem key={cat.id} value={cat.id} className="text-xs">
                      <div className="flex items-center gap-1.5">
                        <Icon className={`w-3.5 h-3.5 ${cat.color}`} />
                        <span>{cat.name}</span>
                      </div>
                    </SelectItem>
                  )
                })}
              </SelectContent>
            </Select>
          </div>

          <div className={`flex items-center gap-2 ${textStyles.caption}`}>
            <span aria-live="polite" aria-atomic="true">{t("benefitsFound", { count: filteredTemplates.length })}</span>
            {templateSearch && (
              <Button
                variant="ghost"
                size="sm"
                className="h-5 text-micro px-1.5"
                onClick={() => { setTemplateSearch(""); setTemplateCategoryFilter("all"); }}
              >
                {t("clearFilters")}
              </Button>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto space-y-2 py-1 pr-1 -mr-1" role="status" aria-live="polite" aria-label={t("loading")}>
          {isLoadingTemplates ? (
            <div className="flex items-center justify-center py-6" role="status" aria-live="polite" aria-label={t("loading")}>
              <div className="text-center" role="status" aria-live="polite" aria-label={t("loading")}>
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none mx-auto mb-2 text-lia-text-secondary" />
                <p className={`${textStyles.description}`}>{t("loading")}</p>
              </div>
            </div>
          ) : filteredTemplates.length === 0 ? (
            <div className="text-center py-6">
              <Gift className="w-4 h-4 mx-auto text-lia-text-disabled mb-2" />
              <p className={`${textStyles.description}`} aria-live="polite" aria-atomic="true">
                {t("noBenefitFound")}
              </p>
              <Button
                variant="ghost"
                size="sm"
                className="mt-1 h-6 text-xs text-lia-text-primary hover:text-lia-text-primary"
                onClick={() => { setTemplateSearch(""); setTemplateCategoryFilter("all"); }}
              >
                {t("clearFiltersBtn")}
              </Button>
            </div>
          ) : (
            BENEFIT_CATEGORIES.map((category) => {
              const catTemplates = templatesByCategory[category.id] || []
              if (catTemplates.length === 0) return null

              const CategoryIcon = category.icon

              return (
                <div key={category.id} className="space-y-1.5">
                  <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md ${category.bgColor}`}>
                    <CategoryIcon className={`w-3.5 h-3.5 ${category.color}`} />
                    <span className={`${textStyles.label}`}>
                      {category.name}
                    </span>
                    <Chip variant="neutral" muted className="text-micro h-4 px-1">
                      {catTemplates.length}
                    </Chip>
                  </div>
                  <div className="grid grid-cols-1 gap-1">
                    {catTemplates.map((template) => {
                      const alreadyAdded = isTemplateAlreadyAdded(template.name)
                      return (
                        <div
                          key={template.id}
                          className={`p-2 border rounded-md cursor-pointer transition-colors motion-reduce:transition-none ${
                            alreadyAdded
                              ? 'bg-status-success/10 dark:bg-status-success/20 border-status-success/30 dark:border-status-success/30'
                              : 'bg-lia-bg-primary dark:bg-lia-bg-secondary border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-medium dark:hover:border-lia-border-medium hover:'
                          }`}
                          onClick={() => !alreadyAdded && onSelectTemplate(template)}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5">
                                <h4 className={`${textStyles.label} truncate`}>
                                  {template.name}
                                </h4>
                                {template.is_popular && (
                                  <Star className="w-3 h-3 text-status-warning fill-current flex-shrink-0" />
                                )}
                              </div>
                              <p className={`${textStyles.caption} truncate`}>
                                {template.description}
                              </p>
                            </div>
                            {alreadyAdded ? (
                              <div className="flex items-center gap-0.5 text-status-success text-micro flex-shrink-0">
                                <Check className="w-3.5 h-3.5" />
                              </div>
                            ) : (
                              <Plus className="w-3.5 h-3.5 text-lia-text-tertiary flex-shrink-0" />
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })
          )}
        </div>

        <DialogFooter className="flex-shrink-0 border-t pt-3 mt-3">
          <div className="flex items-center justify-between w-full">
            <p className={`${textStyles.description}`}>
              {t("notFound")}{" "}
              <Button
                variant="link"
                className={`h-auto p-0 ${textStyles.link}`}
                onClick={() => {
                  onOpenChange(false)
                  onOpenBenefitModal()
                }}
              >
                {t("createCustom")}
              </Button>
            </p>
            <Button
              variant="outline"
              onClick={() => {
                onOpenChange(false)
                setTemplateSearch("")
                setTemplateCategoryFilter("all")
              }}
              className="rounded-md text-xs"
            >
              {t("close")}
            </Button>
          </div>
        </DialogFooter>
      </DraggableDialogContent>
    </Dialog>
  )
}
