"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import {
  Gift,
  Plus,
  ChevronDown,
  ChevronRight,
  Stethoscope,
  Utensils,
  Car,
  GraduationCap,
  Wallet,
  Home,
  Baby,
  Shield,
  Clock,
} from "lucide-react"
import { textStyles, cardStyles } from "@/lib/design-tokens"
import { BenefitItemCard } from "./BenefitItemCard"
import type {
  BenefitCategoryDescriptor,
  BenefitTabRecord,
} from "./benefits-types"

export const BENEFIT_CATEGORIES: BenefitCategoryDescriptor[] = [
  { id: "health", name: "Saúde & Bem-estar", icon: Stethoscope, color: "text-status-error", bgColor: "bg-status-error/10 dark:bg-status-error/20" },
  { id: "food", name: "Alimentação", icon: Utensils, color: "text-wedo-orange-text", bgColor: "bg-wedo-orange/10 dark:bg-wedo-orange/20" },
  { id: "transport", name: "Transporte", icon: Car, color: "text-lia-text-primary", bgColor: "bg-lia-bg-tertiary dark:bg-lia-bg-secondary" },
  { id: "education", name: "Educação & Desenvolvimento", icon: GraduationCap, color: "text-wedo-purple-text", bgColor: "bg-wedo-purple/10 dark:bg-wedo-purple/20" },
  { id: "wellness", name: "Bem-estar", icon: Stethoscope, color: "text-wedo-cyan-text", bgColor: "bg-wedo-cyan/10 dark:bg-wedo-cyan/20" },
  { id: "financial", name: "Financeiro", icon: Wallet, color: "text-status-success", bgColor: "bg-status-success/10 dark:bg-status-success/20" },
  { id: "quality_life", name: "Qualidade de Vida", icon: Home, color: "text-lia-text-secondary", bgColor: "bg-lia-bg-tertiary dark:bg-lia-bg-secondary" },
  { id: "family", name: "Família", icon: Baby, color: "text-wedo-magenta-text", bgColor: "bg-wedo-magenta/10 dark:bg-wedo-magenta/20" },
  { id: "flexibility", name: "Flexibilidade", icon: Clock, color: "text-wedo-purple-text", bgColor: "bg-wedo-purple/10 dark:bg-wedo-purple/20" },
  { id: "security", name: "Segurança", icon: Shield, color: "text-lia-text-primary", bgColor: "bg-lia-bg-secondary dark:bg-lia-bg-secondary/50" },
  { id: "other", name: "Outros", icon: Gift, color: "text-lia-text-secondary", bgColor: "bg-lia-bg-tertiary dark:bg-lia-bg-secondary" },
]

interface BenefitsListProps {
  benefits: BenefitTabRecord[]
  isEditingBenefits: boolean
  onToggleStatus: (benefit: BenefitTabRecord) => void
  onEditBenefit: (benefit: BenefitTabRecord) => void
  onCreateBenefitInCategory: (categoryId: string) => void
  onDelete: (benefitId: string) => void
  /** 'vacancy' reflete o catalogo dentro da vaga (toggle = vincular). */
  mode?: "catalog" | "vacancy"
  linkedIds?: Set<string>
}

export function BenefitsList({
  benefits,
  isEditingBenefits,
  onToggleStatus,
  onEditBenefit,
  onCreateBenefitInCategory,
  onDelete,
  mode = "catalog",
  linkedIds,
}: BenefitsListProps) {
  const isVacancy = mode === "vacancy"
  const linkedCount = (cbs: BenefitTabRecord[]) =>
    cbs.filter((b) => b.id && linkedIds?.has(b.id)).length
  const t = useTranslations("settings.benefits")
  const CATEGORY_NAME_KEYS: Record<string, string> = {
    health: "categoryHealth",
    food: "categoryFood",
    transport: "categoryTransport",
    education: "categoryEducation",
    wellness: "categoryHealth",
    financial: "categoryFinancial",
    quality_life: "categoryQualityLife",
    family: "categoryFamily",
    flexibility: "categoryQualityLife",
    security: "categorySecurity",
    other: "noDescription",
  }
  const [expandedCategories, setExpandedCategories] = React.useState<string[]>(
    BENEFIT_CATEGORIES.map(c => c.id)
  )

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories(prev =>
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    )
  }

  return (
    <div className="space-y-3">
      {BENEFIT_CATEGORIES.map((category) => {
        const categoryBenefits = benefits.filter(b => b.category === category.id)
        const isExpanded = expandedCategories.includes(category.id)
        const CategoryIcon = category.icon

        return (
          <Card
            key={category.id}
            className={`${cardStyles.default} dark:border-lia-border-subtle/50 dark:bg-lia-bg-secondary/80 backdrop-blur-sm rounded-md overflow-hidden`}
          >
            <div
              className={`flex items-center justify-between p-3 cursor-pointer transition-colors motion-reduce:transition-none bg-lia-bg-secondary/60 dark:bg-lia-bg-secondary/40`}
              onClick={() => toggleCategory(category.id)}
              role="button"
              tabIndex={0}
              aria-expanded={isExpanded}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleCategory(category.id) } }}
            >
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-md bg-lia-bg-primary dark:bg-lia-bg-secondary">
                  <CategoryIcon className="w-4 h-4 text-lia-text-secondary" />
                </div>
                <div>
                  <h3 className={textStyles.title}>{t(CATEGORY_NAME_KEYS[category.id] || "noDescription")}</h3>
                  <p className={textStyles.caption}>
                    {t("benefitsFound", { count: categoryBenefits.length })}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Chip variant="neutral" className="text-micro">
                  {isVacancy
                    ? t("linkedBenefits", { count: linkedCount(categoryBenefits) })
                    : t("activeBenefits", { count: categoryBenefits.filter(b => b.is_active).length })}
                </Chip>
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-lia-text-secondary" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-lia-text-secondary" />
                )}
              </div>
            </div>

            {isExpanded && (
              <CardContent className="p-0">
                {categoryBenefits.length === 0 ? (
                  <div className="p-3 text-center">
                    <Gift className="w-4 h-4 mx-auto text-lia-text-disabled mb-2" />
                    <p className={textStyles.bodySmall}>
                      {t("noBenefitsInCategory")}
                    </p>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-2 text-xs text-lia-text-primary hover:text-lia-text-primary"
                      onClick={() => onCreateBenefitInCategory(category.id)}
                      disabled={!isEditingBenefits}
                    >
                      <Plus className="w-3.5 h-3.5 mr-1" />
                      {t("addBenefitBtn")}
                    </Button>
                  </div>
                ) : (
                  <div className="divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
                    {categoryBenefits.map((benefit) => (
                      <BenefitItemCard
                        key={benefit.id}
                        benefit={benefit}
                        isEditingBenefits={isEditingBenefits}
                        onToggleStatus={onToggleStatus}
                        onEdit={onEditBenefit}
                        onDelete={onDelete}
                        mode={mode}
                        isLinked={isVacancy && benefit.id ? !!linkedIds?.has(benefit.id) : false}
                      />
                    ))}
                  </div>
                )}
              </CardContent>
            )}
          </Card>
        )
      })}
    </div>
  )
}
