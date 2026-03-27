"use client"

import React, { useState } from "react"
import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  Utensils,
  Car,
  GraduationCap,
  Wallet,
  Home,
  Baby,
  Stethoscope,
  Shield,
  Star,
  DollarSign,
  Percent,
  Clock,
  type LucideIcon,
} from "lucide-react"
import type { Benefit } from "@/hooks/useCompanyBenefits"
import { BenefitDetailsSheet } from "./BenefitDetailsSheet"

export const BENEFIT_CATEGORIES: {
  id: string
  name: string
  icon: LucideIcon
  color: string
  bgColor: string
}[] = [
  { id: "health", name: "Saúde & Bem-estar", icon: Stethoscope, color: "text-red-500", bgColor: "bg-red-50 dark:bg-red-900/20" },
  { id: "food", name: "Alimentação", icon: Utensils, color: "text-orange-500", bgColor: "bg-orange-50 dark:bg-orange-900/20" },
  { id: "transport", name: "Transporte", icon: Car, color: "text-gray-600 dark:text-gray-400", bgColor: "bg-gray-100 dark:bg-gray-800" },
  { id: "education", name: "Educação & Desenvolvimento", icon: GraduationCap, color: "text-purple-500", bgColor: "bg-purple-50 dark:bg-purple-900/20" },
  { id: "financial", name: "Financeiro", icon: Wallet, color: "text-green-500", bgColor: "bg-green-50 dark:bg-green-900/20" },
 { id: "quality_life", name: "Qualidade de Vida", icon: Home, color: "text-gray-700 dark:text-gray-300", bgColor: "bg-gray-50 dark:bg-gray-800" },
  { id: "family", name: "Família", icon: Baby, color: "text-pink-500", bgColor: "bg-pink-50 dark:bg-pink-900/20" },
  { id: "security", name: "Segurança", icon: Shield, color: "text-gray-800 dark:text-gray-200", bgColor: "bg-gray-50 dark:bg-gray-800/50" },
]

interface BenefitBadgeListProps {
  benefits: Benefit[]
  maxVisible?: number
  showCategory?: boolean
  size?: "sm" | "md" | "lg"
  className?: string
  onBenefitClick?: (benefit: Benefit) => void
}

function getCategoryInfo(categoryId: string) {
  return BENEFIT_CATEGORIES.find(c => c.id === categoryId) || BENEFIT_CATEGORIES[0]
}

function formatBenefitValue(benefit: Benefit): string {
  if (benefit.value_type === "monetary" && benefit.value) {
    const prefix = benefit.is_discount ? "Desconto: " : ""
    return `${prefix}R$ ${benefit.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
  }
  if (benefit.value_type === "percentage" && benefit.percentage_value) {
    return `${benefit.percentage_value}%`
  }
  if (benefit.value_type === "informative") {
    return benefit.value_details || "Informativo"
  }
  return ""
}

function getWaitingPeriodLabel(days: number): string {
  if (days === 0) return "Imediato"
  if (days === 30) return "30 dias"
  if (days === 60) return "60 dias"
  if (days === 90) return "90 dias"
  if (days === 180) return "6 meses"
  if (days === 365) return "1 ano"
  return `${days} dias`
}

export function BenefitBadgeList({
  benefits,
  maxVisible = 5,
  showCategory = true,
  size = "md",
  className = "",
  onBenefitClick,
}: BenefitBadgeListProps) {
  const [showSheet, setShowSheet] = useState(false)
  
  const activeBenefits = benefits.filter(b => b.is_active)
  const visibleBenefits = activeBenefits.slice(0, maxVisible)
  const remainingCount = activeBenefits.length - maxVisible

  const sizeClasses = {
    sm: "text-xs px-1.5 py-0.5 gap-0.5",
    md: "text-xs px-2 py-0.5 gap-1",
    lg: "text-xs px-2.5 py-1 gap-1.5",
  }

  const iconSizes = {
    sm: "w-2.5 h-2.5",
    md: "w-3 h-3",
    lg: "w-3.5 h-3.5",
  }

  if (activeBenefits.length === 0) {
    return null
  }

  return (
    <TooltipProvider delayDuration={200}>
      <div className={`flex flex-wrap items-center gap-1.5 ${className}`}>
        {visibleBenefits.map((benefit, index) => {
          const category = getCategoryInfo(benefit.category)
          const CategoryIcon = category.icon
          const valueDisplay = formatBenefitValue(benefit)

          return (
            <Tooltip key={benefit.id || index}>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={() => onBenefitClick?.(benefit)}
                  className={`
                    inline-flex items-center rounded-full border border-gray-200/60 dark:border-gray-700/60
                    bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm
                    font-medium transition-all duration-200
                    hover:hover:border-gray-300 dark:hover:border-gray-600
                    focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-300
                    ${sizeClasses[size]}
                  `}
                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                >
                  {showCategory && (
                    <span className={`${category.color}`}>
                      <CategoryIcon className={iconSizes[size]} />
                    </span>
                  )}
                  <span className="text-gray-800 dark:text-gray-200 truncate max-w-[100px]">
                    {benefit.name}
                  </span>
                  {benefit.is_highlighted && (
                    <Star className={`${iconSizes[size]} text-yellow-500 fill-yellow-500`} />
                  )}
                </button>
              </TooltipTrigger>
              <TooltipContent 
                side="top" 
                className="max-w-[280px] p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className={`p-1.5 rounded-md ${category.bgColor}`}>
                        <CategoryIcon className={`w-4 h-4 ${category.color}`} />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-950 dark:text-gray-50 text-sm">
                          {benefit.name}
                        </p>
                        <p className="text-xs text-gray-800 dark:text-gray-200">{category.name}</p>
                      </div>
                    </div>
                    {benefit.is_highlighted && (
                      <Star className="w-4 h-4 text-yellow-500 fill-yellow-500 flex-shrink-0" />
                    )}
                  </div>
                  
                  {benefit.description && (
                    <p className="text-xs text-gray-800 dark:text-gray-200 leading-relaxed">
                      {benefit.description}
                    </p>
                  )}
                  
                  <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-gray-100 dark:border-gray-700">
                    {valueDisplay && (
                      <span className="inline-flex items-center gap-1 text-xs text-gray-800 dark:text-gray-200">
                        {benefit.value_type === "monetary" && <DollarSign className="w-3 h-3" />}
                        {benefit.value_type === "percentage" && <Percent className="w-3 h-3" />}
                        {valueDisplay}
                      </span>
                    )}
                    
                    {benefit.waiting_period_days > 0 && (
                      <span className="inline-flex items-center gap-1 text-xs text-gray-800 dark:text-gray-200">
                        <Clock className="w-3 h-3" />
                        {getWaitingPeriodLabel(benefit.waiting_period_days)}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex flex-wrap gap-1">
                    {benefit.is_mandatory && (
                      <Badge variant="secondary" className="text-xs">Obrigatório</Badge>
                    )}
                    {benefit.is_discount && (
                      <Badge variant="outline" className="text-xs text-red-600 border-red-200">Desconto</Badge>
                    )}
                    {benefit.provider && (
                      <Badge variant="outline" className="text-xs">{benefit.provider}</Badge>
                    )}
                  </div>
                </div>
              </TooltipContent>
            </Tooltip>
          )
        })}

        {remainingCount > 0 && (
          <button
            type="button"
            onClick={() => setShowSheet(true)}
            className={`
              inline-flex items-center rounded-full
              border border-dashed border-gray-300 dark:border-gray-600
              bg-gray-50/80 dark:bg-gray-800/80
              text-gray-600 dark:text-gray-400
              font-medium transition-all duration-200
              hover:bg-gray-100 dark:hover:bg-gray-700
              hover:border-gray-400 dark:hover:border-gray-500
              focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-300
              ${sizeClasses[size]}
            `}
            style={{ fontFamily: 'Open Sans, sans-serif' }}
          >
            +{remainingCount} mais
          </button>
        )}

        <BenefitDetailsSheet
          open={showSheet}
          onOpenChange={setShowSheet}
          benefits={activeBenefits}
        />
      </div>
    </TooltipProvider>
  )
}

export default BenefitBadgeList
