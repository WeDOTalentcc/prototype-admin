"use client"


import { CURRENCY_SYMBOL } from"@/lib/pricing"
import React from"react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Switch } from"@/components/ui/switch"
import {
  DollarSign,
  Star,
  Users,
  Clock,
  Pencil,
  Trash2,
} from"lucide-react"
import { textStyles } from"@/lib/design-tokens"

interface Benefit {
  id?: string
  name: string
  description: string
  category: string
  value_type: string
  value?: number
  percentage_value?: number
  value_details?: string
  seniority_levels: string[]
  waiting_period_days: number
  is_mandatory: boolean
  is_active: boolean
  is_highlighted: boolean
  is_discount: boolean
  provider?: string
}

const SENIORITY_LEVELS = [
  { id:"all", name:"Todos os Níveis" },
  { id:"junior", name:"Júnior" },
  { id:"pleno", name:"Pleno" },
  { id:"senior", name:"Sênior" },
  { id:"coordinator", name:"Coordenação+" },
  { id:"manager", name:"Gerência+" },
  { id:"director", name:"Diretoria" },
  { id:"c-level", name:"C-Level" },
]

const WAITING_PERIODS = [
  { id: 0, name:"Imediato" },
  { id: 30, name:"30 dias" },
  { id: 60, name:"60 dias" },
  { id: 90, name:"90 dias" },
  { id: 180, name:"6 meses" },
  { id: 365, name:"1 ano" },
]

interface BenefitItemCardProps {
  benefit: Benefit
  isEditingBenefits: boolean
  onToggleStatus: (benefit: Benefit) => void
  onEdit: (benefit: Benefit) => void
  onDelete: (benefitId: string) => void
}

export const BenefitItemCard = React.memo(function BenefitItemCard({
  benefit,
  isEditingBenefits,
  onToggleStatus,
  onEdit,
  onDelete,
}: BenefitItemCardProps) {
  const formatBenefitValue = (b: Benefit) => {
    if (b.value_type ==="monetary" && b.value) {
      const prefix = b.is_discount ?"Desconto:" :""
      return prefix + CURRENCY_SYMBOL +"" +  b.value.toLocaleString("pt-BR", { minimumFractionDigits: 2 })
    }
    if (b.value_type ==="percentage" && b.percentage_value) {
      return b.percentage_value +"%"
    }
    if (b.value_type ==="informative") {
      return b.value_details ||"Informativo"
    }
    return"-"
  }

  const getSeniorityLabel = (levels: string[]) => {
    if (!levels || levels.length === 0 || levels.includes("all")) {
      return"Todos"
    }
    if (levels.length === 1) {
      return SENIORITY_LEVELS.find((l) => l.id === levels[0])?.name || levels[0]
    }
    return levels.length +" níveis"
  }

  const getWaitingPeriodLabel = (days: number) => {
    const period = WAITING_PERIODS.find((p) => p.id === days)
    return period ? period.name : days +" dias"
  }

  const activeClass = !benefit.is_active ?"opacity-60" :""

  return (
    <div
      className={"p-3 flex items-center justify-between hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50 transition-colors motion-reduce:transition-none" + activeClass}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className={textStyles.subtitle +" truncate"}>
            {benefit.name}
          </h4>
          {benefit.is_highlighted && (
            <Star className="w-3.5 h-3.5 text-status-warning fill-yellow-500" />
          )}
          {benefit.is_mandatory && (
            <Chip variant="neutral" muted className="text-micro">Obrigatório</Chip>
          )}
          {benefit.is_discount && (
            <Chip variant="neutral" className="text-micro text-status-error border-status-error/30">
              Desconto
            </Chip>
          )}
        </div>
        <p className={textStyles.description +" truncate mb-1.5"}>
          {benefit.description ||"Sem descrição"}
        </p>
        <div className="flex items-center gap-3 text-xs text-lia-text-secondary">
          <span className="flex items-center gap-1">
            <DollarSign className="w-3.5 h-3.5" />
            {formatBenefitValue(benefit)}
          </span>
          <span className="flex items-center gap-1">
            <Users className="w-3.5 h-3.5" />
            {getSeniorityLabel(benefit.seniority_levels)}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {getWaitingPeriodLabel(benefit.waiting_period_days)}
          </span>
          {benefit.provider && (
            <span className="text-lia-text-secondary">{benefit.provider}</span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-3 ml-3">
        <Switch
          checked={benefit.is_active}
          onCheckedChange={() => onToggleStatus(benefit)}
          disabled={!isEditingBenefits}
          className={!isEditingBenefits ?"opacity-60" :""}
        />
        {isEditingBenefits && (
          <>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => onEdit(benefit)}
            >
              <Pencil className="w-3.5 h-3.5 text-lia-text-secondary" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-status-error hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/20 dark:hover:text-status-error"
              onClick={() => benefit.id && onDelete(benefit.id)}
            >
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          </>
        )}
      </div>
    </div>
  )
})
