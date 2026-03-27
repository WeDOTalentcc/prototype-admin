'use client'

import React from 'react'
import { DollarSign, Star, CheckCircle2, Plus, Check, Brain, Loader2, TrendingUp, ChevronDown, Settings,
  Stethoscope, Car, GraduationCap, Wallet, Home as HomeIcon, Baby, Shield as ShieldIcon,
  Utensils, Heart
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { textStyles } from '@/lib/design-tokens'
import type { JobBenefit } from '@/types/benefits'
import { BENEFIT_CATEGORY_META, type BenefitCategory } from '@/types/benefits'
import type { SalaryInfo } from '@/components/job-wizard/types'

export type { SalaryInfo }

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
  benefits?: string[]
  [key: string]: any
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

function formatBenefitDisplay(benefit: { value_type?: string; value?: number; percentage_value?: number; value_details?: string }): string {
  if (benefit.value_type === 'monetary' && benefit.value) {
    return `R$ ${benefit.value.toLocaleString('pt-BR')}`
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
        <div className="p-3 bg-gradient-to-r from-green-500/10 to-gray-100 dark:to-gray-800 rounded-md border border-green-500/30">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0">
              <Brain className="w-3.5 h-3.5 text-green-500" />
            </div>
            <div className="flex-1">
              <span className="text-xs font-medium text-green-800" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                Remuneração pré-configurada
              </span>
              <p className="text-micro text-gray-500 mt-0.5">
                Valores baseados nas políticas salariais da empresa.
                <button
                  onClick={handleToggleExpand}
                  className="ml-1 text-gray-600 dark:text-gray-400 hover:underline font-medium"
                >
                  {isExpanded ? 'Ocultar' : 'Editar manualmente'}
                </button>
              </p>
            </div>
            <button
              onClick={handleToggleExpand}
              className="p-1.5 hover:bg-white/50 rounded-md transition-colors"
              aria-label={isExpanded ? 'Recolher painel de salário' : 'Expandir painel de salário'}
            >
              <ChevronDown className={cn(
                "w-4 h-4 text-gray-500 transition-transform",
                isExpanded && "rotate-180"
              )} />
            </button>
          </div>
        </div>
      )}

      {(isFieldRequired || isExpanded) && (
        <>
          {salaryBenchmark && (salaryBenchmark.market || salaryBenchmark.internal) && (
            <div className="p-3 bg-gradient-to-r from-gray-50 dark:from-gray-900 to-green-500/5 rounded-md border border-gray-300 dark:border-gray-600">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <span className="text-xs font-medium text-gray-800" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                  Benchmark de Mercado
                </span>
                {salaryBenchmark.market?.learning_adjusted && (
                  <span className="px-1.5 py-0.5 bg-green-500/10 text-green-800 text-micro font-medium rounded-full">
                    Personalizado
                  </span>
                )}
              </div>

              {salaryBenchmark.internal && salaryBenchmark.internal.sample_size > 0 && (
                <div className="mb-2 p-2 bg-white/50 rounded-md">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-micro text-gray-500">Dados internos ({salaryBenchmark.internal.sample_size} vagas)</span>
                    {salaryBenchmark.internal.trend && salaryBenchmark.internal.trend !== 'stable' && (
                      <span className={`text-micro ${salaryBenchmark.internal.trend === 'increasing' ? 'text-green-500' : 'text-red-500'}`}>
                        {salaryBenchmark.internal.trend === 'increasing' ? '↑ Em alta' : '↓ Em queda'}
                      </span>
                    )}
                  </div>
                  <div className="text-xs font-semibold text-gray-800">
                    R$ {salaryBenchmark.internal.min.toLocaleString()} - R$ {salaryBenchmark.internal.max.toLocaleString()}
                  </div>
                </div>
              )}

              {salaryBenchmark.market && salaryBenchmark.market.min > 0 && (
                <div className="mb-2 p-2 bg-white/50 rounded-md">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-micro text-gray-500">
                      Dados de mercado ({salaryBenchmark.market.sources?.slice(0, 2).join(', ')})
                    </span>
                    <span className={`text-micro px-1.5 py-0.5 rounded-full ${
                      salaryBenchmark.market.confidence === 'high' ? 'bg-green-500/10 text-green-800' :
                      salaryBenchmark.market.confidence === 'medium' ? 'bg-amber-500/10 text-amber-800' :
                      'bg-red-500/10 text-red-800'
                    }`}>
                      {salaryBenchmark.market.confidence === 'high' ? 'Alta confiança' :
                       salaryBenchmark.market.confidence === 'medium' ? 'Média confiança' : 'Baixa confiança'}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-gray-800">
                    R$ {salaryBenchmark.market.min.toLocaleString()} - R$ {salaryBenchmark.market.max.toLocaleString()}
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
                  className="w-full py-1.5 mt-1 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-micro font-medium rounded-md transition-colors flex items-center justify-center gap-1 focus-visible:ring-2 focus-visible:ring-gray-400"
                >
                  <Brain className="w-3 h-3 text-wedo-cyan" />
                  Aplicar sugestão: R$ {salaryBenchmark.combined.min.toLocaleString()} - R$ {salaryBenchmark.combined.max.toLocaleString()}
                </button>
              )}

              <p className="text-micro text-gray-400 mt-2 italic">
                Estimativa baseada em dados públicos. Valores podem variar.
              </p>
            </div>
          )}

          {isLoadingBenchmark && (
            <div className="p-3 bg-gray-50 rounded-md border border-gray-200 flex items-center gap-2">
              <Loader2 className="w-4 h-4 text-gray-600 dark:text-gray-400 animate-spin" />
              <span className="text-xs text-gray-500">Buscando benchmark de mercado...</span>
            </div>
          )}

          <div className={cn(
            "transition-all duration-300",
            (isFieldHighlighted('minSalary') || isFieldHighlighted('maxSalary') || isFieldHighlighted('salary') || isFieldHighlighted('salario')) && "field-highlight field-pulse"
          )}>
            <label className={`block ${textStyles.label} text-gray-500 uppercase tracking-wide mb-2`}>
              <DollarSign className="w-3.5 h-3.5 inline mr-1 text-gray-600 dark:text-gray-400" />
              Salário Base (CLT)
            </label>
            <div className="flex gap-2">
              <div className="flex-1">
                <span className="text-micro text-gray-400">De</span>
                <div className={cn(
                  "relative mt-1",
                  isFieldHighlighted('minSalary') && "field-highlight field-pulse"
                )}>
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">R$</span>
                  <input
                    type="text"
                    value={salaryInfo.minSalary}
                    onChange={(e) => onSalaryChange({ minSalary: e.target.value })}
                    placeholder="12.000"
                    className="w-full pl-9 pr-3 py-1.5 border border-gray-200 rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors"
                    style={{ fontFamily: '"Open Sans", sans-serif' }}
                    aria-label="Salário mínimo base"
                  />
                </div>
              </div>
              <div className="flex-1">
                <span className="text-micro text-gray-400">Até</span>
                <div className={cn(
                  "relative mt-1",
                  isFieldHighlighted('maxSalary') && "field-highlight field-pulse"
                )}>
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">R$</span>
                  <input
                    type="text"
                    value={salaryInfo.maxSalary}
                    onChange={(e) => onSalaryChange({ maxSalary: e.target.value })}
                    placeholder="18.000"
                    className="w-full pl-9 pr-3 py-1.5 border border-gray-200 rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors"
                    style={{ fontFamily: '"Open Sans", sans-serif' }}
                    aria-label="Salário máximo base"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className={cn(
            "transition-all duration-300",
            (isFieldHighlighted('minBonus') || isFieldHighlighted('maxBonus') || isFieldHighlighted('bonus')) && "field-highlight field-pulse"
          )}>
            <label className={`block ${textStyles.label} text-gray-500 uppercase tracking-wide mb-2`}>
              <Star className="w-3.5 h-3.5 inline mr-1 text-gray-600 dark:text-gray-400" />
              Bônus Anual
            </label>
            <div className="flex gap-2 mb-1.5">
              <div className="flex-1">
                <span className="text-micro text-gray-400">De</span>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">R$</span>
                  <input
                    type="text"
                    value={salaryInfo.minBonus}
                    onChange={(e) => onSalaryChange({ minBonus: e.target.value })}
                    placeholder="10.000"
                    className="w-full pl-9 pr-3 py-1.5 border border-gray-200 rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors"
                    style={{ fontFamily: '"Open Sans", sans-serif' }}
                    aria-label="Bônus mínimo anual"
                  />
                </div>
              </div>
              <div className="flex-1">
                <span className="text-micro text-gray-400">Até</span>
                <div className="relative mt-1">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">R$</span>
                  <input
                    type="text"
                    value={salaryInfo.maxBonus}
                    onChange={(e) => onSalaryChange({ maxBonus: e.target.value })}
                    placeholder="20.000"
                    className="w-full pl-9 pr-3 py-1.5 border border-gray-200 rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors"
                    style={{ fontFamily: '"Open Sans", sans-serif' }}
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
              className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors"
              style={{ fontFamily: '"Open Sans", sans-serif' }}
            />
          </div>

          <div className={cn(
            "transition-all duration-300",
            (isFieldHighlighted('benefit') || isFieldHighlighted('benefits') || isFieldHighlighted('beneficios')) && "field-highlight field-pulse"
          )}>
            <label className={`block ${textStyles.label} text-gray-500 uppercase tracking-wide mb-2`}>
              <CheckCircle2 className="w-3.5 h-3.5 inline mr-1 text-gray-600 dark:text-gray-400" />
              Benefícios
              {companyConfig?.benefits && companyConfig.benefits.length > 0 && (
                <Settings className="w-3 h-3 inline ml-1.5 text-gray-600 dark:text-gray-400" />
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
                      <CategoryIcon className="w-3 h-3 text-gray-500" />
                      <span className="text-micro font-semibold text-gray-500 uppercase tracking-wide">
                        {meta.name}
                      </span>
                      <span className="text-micro text-gray-400">({categoryBenefits.length})</span>
                    </div>
                    <div className="grid grid-cols-2 gap-1.5">
                      {categoryBenefits.map((benefit) => {
                        const valueDisplay = formatBenefitDisplay(benefit)
                        return (
                          <button
                            key={benefit.id || benefit.name}
                            onClick={() => handleBenefitToggle(benefit.id || benefit.name)}
                            className={cn(
                              "flex items-center gap-1.5 p-2 rounded-md text-left transition-all",
                              benefit.enabled
                                ? "bg-gray-100 dark:bg-gray-800 border border-gray-900 dark:border-gray-50"
                                : "bg-gray-50 border border-transparent hover:border-gray-200"
                            )}
                            aria-label={benefit.enabled ? `Remover benefício: ${benefit.name}` : `Adicionar benefício: ${benefit.name}`}
                          >
                            <div className={cn(
                              "w-3.5 h-3.5 rounded flex items-center justify-center flex-shrink-0",
                              benefit.enabled ? "bg-gray-900 dark:bg-gray-50" : "border border-gray-200"
                            )}>
                              {benefit.enabled && <Check className="w-2.5 h-2.5 text-white" />}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1">
                                <span className="text-micro font-medium text-gray-800 block truncate" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                                  {benefit.name}
                                </span>
                                {benefit.is_highlighted && (
                                  <Heart className="w-2.5 h-2.5 text-pink-500 fill-pink-500 flex-shrink-0" />
                                )}
                                {benefit.is_mandatory && (
                                  <span className="text-micro px-1 py-0 rounded bg-gray-200 text-gray-600 flex-shrink-0">obrig.</span>
                                )}
                              </div>
                              {valueDisplay && (
                                <span className={`${textStyles.description} text-gray-400`}>{valueDisplay}</span>
                              )}
                              {benefit.provider && (
                                <span className="text-micro text-gray-400 block truncate">{benefit.provider}</span>
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
              className="w-full mt-1.5 py-1.5 border border-dashed border-gray-200 rounded-md text-xs text-gray-600 dark:text-gray-400 hover:border-gray-900 dark:hover:border-gray-50 hover:bg-gray-50 dark:bg-gray-800/50 transition-all flex items-center justify-center gap-2"
              aria-label="Adicionar benefício para a vaga"
            >
              <Plus className="w-3.5 h-3.5" /> Adicionar benefício
            </button>
          </div>

          <div className="p-2 bg-gray-50 rounded-md border border-gray-300 dark:border-gray-600">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500" style={{ fontFamily: '"Open Sans", sans-serif' }}>Benefícios selecionados:</span>
              <span className="font-semibold text-gray-900 dark:text-gray-50">{salaryInfo.benefits.filter(b => b.enabled).length}</span>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
