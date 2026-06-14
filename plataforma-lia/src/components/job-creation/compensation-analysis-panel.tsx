"use client"

import React from"react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from"@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Progress } from"@/components/ui/progress"
import { cn } from"@/lib/utils"
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  Building2, 
  BarChart3, 
  History, 
  Brain, 
  PenLine,
  Gift,
  Target,
  Check,
  X,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  ChevronRight,
  PieChart
} from"lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from"@/components/ui/tooltip"

export type DataSource = 'company_policy' | 'market_benchmark' | 'internal_history' | 'inference' | 'user_input'

export type CompetitivenessStatus = 'competitive' | 'below_market' | 'above_market'

export interface SalaryRange {
  min: number
  max: number
}

export interface BenefitItem {
  id: string
  name: string
  value?: string
  annualValue?: number
  included: boolean
  isCompanyStandard?: boolean
}

export interface CompensationAnalysisResult {
  overallStatus: CompetitivenessStatus
  executiveSummary: string
  salary: {
    proposed: SalaryRange
    market: SalaryRange
    policy?: SalaryRange
    source: DataSource
    percentileVsMarket: number
    suggestion?: SalaryRange
  }
  bonus: {
    proposedPercentage: number
    policyPercentage?: number
    criteria?: string
    source: DataSource
    suggestion?: number
  }
  benefits: {
    proposed: BenefitItem[]
    companyStandard: BenefitItem[]
    totalAnnualValue: number
    missingFromStandard: BenefitItem[]
    source: DataSource
  }
  totalCompensation: {
    proposedAnnual: number
    marketAnnual?: number
    policyAnnual?: number
    breakdown: {
      salaryPercentage: number
      bonusPercentage: number
      benefitsPercentage: number
    }
  }
}

export interface SuggestedValues {
  salary?: SalaryRange
  bonusPercentage?: number
  benefits?: string[]
}

export interface CompensationAnalysisPanelProps {
  analysis: CompensationAnalysisResult | null
  isLoading: boolean
  onApplySuggestions: (suggestions: SuggestedValues) => void
  onDismiss: () => void
  onAdjustManually?: () => void
}

const DATA_SOURCE_CONFIG: Record<DataSource, {
  icon: string
  label: string
  className: string
}> = {
  company_policy: {
    icon: '🏢',
    label: 'Política da Empresa',
    className: ' border-wedo-cyan/30 dark:bg-wedo-cyan/10 dark:border-wedo-cyan/30'
  },
  market_benchmark: {
    icon: '📊',
    label: 'Benchmark de Mercado',
    className: ' border-wedo-purple/30 dark:bg-wedo-purple/10 dark:text-wedo-purple dark:border-wedo-purple/30'
  },
  internal_history: {
    icon: '📈',
    label: 'Histórico Interno',
    className: ' border-status-success/30 dark:bg-status-success dark:border-status-success/30'
  },
  inference: {
    icon: '🤖',
    label: 'Inferência IA',
    className: ' border-status-warning/30 dark:bg-status-warning dark:border-status-warning/30'
  },
  user_input: {
    icon: '✏️',
    label: 'Informado',
    className: 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-subtle'
  }
}

const STATUS_CONFIG: Record<CompetitivenessStatus, {
  icon: React.ElementType
  label: string
  description: string
  className: string
  bgClassName: string
}> = {
  competitive: {
    icon: CheckCircle2,
    label: 'Competitivo',
    description: 'A remuneração está alinhada com o mercado',
    className: 'text-status-success',
    bgClassName: 'bg-status-success/10 border-status-success/30 dark:bg-status-success/30 dark:border-status-success/30'
  },
  below_market: {
    icon: AlertTriangle,
    label: 'Abaixo do Mercado',
    description: 'A remuneração pode dificultar atração de talentos',
    className: 'text-status-warning',
    bgClassName: 'bg-status-warning/10 border-status-warning/30 dark:bg-status-warning/30 dark:border-status-warning/30'
  },
  above_market: {
    icon: TrendingUp,
    label: 'Acima do Mercado',
    description: 'A remuneração está acima da média de mercado',
    className: 'text-wedo-cyan-text',
    bgClassName: 'bg-wedo-cyan/10 border-wedo-cyan/30 dark:border-wedo-cyan/30'
  }
}

function DataSourceBadge({ source }: { source: DataSource }) {
  const config = DATA_SOURCE_CONFIG[source]
  return (
    <Chip density="compact" variant="neutral" muted>
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </Chip>
  )
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

function SalaryComparisonBar({ 
  proposed, 
  market, 
  policy 
}: { 
  proposed: SalaryRange
  market: SalaryRange
  policy?: SalaryRange
}) {
  const allValues = [
    proposed.min, proposed.max,
    market.min, market.max,
    ...(policy ? [policy.min, policy.max] : [])
  ]
  const minValue = Math.min(...allValues) * 0.9
  const maxValue = Math.max(...allValues) * 1.1
  const range = maxValue - minValue

  const getPosition = (value: number) => ((value - minValue) / range) * 100

  return (
    <div className="relative h-16 mt-4 mb-2">
      <div className="absolute inset-x-0 top-6 h-2 bg-lia-bg-tertiary rounded-full" />
      
      <div 
        className="absolute top-6 h-2 bg-wedo-purple/20 dark:bg-wedo-purple rounded-full"
        style={{left: `${getPosition(market.min)}%`,
          width: `${getPosition(market.max) - getPosition(market.min)}%`}}
      />
      
      {policy && (
        <div 
          className="absolute top-6 h-2 bg-wedo-cyan/20 dark:bg-wedo-cyan/10 rounded-full opacity-60"
          style={{left: `${getPosition(policy.min)}%`,
            width: `${getPosition(policy.max) - getPosition(policy.min)}%`}}
        />
      )}
      
      <div 
        className="absolute top-5 h-4 bg-status-success dark:bg-status-success rounded-full"
        style={{left: `${getPosition(proposed.min)}%`,
          width: `${getPosition(proposed.max) - getPosition(proposed.min)}%`}}
      />

      <div className="absolute top-11 left-0 text-micro text-lia-text-tertiary">
        {formatCurrency(minValue)}
      </div>
      <div className="absolute top-11 right-0 text-micro text-lia-text-tertiary">
        {formatCurrency(maxValue)}
      </div>

      <div className="flex justify-center gap-4 absolute top-0 inset-x-0">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-status-success" />
          <span className="text-micro text-lia-text-tertiary">Proposto</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-wedo-purple/10" />
          <span className="text-micro text-lia-text-tertiary">Mercado</span>
        </div>
        {policy && (
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-wedo-cyan/10" />
            <span className="text-micro text-lia-text-tertiary">Política</span>
          </div>
        )}
      </div>
    </div>
  )
}

function CompensationBreakdownChart({
  breakdown
}: {
  breakdown: {
    salaryPercentage: number
    bonusPercentage: number
    benefitsPercentage: number
  }
}) {
  const segments = [
    { label: 'Salário', percentage: breakdown.salaryPercentage, color: 'bg-wedo-cyan' },
    { label: 'Bônus', percentage: breakdown.bonusPercentage, color: 'bg-status-success' },
    { label: 'Benefícios', percentage: breakdown.benefitsPercentage, color: 'bg-wedo-purple' }
  ]

  return (
    <div className="space-y-3">
      <div className="flex h-4 rounded-full overflow-hidden">
        {segments.map((segment, index) => (
          <div
            key={segment.label}
            className={cn(segment.color, 'transition-colors motion-reduce:transition-none')}
            style={{width: `${segment.percentage}%`}}
          />
        ))}
      </div>
      <div className="flex justify-between text-micro">
        {segments.map((segment) => (
          <div key={segment.label} className="flex items-center gap-1">
            <div className={cn('w-2 h-2 rounded-full', segment.color)} />
            <span className="text-lia-text-tertiary">{segment.label}</span>
            <span className="font-medium">{segment.percentage.toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function CompensationAnalysisPanel({
  analysis,
  isLoading,
  onApplySuggestions,
  onDismiss,
  onAdjustManually
}: CompensationAnalysisPanelProps) {
  if (isLoading) {
    return (
      <Card className="border-dashed rounded-md">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin motion-reduce:animate-none text-lia-text-tertiary mb-3" />
          <p className="text-sm text-lia-text-tertiary">Analisando remuneração...</p>
        </CardContent>
      </Card>
    )
  }

  if (!analysis) {
    return null
  }

  const statusConfig = STATUS_CONFIG[analysis.overallStatus]
  const StatusIcon = statusConfig.icon

  const hasSuggestions = !!(
    analysis.salary.suggestion ||
    analysis.bonus.suggestion ||
    analysis.benefits.missingFromStandard.length > 0
  )

  const buildSuggestions = (): SuggestedValues => {
    const suggestions: SuggestedValues = {}
    
    if (analysis.salary.suggestion) {
      suggestions.salary = analysis.salary.suggestion
    }
    
    if (analysis.bonus.suggestion !== undefined) {
      suggestions.bonusPercentage = analysis.bonus.suggestion
    }
    
    if (analysis.benefits.missingFromStandard.length > 0) {
      suggestions.benefits = analysis.benefits.missingFromStandard.map(b => b.id)
    }
    
    return suggestions
  }

  return (
    <Card className="overflow-hidden rounded-xl">
      <CardHeader className={cn('', statusConfig.bgClassName)}>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <StatusIcon className={cn('h-5 w-5', statusConfig.className)} />
            <div>
              <CardTitle className="text-sm font-sans">{statusConfig.label}</CardTitle>
              <CardDescription className="text-xs mt-0.5">
                {statusConfig.description}
              </CardDescription>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onDismiss} className="h-7 w-7 p-0 hover:bg-lia-interactive-hover">
            <X className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-xs text-lia-text-tertiary mt-2">
          {analysis.executiveSummary}
        </p>
      </CardHeader>

      <CardContent className="p-4 space-y-6">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-lia-text-tertiary" />
              <h4 className="text-xs font-medium">Salário</h4>
            </div>
            <DataSourceBadge source={analysis.salary.source} />
          </div>

          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-2 rounded-xl bg-status-success/10 dark:bg-status-success/30 border border-status-success/30 dark:border-status-success/30">
              <p className="text-micro text-lia-text-tertiary mb-1">Proposto</p>
              <p className="text-xs font-semibold text-status-success">
                {formatCurrency(analysis.salary.proposed.min)} - {formatCurrency(analysis.salary.proposed.max)}
              </p>
            </div>
            <div className="p-2 rounded-xl bg-wedo-purple/10 border border-wedo-purple/30 dark:border-wedo-purple/30">
              <p className="text-micro text-lia-text-tertiary mb-1">Mercado</p>
              <p className="text-xs font-semibold text-wedo-purple-text dark:text-wedo-purple">
                {formatCurrency(analysis.salary.market.min)} - {formatCurrency(analysis.salary.market.max)}
              </p>
            </div>
            {analysis.salary.policy && (
              <div className="p-2 rounded-xl bg-wedo-cyan/10 border border-wedo-cyan/30 dark:border-wedo-cyan/30">
                <p className="text-micro text-lia-text-tertiary mb-1">Política</p>
                <p className="text-xs font-semibold text-wedo-cyan-text">
                  {formatCurrency(analysis.salary.policy.min)} - {formatCurrency(analysis.salary.policy.max)}
                </p>
              </div>
            )}
          </div>

          <SalaryComparisonBar 
            proposed={analysis.salary.proposed}
            market={analysis.salary.market}
            policy={analysis.salary.policy}
          />

          <div className="flex items-center justify-between text-xs">
            <span className="text-lia-text-tertiary">Posição vs. Mercado:</span>
            <span className={cn(
 'font-medium',
              analysis.salary.percentileVsMarket >= 50 ? 'text-status-success' : 'text-status-warning'
            )}>
              Percentil {analysis.salary.percentileVsMarket}
            </span>
          </div>

          {analysis.salary.suggestion && (
            <div className="p-2 rounded-xl bg-status-warning/10 dark:bg-status-warning/30 border border-status-warning/30 dark:border-status-warning/30 flex items-center gap-2">
              <AlertTriangle className="h-3.5 w-3.5 text-status-warning flex-shrink-0" />
              <p className="text-micro text-status-warning">
                Sugestão: Ajustar para {formatCurrency(analysis.salary.suggestion.min)} - {formatCurrency(analysis.salary.suggestion.max)}
              </p>
            </div>
          )}
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-lia-text-tertiary" />
              <h4 className="text-xs font-medium">Bônus</h4>
            </div>
            <DataSourceBadge source={analysis.bonus.source} />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="p-2 rounded-xl bg-lia-bg-secondary border">
              <p className="text-micro text-lia-text-tertiary mb-1">Proposto</p>
              <p className="text-sm font-semibold">{analysis.bonus.proposedPercentage}%</p>
            </div>
            {analysis.bonus.policyPercentage !== undefined && (
              <div className="p-2 rounded-xl bg-wedo-cyan/10 border border-wedo-cyan/30 dark:border-wedo-cyan/30">
                <p className="text-micro text-lia-text-tertiary mb-1">Política da Empresa</p>
                <p className="text-sm font-semibold text-wedo-cyan-text">
                  {analysis.bonus.policyPercentage}%
                </p>
              </div>
            )}
          </div>

          {analysis.bonus.criteria && (
            <p className="text-micro text-lia-text-tertiary">
              <span className="font-medium">Critérios:</span> {analysis.bonus.criteria}
            </p>
          )}

          {analysis.bonus.suggestion !== undefined && analysis.bonus.suggestion !== analysis.bonus.proposedPercentage && (
            <div className="p-2 rounded-xl bg-status-warning/10 dark:bg-status-warning/30 border border-status-warning/30 dark:border-status-warning/30 flex items-center gap-2">
              <AlertTriangle className="h-3.5 w-3.5 text-status-warning flex-shrink-0" />
              <p className="text-micro text-status-warning">
                Sugestão: Ajustar bônus para {analysis.bonus.suggestion}%
              </p>
            </div>
          )}
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Gift className="h-4 w-4 text-lia-text-tertiary" />
              <h4 className="text-xs font-medium">Benefícios</h4>
            </div>
            <DataSourceBadge source={analysis.benefits.source} />
          </div>

          <div className="space-y-2">
            <p className="text-micro text-lia-text-tertiary font-medium">Benefícios Incluídos:</p>
            <div className="flex flex-wrap gap-1">
              {analysis.benefits.proposed.filter(b => b.included).map((benefit) => (
                <TooltipProvider key={benefit.id}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Chip density="compact" variant="neutral" muted>
                        <Check className="h-3 w-3" />
                        {benefit.name}
                        {benefit.isCompanyStandard && (
                          <span className="opacity-60">🏢</span>
                        )}
                      </Chip>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="text-xs">
                        {benefit.value || 'Incluído'}
                        {benefit.annualValue && ` • ${formatCurrency(benefit.annualValue)}/ano`}
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              ))}
            </div>
          </div>

          {analysis.benefits.missingFromStandard.length > 0 && (
            <div className="space-y-2">
              <p className="text-micro text-status-warning font-medium">
                Benefícios Padrão Não Incluídos:
              </p>
              <div className="flex flex-wrap gap-1">
                {analysis.benefits.missingFromStandard.map((benefit) => (
                  <Chip
                    key={benefit.id}
                    density="compact"
                    variant="warning"
                  >
                    <X className="h-3 w-3" />
                    {benefit.name}
                  </Chip>
                ))}
              </div>
            </div>
          )}

          <div className="p-2 rounded-xl bg-lia-bg-secondary border">
            <div className="flex items-center justify-between">
              <span className="text-micro text-lia-text-tertiary">Valor Monetizável Anual:</span>
              <span className="text-xs font-semibold">
                {formatCurrency(analysis.benefits.totalAnnualValue)}
              </span>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <PieChart className="h-4 w-4 text-lia-text-tertiary" />
            <h4 className="text-xs font-medium">Total Compensation</h4>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-2 rounded-xl bg-lia-bg-secondary border">
              <p className="text-micro text-lia-text-tertiary mb-1">Proposto Anual</p>
              <p className="text-xs font-semibold">
                {formatCurrency(analysis.totalCompensation.proposedAnnual)}
              </p>
            </div>
            {analysis.totalCompensation.marketAnnual && (
              <div className="p-2 rounded-xl bg-wedo-purple/10 border border-wedo-purple/30 dark:border-wedo-purple/30">
                <p className="text-micro text-lia-text-tertiary mb-1">Mercado</p>
                <p className="text-xs font-semibold text-wedo-purple-text dark:text-wedo-purple">
                  {formatCurrency(analysis.totalCompensation.marketAnnual)}
                </p>
              </div>
            )}
            {analysis.totalCompensation.policyAnnual && (
              <div className="p-2 rounded-xl bg-wedo-cyan/10 border border-wedo-cyan/30 dark:border-wedo-cyan/30">
                <p className="text-micro text-lia-text-tertiary mb-1">Política</p>
                <p className="text-xs font-semibold text-wedo-cyan-text">
                  {formatCurrency(analysis.totalCompensation.policyAnnual)}
                </p>
              </div>
            )}
          </div>

          <CompensationBreakdownChart breakdown={analysis.totalCompensation.breakdown} />
        </div>

        <div className="flex gap-2 pt-2 border-t border-lia-border-subtle">
          {hasSuggestions && (
            <Button 
              variant="primary" 
              size="sm" 
              className="flex-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
              onClick={() => onApplySuggestions(buildSuggestions())}
            >
              <Brain className="h-3.5 w-3.5 mr-1 text-wedo-cyan" />
              Aplicar Sugestões
            </Button>
          )}
          {onAdjustManually && (
            <Button 
              variant="outline" 
              size="sm" 
              className="flex-1 hover:bg-lia-interactive-hover"
              onClick={onAdjustManually}
            >
              <PenLine className="h-3.5 w-3.5 mr-1" />
              Ajustar Manualmente
            </Button>
          )}
          <Button 
            variant={hasSuggestions ?"ghost" :"primary"}
            size="sm" 
 className={cn("flex-1", !hasSuggestions &&"hover:text-white dark:hover:bg-lia-interactive-active", hasSuggestions &&"dark:text-lia-text-secondary hover:bg-lia-interactive-hover")}
            onClick={onDismiss}
          >
            Prosseguir
            <ChevronRight className="h-3.5 w-3.5 ml-1" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default CompensationAnalysisPanel
