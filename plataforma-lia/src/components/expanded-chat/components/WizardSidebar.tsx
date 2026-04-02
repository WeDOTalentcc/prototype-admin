"use client"

import React from "react"
import { Check } from "lucide-react"
import { cn } from "@/lib/utils"
import { WIZARD_PHASES, WIZARD_STAGES, type WizardStage, type WizardPhase, type WizardPhaseConfig, type ExtendedWizardStageConfig } from "../config"

export interface WizardSidebarProps {
  currentStageIndex: number
  onStageClick?: (stageId: WizardStage, stageIndex: number) => void
  allowNavigateToCompleted?: boolean
  orientation?: 'horizontal' | 'vertical'
  compact?: boolean
  className?: string
}

export function WizardSidebar({
  currentStageIndex,
  onStageClick,
  allowNavigateToCompleted = true,
  orientation = 'horizontal',
  compact = false,
  className
}: WizardSidebarProps) {
  const handleStageClick = (stageId: WizardStage, stageIndex: number) => {
    if (!onStageClick) return
    if (stageIndex < currentStageIndex && allowNavigateToCompleted) {
      onStageClick(stageId, stageIndex)
    }
  }

  if (orientation === 'vertical') {
    return (
      <div className={cn("flex flex-col gap-4 p-4", className)}>
        {WIZARD_PHASES.map((phase) => {
          const phaseStages = phase.stages
          const firstStageIndex = WIZARD_STAGES.findIndex(s => s.id === phaseStages[0])
          const lastStageIndex = WIZARD_STAGES.findIndex(s => s.id === phaseStages[phaseStages.length - 1])
          const isPhaseActive = currentStageIndex >= firstStageIndex && currentStageIndex <= lastStageIndex
          const isPhaseCompleted = currentStageIndex > lastStageIndex

          return (
            <div key={phase.id} className="flex flex-col">
              <div className="flex items-center gap-2 mb-2">
                <div 
                  className={cn(
 "w-2 h-2 rounded-full transition-[width,height]",
                    isPhaseActive 
                      ? "bg-lia-btn-primary-bg" 
                      : isPhaseCompleted 
                        ? "bg-status-success" 
                        : "bg-lia-border-default"
                  )}
                />
                <span 
                  className={cn(
 "text-micro font-semibold uppercase tracking-wide",
                    isPhaseActive 
                      ? "text-lia-text-secondary" 
                      : isPhaseCompleted 
                        ? "lia-text-secondary" 
                        : "lia-text-secondary"
                  )}
                 
                >
                  {phase.label}
                </span>
                {isPhaseCompleted && (
                  <Check className="w-3 h-3 text-status-success" strokeWidth={3} />
                )}
              </div>
              
              <div className="flex flex-col gap-1 ml-4 border-l-2 border-lia-border-subtle pl-3">
                {phaseStages.map((stageId) => {
                  const stageIndex = WIZARD_STAGES.findIndex(s => s.id === stageId)
                  const stage = WIZARD_STAGES[stageIndex]
                  const isActive = stageIndex === currentStageIndex
                  const isCompleted = stageIndex < currentStageIndex
                  const isClickable = isCompleted && allowNavigateToCompleted && onStageClick

                  return (
                    <button
                      key={stageId}
                      onClick={() => handleStageClick(stageId, stageIndex)}
                      disabled={!isClickable}
                      className={cn(
 "flex items-center gap-2 py-1.5 px-2 rounded-md text-left transition-colors focus-visible:ring-2 focus-visible:ring-lia-border-default",
                        isActive && "bg-lia-bg-tertiary border border-lia-border-default",
                        isCompleted && isClickable && "hover:bg-lia-interactive-hover cursor-pointer",
                        !isClickable && !isActive && "cursor-default"
                      )}
                    >
                      <div 
                        className={cn(
 "w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 transition-[width,height]",
                          isActive 
                            ? "bg-lia-btn-primary-bg" 
                            : isCompleted 
                              ? "bg-status-success" 
                              : "border border-lia-border-default"
                        )}
                      >
                        {isCompleted && (
                          <Check className="w-2.5 h-2.5 text-white" strokeWidth={3} />
                        )}
                        {isActive && (
                          <div className="w-1.5 h-1.5 rounded-full bg-lia-bg-primary" />
                        )}
                      </div>
                      <span 
                        className={cn(
 "text-xs font-medium",
                          isActive 
                            ? "text-lia-text-secondary" 
                            : isCompleted 
                              ? "text-lia-text-secondary" 
                              : "lia-text-secondary"
                        )}
                       
                      >
                        {stage.title}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className={cn("flex items-stretch gap-1.5", className)}>
      {WIZARD_PHASES.map((phase) => {
        const phaseStages = phase.stages
        const firstStageIndex = WIZARD_STAGES.findIndex(s => s.id === phaseStages[0])
        const lastStageIndex = WIZARD_STAGES.findIndex(s => s.id === phaseStages[phaseStages.length - 1])
        const isPhaseActive = currentStageIndex >= firstStageIndex && currentStageIndex <= lastStageIndex
        const isPhaseCompleted = currentStageIndex > lastStageIndex
        
        const phaseFlexClass = phase.id === 'construction' 
          ? 'flex-[5]' 
          : phase.id === 'activation' 
            ? 'flex-[1]' 
            : 'flex-[2]'
        
        return (
          <div key={phase.id} className={`${phaseFlexClass} flex flex-col`}>
            <div className="flex items-center gap-1 mb-1">
              <span 
                className={cn(
 "text-micro font-semibold uppercase tracking-wide",
                  isPhaseActive 
                    ? "text-lia-text-secondary" 
                    : isPhaseCompleted 
                      ? "lia-text-secondary" 
                      : "lia-text-secondary"
                )}
               
              >
                {phase.label}
              </span>
              {isPhaseCompleted && (
                <Check className="w-2.5 h-2.5 text-status-success" strokeWidth={3} />
              )}
            </div>
            
            <div className="flex items-center gap-0.5">
              {phaseStages.map((stageId) => {
                const stageIndex = WIZARD_STAGES.findIndex(s => s.id === stageId)
                const stage = WIZARD_STAGES[stageIndex]
                const isActive = stageIndex === currentStageIndex
                const isCompleted = stageIndex < currentStageIndex
                const isClickable = isCompleted && allowNavigateToCompleted && onStageClick
                
                return (
                  <button
                    key={stageId}
                    onClick={() => handleStageClick(stageId, stageIndex)}
                    disabled={!isClickable}
                    className={cn(
 "flex-1 flex flex-col items-center transition-colors focus-visible:ring-2 focus-visible:ring-lia-border-default rounded-md",
                      isClickable && "hover:opacity-80 cursor-pointer",
                      !isClickable && "cursor-default"
                    )}
                  >
                    <div 
                      className={cn(
 "w-full h-1.5 rounded-full transition-[width,height]",
 isActive ? "bg-lia-btn-primary-bg" : isCompleted ? "bg-status-success" : "bg-lia-interactive-active"
                      )}
                    />
                    {!compact && (
                      <span 
                        className={cn(
 "text-micro mt-1 truncate max-w-full px-0.5 text-center leading-tight",
                          isActive 
                            ? "font-semibold text-lia-text-primary" 
                            : isCompleted 
                              ? "lia-text-secondary" 
                              : "lia-text-secondary"
                        )}
                       
                      >
                        {stage.title.length > 10 ? stage.title.split(' ')[0] : stage.title}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
