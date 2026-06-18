"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { formatBRL } from"@/lib/pricing"

import React from"react"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from"@/components/ui/sheet"
import { Chip } from "@/components/ui/chip"
import { ScrollArea } from"@/components/ui/scroll-area"
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
  Users,
  Gift,
  type LucideIcon,
} from"lucide-react"
import type { Benefit } from"@/hooks/company/useCompanyBenefits"

const BENEFIT_CATEGORIES: {
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

const SENIORITY_LEVELS: { id: string; name: string }[] = [
  { id:"all", name:"Todos os Níveis" },
  { id:"junior", name:"Júnior" },
  { id:"pleno", name:"Pleno" },
  { id:"senior", name:"Sênior" },
  { id:"coordinator", name:"Coordenação+" },
  { id:"manager", name:"Gerência+" },
  { id:"director", name:"Diretoria" },
  { id:"c-level", name:"C-Level" },
]

interface BenefitDetailsSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  benefits: Benefit[]
  title?: string
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
    return benefit.value_details ||""
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

function getSeniorityLabel(levels: string[]): string {
  if (!levels || levels.length === 0 || levels.includes('all')) {
    return"Todos os níveis"
  }
  if (levels.length === 1) {
    return SENIORITY_LEVELS.find(l => l.id === levels[0])?.name || levels[0]
  }
  return `${levels.length} níveis`
}

function groupBenefitsByCategory(benefits: Benefit[]): Map<string, Benefit[]> {
  const grouped = new Map<string, Benefit[]>()
  
  for (const category of BENEFIT_CATEGORIES) {
    const categoryBenefits = benefits.filter(b => b.category === category.id && b.is_active)
    if (categoryBenefits.length > 0) {
      grouped.set(category.id, categoryBenefits)
    }
  }
  
  return grouped
}

export function BenefitDetailsSheet({
  open,
  onOpenChange,
  benefits,
  title ="Benefícios da Empresa",
}: BenefitDetailsSheetProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('benefit-details', open)

  const groupedBenefits = groupBenefitsByCategory(benefits)
  const highlightedBenefits = benefits.filter(b => b.is_highlighted && b.is_active)
  const totalBenefits = benefits.filter(b => b.is_active).length

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-md p-0 flex flex-col">
        <SheetHeader className="px-6 pt-6 pb-4">
          <div className="flex items-center gap-3">
            <div 
              className="p-2.5 rounded-md bg-lia-interactive-active/30"
            >
              <Gift className="w-5 h-5 text-lia-text-secondary" />
            </div>
            <div>
              <SheetTitle 
                className="text-lg font-semibold text-lia-text-primary"
              >
                {title}
              </SheetTitle>
              <SheetDescription 
                className="text-sm text-lia-text-primary"
               
              >
                {totalBenefits} benefícios disponíveis
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <ScrollArea className="flex-1 px-6">
          <div className="py-4 space-y-6">
            {highlightedBenefits.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Star className="w-4 h-4 text-status-warning fill-yellow-500" />
                  <h3 
                    className="text-sm font-semibold text-lia-text-primary"
                  >
                    Destaques
                  </h3>
                </div>
                <div className="space-y-2">
                  {highlightedBenefits.map((benefit, index) => (
                    <BenefitCard key={benefit.id || `highlighted-${index}`} benefit={benefit} isHighlighted />
                  ))}
                </div>
              </div>
            )}

            {Array.from(groupedBenefits.entries()).map(([categoryId, categoryBenefits]) => {
              const category = getCategoryInfo(categoryId)
              const CategoryIcon = category.icon

              return (
                <div key={categoryId} className="space-y-3">
                  <div className="flex items-center gap-2">
                    <div className={`p-1.5 rounded-md ${category.bgColor}`}>
                      <CategoryIcon className={`w-4 h-4 ${category.color}`} />
                    </div>
                    <h3 
                      className="text-sm font-semibold text-lia-text-primary"
                    >
                      {category.name}
                    </h3>
                    <span className="text-xs text-lia-text-primary">
                      ({categoryBenefits.length})
                    </span>
                  </div>
                  <div className="space-y-2">
                    {categoryBenefits.map((benefit, index) => (
                      <BenefitCard key={benefit.id || `${categoryId}-${index}`} benefit={benefit} />
                    ))}
                  </div>
                </div>
              )
            })}

            {groupedBenefits.size === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Gift className="w-12 h-12 text-lia-text-tertiary mb-3" />
                <p 
                  className="text-sm text-lia-text-primary"
                 
                >
                  Nenhum benefício disponível
                </p>
              </div>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}

interface BenefitCardProps {
  benefit: Benefit
  isHighlighted?: boolean
}

function BenefitCard({ benefit, isHighlighted = false }: BenefitCardProps) {
  const category = getCategoryInfo(benefit.category)
  const valueDisplay = formatBenefitValue(benefit)

  return (
    <div 
      className={`
 p-3 rounded-md border transition-colors duration-200
        ${isHighlighted 
          ? 'border-status-warning/30 dark:border-status-warning/30/50 bg-status-warning/10/50' 
          : 'border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary/50'
        }
        hover:hover:border-lia-border-subtle dark:hover:border-lia-border-strong
      `}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 
              className="font-medium text-lia-text-primary text-sm truncate"
             
            >
              {benefit.name}
            </h4>
            {benefit.is_highlighted && !isHighlighted && (
              <Star className="w-3.5 h-3.5 text-status-warning fill-yellow-500 flex-shrink-0" />
            )}
          </div>
          
          {benefit.description && (
            <p 
              className="text-xs text-lia-text-primary line-clamp-2 mb-2"
             
            >
              {benefit.description}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-2 text-xs text-lia-text-primary">
            {valueDisplay && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                {benefit.value_type ==="monetary" && <DollarSign className="w-3 h-3" />}
                {benefit.value_type ==="percentage" && <Percent className="w-3 h-3" />}
                {valueDisplay}
              </span>
            )}
            
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-secondary">
              <Clock className="w-3 h-3" />
              {getWaitingPeriodLabel(benefit.waiting_period_days)}
            </span>
            
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-secondary">
              <Users className="w-3 h-3" />
              {getSeniorityLabel(benefit.seniority_levels)}
            </span>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-1 mt-2">
        {benefit.is_mandatory && (
          <Chip density="relaxed" variant="neutral" muted >Obrigatório</Chip>
        )}
        {benefit.is_discount && (
          <Chip density="relaxed" variant="danger" >
            Desconto
          </Chip>
        )}
        {benefit.provider && (
          <Chip density="relaxed" variant="neutral" >{benefit.provider}</Chip>
        )}
      </div>
    </div>
  )
}

export default BenefitDetailsSheet
