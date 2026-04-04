"use client"

import React, { useState } from "react"
import type {
  ExtendedWizardStageConfig, WizardStage,
  TechnicalSkill, BehavioralCompetency,
  DetectedCriteria
} from '..'
import type { Message, WSIQuestionCandidate } from '../types'
import { WIZARD_STAGES } from '..'

interface UseStageValidationAndNavigationParams {
  currentStage: WizardStage
  currentStageIndex: number
  salaryInfo: {
    minSalary: string
    maxSalary: string
    minBonus?: string
    maxBonus?: string
    benefits: Array<{ enabled: boolean }>
  }
  messages: Message[]
  detectedCriteria: DetectedCriteria
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]
  wsiQualityGates: { canAdvance: boolean }
  wsiCandidates: WSIQuestionCandidate[]
  companyDefaultQuestions: Array<{ enabled: boolean }>
  calibrationComplete: boolean
  approvedCandidates: string[]
  publishedJobId: string | null
  basicInfoFields: { cargo: string; area: string; [key: string]: unknown }
  setStageTransition: React.Dispatch<React.SetStateAction<string>>
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  setDisplayedText: React.Dispatch<React.SetStateAction<string>>
  setCurrentStage: React.Dispatch<React.SetStateAction<WizardStage>>
  fetchDeduplicatedSkills: (
    cargo: string,
    alreadySelected: string[],
    seniority?: string
  ) => Promise<Array<{ name: string }>>
  typeText: (text: string, messageId: string) => void
  proceedToNextStage: () => void
  generateCompetencyAnalysisMessage: (
    cargo: string | null,
    area: string | null,
    criteria: DetectedCriteria,
    skillNames?: string[]
  ) => string
  generateWSIExplanationMessage: (
    techSkills: string[],
    behavioralComps: string[],
    cargo: string
  ) => string
}

export function useStageValidationAndNavigation({
  currentStage,
  currentStageIndex,
  salaryInfo,
  messages,
  detectedCriteria,
  technicalSkills,
  behavioralCompetencies,
  wsiQualityGates,
  wsiCandidates,
  companyDefaultQuestions,
  calibrationComplete,
  approvedCandidates,
  publishedJobId,
  basicInfoFields,
  setStageTransition,
  setMessages,
  setDisplayedText,
  setCurrentStage,
  fetchDeduplicatedSkills,
  typeText,
  proceedToNextStage,
  generateCompetencyAnalysisMessage,
  generateWSIExplanationMessage,
}: UseStageValidationAndNavigationParams) {
  const [validationError, setValidationError] = useState<string | null>(null)

  const validateCurrentStage = (): { isValid: boolean; errorMessage?: string } => {
    switch (currentStage) {
      case 'input-evaluation':
        return { isValid: true }

      case 'jd-enrichment':
        return { isValid: true }

      case 'competencies':
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

      case 'wsi-questions':
        return { isValid: true }

      case 'review-publish':
        return { isValid: true }

      default:
        return { isValid: true }
    }
  }

  const goToNextStage = () => {
    const validation = validateCurrentStage()
    if (!validation.isValid) {
      setValidationError(validation.errorMessage || 'Por favor, preencha os campos obrigatórios.')
      setTimeout(() => setValidationError(null), 4000)
      return
    }
    setValidationError(null)

    const nextIndex = currentStageIndex + 1
    if (nextIndex < WIZARD_STAGES.length) {
      const nextStage = WIZARD_STAGES[nextIndex]

      setStageTransition('loading')

      if (currentStage === 'salary' && nextStage.id === 'competencies') {
        const thinkingMessage: Message = {
          id: `lia-thinking-${Date.now()}`,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          processingState: 'thinking' as const
        }
        setMessages(prev => [...prev, thinkingMessage])

        const alreadySelectedSkills = [
          ...technicalSkills.map(s => s.name),
          ...behavioralCompetencies.filter(c => c.enabled).map(c => c.name)
        ]

        fetchDeduplicatedSkills(
          basicInfoFields.cargo || 'profissional',
          alreadySelectedSkills,
          detectedCriteria.senioridadeIdiomas || undefined
        ).then(deduplicatedSkills => {
          setMessages(prev => prev.filter(m => m.id !== thinkingMessage.id))

          const skillNames = deduplicatedSkills.map(s => s.name)

          const analysisContent = generateCompetencyAnalysisMessage(
            basicInfoFields.cargo,
            basicInfoFields.area,
            detectedCriteria,
            skillNames.length > 0 ? skillNames : undefined
          )

          const analysisMessage: Message = {
            id: `lia-competencies-analysis-${Date.now()}`,
            role: 'assistant',
            content: analysisContent,
            timestamp: new Date(),
            isTyping: true
          }
          setMessages(prev => [...prev, analysisMessage])
          setDisplayedText("")

          setTimeout(() => {
            typeText(analysisContent, analysisMessage.id)
          }, 200)

          setTimeout(() => {
            setStageTransition('idle')
            proceedToNextStage()
          }, 500)
        }).catch(() => {
          setMessages(prev => prev.filter(m => m.id !== thinkingMessage.id))
          setStageTransition('idle')
          proceedToNextStage()
        })
        return
      }

      if (currentStage === 'competencies' && nextStage.id === 'wsi-questions') {
        const thinkingMessage: Message = {
          id: `lia-thinking-wsi-${Date.now()}`,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          processingState: 'thinking' as const
        }
        setMessages(prev => [...prev, thinkingMessage])

        setTimeout(() => {
          setMessages(prev => prev.filter(m => m.id !== thinkingMessage.id))

          const enabledCompetencies = behavioralCompetencies.filter(c => c.enabled).map(c => c.name)
          const wsiExplanation = generateWSIExplanationMessage(
            technicalSkills.map(s => s.name),
            enabledCompetencies,
            basicInfoFields.cargo
          )

          const wsiMessage: Message = {
            id: `lia-wsi-explanation-${Date.now()}`,
            role: 'assistant',
            content: wsiExplanation,
            timestamp: new Date(),
            isTyping: true
          }
          setMessages(prev => [...prev, wsiMessage])
          setDisplayedText("")

          setTimeout(() => {
            typeText(wsiExplanation, wsiMessage.id)
          }, 200)

          setTimeout(() => {
            setStageTransition('idle')
            proceedToNextStage()
          }, 500)
        }, 800)
        return
      }

      setTimeout(() => {
        setStageTransition('idle')
        proceedToNextStage()
      }, 300)
    }
  }

  const goToPreviousStage = () => {
    const prevIndex = currentStageIndex - 1
    if (prevIndex >= 0) {
      const prevStage = WIZARD_STAGES[prevIndex]
      setCurrentStage(prevStage.id)
    }
  }

  const canAdvanceToNextStage = (): boolean => {
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
          parseFloat(salaryInfo.maxBonus.replace(/\./g, '').replace(',', '.')) > 0
        )
        const hasAtLeastOneBenefit = salaryInfo.benefits.some(b => b.enabled)
        return hasSalaryRange && bonusValid && hasAtLeastOneBenefit
      case 'wsi-questions':
        const hasMinimumQuestions = wsiCandidates.filter(q => q.selected).length >= 1 || companyDefaultQuestions.filter(q => q.enabled).length >= 1
        return hasMinimumQuestions && wsiQualityGates.canAdvance
      case 'review-publish':
        return true
      case 'search-calibration':
        return calibrationComplete || approvedCandidates.length >= 3 || publishedJobId !== null
      default:
        return true
    }
  }

  return {
    validationError,
    setValidationError,
    validateCurrentStage,
    goToNextStage,
    goToPreviousStage,
    canAdvanceToNextStage,
  }
}
