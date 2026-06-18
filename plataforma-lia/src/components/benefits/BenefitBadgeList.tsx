"use client"

import { formatBRL } from"@/lib/pricing"

import React, { useState } from"react"
import { Chip } from "@/components/ui/chip"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from"@/components/ui/tooltip"
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
} from"lucide-react"
import type { Benefit } from"@/hooks/company/useCompanyBenefits"
import { BenefitDetailsSheet } from"./BenefitDetailsSheet"

export const BENEFIT_CATEGORIES: {
  id: string
  name: string
  icon: LucideIcon
  color: string
  bgColor: string
}[] = [
  { id:"health", name:"Saúde & Bem-estar", icon: Stethoscope, color:"text-status-error", bgColor:"bg-status-error/10 dark:bg-status-error/20" },
  { id:"food", name:"Alimentação", icon: Utensils, color:"text-wedo-orange-text", bgColor:"bg-wedo-orange/10 dark:bg-wedo-orange/10/20" },
  { id:"transport", name:"Transporte", icon: Car, color:"text-lia-text-secondary", bgColor:"bg-lia-bg-tertiary dark:bg-lia-bg-secondary" },
  { id:"education", name:"Educação & Desenvolvimento", icon: GraduationCap, color:"text-wedo-purple-text", bgColor:"bg-wedo-purple/10 dark:bg-wedo-purple/20" },
  { id:"financial", name:"Financeiro", icon: Wallet, color:"text-status-success", bgColor:"bg-status-success/10 dark:bg-status-success/20" },
 { id:"quality_life", name:"Qualidade de Vida", icon: Home, color:"text-lia-text-secondary", bgColor:"bg-lia-bg-secondary dark:bg-lia-bg-secondary" },
  { id:"family", name:"Família", icon: Baby, color:"text-wedo-magenta-text", bgColor:"bg-wedo-magenta/10 dark:bg-wedo-magenta/20" },
  { id:"security", name:"Segurança", icon: Shield, color:"text-lia-text-primary", bgColor:"bg-lia-bg-secondary dark:bg-lia-bg-secondary/50" },
]

interface BenefitBadgeListProps {
  benefits: Benefit[]
  maxVisible?: number
  showCategory?: boolean
  size?:"sm" |"md" |"lg"
  className?: string
  onBenefitClick?: (benefit: Benefit) => void
}

function getCategoryInfo(categoryId: string) {
  return BENEFIT_CATEGORIES.find(c => c.id === categoryId) || BENEFIT_CATEGORIES[0]
}

function formatBenefitValue(benefit: Benefit): string {
  if (benefit.value_type ==="monetary" && benefit.value) {
    const prefix = benefit.is_discount ?"Desconto:" :""
    return `${prefix}${formatBRL(benefit.value)}`
  }
  if (benefit.value_type ==="percentage" && benefit.percentage_value) {
    return `${benefit.percentage_value}%`
  }
  if (benefit.value_type ==="informative") {
    return benefit.value_details ||"Informativo"
  }
  return""
}

function getWaitingPeriodLabel(days: number): string {
  if (days === 0) return"Imediato"
  if (days === 30) return"30 dias"
  if (days === 60) return"60 dias"
  if (days === 90) return"90 dias"
  if (days === 180) return"6 meses"
  if (days === 365) return"1 ano"
  return `${days} dias`
}

export function BenefitBadgeList({
  benefits,
  maxVisible = 5,
  showCategory = true,
  size ="md",
  className ="",
  onBenefitClick,
}: BenefitBadgeListProps) {
  const [showSheet, setShowSheet] = useState(false)
  
  const activeBenefits = benefits.filter(b => b.is_active)
  const visibleBenefits = activeBenefits.slice(0, maxVisible)
  const remainingCount = activeBenefits.length - maxVisible

  const sizeClasses = {
    sm:"text-xs px-1.5 py-0.5 gap-0.5",
    md:"text-xs px-2 py-0.5 gap-1",
    lg:"text-xs px-2.5 py-1 gap-1.5",
  }

  const iconSizes = {
    sm:"w-2.5 h-2.5",
    md:"w-3 h-3",
    lg:"w-3.5 h-3.5",
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
 inline-flex items-center rounded-full border border-lia-border-subtle/60 dark:border-lia-border-subtle/60
                    bg-lia-bg-primary/80 dark:bg-lia-bg-secondary/80 backdrop-blur-sm
                    font-medium transition-colors duration-200
                    hover:hover:border-lia-border-default dark:hover:border-lia-border-medium
                    focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-lia-border-default
                    ${sizeClasses[size]}
                  `}
                 
                >
                  {showCategory && (
                    <span className={`${category.color}`}>
                      <CategoryIcon className={iconSizes[size]} />
                    </span>
                  )}
                  <span className="text-lia-text-primary truncate max-w-[100px]">
                    {benefit.name}
                  </span>
                  {benefit.is_highlighted && (
                    <Star className={`${iconSizes[size]} text-status-warning fill-yellow-500`} />
                  )}
                </button>
              </TooltipTrigger>
              <TooltipContent 
                side="top" 
                className="max-w-[280px] p-3 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className={`p-1.5 rounded-md ${category.bgColor}`}>
                        <CategoryIcon className={`w-4 h-4 ${category.color}`} />
                      </div>
                      <div>
                        <p className="font-semibold text-lia-text-primary text-sm">
                          {benefit.name}
                        </p>
                        <p className="text-xs text-lia-text-primary">{category.name}</p>
                      </div>
                    </div>
                    {benefit.is_highlighted && (
                      <Star className="w-4 h-4 text-status-warning fill-yellow-500 flex-shrink-0" />
                    )}
                  </div>
                  
                  {benefit.description && (
                    <p className="text-xs text-lia-text-primary leading-relaxed">
                      {benefit.description}
                    </p>
                  )}
                  
                  <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                    {valueDisplay && (
                      <span className="inline-flex items-center gap-1 text-xs text-lia-text-primary">
                        {benefit.value_type ==="monetary" && <DollarSign className="w-3 h-3" />}
                        {benefit.value_type ==="percentage" && <Percent className="w-3 h-3" />}
                        {valueDisplay}
                      </span>
                    )}
                    
                    {benefit.waiting_period_days > 0 && (
                      <span className="inline-flex items-center gap-1 text-xs text-lia-text-primary">
                        <Clock className="w-3 h-3" />
                        {getWaitingPeriodLabel(benefit.waiting_period_days)}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex flex-wrap gap-1">
                    {benefit.is_mandatory && (
                      <Chip density="relaxed" variant="neutral" muted >Obrigatório</Chip>
                    )}
                    {benefit.is_discount && (
                      <Chip density="relaxed" variant="danger" >Desconto</Chip>
                    )}
                    {benefit.provider && (
                      <Chip density="relaxed" variant="neutral" >{benefit.provider}</Chip>
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
              border border-dashed border-lia-border-default dark:border-lia-border-default
              bg-lia-bg-secondary/80 dark:bg-lia-bg-secondary/80
              text-lia-text-secondary
              font-medium transition-colors duration-200
              hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse
              hover:border-lia-border-medium dark:hover:border-lia-border-medium
              focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-lia-border-default
              ${sizeClasses[size]}
            `}
           
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
