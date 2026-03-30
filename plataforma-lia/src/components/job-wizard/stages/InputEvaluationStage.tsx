'use client'

import React from 'react'
import { Check, Settings, Brain } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWizardContext } from '../WizardContext'
import { CompensationAnalysisPanel } from '@/components/job-creation/compensation-analysis-panel'

interface DetectedCriteriaItem {
  key: string
  label: string
  value: string | string[] | boolean | null
}

export function InputEvaluationStage() {
  const {
    detectedCriteria,
    companyConfig,
    salaryInfo,
    setSalaryInfo,
    setCurrentStage
  } = useWizardContext()
  
  const [showCompensationPanel, setShowCompensationPanel] = React.useState(false)
  const [compensationAnalysis, setCompensationAnalysis] = React.useState<any>(null)
  const [isEvaluating, setIsEvaluating] = React.useState(false)
  
  const configLoaded = companyConfig !== null
  const hasConfigData = companyConfig && (
    companyConfig.workModel || 
    companyConfig.employmentTypes?.length || 
    companyConfig.benefits?.length
  )
  
  const criteriaItems: DetectedCriteriaItem[] = [
    { key: 'cargo', label: 'Cargo e Senioridade', value: detectedCriteria.cargo },
    { key: 'gestor', label: 'Gestor/Área', value: detectedCriteria.gestorArea },
    { key: 'responsabilidades', label: 'Responsabilidades', value: detectedCriteria.responsabilidades },
    { key: 'competenciasTecnicas', label: 'Competências Técnicas (min. 3)', value: detectedCriteria.competenciasTecnicas },
    { key: 'competenciasComportamentais', label: 'Competências Comportamentais (min. 3)', value: detectedCriteria.competenciasComportamentais },
    { key: 'senioridade', label: 'Senioridade e Idiomas', value: detectedCriteria.senioridadeIdiomas },
    { key: 'salario', label: 'Faixa Salarial', value: detectedCriteria.salario },
  ]
  
  const detectedCriteriaItems = [
    ...criteriaItems,
    { key: 'afirmativa', label: 'Vaga Afirmativa', value: detectedCriteria.isAffirmative }
  ]
  
  const getCriteriaStatus = (value: string | string[] | boolean | null): boolean => {
    if (value === null || value === undefined) return false
    if (typeof value === 'boolean') return value
    if (Array.isArray(value)) return value.length > 0
    return value.length > 0
  }
  
  const detectedCount = criteriaItems.filter(item => getCriteriaStatus(item.value)).length
  const totalCount = criteriaItems.length

  return (
    <>
      {/* Banner when using company config */}
      {configLoaded && hasConfigData && (
        <div className="mb-3 px-3 py-2 bg-gray-100 dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-default rounded-md flex items-center gap-2">
          <Settings className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
          <span className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
            Usando dados das Configurações da sua empresa
          </span>
        </div>
      )}
      
      {/* Seção: Critérios Detectados */}
      <div className="mb-4">
        <h4 className="text-micro font-semibold lia-text-secondary uppercase tracking-wider mb-2 px-1">
          Critérios Detectados
        </h4>
        <div className="space-y-2">
          {detectedCriteriaItems.map((item) => {
            const isDetected = getCriteriaStatus(item.value)
            const displayValue = Array.isArray(item.value) 
              ? item.value.join(', ')
              : typeof item.value === 'boolean' 
                ? (item.value ? 'Sim' : 'Não')
                : item.value

            return (
              <div
                key={item.key}
                className={cn(
 "flex items-center gap-2.5 py-2 px-3 rounded-md transition-colors duration-300",
                  isDetected 
                    ? "bg-gray-50" 
                    : "bg-lia-bg-primary"
                )}
                style={{boxShadow: isDetected ? 'var(--status-success-shadow)' : '0 1px 2px var(--overlay-04)'}}
              >
                <div 
                  className={cn(
 "w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 transition-[width,height] duration-300",
                    isDetected 
                      ? "bg-status-success" 
                      : "border border-lia-border-default"
                  )}
                >
                  {isDetected && (
                    <Check className="w-2.5 h-2.5 text-white" strokeWidth={3} />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p 
                    className="text-xs font-medium lia-text-strong transition-colors duration-300"
                   
                  >
                    {item.label}
                  </p>
                  {isDetected && displayValue && (
                    <p className="text-micro mt-0.5 truncate text-lia-text-secondary dark:text-lia-text-tertiary font-medium">
                      {displayValue}
                    </p>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Progress Summary */}
      <div className="mt-3 p-2.5 rounded-md bg-lia-bg-primary">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-micro lia-text-base">
            Detectando critérios...
          </span>
          <span className="text-micro font-semibold text-lia-text-primary">
            {detectedCount} / {totalCount}
          </span>
        </div>
        <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full rounded-full transition-[width,height] duration-500 bg-gray-900"
            style={{width: `${(detectedCount / totalCount) * 100}%`}}
          />
        </div>
      </div>

      {/* Compensation Analysis Panel */}
      {(showCompensationPanel || isEvaluating) && (
        <div className="mt-4">
          <CompensationAnalysisPanel
            analysis={compensationAnalysis}
            isLoading={isEvaluating}
            onApplySuggestions={(suggestions) => {
              if (suggestions.salary) {
                setSalaryInfo(prev => ({
                  ...prev,
                  minSalary: suggestions.salary?.min?.toString() || prev.minSalary,
                  maxSalary: suggestions.salary?.max?.toString() || prev.maxSalary,
                }))
              }
              setShowCompensationPanel(false)
              setCompensationAnalysis(null)
            }}
            onDismiss={() => {
              setShowCompensationPanel(false)
              setCompensationAnalysis(null)
            }}
            onAdjustManually={() => {
              setCurrentStage('salary')
              setShowCompensationPanel(false)
            }}
          />
        </div>
      )}
    </>
  )
}

export default InputEvaluationStage
