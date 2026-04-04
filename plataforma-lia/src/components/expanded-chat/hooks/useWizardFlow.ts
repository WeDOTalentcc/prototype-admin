"use client"

import { useState, useCallback } from "react"
import type { DetectedCriteria, BasicInfoFields, TechnicalSkill, BehavioralCompetency, SalaryInfo } from '../ExpandedChatContext'
import type { Message, WSIQuestionCandidate } from '../types'
import type { WizardStage, ExtendedWizardStageConfig } from '../config'
import { WIZARD_STAGES, getMissingCriticalFields } from '../config'

interface CompanyDefaultQuestion {
  id: string
  question: string
  type: 'yes-no' | 'numeric' | 'open' | 'multiple-choice'
  enabled: boolean
  fromConfig: boolean
}

export interface UseWizardFlowOptions {
  currentStage: WizardStage
  currentStageIndex: number
  detectedCriteria: DetectedCriteria
  basicInfoFields: BasicInfoFields
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]
  salaryInfo: SalaryInfo
  wsiCandidates: WSIQuestionCandidate[]
  companyDefaultQuestions: CompanyDefaultQuestion[]
  wsiQualityGates: { canAdvance: boolean }
  calibrationComplete: boolean
  approvedCandidates: string[]
  publishedJobId: string | null
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  setCurrentStage: (stage: WizardStage) => void
  setDisplayedText: (text: string) => void
  saveWizardDraft: () => void
  typeText: (text: string, messageId: string) => void
}

export interface UseWizardFlowReturn {
  state: {
    validationError: string | null
  }
  actions: {
    proceedToNextStage: () => void
    goToNextStage: () => void
    goToPreviousStage: () => void
    canAdvanceToNextStage: () => boolean
    validateCurrentStage: () => { isValid: boolean; errorMessage?: string }
  }
  setStageTransition: React.Dispatch<React.SetStateAction<'idle' | 'loading' | 'waiting-response'>>
  stageTransition: 'idle' | 'loading' | 'waiting-response'
}

export function useWizardFlow(options: UseWizardFlowOptions): UseWizardFlowReturn {
  const {
    currentStage, currentStageIndex,
    detectedCriteria, basicInfoFields,
    technicalSkills, behavioralCompetencies,
    salaryInfo, wsiCandidates, companyDefaultQuestions,
    wsiQualityGates, calibrationComplete, approvedCandidates, publishedJobId,
    messages, setMessages, setCurrentStage, setDisplayedText,
    saveWizardDraft, typeText,
  } = options

  const [validationError, setValidationError] = useState<string | null>(null)
  const [stageTransition, setStageTransition] = useState<'idle' | 'loading' | 'waiting-response'>('idle')

  const validateCurrentStage = useCallback((): { isValid: boolean; errorMessage?: string } => {
    switch (currentStage) {
      case 'input-evaluation':
      case 'jd-enrichment':
      case 'competencies':
      case 'wsi-questions':
      case 'review-publish':
        return { isValid: true }

      case 'salary':
        const minSalary = parseFloat(salaryInfo.minSalary)
        const maxSalary = parseFloat(salaryInfo.maxSalary)
        if (isNaN(minSalary) || minSalary <= 0) {
          return { isValid: false, errorMessage: 'Informe o salário mínimo.' }
        }
        if (isNaN(maxSalary) || maxSalary <= 0) {
          return { isValid: false, errorMessage: 'Informe o salário máximo.' }
        }
        if (maxSalary < minSalary) {
          return { isValid: false, errorMessage: 'O salário máximo deve ser maior que o mínimo.' }
        }
        return { isValid: true }

      default:
        return { isValid: true }
    }
  }, [currentStage, salaryInfo])

  const canAdvanceToNextStage = useCallback((): boolean => {
    switch (currentStage) {
      case 'input-evaluation':
        const hasUserSentMessage = messages.some(m => m.role === 'user')
        if (!hasUserSentMessage) return false
        const filledCriteria = [
          detectedCriteria.cargo,
          detectedCriteria.gestorArea,
          detectedCriteria.competenciasTecnicas.length > 0,
          detectedCriteria.senioridadeIdiomas,
          detectedCriteria.modeloTrabalho,
          detectedCriteria.localizacao
        ].filter(Boolean).length
        return filledCriteria >= 2

      case 'jd-enrichment':
        return !!detectedCriteria.cargo

      case 'competencies':
        const hasMinimumTechnicalSkills = technicalSkills.length >= 1
        return hasMinimumTechnicalSkills && wsiQualityGates.canAdvance

      case 'salary':
        const hasSalaryRange = !!(salaryInfo.minSalary && salaryInfo.maxSalary &&
          parseFloat(salaryInfo.minSalary.replace(/\./g, '').replace(',', '.')) > 0 &&
          parseFloat(salaryInfo.maxSalary.replace(/\./g, '').replace(',', '.')) > 0)
        const bonusStarted = !!(salaryInfo.minBonus || salaryInfo.maxBonus)
        const bonusValid = !bonusStarted || !!(
          salaryInfo.minBonus && salaryInfo.maxBonus &&
          parseFloat(salaryInfo.minBonus.replace(/\./g, '').replace(',', '.')) > 0 &&
          parseFloat(salaryInfo.maxBonus.replace(/\./g, '').replace(',', '.')) > 0)
        const hasAtLeastOneBenefit = salaryInfo.benefits.some(b => b.enabled)
        return hasSalaryRange && bonusValid && hasAtLeastOneBenefit

      case 'wsi-questions':
        const hasMinimumQuestions = wsiCandidates.filter((q) => q.selected).length >= 1 || companyDefaultQuestions.filter((q) => q.enabled).length >= 1
        return hasMinimumQuestions && wsiQualityGates.canAdvance

      case 'review-publish':
        return true

      case 'search-calibration':
        return calibrationComplete || approvedCandidates.length >= 3 || publishedJobId !== null

      default:
        return true
    }
  }, [currentStage, messages, detectedCriteria, technicalSkills, wsiQualityGates, salaryInfo, wsiCandidates, companyDefaultQuestions, calibrationComplete, approvedCandidates, publishedJobId])

  const proceedToNextStage = useCallback(() => {
    const nextIndex = currentStageIndex + 1
    if (nextIndex < WIZARD_STAGES.length) {
      const currentStageConfig = WIZARD_STAGES[currentStageIndex] as ExtendedWizardStageConfig
      const nextStage = WIZARD_STAGES[nextIndex] as ExtendedWizardStageConfig

      let transitionContent = ""
      if (currentStageConfig.transition) {
        const { congratsMessage, nextStepExplanation, whyItMatters, proactiveTips } = currentStageConfig.transition
        transitionContent = `${congratsMessage}\n\n`
        transitionContent += `**Próximo passo:** ${nextStepExplanation}\n\n`
        transitionContent += `💡 *${whyItMatters}*`
        if (proactiveTips && proactiveTips.length > 0) {
          transitionContent += `\n\n**O que vou fazer:**\n`
          proactiveTips.forEach(tip => {
            transitionContent += `• ${tip}\n`
          })
        }
      }
      const missingFields = getMissingCriticalFields(currentStageConfig.id, detectedCriteria as any)
      if (missingFields.recommended.length > 0) {
        transitionContent += `\n\n📝 *Campos opcionais não preenchidos: ${missingFields.recommended.join(', ')}*`
      }

      if (transitionContent) {
        const transitionMessage: Message = {
          id: `transition-${currentStageConfig.id}-${Date.now()}`,
          role: 'assistant',
          content: transitionContent,
          timestamp: new Date(),
          isTyping: true
        }
        setMessages(prev => [...prev, transitionMessage])
        typeText(transitionContent, transitionMessage.id)

        setTimeout(() => {
          setCurrentStage(nextStage.id)
          saveWizardDraft()
          const stageMessage: Message = {
            id: `stage-${nextStage.id}-${Date.now()}`,
            role: 'assistant',
            content: nextStage.liaMessage,
            timestamp: new Date(),
            isTyping: true
          }
          setMessages(prev => [...prev, stageMessage])
          setDisplayedText("")
          setTimeout(() => {
            typeText(nextStage.liaMessage, stageMessage.id)
          }, 300)
        }, 2000)
      } else {
        setCurrentStage(nextStage.id)
        saveWizardDraft()
        const stageMessage: Message = {
          id: `stage-${nextStage.id}-${Date.now()}`,
          role: 'assistant',
          content: nextStage.liaMessage,
          timestamp: new Date(),
          isTyping: true
        }
        setMessages(prev => [...prev, stageMessage])
        setDisplayedText("")
        setTimeout(() => {
          typeText(nextStage.liaMessage, stageMessage.id)
        }, 300)
      }
    }
  }, [currentStageIndex, detectedCriteria, setMessages, setCurrentStage, setDisplayedText, saveWizardDraft, typeText])

  const goToNextStage = useCallback(() => {
    const validation = validateCurrentStage()
    if (!validation.isValid) {
      setValidationError(validation.errorMessage || 'Por favor, preencha os campos obrigatórios.')
      setTimeout(() => setValidationError(null), 4000)
      return
    }
    setValidationError(null)

    const nextIndex = currentStageIndex + 1
    if (nextIndex < WIZARD_STAGES.length) {
      setStageTransition('loading')
      setTimeout(() => {
        setStageTransition('idle')
        proceedToNextStage()
      }, 300)
    }
  }, [currentStageIndex, validateCurrentStage, proceedToNextStage])

  const goToPreviousStage = useCallback(() => {
    const prevIndex = currentStageIndex - 1
    if (prevIndex >= 0) {
      const prevStage = WIZARD_STAGES[prevIndex]
      setCurrentStage(prevStage.id)
    }
  }, [currentStageIndex, setCurrentStage])

  return {
    state: { validationError },
    actions: {
      proceedToNextStage,
      goToNextStage,
      goToPreviousStage,
      canAdvanceToNextStage,
      validateCurrentStage,
    },
    setStageTransition,
    stageTransition,
  }
}
