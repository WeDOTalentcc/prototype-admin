'use client'

import React, { useState } from 'react'
import { ChevronLeft, ChevronRight, Check, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { WizardProvider, useWizardContext } from './WizardContext'
import { useWizardNavigation } from './hooks/useWizardNavigation'
import { useStageValidation } from './hooks/useStageValidation'
import { WIZARD_STAGES, WIZARD_PHASES } from './constants'
import type { WizardStage } from './types'

interface WizardContainerProps {
  onClose: () => void
  onMinimize?: () => void
  onJobCreated?: () => void
  companyId?: string
  inline?: boolean
}

function WizardContent({ onClose, onMinimize, onJobCreated, inline }: Omit<WizardContainerProps, 'companyId'>) {
  const {
    currentStage,
    goToNextStage,
    goToPreviousStage,
    currentStageIndex,
    canAdvance,
    currentStageConfig,
  } = useWizardNavigation()

  const { setCurrentStage } = useWizardContext()
  
  const validation = useStageValidation()
  
  const [isPanelOpen, setIsPanelOpen] = useState(true)
  const [panelWidth] = useState(42)
  
  const isFirstStage = currentStageIndex === 0
  const isLastStage = currentStageIndex === WIZARD_STAGES.length - 1
  const isReviewStage = currentStage === 'review-publish'
  const isCalibrationStage = currentStage === 'search-calibration'
  
  const getCurrentPhase = () => {
    for (const phase of WIZARD_PHASES) {
      if (phase.stages.includes(currentStage)) {
        return phase
      }
    }
    return WIZARD_PHASES[0]
  }
  
  const currentPhase = getCurrentPhase()

  const handleStageNavigate = (stage: WizardStage, index: number) => {
    if (index < currentStageIndex) {
      setCurrentStage(stage)
    }
  }
  
  const renderStageIndicator = (stage: WizardStage, index: number) => {
    const stageConfig = WIZARD_STAGES.find(s => s.id === stage)
    const isCurrent = stage === currentStage
    const isPast = index < currentStageIndex
    
    return (
      <div
        key={stage}
        className={cn(
 "flex items-center gap-1.5 px-2 py-1 rounded-md transition-colors",
          isCurrent && "bg-gray-100 dark:bg-lia-bg-secondary",
          isPast && "opacity-70 cursor-pointer hover:opacity-100",
          !isPast && !isCurrent && "cursor-default"
        )}
        onClick={() => handleStageNavigate(stage, index)}
      >
        <div className={cn(
 "w-4 h-4 rounded-full flex items-center justify-center text-micro font-semibold",
          isCurrent && "bg-gray-900 text-white",
          isPast && "bg-status-success text-white",
          !isCurrent && !isPast && "border border-lia-border-default lia-text-secondary"
        )}>
          {isPast ? <Check className="w-2.5 h-2.5" /> : index + 1}
        </div>
        <span className={cn(
 "text-micro font-medium",
          isCurrent && "text-gray-600 dark:text-lia-text-tertiary",
          isPast && "text-status-success",
          !isCurrent && !isPast && "lia-text-secondary"
        )}>
          {stageConfig?.title || stage}
        </span>
      </div>
    )
  }

  return (
    <div className={cn(
 "flex flex-col bg-gray-50 h-full",
      inline ? "rounded-md border border-lia-border-subtle" : "fixed inset-0 z-50"
    )}>
      {/* Header with phase navigation */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-lia-bg-primary border-b border-lia-border-subtle">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-100 dark:from-gray-800 to-wedo-cyan-dark flex items-center justify-center">
              <span className="text-white text-sm font-bold">L</span>
            </div>
            <span className="text-sm font-semibold lia-text-strong">
              LIA • Criação de Vaga
            </span>
          </div>
          <div className="h-4 w-px bg-gray-200" />
          <div className="flex items-center gap-1 bg-gray-100 rounded-md px-2 py-1">
            {WIZARD_PHASES.map((phase, phaseIndex) => (
              <React.Fragment key={phase.id}>
                <span className={cn(
 "text-micro font-medium px-2 py-0.5 rounded-full",
                  currentPhase.id === phase.id
                    ? "bg-gray-900 text-white"
                    : "lia-text-secondary"
                )}>
                  {phase.label}
                </span>
                {phaseIndex < WIZARD_PHASES.length - 1 && (
                  <ChevronRight className="w-3 h-3 lia-text-secondary" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {onMinimize && (
            <button
              onClick={onMinimize}
              className="p-1.5 lia-text-secondary hover:lia-text-base transition-colors"
              aria-label="Minimizar"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={onClose}
            className="p-1.5 lia-text-secondary hover:lia-text-base transition-colors"
            aria-label="Fechar"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Stage navigation bar */}
      <div className="flex items-center gap-1 px-4 py-2 bg-lia-bg-primary border-b border-lia-border-subtle overflow-x-auto">
        {WIZARD_STAGES.map((stage, index) => renderStageIndicator(stage.id, index))}
      </div>

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left side - Chat area (placeholder - will be passed as children or props) */}
        <div className="flex flex-col transition-colors duration-300 flex-1" style={{width: isPanelOpen ? `${100 - panelWidth}%` : '100%'}}>
          <div className="flex-1 overflow-y-auto p-4">
            {/* Stage content will be rendered here */}
            <div className="text-center lia-text-secondary py-8">
              <p className="text-sm">Stage: {currentStageConfig?.title}</p>
              <p className="text-xs lia-text-secondary mt-1">{currentStageConfig?.liaMessage?.slice(0, 100)}...</p>
            </div>
          </div>
        </div>

        {/* Right side - Panel area */}
        {isPanelOpen && (
          <div 
            className="border-l border-lia-border-subtle bg-lia-bg-primary flex flex-col"
            style={{width: `${panelWidth}%`}}
          >
            <div className="p-3 border-b border-lia-border-subtle">
              <h3 className="text-xs font-semibold lia-text-strong">
                {currentStageConfig?.panelTitle || 'Painel'}
              </h3>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {/* Panel content will be rendered here by each stage */}
            </div>
          </div>
        )}
      </div>

      {/* Footer with navigation buttons */}
      <div className="flex items-center justify-between px-4 py-3 bg-lia-bg-primary border-t border-lia-border-subtle">
        <button
          onClick={goToPreviousStage}
          disabled={isFirstStage}
          className={cn(
 "flex items-center gap-1.5 px-4 py-2 rounded-md text-xs font-medium transition-colors",
            isFirstStage
              ? "lia-text-secondary cursor-not-allowed"
              : "text-gray-600 dark:text-lia-text-tertiary hover:bg-gray-100 dark:bg-lia-bg-secondary"
          )}
         
        >
          <ChevronLeft className="w-4 h-4" />
          Voltar
        </button>

        <div className="flex items-center gap-2">
          {/* Validation warnings */}
          {validation.warnings.length > 0 && (
            <div className="flex items-center gap-1 text-status-warning">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span className="text-micro">{validation.warnings[0]}</span>
            </div>
          )}
          
          {/* Progress indicator */}
          <div className="flex items-center gap-1">
            <span className="text-micro lia-text-secondary">
              {currentStageIndex + 1} de {WIZARD_STAGES.length}
            </span>
            <div className="w-16 h-1 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gray-900 transition-[width,height] duration-300"
                style={{width: `${((currentStageIndex + 1) / WIZARD_STAGES.length) * 100}%`}}
              />
            </div>
          </div>
        </div>

        {isCalibrationStage ? (
          <button
            onClick={() => {
              // Handle calibration complete
              if (onJobCreated) onJobCreated()
              onClose()
            }}
            className="flex items-center gap-1.5 px-4 py-2 bg-status-success text-white rounded-md text-xs font-medium hover:bg-status-success transition-colors"
           
          >
            <Check className="w-4 h-4" />
            Finalizar
          </button>
        ) : isReviewStage ? (
          <button
            className="flex items-center gap-1.5 px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200 rounded-md text-xs font-medium transition-colors"
           
          >
            Publicar Vaga
            <ChevronRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={goToNextStage}
            disabled={!canAdvance && currentStage !== 'salary'}
            className={cn(
 "flex items-center gap-1.5 px-4 py-2 rounded-md text-xs font-medium transition-colors",
              canAdvance || currentStage === 'salary'
                ? "bg-gray-900 text-white hover:bg-gray-800 dark:hover:bg-gray-200"
                : "bg-gray-300 lia-text-secondary cursor-not-allowed"
            )}
           
          >
            Avançar
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}

export function WizardContainer({ companyId = 'default', ...props }: WizardContainerProps) {
  return (
    <WizardProvider companyId={companyId}>
      <WizardContent {...props} />
    </WizardProvider>
  )
}

export default WizardContainer
