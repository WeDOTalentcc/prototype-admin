'use client'

import { formatBRL, CURRENCY_SYMBOL } from "@/lib/pricing"

import React from 'react'
import { DollarSign, Star, CheckCircle2, Plus, Check, Brain, Loader2, TrendingUp, ChevronDown, Settings,
  Stethoscope, Car, GraduationCap, Wallet, Home as HomeIcon, Baby, Shield as ShieldIcon,
  Utensils, Heart
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { textStyles } from '@/lib/design-tokens'
import { BENEFIT_CATEGORY_META, type BenefitCategory } from '@/types/benefits'

export interface Benefit {
  id: string
  name: string
  enabled: boolean
  category?: string
  value?: string
  value_type?: string
  percentage_value?: number
  value_details?: string
  is_highlighted?: boolean
  is_mandatory?: boolean
  provider?: string
}

export interface SalaryInfo {
  minSalary: string
  maxSalary: string
  minBonus: string
  maxBonus: string
  bonusCriteria: string
  benefits: Benefit[]
}

export interface SalaryBenchmark {
  internal?: {
    min: number
    max: number
    sample_size: number
    trend?: 'increasing' | 'stable' | 'decreasing'
  }
  market?: {
    min: number
    max: number
    confidence: 'high' | 'medium' | 'low'
    sources?: string[]
    learning_adjusted?: boolean
  }
  combined?: {
    min: number
    max: number
  }
}

export interface CompanyConfig {
  benefits?: string[] | { name: string; category: string; value?: number; is_active: boolean }[]
  [key: string]: unknown
}

export interface SalaryStageProps {
  salaryInfo: SalaryInfo
  onSalaryChange: (info: Partial<SalaryInfo>) => void
  salaryBenchmark?: SalaryBenchmark | null
  isLoadingBenchmark?: boolean
  companyConfig?: CompanyConfig | null
  isCollapsed?: boolean
  onExpandEdit?: () => void
  isFieldRequired?: boolean
  onShowAddBenefitModal?: () => void
  highlightedFields?: Set<string>
}

const CATEGORY_ICONS: Record<BenefitCategory, any> = {
  health: Stethoscope,
  food: Utensils,
  transport: Car,
  education: GraduationCap,
  financial: Wallet,
  quality_life: HomeIcon,
  family: Baby,
  security: ShieldIcon,
}

function formatBenefitDisplay(benefit: { value_type?: string; value?: string; percentage_value?: number; value_details?: string }): string {
  if (benefit.value_type === 'monetary' && benefit.value) {
    const numValue = parseFloat(benefit.value)
    return isNaN(numValue) ? `${CURRENCY_SYMBOL} ${benefit.value}` : formatBRL(numValue)
  }
  if (benefit.value_type === 'percentage' && benefit.percentage_value) {
    return `${benefit.percentage_value}%`
  }
  if (benefit.value_type === 'informative' && benefit.value_details) {
    return benefit.value_details
  }
  return ''
}

export function SalaryStage({
  salaryInfo,
  onSalaryChange,
  salaryBenchmark,
  isLoadingBenchmark = false,
  companyConfig,
  isCollapsed = false,
  onExpandEdit,
  isFieldRequired = true,
  onShowAddBenefitModal,
  highlightedFields,
}: SalaryStageProps) {
  const [isExpanded, setIsExpanded] = React.useState(!isCollapsed)

  const isFieldHighlighted = (fieldId: string) => highlightedFields?.has(fieldId) ?? false

  const handleToggleExpand = () => {
    setIsExpanded(!isExpanded)
    onExpandEdit?.()
  }

  const handleBenefitToggle = (benefitIdOrName: string) => {
    onSalaryChange({
      benefits: salaryInfo.benefits.map(b =>
        (b.id === benefitIdOrName || b.name === benefitIdOrName) ? { ...b, enabled: !b.enabled } : b
      )
    })
  }

  const groupedBenefits = React.useMemo(() => {
    const groups: Record<string, typeof salaryInfo.benefits> = {}
    for (const b of salaryInfo.benefits) {
      const cat = b.category || 'quality_life'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(b)
    }
    return groups
  }, [salaryInfo.benefits])

  return (
    <div className="space-y-3">
      {!isFieldRequired && (
        <div className="p-3 bg-gradient-to-r from-green-500/10 to-lia-bg-tertiary dark:to-lia-bg-primary rounded-md border border-status-success/30/30">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-status-success/20 flex items-center justify-center flex-shrink-0">
              <Brain className="w-3.5 h-3.5 text-status-success" />
            </div>
            <div className="flex-1">
              <span className="text-xs font-medium text-status-success">
                Remuneração pré-configurada
              </span>
              <p className="text-micro text-lia-text-secondary mt-0.5">
                Valores baseados nas políticas salariais da empresa.
                <button
                  onClick={handleToggleExpand}
                  className="ml-1 text-lia-text-secondary hover:underline font-medium"
                >
                  {isExpanded ? 'Ocultar' : 'Editar manualmente'}
                </button>
              </p>
            </div>
            <button
              onClick={handleToggleExpand}
              className="p-1.5 hover:bg-lia-bg-primary/50 rounded-md transition-colors motion-reduce:transition-none"
              aria-label={isExpanded ? 'Recolher painel de salário' : 'Expandir painel de salário'}
            >
              <ChevronDown className={cn(
 "w-4 h-4 text-lia-text-secondary transition-transform",
                isExpanded && "rotate-180"
              )} />
            </button>
          </div>
        </div>
      )}

      {(isFieldRequired || isExpanded) && (
        <>
          {salaryBenchmark && (salaryBenchmark.market || salaryBenchmark.internal) && (
            <div className="p-3 bg-gradient-to-r from-lia-bg-secondary dark:from-lia-bg-primary to-green-500/5 rounded-md border border-lia-border-default">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-lia-text-secondary" />
                <span className="text-xs font-medium text-lia-text-primary">
                  Benchmark de Mercado
                </span>
                {salaryBenchmark.market?.learning_adjusted && (
                  <span className="px-1.5 py-0.5 bg-status-success/10 text-status-success text-micro font-medium rounded-full">
                    Personalizado
                  </span>
                )}
              </div>

              {salaryBenchmark.internal && salaryBenchmark.internal.sample_size > 0 && (
                <div className="mb-2 p-2 bg-lia-bg-primary/50 rounded-md">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">Dados internos ({salaryBenchmark.internal.sample_size} vagas)</span>
                    {salaryBenchmark.internal.trend && salaryBenchmark.internal.trend !== 'stable' && (
                      <span className={`text-micro ${salaryBenchmark.internal.trend === 'increasing' ? 'text-status-success' : 'text-status-error'}`}>
                        {salaryBenchmark.internal.trend === 'increasing' ? '↑ Em alta' : '↓ Em queda'}
                      </span>
                    )}
                  </div>
                  <div className="text-xs font-semibold text-lia-text-primary">
                    {formatBRL(salaryBenchmark.internal.min)} - {formatBRL(salaryBenchmark.internal.max)}
                  </div>
                </div>
              )}

              {salaryBenchmark.market && salaryBenchmark.market.min > 0 && (
                <div className="mb-2 p-2 bg-lia-bg-primary/50 rounded-md">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-micro text-lia-text-secondary">
                      Dados de mercado ({salaryBenchmark.market.sources?.slice(0, 2).join(', ')})
                    </span>
                    <span className={`text-micro px-1.5 py-0.5 rounded-full ${
 salaryBenchmark.market.confidence === 'high' ? 'bg-status-success/10 text-status-success' :
                      salaryBenchmark.market.confidence === 'medium' ? 'bg-status-warning/10 text-status-warning' :
                      'bg-status-error/10 text-status-error'
                    }`}>
                      {salaryBenchmark.market.confidence === 'high' ? 'Alta confiança' :
                       salaryBenchmark.market.confidence === 'medium' ? 'Média confiança' : 'Baixa confiança'}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-lia-text-primary">
                    {formatBRL(salaryBenchmark.market.min)} - {formatBRL(salaryBenchmark.market.max)}
                  </div>
                </div>
              )}

              {salaryBenchmark.combined && (
                <button
                  onClick={() => {
                    onSalaryChange({
                      minSalary: salaryBenchmark.combined!.min.toLocaleString(),
                      maxSalary: salaryBenchmark.combined!.max.toLocaleString()
                    })
                  }}
                  className="w-full py-1.5 mt-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text text-micro font-medium rounded-md transition-colors motion-reduce:transition-none flex items-center justify-center gap-1 focus-visible:ring-2 focus-visible:ring-lia-border-default"
                >
                  <Brain className="w-3 h-3 text-wedo-cyan" />
                  Aplicar sugestão: {formatBRL(salaryBenchmark.combined.min)} - {formatBRL(salaryBenchmark.combined.max)}
                </button>
              )}

              <p className="text-micro text-lia-text-secondary mt-2 italic">
                Estimativa baseada em dados públicos. Valores podem variar.
              </p>
            </div>
          )}

          {isLoadingBenchmark && (
            <div className="p-3 bg-lia-bg-secondary rounded-md border border-lia-border-subtle flex items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-4 h-4 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
              <span className="text-xs text-lia-text-secondary">Buscando benchmark de mercado...</span>
            </div>
          )}

          <div className={cn(
 "transition-colors duration-300",
            (isFieldHighlighted('minSalary') || isFieldHighlighted('maxSalary') || isFieldHighlighted('salary') || isFieldHighlighted('salario')) && "field-highlight field-pulse"
          )}>
            <label className={`block ${textStyles.label} text-lia-text-secondary uppercase tracking-wide mb-2`}>
              <DollarSign className="w-3.5 h-3.5 inline mr-1 text-lia-text-secondary" />
              Salário Base (CLT)
            </label>
            <div className="flex gap-2">
              <div className="flex-1">
                <span className="text-micro text-lia-text-secondary">De</span>
                <div className={cn(
 "relative mt-1",
                  isFieldHighlighted('minSalary') && "field-highlight field-pulse"
                )}>
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-lia-text-secondary">{CURRENCY_SYMBOL}</span>
                  <input
                    type="text"
                    value={salaryInfo.minSalary}
                    onChange={(e) => onSalaryChange({ minSalary: e.target.value })}
                    placeholder="12.000"
                    className="w-full pl-9 pr-3 py-1.5 border border-lia-border-subtle rounded-md text-xs focus:outline-none focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
                   
                    aria-label="Salário mínimo base"
                  />
                </div>
              </div>
              <div className="flex-1">
                <span className="text-micro text-lia-text-secondary">Até</span>
                <div className={cn(
 "relative mt-1",
                  isFieldHighlighted('maxSalary') && "field-highlight field-pulse"
                )}>
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-lia-text-secondary">{CURRENCY_SYMBOL}</span>
                  <input
                    type="text"
                    value={salaryInfo.maxSalary}
                    onChange={(e) => onSalaryChange({ maxSalary: e.target.value })}
                    placeholder="18.000"
                    className="w-full pl-9 pr-3 py-1.5 border border-lia-border-subtle rounded-md text-xs focus:outline-none focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
                   
                    aria-label="Salário máximo base"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className={cn(
 "transition-colors duration-300",
            (isFieldHighlighted('minBonus') || isFieldHighlighted('maxBonus') || isFieldHighlighted('bonus')) && "field-highlight field-pulse"
          )}>
            <label className={`block ${textStyles.label} text-lia-text-secondary uppercase tracking-wide mb-2`}>
              <Star className="w-3.5 h-3.5 inline mr-1 text-lia-text-secondary" />
              Bônus Anual
            </label>
            <div className="flex gap-2 mb-1.5">
              <div className="flex-1">
                <span className="text-micro text-lia-text-secondary">De</span>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-lia-text-secondary">{CURRENCY_SYMBOL}</span>
                  <input
                    type="text"
                    value={salaryInfo.minBonus}
                    onChange={(e) => onSalaryChange({ minBonus: e.target.value })}
                    placeholder="10.000"
                    className="w-full pl-9 pr-3 py-1.5 border border-lia-border-subtle rounded-md text-xs focus:outline-none focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
                   
                    aria-label="Bônus mínimo anual"
                  />
                </div>
              </div>
              <div className="flex-1">
                <span className="text-micro text-lia-text-secondary">Até</span>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-lia-text-secondary">{CURRENCY_SYMBOL}</span>
                  <input
                    type="text"
                    value={salaryInfo.maxBonus}
                    onChange={(e) => onSalaryChange({ maxBonus: e.target.value })}
                    placeholder="20.000"
                    className="w-full pl-9 pr-3 py-1.5 border border-lia-border-subtle rounded-md text-xs focus:outline-none focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
                   
                    aria-label="Bônus máximo anual"
                  />
                </div>
              </div>
            </div>
            <input
              type="text"
              value={salaryInfo.bonusCriteria}
              onChange={(e) => onSalaryChange({ bonusCriteria: e.target.value })}
              placeholder="Critérios: Desempenho individual + metas da empresa"
              className="w-full px-3 py-1.5 border border-lia-border-subtle rounded-md text-xs focus:outline-none focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
             
            />
          </div>

          <div className={cn(
 "transition-colors duration-300",
            (isFieldHighlighted('benefit') || isFieldHighlighted('benefits') || isFieldHighlighted('beneficios')) && "field-highlight field-pulse"
          )}>
            <label className={`block ${textStyles.label} text-lia-text-secondary uppercase tracking-wide mb-2`}>
              <CheckCircle2 className="w-3.5 h-3.5 inline mr-1 text-lia-text-secondary" />
              Benefícios
              {companyConfig?.benefits && companyConfig.benefits.length > 0 && (
                <Settings className="w-3 h-3 inline ml-1.5 text-lia-text-secondary" />
              )}
            </label>
            <div className="space-y-3">
              {Object.entries(groupedBenefits).map(([categoryId, categoryBenefits]) => {
                const meta = BENEFIT_CATEGORY_META[categoryId as BenefitCategory]
                const CategoryIcon = CATEGORY_ICONS[categoryId as BenefitCategory] || HomeIcon
                if (!meta) return null

                return (
                  <div key={categoryId}>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <CategoryIcon className="w-3 h-3 text-lia-text-secondary" />
                      <span className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wide">
                        {meta.name}
                      </span>
                      <span className="text-micro text-lia-text-secondary">({categoryBenefits.length})</span>
                    </div>
                    <div className="grid grid-cols-2 gap-1.5">
                      {categoryBenefits.map((benefit) => {
                        const valueDisplay = formatBenefitDisplay(benefit)
                        return (
                          <button
                            key={benefit.id || benefit.name}
                            onClick={() => handleBenefitToggle(benefit.id || benefit.name)}
                            className={cn(
 "flex items-center gap-1.5 p-2 rounded-md text-left transition-colors",
                              benefit.enabled
                                ? "bg-lia-bg-tertiary border border-lia-btn-primary-bg"
                                : "bg-lia-bg-secondary border border-transparent hover:border-lia-border-subtle"
                            )}
                            aria-label={benefit.enabled ? `Remover benefício: ${benefit.name}` : `Adicionar benefício: ${benefit.name}`}
                          >
                            <div className={cn(
 "w-3.5 h-3.5 rounded-md flex items-center justify-center flex-shrink-0",
                              benefit.enabled ? "bg-lia-btn-primary-bg" : "border border-lia-border-subtle"
                            )}>
                              {benefit.enabled && <Check className="w-2.5 h-2.5 text-white" />}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1">
                                <span className="text-micro font-medium text-lia-text-primary block truncate">
                                  {benefit.name}
                                </span>
                                {benefit.is_highlighted && (
                                  <Heart className="w-2.5 h-2.5 text-wedo-magenta fill-pink-500 flex-shrink-0" />
                                )}
                                {benefit.is_mandatory && (
                                  <span className="text-micro px-1 py-0 rounded-md bg-lia-interactive-active text-lia-text-secondary flex-shrink-0">obrig.</span>
                                )}
                              </div>
                              {valueDisplay && (
                                <span className={`${textStyles.description} text-lia-text-secondary`}>{valueDisplay}</span>
                              )}
                              {benefit.provider && (
                                <span className="text-micro text-lia-text-secondary block truncate">{benefit.provider}</span>
                              )}
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
            <button
              onClick={onShowAddBenefitModal}
              className="w-full mt-1.5 py-1.5 border border-dashed border-lia-border-subtle rounded-md text-xs text-lia-text-secondary hover:border-lia-btn-primary-bg hover:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
              aria-label="Adicionar benefício para a vaga"
            >
              <Plus className="w-3.5 h-3.5" /> Adicionar benefício
            </button>
          </div>

          <div className="p-2 bg-lia-bg-secondary rounded-md border border-lia-border-default">
            <div className="flex items-center justify-between text-xs">
              <span className="lia-text-secondary">Benefícios selecionados:</span>
              <span className="font-semibold text-lia-text-primary">{salaryInfo.benefits.filter(b => b.enabled).length}</span>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
