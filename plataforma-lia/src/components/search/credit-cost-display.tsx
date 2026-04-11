"use client"

import { useMemo } from"react"
import { AlertCircle, Coins, TrendingUp, Zap } from"lucide-react"
import { Badge } from"@/components/ui/badge"
import { 
  CreditEstimate,
  calculateCreditsLocally 
} from"@/lib/api/candidate-search"
import {
  formatCreditCost,
  getCostLevel,
  getCostColor,
  getCostBgColor,
  describeCostBreakdown
} from"@/hooks/useCreditEstimator"

interface PearchOptions {
  searchType?:"fast" |"pro"
  highFreshness?: boolean
  requireEmails?: boolean
  showEmails?: boolean
  requirePhoneNumbers?: boolean
  showPhoneNumbers?: boolean
  requirePhonesOrEmails?: boolean
}

interface CreditCostDisplayProps {
  options: PearchOptions
  limit?: number
  showBreakdown?: boolean
  compact?: boolean
  className?: string
}

export function CreditCostDisplay({
  options,
  limit = 15,
  showBreakdown = true,
  compact = false,
  className =""
}: CreditCostDisplayProps) {
  const estimate = useMemo(() => {
    return calculateCreditsLocally({
      searchType: options.searchType ||"fast",
      limit,
      highFreshness: options.highFreshness || false,
      requireEmails: options.requireEmails || false,
      showEmails: options.showEmails || false,
      requirePhoneNumbers: options.requirePhoneNumbers || false,
      showPhoneNumbers: options.showPhoneNumbers || false,
      requirePhonesOrEmails: options.requirePhonesOrEmails || false
    })
  }, [options, limit])

  const costLevel = getCostLevel(estimate.total_estimated)
  const costColor = getCostColor(costLevel)
  const costBgColor = getCostBgColor(costLevel)

  if (compact) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <Coins className="w-4 h-4 text-lia-text-primary" />
        <span className={`text-sm font-medium ${costColor}`}>
          {formatCreditCost(estimate.total_estimated)}
        </span>
        {estimate.warnings.length > 0 && (
          <AlertCircle className="w-4 h-4 text-status-warning" />
        )}
      </div>
    )
  }

  return (
    <div className={`rounded-md border p-4 border-lia-border-default dark:border-lia-border-default ${costBgColor} ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Coins className="w-5 h-5 text-lia-text-primary" />
          <span className="font-semibold text-sm">Estimativa de Custos</span>
        </div>
        <Badge 
          variant="outline" 
          className={`${costColor} border-current`}
        >
          {formatCreditCost(estimate.total_estimated)}
        </Badge>
      </div>

      {showBreakdown && (
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between text-lia-text-secondary">
            <span className="flex items-center gap-1">
              <Zap className="w-3 h-3" />
              Tipo de Busca
            </span>
            <span className="font-medium">
              {estimate.pearch_type ==="fast" ?"Rapida" :"Profissional"} ({estimate.base_cost}/cand.)
            </span>
          </div>

          {estimate.insights_cost > 0 && (
            <div className="flex items-center justify-between text-lia-text-secondary">
              <span>Insights + Scoring</span>
              <span className="font-medium">+{estimate.insights_cost}/cand.</span>
            </div>
          )}

          {estimate.freshness_cost > 0 && (
            <div className="flex items-center justify-between text-lia-text-secondary">
              <span>Dados Atualizados</span>
              <span className="font-medium">+{estimate.freshness_cost}/cand.</span>
            </div>
          )}

          {estimate.email_cost > 0 && (
            <div className="flex items-center justify-between text-lia-text-secondary">
              <span>Opcoes de Email</span>
              <span className="font-medium">+{estimate.email_cost}/cand.</span>
            </div>
          )}

          {estimate.phone_cost > 0 && (
            <div className="flex items-center justify-between text-status-warning">
              <span className="flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                Opcoes de Telefone
              </span>
              <span className="font-medium">+{estimate.phone_cost}/cand.</span>
            </div>
          )}

          <div className="border-t pt-2 mt-2 border-lia-border-default dark:border-lia-border-default">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                Por Candidato
              </span>
              <span className="font-semibold">{estimate.cost_per_candidate} creditos</span>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span>Total ({limit} candidatos)</span>
              <span className={`font-semibold text-lg ${costColor}`}>
                {estimate.total_estimated} creditos
              </span>
            </div>
          </div>
        </div>
      )}

      {estimate.warnings.length > 0 && (
        <div className="mt-3 p-2 bg-status-warning/10 rounded-xl border border-status-warning/30">
          {estimate.warnings.map((warning, idx) => (
            <div key={idx} className="flex items-start gap-2 text-xs text-status-warning">
              <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
              <span>{warning}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

interface CreditCostBadgeProps {
  cost: number
  suffix?: string
  className?: string
}

export function CreditCostBadge({ cost, suffix ="", className ="" }: CreditCostBadgeProps) {
  const level = getCostLevel(cost)
  const color = getCostColor(level)
  
  return (
    <Badge 
      variant="secondary" 
      className={`text-xs ${color} ${className}`}
    >
      {cost > 0 ? `+${cost}` : cost} {suffix ||"creditos"}
    </Badge>
  )
}

interface InlineCreditCostProps {
  cost: number
  label: string
  highlight?: boolean
}

export function InlineCreditCost({ cost, label, highlight = false }: InlineCreditCostProps) {
  const level = getCostLevel(cost)
  const color = highlight ?"text-status-warning" : getCostColor(level)
  
  return (
    <span className={`text-xs ${color}`}>
      {label} {cost > 0 && `(+${cost})`}
    </span>
  )
}
