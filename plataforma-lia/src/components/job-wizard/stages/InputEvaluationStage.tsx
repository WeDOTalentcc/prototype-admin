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
        <div className="mb-3 px-3 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md flex items-center gap-2">
          <Settings className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          <span className="text-xs text-gray-600 dark:text-gray-400">
            Usando dados das Configurações da sua empresa
          </span>
        </div>
      )}
      
      {/* Seção: Critérios Detectados */}
      <div className="mb-4">
        <h4 className="text-micro font-semibold text-gray-500 uppercase tracking-wider mb-2 px-1">
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
                  "flex items-center gap-2.5 py-2 px-3 rounded-md transition-all duration-300",
                  isDetected 
                    ? "bg-gray-50" 
                    : "bg-white"
                )}
                style={{ 
                  boxShadow: isDetected ? '0 1px 3px rgb(34 197 94 / 0.12)' : '0 1px 2px rgb(0 0 0 / 0.04)'
                }}
              >
                <div 
                  className={cn(
                    "w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300",
                    isDetected 
                      ? "bg-status-success" 
                      : "border border-gray-300"
                  )}
                >
                  {isDetected && (
                    <Check className="w-2.5 h-2.5 text-white" strokeWidth={3} />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p 
                    className="text-xs font-medium text-gray-800 transition-colors duration-300"
                   
                  >
                    {item.label}
                  </p>
                  {isDetected && displayValue && (
                    <p className="text-micro mt-0.5 truncate text-gray-600 dark:text-gray-400 font-medium">
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
      <div className="mt-3 p-2.5 rounded-md bg-white">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-micro text-gray-600">
            Detectando critérios...
          </span>
          <span className="text-micro font-semibold text-gray-900 dark:text-gray-50">
            {detectedCount} / {totalCount}
          </span>
        </div>
        <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full rounded-full transition-all duration-500 bg-gray-900 dark:bg-gray-50"
            style={{ 
              width: `${(detectedCount / totalCount) * 100}%`
            }}
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
