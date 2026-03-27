"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
} from "lucide-react"
import type { CompanyBenefit } from "@/types/benefits"

const CATEGORY_MAP: Record<string, { name: string; icon: LucideIcon; color: string }> = {
  health: { name: "Saúde", icon: Stethoscope, color: "text-red-500" },
  food: { name: "Alimentação", icon: Utensils, color: "text-orange-500" },
  transport: { name: "Transporte", icon: Car, color: "text-gray-600 dark:text-gray-400" },
  education: { name: "Educação", icon: GraduationCap, color: "text-purple-500" },
  financial: { name: "Financeiro", icon: Wallet, color: "text-green-500" },
  quality_life: { name: "Qualidade", icon: Home, color: "text-gray-700 dark:text-gray-300" },
  family: { name: "Família", icon: Baby, color: "text-pink-500" },
  security: { name: "Segurança", icon: Shield, color: "text-gray-800 dark:text-gray-200" },
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
    if (benefit.value_type === "monetary" && benefit.value) {
      return `R$ ${benefit.value.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`
    }
    if (benefit.value_type === "percentage" && benefit.percentage_value) {
      return `${benefit.percentage_value}%`
    }
    if (benefit.value_type === "informative" && benefit.value_details) {
      return benefit.value_details
    }
    return null
  }

  const getCategoryInfo = (categoryId: string) => {
    return CATEGORY_MAP[categoryId] || { name: categoryId, icon: Gift, color: "text-gray-800 dark:text-gray-200" }
  }

  return (
    <Card className="w-full max-w-md bg-purple-50 dark:bg-purple-950/20">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Gift className="w-4 h-4 text-purple-600" />
          <span>Benefícios da Empresa</span>
          {highlighted_count && highlighted_count > 0 && (
            <Badge variant="outline" className="ml-auto text-xs text-purple-700">
              <Star className="w-3 h-3 mr-1 fill-current" />
              {highlighted_count} em destaque
            </Badge>
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
              <Badge
                key={benefit.id || index}
                variant="outline"
                className="flex items-center gap-1 py-1 px-2 text-xs bg-white dark:bg-gray-800"
                title={benefit.description}
              >
                <CategoryIcon className={`w-3 h-3 ${categoryInfo.color}`} />
                <span className="truncate max-w-[120px]">{benefit.name}</span>
                {value && (
                  <span className="text-gray-800 dark:text-gray-200 text-[11px]">
                    ({value})
                  </span>
                )}
                {benefit.is_highlighted && (
                  <Star className="w-2.5 h-2.5 text-yellow-500 fill-current" />
                )}
                {benefit.is_mandatory && (
                  <span className="text-[9px] px-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400">obr.</span>
                )}
                {benefit.is_discount && (
                  <span className="text-[9px] px-0.5 rounded bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400">desc.</span>
                )}
              </Badge>
            )
          })}
          {remainingCount > 0 && (
            <Badge
              variant="outline"
              className="py-1 px-2 text-xs bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 cursor-pointer hover:bg-purple-100"
              onClick={onViewAll}
            >
              +{remainingCount} mais
            </Badge>
          )}
        </div>
        
        {(onViewAll || onAction) && (
          <div className="flex justify-end pt-1">
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-purple-600 hover:text-purple-700 hover:bg-purple-50"
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
