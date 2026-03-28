'use client'

import { useCallback, useMemo } from 'react'
import {
  type WizardStage,
  WIZARD_STAGES,
  WIZARD_PHASES,
  FRONTEND_TO_BACKEND_STAGE,
  getBackendStageNumber,
  getMissingCriticalFields,
  generateMissingFieldsMessage,
} from '../config'
import { getStageLabel } from '../utils'
import type { DetectedCriteria, BasicInfoFields, TechnicalSkill, BehavioralCompetency, SalaryInfo, WSIQuestion } from '../ExpandedChatContext'

export interface StageValidationResult {
  isValid: boolean
  missingRequired: string[]
  missingRecommended: string[]
  validationMessage: string | null
}

export interface ChatNavigationResult {
  success: boolean
  targetStage: WizardStage | null
  message: string
  validationIssues?: string[]
}

export interface UseWizardNavigationOptions {
  currentStage: WizardStage
  detectedCriteria: DetectedCriteria
  basicInfoFields: BasicInfoFields
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]
  salaryInfo: SalaryInfo
  wsiQuestions: WSIQuestion[]
  onStageChange?: (stage: WizardStage) => void
}

export interface UseWizardNavigationReturn {
  currentStageIndex: number
  currentStageConfig: (typeof WIZARD_STAGES)[number] | undefined
  currentPhase: (typeof WIZARD_PHASES)[number] | undefined
  canAdvance: boolean
  canGoBack: boolean
  backendStageNumber: number
  validateCurrentStage: () => StageValidationResult
  getStageValidation: (stageId: WizardStage) => StageValidationResult
  isStageComplete: (stageId: WizardStage) => boolean
  isStageAccessible: (stageId: WizardStage) => boolean
  getNextStage: () => WizardStage | null
  getPreviousStage: () => WizardStage | null
  getStageProgress: () => { current: number; total: number; percentage: number }
  getPhaseProgress: () => { currentPhase: number; totalPhases: number; stagesInPhase: number; completedInPhase: number }
  handleChatNavigation: (targetStage: WizardStage) => ChatNavigationResult
  canNavigateToStage: (targetStage: WizardStage) => { canNavigate: boolean; reason?: string }
}

export function useWizardNavigation(options: UseWizardNavigationOptions): UseWizardNavigationReturn {
  const {
    currentStage,
    detectedCriteria,
    basicInfoFields,
    technicalSkills,
    behavioralCompetencies,
    salaryInfo,
    wsiQuestions,
  } = options

  const currentStageIndex = useMemo(() => {
    return WIZARD_STAGES.findIndex(s => s.id === currentStage)
  }, [currentStage])

  const currentStageConfig = useMemo(() => {
    return WIZARD_STAGES.find(s => s.id === currentStage)
  }, [currentStage])

  const currentPhase = useMemo(() => {
    return WIZARD_PHASES.find(phase => phase.stages.includes(currentStage))
  }, [currentStage])

  const backendStageNumber = useMemo(() => {
    return getBackendStageNumber(currentStage)
  }, [currentStage])

  const getStageValidation = useCallback((stageId: WizardStage): StageValidationResult => {
    const criteriaForValidation: Record<string, unknown> = {
      cargo: detectedCriteria.cargo || basicInfoFields.cargo,
      senioridadeIdiomas: detectedCriteria.senioridadeIdiomas,
      gestorArea: detectedCriteria.gestorArea || basicInfoFields.gestor,
      modeloTrabalho: detectedCriteria.modeloTrabalho || basicInfoFields.modeloTrabalho,
      localizacao: detectedCriteria.localizacao || basicInfoFields.localidade,
      salarioMin: salaryInfo.minSalary,
      salarioMax: salaryInfo.maxSalary,
      competenciasTecnicas: technicalSkills.length > 0 ? technicalSkills : null,
      competenciasComportamentais: behavioralCompetencies.filter(c => c.enabled).length > 0 ? behavioralCompetencies.filter(c => c.enabled) : null,
      perguntasTriagem: wsiQuestions.length > 0 ? wsiQuestions : null,
    }

    const missing = getMissingCriticalFields(stageId, criteriaForValidation)
    const validationMessage = generateMissingFieldsMessage(missing)

    return {
      isValid: missing.required.length === 0,
      missingRequired: missing.required,
      missingRecommended: missing.recommended,
      validationMessage: validationMessage || null,
    }
  }, [detectedCriteria, basicInfoFields, technicalSkills, behavioralCompetencies, salaryInfo, wsiQuestions])

  const validateCurrentStage = useCallback((): StageValidationResult => {
    return getStageValidation(currentStage)
  }, [currentStage, getStageValidation])

  const isStageComplete = useCallback((stageId: WizardStage): boolean => {
    const validation = getStageValidation(stageId)
    return validation.isValid
  }, [getStageValidation])

  const isStageAccessible = useCallback((stageId: WizardStage): boolean => {
    const stageIndex = WIZARD_STAGES.findIndex(s => s.id === stageId)
    if (stageIndex === 0) return true
    if (stageIndex <= currentStageIndex) return true
    for (let i = 0; i < stageIndex; i++) {
      const prevStage = WIZARD_STAGES[i].id as WizardStage
      if (!isStageComplete(prevStage)) {
        return false
      }
    }
    return true
  }, [currentStageIndex, isStageComplete])

  const canAdvance = useMemo(() => {
    if (currentStageIndex >= WIZARD_STAGES.length - 1) return false
    const validation = validateCurrentStage()
    return validation.isValid
  }, [currentStageIndex, validateCurrentStage])

  const canGoBack = useMemo(() => {
    return currentStageIndex > 0
  }, [currentStageIndex])

  const getNextStage = useCallback((): WizardStage | null => {
    const nextIndex = currentStageIndex + 1
    if (nextIndex >= WIZARD_STAGES.length) return null
    return WIZARD_STAGES[nextIndex].id as WizardStage
  }, [currentStageIndex])

  const getPreviousStage = useCallback((): WizardStage | null => {
    const prevIndex = currentStageIndex - 1
    if (prevIndex < 0) return null
    return WIZARD_STAGES[prevIndex].id as WizardStage
  }, [currentStageIndex])

  const getStageProgress = useCallback(() => {
    const total = WIZARD_STAGES.length
    const current = currentStageIndex + 1
    const percentage = Math.round((current / total) * 100)
    return { current, total, percentage }
  }, [currentStageIndex])

  const getPhaseProgress = useCallback(() => {
    const phaseIndex = WIZARD_PHASES.findIndex(phase => phase.stages.includes(currentStage))
    const phase = WIZARD_PHASES[phaseIndex]
    if (!phase) {
      return { currentPhase: 1, totalPhases: WIZARD_PHASES.length, stagesInPhase: 1, completedInPhase: 0 }
    }
    const stagesInPhase = phase.stages.length
    const stageIndexInPhase = phase.stages.indexOf(currentStage)
    const completedInPhase = stageIndexInPhase

    return {
      currentPhase: phaseIndex + 1,
      totalPhases: WIZARD_PHASES.length,
      stagesInPhase,
      completedInPhase,
    }
  }, [currentStage])

  const canNavigateToStage = useCallback((targetStage: WizardStage): { canNavigate: boolean; reason?: string } => {
    if (targetStage === currentStage) {
      return { canNavigate: false, reason: `Você já está na etapa de ${getStageLabel(targetStage)}.` }
    }

    const targetIndex = WIZARD_STAGES.findIndex(s => s.id === targetStage)
    if (targetIndex === -1) {
      return { canNavigate: false, reason: 'Etapa não encontrada.' }
    }

    if (targetIndex < currentStageIndex) {
      return { canNavigate: true }
    }

    if (targetIndex > currentStageIndex) {
      for (let i = currentStageIndex; i < targetIndex; i++) {
        const stage = WIZARD_STAGES[i].id as WizardStage
        const validation = getStageValidation(stage)
        if (!validation.isValid) {
          const stageLabel = getStageLabel(stage)
          return {
            canNavigate: false,
            reason: `Antes de ir para ${getStageLabel(targetStage)}, complete a etapa de ${stageLabel}.`,
          }
        }
      }
      return { canNavigate: true }
    }

    return { canNavigate: true }
  }, [currentStage, currentStageIndex, getStageValidation])

  const handleChatNavigation = useCallback((targetStage: WizardStage): ChatNavigationResult => {
    const { canNavigate, reason } = canNavigateToStage(targetStage)

    if (!canNavigate) {
      return {
        success: false,
        targetStage: null,
        message: reason || `Não é possível navegar para ${getStageLabel(targetStage)} no momento.`,
      }
    }

    const targetLabel = getStageLabel(targetStage)
    
    const targetValidation = getStageValidation(targetStage)
    const validationIssues = targetValidation.missingRequired.length > 0 
      ? targetValidation.missingRequired 
      : undefined

    return {
      success: true,
      targetStage,
      message: `✅ Navegando para a etapa de **${targetLabel}**.`,
      validationIssues,
    }
  }, [canNavigateToStage, getStageValidation])

  return {
    currentStageIndex,
    currentStageConfig,
    currentPhase,
    canAdvance,
    canGoBack,
    backendStageNumber,
    validateCurrentStage,
    getStageValidation,
    isStageComplete,
    isStageAccessible,
    getNextStage,
    getPreviousStage,
    getStageProgress,
    getPhaseProgress,
    handleChatNavigation,
    canNavigateToStage,
  }
}
