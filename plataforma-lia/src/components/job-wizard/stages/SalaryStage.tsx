'use client'


import { formatBRL, CURRENCY_SYMBOL } from "@/lib/pricing"
import React, { useState } from 'react'
import { 
  DollarSign, Star, CheckCircle2, Plus, Check, Settings, TrendingUp, 
  Brain, Loader2,
  Stethoscope, Car, GraduationCap, Wallet, Home, Baby, Shield as ShieldIcon,
  Utensils, Clock, Heart
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWizardContext } from '../WizardContext'
import { useCompanyBenefits } from '@/hooks/company/useCompanyBenefits'
import type { JobBenefit, BenefitCategory } from '@/types/benefits'
import { BENEFIT_CATEGORY_META } from '@/types/benefits'

const CATEGORY_ICONS: Record<BenefitCategory, any> = {
  health: Stethoscope,
  food: Utensils,
  transport: Car,
  education: GraduationCap,
  financial: Wallet,
  quality_life: Home,
  family: Baby,
  security: ShieldIcon,
}

function formatBenefitDisplay(benefit: JobBenefit): string {
  if (benefit.value_type === 'monetary' && benefit.value) {
    return formatBRL(benefit.value)
  }
  if (benefit.value_type === 'percentage' && benefit.percentage_value) {
    return `${benefit.percentage_value}%`
  }
  if (benefit.value_type === 'informative' && benefit.value_details) {
    return benefit.value_details
  }
  return ''
}

export function SalaryStage() {
  const {
    salaryInfo,
    setSalaryInfo,
    salaryBenchmark,
    companyConfig
  } = useWizardContext()

  const [showAddBenefitModal, setShowAddBenefitModal] = useState(false)
  const [newBenefitName, setNewBenefitName] = useState('')
  const [newBenefitValue, setNewBenefitValue] = useState('')
  const [newBenefitCategory, setNewBenefitCategory] = useState<BenefitCategory>('quality_life')
  const [newBenefitProvider, setNewBenefitProvider] = useState('')
  const [isLoadingBenchmark, setIsLoadingBenchmark] = useState(false)

  const groupedBenefits = React.useMemo(() => {
    const groups: Record<string, JobBenefit[]> = {}
    for (const b of salaryInfo.benefits) {
      const cat = b.category || 'quality_life'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(b)
    }
    return groups
  }, [salaryInfo.benefits])

  const toggleBenefit = (benefitIdOrName: string) => {
    setSalaryInfo(prev => ({
      ...prev,
      benefits: prev.benefits.map(b => 
        (b.id === benefitIdOrName || b.name === benefitIdOrName) ? { ...b, enabled: !b.enabled } : b
      )
    }))
  }

  const addBenefit = () => {
    if (!newBenefitName.trim()) return
    
    const newBenefit: JobBenefit = {
      id: `benefit-${Date.now()}`,
      name: newBenefitName.trim(),
      description: '',
      category: newBenefitCategory,
      value_type: newBenefitValue.trim() ? 'informative' : 'informative',
      value_details: newBenefitValue.trim() || undefined,
      seniority_levels: ['all'],
      waiting_period_days: 0,
      is_mandatory: false,
      is_active: true,
      is_highlighted: false,
      is_discount: false,
      provider: newBenefitProvider.trim() || undefined,
      enabled: true
    }
    
    setSalaryInfo(prev => ({
      ...prev,
      benefits: [...prev.benefits, newBenefit]
    }))
    
    setNewBenefitName('')
    setNewBenefitValue('')
    setNewBenefitCategory('quality_life')
    setNewBenefitProvider('')
    setShowAddBenefitModal(false)
  }

  const applySuggestion = () => {
    if (salaryBenchmark?.combined) {
      setSalaryInfo(prev => ({
        ...prev,
        minSalary: salaryBenchmark.combined!.min.toLocaleString(),
        maxSalary: salaryBenchmark.combined!.max.toLocaleString()
      }))
    }
  }

  const enabledBenefitsCount = salaryInfo.benefits.filter(b => b.enabled).length

  return (
    <div className="space-y-3">
      {/* Market Benchmark Card */}
      {salaryBenchmark && (salaryBenchmark.market || salaryBenchmark.internal) && (
        <div className="p-3 bg-gradient-to-r from-lia-bg-secondary dark:from-lia-bg-primary to-wedo-green-bright/5 rounded-xl border border-lia-border-default dark:border-lia-border-default">
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
          
          {/* Internal Data */}
          {salaryBenchmark.internal && salaryBenchmark.internal.sample_size > 0 && (
            <div className="mb-2 p-2 bg-lia-bg-primary/50 rounded-xl">
              <div className="flex items-center justify-between mb-1">
                <span className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                  Dados internos ({salaryBenchmark.internal.sample_size} vagas)
                </span>
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
          
          {/* Market Data */}
          {salaryBenchmark.market && salaryBenchmark.market.min > 0 && (
            <div className="mb-2 p-2 bg-lia-bg-primary/50 rounded-xl">
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
          
          {/* Apply Recommendation Button */}
          {salaryBenchmark.combined && (
            <button
              onClick={applySuggestion}
              className="w-full py-1.5 mt-1 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active text-micro font-medium rounded-md transition-colors motion-reduce:transition-none flex items-center justify-center gap-1"
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
      
      {/* Loading Benchmark */}
      {isLoadingBenchmark && (
        <div className="p-3 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle flex items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-4 h-4 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
          <span className="text-xs text-lia-text-secondary">Buscando benchmark de mercado...</span>
        </div>
      )}
      
      {/* Salary Range */}
      <div>
        <label className="block text-micro font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
          <DollarSign className="w-3.5 h-3.5 inline mr-1 text-lia-text-secondary" />
          Salário Base (CLT)
        </label>
        <div className="flex gap-2">
          <div className="flex-1">
            <span className="text-micro text-lia-text-secondary">De</span>
            <div className="relative mt-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-lia-text-secondary">{CURRENCY_SYMBOL}</span>
              <input
                type="text"
                value={salaryInfo.minSalary}
                onChange={(e) => setSalaryInfo(prev => ({ ...prev, minSalary: e.target.value }))}
                placeholder="12.000"
                className="w-full pl-9 pr-3 py-1.5 border border-lia-border-subtle rounded-xl text-xs focus:outline-none focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
               
              />
            </div>
          </div>
          <div className="flex-1">
            <span className="text-micro text-lia-text-secondary">Até</span>
            <div className="relative mt-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-lia-text-secondary">{CURRENCY_SYMBOL}</span>
              <input
                type="text"
                value={salaryInfo.maxSalary}
                onChange={(e) => setSalaryInfo(prev => ({ ...prev, maxSalary: e.target.value }))}
                placeholder="18.000"
                className="w-full pl-9 pr-3 py-1.5 border border-lia-border-subtle rounded-xl text-xs focus:outline-none focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
               
              />
            </div>
          </div>
        </div>
      </div>

      {/* Bonus */}
      <div>
        <label className="block text-micro font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
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
                onChange={(e) => setSalaryInfo(prev => ({ ...prev, minBonus: e.target.value }))}
                placeholder="10.000"
                className="w-full pl-9 pr-3 py-1.5 border border-lia-border-subtle rounded-xl text-xs focus:outline-none focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
               
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
                onChange={(e) => setSalaryInfo(prev => ({ ...prev, maxBonus: e.target.value }))}
                placeholder="20.000"
                className="w-full pl-9 pr-3 py-1.5 border border-lia-border-subtle rounded-xl text-xs focus:outline-none focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
               
              />
            </div>
          </div>
        </div>
        <input
          type="text"
          value={salaryInfo.bonusCriteria}
          onChange={(e) => setSalaryInfo(prev => ({ ...prev, bonusCriteria: e.target.value }))}
          placeholder="Critérios: Desempenho individual + metas da empresa"
          className="w-full px-3 py-1.5 border border-lia-border-subtle rounded-xl text-xs focus:outline-none focus:border-lia-border-medium transition-colors motion-reduce:transition-none"
         
        />
      </div>

      {/* Benefits */}
      <div>
        <label className="block text-micro font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
          <CheckCircle2 className="w-3.5 h-3.5 inline mr-1 text-lia-text-secondary" />
          Benefícios
          {companyConfig?.benefits && companyConfig.benefits.length > 0 && (
            <Settings className="w-3 h-3 inline ml-1.5 text-lia-text-secondary" />
          )}
        </label>
        <div className="space-y-3">
          {Object.entries(groupedBenefits).map(([categoryId, categoryBenefits]) => {
            const meta = BENEFIT_CATEGORY_META[categoryId as BenefitCategory]
            const CategoryIcon = CATEGORY_ICONS[categoryId as BenefitCategory] || Home
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
                        onClick={() => toggleBenefit(benefit.id || benefit.name)}
                        className={cn(
 "flex items-center gap-1.5 p-2 rounded-md text-left transition-colors",
                          benefit.enabled 
                            ? "bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-btn-primary-bg" 
                            : "bg-lia-bg-secondary border border-transparent hover:border-lia-border-subtle"
                        )}
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
                            <span className="text-micro text-lia-text-secondary">{valueDisplay}</span>
                          )}
                          {benefit.provider && (
                            <span className="text-micro text-lia-text-tertiary block truncate">{benefit.provider}</span>
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
        
        {/* Add Benefit Button */}
        <button 
          onClick={() => setShowAddBenefitModal(true)}
          className="w-full mt-1.5 py-1.5 border border-dashed border-lia-border-subtle rounded-xl text-xs text-lia-text-secondary hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
        >
          <Plus className="w-3.5 h-3.5" /> Adicionar benefício
        </button>
        
        {/* Add Benefit Modal */}
        {showAddBenefitModal && (
          <div className="mt-2 p-3 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle space-y-2">
            <input
              type="text"
              value={newBenefitName}
              onChange={(e) => setNewBenefitName(e.target.value)}
              placeholder="Nome do benefício..."
              className="w-full px-3 py-1.5 border border-lia-border-subtle rounded-xl text-xs"
              autoFocus
            />
            <div className="flex gap-2">
              <select
                value={newBenefitCategory}
                onChange={(e) => setNewBenefitCategory(e.target.value as BenefitCategory)}
                className="flex-1 px-3 py-1.5 border border-lia-border-subtle rounded-xl text-xs bg-lia-bg-primary"
              >
                {Object.entries(BENEFIT_CATEGORY_META).map(([key, meta]) => (
                  <option key={key} value={key}>{meta.name}</option>
                ))}
              </select>
            </div>
            <input
              type="text"
              value={newBenefitValue}
              onChange={(e) => setNewBenefitValue(e.target.value)}
              placeholder={`Valor (opcional, ex: ${CURRENCY_SYMBOL} 500/mês)...`}
              className="w-full px-3 py-1.5 border border-lia-border-subtle rounded-xl text-xs"
            />
            <input
              type="text"
              value={newBenefitProvider}
              onChange={(e) => setNewBenefitProvider(e.target.value)}
              placeholder="Fornecedor (opcional, ex: Unimed)..."
              className="w-full px-3 py-1.5 border border-lia-border-subtle rounded-xl text-xs"
            />
            <div className="flex gap-2">
              <button
                onClick={() => setShowAddBenefitModal(false)}
                className="flex-1 py-1.5 px-3 rounded-xl border border-lia-border-subtle text-xs text-lia-text-secondary"
              >
                Cancelar
              </button>
              <button
                onClick={addBenefit}
                disabled={!newBenefitName.trim()}
                className="flex-1 py-1.5 px-3 rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs disabled:opacity-50"
              >
                Adicionar
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="p-2 bg-lia-bg-secondary rounded-xl border border-lia-border-default dark:border-lia-border-default">
        <div className="flex items-center justify-between text-xs">
          <span className="lia-text-secondary">
            Benefícios selecionados:
          </span>
          <span className="font-semibold text-lia-text-primary">{enabledBenefitsCount}</span>
        </div>
      </div>
    </div>
  )
}

export default SalaryStage
