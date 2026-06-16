"use client"

import { formatBRL } from"@/lib/pricing"

import React from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import {
  Gift,
  ChevronRight,
  Star,
  Utensils,
  Car,
  GraduationCap,
  Wallet,
  Home,
  Baby,
  Stethoscope,
  Shield,
  type LucideIcon,
} from"lucide-react"
import type { CompanyBenefit } from"@/types/benefits"

const CATEGORY_MAP: Record<string, { name: string; icon: LucideIcon; color: string }> = {
  health: { name:"Saúde", icon: Stethoscope, color:"text-status-error" },
  food: { name:"Alimentação", icon: Utensils, color:"text-wedo-orange-text" },
  transport: { name:"Transporte", icon: Car, color:"text-lia-text-secondary" },
  education: { name:"Educação", icon: GraduationCap, color:"text-lia-text-secondary" },
  financial: { name:"Financeiro", icon: Wallet, color:"text-status-success" },
  quality_life: { name:"Qualidade", icon: Home, color:"text-lia-text-secondary" },
  family: { name:"Família", icon: Baby, color:"text-wedo-magenta-text" },
  security: { name:"Segurança", icon: Shield, color:"text-lia-text-primary" },
}

export interface CompanyBenefitsData {
  benefits: CompanyBenefit[]
  total_count?: number
  highlighted_count?: number
}

interface CompanyBenefitsSummaryCardProps {
  data: CompanyBenefitsData
  onViewAll?: () => void
  onAction?: (action: string, data: unknown) => void
}

export function CompanyBenefitsSummaryCard({
  data,
  onViewAll,
  onAction,
}: CompanyBenefitsSummaryCardProps) {
  const { benefits, total_count, highlighted_count } = data
  
  const highlighted = benefits.filter(b => b.is_highlighted)
  const displayBenefits = highlighted.length > 0 ? highlighted.slice(0, 5) : benefits.slice(0, 5)
  const remainingCount = (total_count || benefits.length) - displayBenefits.length

  const formatValue = (benefit: CompanyBenefit) => {
    if (benefit.value_type ==="monetary" && benefit.value) {
      return `${formatBRL(benefit.value)}`
    }
    if (benefit.value_type ==="percentage" && benefit.percentage_value) {
      return `${benefit.percentage_value}%`
    }
    if (benefit.value_type ==="informative" && benefit.value_details) {
      return benefit.value_details
    }
    return null
  }

  const getCategoryInfo = (categoryId: string) => {
    return CATEGORY_MAP[categoryId] || { name: categoryId, icon: Gift, color:"text-lia-text-primary" }
  }

  return (
    <Card className="w-full max-w-md bg-wedo-purple/10">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Gift className="w-4 h-4 text-wedo-purple" />
          <span>Benefícios da Empresa</span>
          {highlighted_count && highlighted_count > 0 && (
            <Chip density="relaxed" variant="neutral" className="ml-auto text-lia-text-secondary">
              <Star className="w-3 h-3 mr-1 fill-current" />
              {highlighted_count} em destaque
            </Chip>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-1.5">
          {displayBenefits.map((benefit, index) => {
            const categoryInfo = getCategoryInfo(benefit.category)
            const CategoryIcon = categoryInfo.icon
            const value = formatValue(benefit)
            
            return (
              <Chip
                key={benefit.id || index}
                variant="neutral"
                className="flex items-center gap-1 py-1 px-2 text-xs bg-lia-bg-primary dark:bg-lia-bg-secondary"
                title={benefit.description}
              >
                <CategoryIcon className={`w-3 h-3 ${categoryInfo.color}`} />
                <span className="truncate max-w-[120px]">{benefit.name}</span>
                {value && (
                  <span className="text-lia-text-primary text-xs">
                    ({value})
                  </span>
                )}
                {benefit.is_highlighted && (
                  <Star className="w-2.5 h-2.5 text-status-warning fill-current" />
                )}
                {benefit.is_mandatory && (
                  <span className="text-micro px-0.5 rounded-xl bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-secondary">obr.</span>
                )}
                {benefit.is_discount && (
                  <span className="text-micro px-0.5 rounded-md bg-status-error/15 dark:bg-status-error/30 text-status-error dark:text-status-error">desc.</span>
                )}
              </Chip>
            )
          })}
          {remainingCount > 0 && (
            <Chip
              variant="neutral"
              className="py-1 px-2 text-xs bg-wedo-purple/10 dark:bg-wedo-purple/30 text-wedo-purple-text dark:text-wedo-purple cursor-pointer hover:bg-wedo-purple/15"
              onClick={onViewAll}
            >
              +{remainingCount} mais
            </Chip>
          )}
        </div>
        
        {(onViewAll || onAction) && (
          <div className="flex justify-end pt-1">
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-wedo-purple-text hover:text-wedo-purple hover:bg-wedo-purple/10"
              onClick={() => onAction?.("view_all", data) || onViewAll?.()}
            >
              Ver todos os benefícios
              <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
