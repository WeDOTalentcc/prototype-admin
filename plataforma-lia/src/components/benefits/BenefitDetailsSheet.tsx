"use client"

import React from "react"
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
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
} from "lucide-react"
import type { Benefit } from "@/hooks/useCompanyBenefits"

const BENEFIT_CATEGORIES: {
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

const SENIORITY_LEVELS: { id: string; name: string }[] = [
  { id: "all", name: "Todos os Níveis" },
  { id: "junior", name: "Júnior" },
  { id: "pleno", name: "Pleno" },
  { id: "senior", name: "Sênior" },
  { id: "coordinator", name: "Coordenação+" },
  { id: "manager", name: "Gerência+" },
  { id: "director", name: "Diretoria" },
  { id: "c-level", name: "C-Level" },
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
  if (benefit.value_type === "monetary" && benefit.value) {
    const prefix = benefit.is_discount ? "Desconto: " : ""
    return `${prefix}R$ ${benefit.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
  }
  if (benefit.value_type === "percentage" && benefit.percentage_value) {
    return `${benefit.percentage_value}%`
  }
  if (benefit.value_type === "informative") {
    return benefit.value_details || ""
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

function getSeniorityLabel(levels: string[]): string {
  if (!levels || levels.length === 0 || levels.includes('all')) {
    return "Todos os níveis"
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
  title = "Benefícios da Empresa",
}: BenefitDetailsSheetProps) {
  const groupedBenefits = groupBenefitsByCategory(benefits)
  const highlightedBenefits = benefits.filter(b => b.is_highlighted && b.is_active)
  const totalBenefits = benefits.filter(b => b.is_active).length

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-md p-0 flex flex-col">
        <SheetHeader className="px-6 pt-6 pb-4 border-b border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div 
              className="p-2.5 rounded-md"
              style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
            >
              <Gift className="w-5 h-5 text-gray-700" />
            </div>
            <div>
              <SheetTitle 
                className="text-lg font-semibold text-gray-950 dark:text-gray-50"
              >
                {title}
              </SheetTitle>
              <SheetDescription 
                className="text-sm text-gray-800 dark:text-gray-200"
                style={{ fontFamily: 'Open Sans, sans-serif' }}
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
                  <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                  <h3 
                    className="text-sm font-semibold text-gray-950 dark:text-gray-50"
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
                      className="text-sm font-semibold text-gray-950 dark:text-gray-50"
                    >
                      {category.name}
                    </h3>
                    <span className="text-xs text-gray-800 dark:text-gray-200">
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
                <Gift className="w-12 h-12 text-gray-300 mb-3" />
                <p 
                  className="text-sm text-gray-800 dark:text-gray-200"
                  style={{ fontFamily: 'Open Sans, sans-serif' }}
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
        p-3 rounded-md border transition-all duration-200
        ${isHighlighted 
          ? 'border-yellow-200 dark:border-yellow-800/50 bg-yellow-50/50 dark:bg-yellow-900/10' 
          : 'border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900/50'
        }
        hover:hover:border-gray-200 dark:hover:border-gray-700
      `}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 
              className="font-medium text-gray-950 dark:text-gray-50 text-sm truncate"
              style={{ fontFamily: 'Open Sans, sans-serif' }}
            >
              {benefit.name}
            </h4>
            {benefit.is_highlighted && !isHighlighted && (
              <Star className="w-3.5 h-3.5 text-yellow-500 fill-yellow-500 flex-shrink-0" />
            )}
          </div>
          
          {benefit.description && (
            <p 
              className="text-xs text-gray-800 dark:text-gray-200 line-clamp-2 mb-2"
              style={{ fontFamily: 'Open Sans, sans-serif' }}
            >
              {benefit.description}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-2 text-xs text-gray-800 dark:text-gray-200">
            {valueDisplay && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-gray-50 dark:bg-gray-800">
                {benefit.value_type === "monetary" && <DollarSign className="w-3 h-3" />}
                {benefit.value_type === "percentage" && <Percent className="w-3 h-3" />}
                {valueDisplay}
              </span>
            )}
            
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-gray-50 dark:bg-gray-800">
              <Clock className="w-3 h-3" />
              {getWaitingPeriodLabel(benefit.waiting_period_days)}
            </span>
            
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-gray-50 dark:bg-gray-800">
              <Users className="w-3 h-3" />
              {getSeniorityLabel(benefit.seniority_levels)}
            </span>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-1 mt-2">
        {benefit.is_mandatory && (
          <Badge variant="secondary" className="text-xs">Obrigatório</Badge>
        )}
        {benefit.is_discount && (
          <Badge variant="outline" className="text-xs text-red-600 border-red-200 dark:text-red-400 dark:border-red-800">
            Desconto
          </Badge>
        )}
        {benefit.provider && (
          <Badge variant="outline" className="text-xs">{benefit.provider}</Badge>
        )}
      </div>
    </div>
  )
}

export default BenefitDetailsSheet
