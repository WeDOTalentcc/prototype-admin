import { useCallback } from 'react'
import { useWizardContext } from '../WizardContext'
import type { WizardStage } from '../types'
import { WIZARD_STAGES, AUTO_ADVANCE_CONFIDENCE_THRESHOLDS } from '../constants'

export function useWizardNavigation() {
  const {
    currentStage,
    setCurrentStage,
    currentStageIndex,
    canAdvance
  } = useWizardContext()
  
  const goToStage = useCallback((stage: WizardStage) => {
    setCurrentStage(stage)
  }, [setCurrentStage])
  
  const goToNextStage = useCallback(() => {
    const nextIndex = currentStageIndex + 1
    if (nextIndex < WIZARD_STAGES.length) {
      setCurrentStage(WIZARD_STAGES[nextIndex].id)
    }
  }, [currentStageIndex, setCurrentStage])
  
  const goToPreviousStage = useCallback(() => {
    const prevIndex = currentStageIndex - 1
    if (prevIndex >= 0) {
      setCurrentStage(WIZARD_STAGES[prevIndex].id)
    }
  }, [currentStageIndex, setCurrentStage])
  
  const isFirstStage = currentStageIndex === 0
  const isLastStage = currentStageIndex === WIZARD_STAGES.length - 1
  
  const currentStageConfig = WIZARD_STAGES[currentStageIndex]
  
  const shouldAutoAdvance = useCallback((confidence: number): boolean => {
    const threshold = AUTO_ADVANCE_CONFIDENCE_THRESHOLDS[currentStage]
    if (currentStage === 'review-publish' || currentStage === 'search-calibration') {
      return false
    }
    return confidence >= threshold
  }, [currentStage])
  
  const getStageProgress = useCallback(() => {
    return {
      current: currentStageIndex + 1,
      total: WIZARD_STAGES.length,
      percentage: ((currentStageIndex + 1) / WIZARD_STAGES.length) * 100
    }
  }, [currentStageIndex])
  
  return {
    currentStage,
    currentStageIndex,
    currentStageConfig,
    canAdvance,
    goToStage,
    goToNextStage,
    goToPreviousStage,
    isFirstStage,
    isLastStage,
    shouldAutoAdvance,
    getStageProgress
  }
}
