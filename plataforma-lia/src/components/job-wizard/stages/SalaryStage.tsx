'use client'

import React, { useState } from 'react'
import { 
  DollarSign, Star, CheckCircle2, Plus, Check, Settings, TrendingUp, 
  Brain, Loader2,
  Stethoscope, Car, GraduationCap, Wallet, Home, Baby, Shield as ShieldIcon,
  Utensils, Clock, Heart
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWizardContext } from '../WizardContext'
import { useCompanyBenefits } from '@/hooks/useCompanyBenefits'
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
        <div className="p-3 bg-gradient-to-r from-gray-50 dark:from-gray-900 to-[#22C55E]/5 rounded-md border border-gray-300 dark:border-gray-600">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            <span className="text-xs font-medium text-gray-800" style={{ fontFamily: '"Open Sans", sans-serif' }}>
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
            <div className="mb-2 p-2 bg-white/50 rounded-md">
              <div className="flex items-center justify-between mb-1">
                <span className="text-micro text-gray-500">
                  Dados internos ({salaryBenchmark.internal.sample_size} vagas)
                </span>
                {salaryBenchmark.internal.trend && salaryBenchmark.internal.trend !== 'stable' && (
                  <span className={`text-micro ${salaryBenchmark.internal.trend === 'increasing' ? 'text-status-success' : 'text-status-error'}`}>
                    {salaryBenchmark.internal.trend === 'increasing' ? '↑ Em alta' : '↓ Em queda'}
                  </span>
                )}
              </div>
              <div className="text-xs font-semibold text-gray-800">
                R$ {salaryBenchmark.internal.min.toLocaleString()} - R$ {salaryBenchmark.internal.max.toLocaleString()}
              </div>
            </div>
          )}
          
          {/* Market Data */}
          {salaryBenchmark.market && salaryBenchmark.market.min > 0 && (
            <div className="mb-2 p-2 bg-white/50 rounded-md">
              <div className="flex items-center justify-between mb-1">
                <span className="text-micro text-gray-500">
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
              <div className="text-xs font-semibold text-gray-800">
                R$ {salaryBenchmark.market.min.toLocaleString()} - R$ {salaryBenchmark.market.max.toLocaleString()}
              </div>
            </div>
          )}
          
          {/* Apply Recommendation Button */}
          {salaryBenchmark.combined && (
            <button
              onClick={applySuggestion}
              className="w-full py-1.5 mt-1 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-micro font-medium rounded-md transition-colors flex items-center justify-center gap-1"
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
      
      {/* Loading Benchmark */}
      {isLoadingBenchmark && (
        <div className="p-3 bg-gray-50 rounded-md border border-gray-200 flex items-center gap-2">
          <Loader2 className="w-4 h-4 text-gray-600 dark:text-gray-400 animate-spin" />
          <span className="text-xs text-gray-500">Buscando benchmark de mercado...</span>
        </div>
      )}
      
      {/* Salary Range */}
      <div>
        <label className="block text-micro font-semibold text-gray-500 uppercase tracking-wide mb-2">
          <DollarSign className="w-3.5 h-3.5 inline mr-1 text-gray-600 dark:text-gray-400" />
          Salário Base (CLT)
        </label>
        <div className="flex gap-2">
          <div className="flex-1">
            <span className="text-micro text-gray-400">De</span>
            <div className="relative mt-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">R$</span>
              <input
                type="text"
                value={salaryInfo.minSalary}
                onChange={(e) => setSalaryInfo(prev => ({ ...prev, minSalary: e.target.value }))}
                placeholder="12.000"
                className="w-full pl-9 pr-3 py-1.5 border border-gray-200 rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors"
                style={{ fontFamily: '"Open Sans", sans-serif' }}
              />
            </div>
          </div>
          <div className="flex-1">
            <span className="text-micro text-gray-400">Até</span>
            <div className="relative mt-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-gray-400">R$</span>
              <input
                type="text"
                value={salaryInfo.maxSalary}
                onChange={(e) => setSalaryInfo(prev => ({ ...prev, maxSalary: e.target.value }))}
                placeholder="18.000"
                className="w-full pl-9 pr-3 py-1.5 border border-gray-200 rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors"
                style={{ fontFamily: '"Open Sans", sans-serif' }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Bonus */}
      <div>
        <label className="block text-micro font-semibold text-gray-500 uppercase tracking-wide mb-2">
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
                onChange={(e) => setSalaryInfo(prev => ({ ...prev, minBonus: e.target.value }))}
                placeholder="10.000"
                className="w-full pl-9 pr-3 py-1.5 border border-gray-200 rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors"
                style={{ fontFamily: '"Open Sans", sans-serif' }}
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
                onChange={(e) => setSalaryInfo(prev => ({ ...prev, maxBonus: e.target.value }))}
                placeholder="20.000"
                className="w-full pl-9 pr-3 py-1.5 border border-gray-200 rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors"
                style={{ fontFamily: '"Open Sans", sans-serif' }}
              />
            </div>
          </div>
        </div>
        <input
          type="text"
          value={salaryInfo.bonusCriteria}
          onChange={(e) => setSalaryInfo(prev => ({ ...prev, bonusCriteria: e.target.value }))}
          placeholder="Critérios: Desempenho individual + metas da empresa"
          className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-xs focus:outline-none focus:border-gray-400 transition-colors"
          style={{ fontFamily: '"Open Sans", sans-serif' }}
        />
      </div>

      {/* Benefits */}
      <div>
        <label className="block text-micro font-semibold text-gray-500 uppercase tracking-wide mb-2">
          <CheckCircle2 className="w-3.5 h-3.5 inline mr-1 text-gray-600 dark:text-gray-400" />
          Benefícios
          {companyConfig?.benefits && companyConfig.benefits.length > 0 && (
            <Settings className="w-3 h-3 inline ml-1.5 text-gray-600 dark:text-gray-400" />
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
                        onClick={() => toggleBenefit(benefit.id || benefit.name)}
                        className={cn(
                          "flex items-center gap-1.5 p-2 rounded-md text-left transition-all",
                          benefit.enabled 
                            ? "bg-gray-100 dark:bg-gray-800 border border-gray-900 dark:border-gray-50" 
                            : "bg-gray-50 border border-transparent hover:border-gray-200"
                        )}
                      >
                        <div className={cn(
                          "w-3.5 h-3.5 rounded flex items-center justify-center flex-shrink-0",
                          benefit.enabled ? "bg-gray-900 dark:bg-gray-50" : "border border-gray-200"
                        )}>
                          {benefit.enabled && <Check className="w-2.5 h-2.5 text-white dark:text-gray-900" />}
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
                            <span className="text-micro text-gray-400">{valueDisplay}</span>
                          )}
                          {benefit.provider && (
                            <span className="text-micro text-gray-300 block truncate">{benefit.provider}</span>
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
          className="w-full mt-1.5 py-1.5 border border-dashed border-gray-200 rounded-md text-xs text-gray-600 dark:text-gray-400 hover:border-gray-900 dark:hover:border-gray-50 hover:bg-gray-50 dark:bg-gray-800/50 transition-all flex items-center justify-center gap-2"
        >
          <Plus className="w-3.5 h-3.5" /> Adicionar benefício
        </button>
        
        {/* Add Benefit Modal */}
        {showAddBenefitModal && (
          <div className="mt-2 p-3 bg-gray-50 rounded-md border border-gray-200 space-y-2">
            <input
              type="text"
              value={newBenefitName}
              onChange={(e) => setNewBenefitName(e.target.value)}
              placeholder="Nome do benefício..."
              className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-xs"
              autoFocus
            />
            <div className="flex gap-2">
              <select
                value={newBenefitCategory}
                onChange={(e) => setNewBenefitCategory(e.target.value as BenefitCategory)}
                className="flex-1 px-3 py-1.5 border border-gray-200 rounded-md text-xs bg-white"
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
              placeholder="Valor (opcional, ex: R$ 500/mês)..."
              className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-xs"
            />
            <input
              type="text"
              value={newBenefitProvider}
              onChange={(e) => setNewBenefitProvider(e.target.value)}
              placeholder="Fornecedor (opcional, ex: Unimed)..."
              className="w-full px-3 py-1.5 border border-gray-200 rounded-md text-xs"
            />
            <div className="flex gap-2">
              <button
                onClick={() => setShowAddBenefitModal(false)}
                className="flex-1 py-1.5 px-3 rounded-md border border-gray-200 text-xs text-gray-500"
              >
                Cancelar
              </button>
              <button
                onClick={addBenefit}
                disabled={!newBenefitName.trim()}
                className="flex-1 py-1.5 px-3 rounded-md bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900 text-xs disabled:opacity-50"
              >
                Adicionar
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="p-2 bg-gray-50 rounded-md border border-gray-300 dark:border-gray-600">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-500" style={{ fontFamily: '"Open Sans", sans-serif' }}>
            Benefícios selecionados:
          </span>
          <span className="font-semibold text-gray-900 dark:text-gray-50">{enabledBenefitsCount}</span>
        </div>
      </div>
    </div>
  )
}

export default SalaryStage
