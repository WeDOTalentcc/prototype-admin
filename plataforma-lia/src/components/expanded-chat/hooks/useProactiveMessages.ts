import type { BackendRecord } from '@/types/api'
"use client"

import { useState, useEffect, useRef } from "react"
import type { WizardStage } from '../config'
import type { Message } from '../types'
import type { BasicInfoFields } from '../ExpandedChatContext'

export interface UseProactiveMessagesOptions {
  currentStage: WizardStage
  salaryInfo: { minSalary: string; maxSalary: string; benefits: Array<{ enabled: boolean }> }
  technicalSkills: Array<BackendRecord>
  behavioralCompetencies: Array<{ enabled: boolean; name?: string }>
  wsiCandidates: Array<{ selected?: boolean; type?: string }>
  approvedCandidates: Array<BackendRecord>
  rejectedCandidates: Array<BackendRecord>
  calibrationComplete: boolean
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  basicInfoFields: BasicInfoFields
  isFieldRequiredForWizard: (fieldName: string) => boolean
  proactiveDelay?: number
}

export interface UseProactiveMessagesReturn {
  state: {
    inputEvaluationStageCompletionShown: boolean
    salaryStageCompletionShown: boolean
    competenciesStageCompletionShown: boolean
    wsiQuestionsStageCompletionShown: boolean
    calibrationStageCompletionShown: boolean
    awaitingStageAdvanceConfirmation: string | null
  }
  actions: {
    setInputEvaluationStageCompletionShown: (v: boolean) => void
    setSalaryStageCompletionShown: (v: boolean) => void
    setCompetenciesStageCompletionShown: (v: boolean) => void
    setWsiQuestionsStageCompletionShown: (v: boolean) => void
    setCalibrationStageCompletionShown: (v: boolean) => void
    setAwaitingStageAdvanceConfirmation: (v: string | null) => void
  }
}

export function useProactiveMessages(options: UseProactiveMessagesOptions): UseProactiveMessagesReturn {
  const {
    currentStage, salaryInfo, technicalSkills, behavioralCompetencies,
    wsiCandidates, approvedCandidates, rejectedCandidates,
    calibrationComplete, setMessages, basicInfoFields, isFieldRequiredForWizard,
    proactiveDelay = 6000,
  } = options

  const [inputEvaluationStageCompletionShown, setInputEvaluationStageCompletionShown] = useState(false)
  const [salaryStageCompletionShown, setSalaryStageCompletionShown] = useState(false)
  const [competenciesStageCompletionShown, setCompetenciesStageCompletionShown] = useState(false)
  const [wsiQuestionsStageCompletionShown, setWsiQuestionsStageCompletionShown] = useState(false)
  const [calibrationStageCompletionShown, setCalibrationStageCompletionShown] = useState(false)
  const [awaitingStageAdvanceConfirmation, setAwaitingStageAdvanceConfirmation] = useState<string | null>(null)

  const salaryProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const competenciesProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const inputEvaluationProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const wsiQuestionsProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const calibrationProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (salaryProactiveTimerRef.current) {
      clearTimeout(salaryProactiveTimerRef.current)
      salaryProactiveTimerRef.current = null
    }

    if (currentStage !== 'salary' || salaryStageCompletionShown) return

    const minSalary = parseFloat(salaryInfo.minSalary?.replace(/\./g, '').replace(',', '.') || '0')
    const maxSalary = parseFloat(salaryInfo.maxSalary?.replace(/\./g, '').replace(',', '.') || '0')
    const enabledBenefits = salaryInfo.benefits?.filter(b => b.enabled).length || 0

    const isSalaryRequired = isFieldRequiredForWizard('salario')

    let isStageComplete = false
    if (!isSalaryRequired) {
      isStageComplete = true
    } else {
      const hasSalaryRange = minSalary > 0 && maxSalary > 0
      isStageComplete = hasSalaryRange
    }

    if (!isStageComplete) return

    salaryProactiveTimerRef.current = setTimeout(() => {
      if (currentStage !== 'salary' || salaryStageCompletionShown) return

      const statusParts: string[] = []
      if (minSalary > 0 && maxSalary > 0) {
        statusParts.push(`**Faixa salarial:** R$ ${minSalary.toLocaleString('pt-BR')} - R$ ${maxSalary.toLocaleString('pt-BR')}`)
      } else if (!isSalaryRequired) {
        statusParts.push('**Remuneração:** Usando configuração padrão da empresa')
      }
      if (enabledBenefits > 0) {
        statusParts.push(`**${enabledBenefits} benefícios** selecionados`)
      }

      const proactiveMessage: Message = {
        id: `salary-complete-${Date.now()}`,
        role: 'assistant',
        content: `✅ **Etapa de Remuneração pronta!**

Detectei que você configurou:
${statusParts.map(s => `• ${s}`).join('\n')}

Quer que eu avance para a etapa de **Competências**, ou prefere ajustar algo antes?`,
        timestamp: new Date(),
        awaitingStageConfirmation: 'competencies',
      }
      setMessages(prev => [...prev, proactiveMessage])
      setAwaitingStageAdvanceConfirmation('competencies')
      setSalaryStageCompletionShown(true)
    }, proactiveDelay)

    return () => {
      if (salaryProactiveTimerRef.current) {
        clearTimeout(salaryProactiveTimerRef.current)
        salaryProactiveTimerRef.current = null
      }
    }
  }, [currentStage, salaryInfo, salaryStageCompletionShown, isFieldRequiredForWizard, proactiveDelay, setMessages])

  useEffect(() => {
    if (inputEvaluationProactiveTimerRef.current) {
      clearTimeout(inputEvaluationProactiveTimerRef.current)
      inputEvaluationProactiveTimerRef.current = null
    }

    if (currentStage !== 'input-evaluation' || inputEvaluationStageCompletionShown) return

    const hasCargo = !!basicInfoFields.cargo?.trim()
    const hasLocalidade = !!basicInfoFields.localidade?.trim()
    const hasModeloTrabalho = !!basicInfoFields.modeloTrabalho?.trim()

    const isStageComplete = hasCargo && hasLocalidade && hasModeloTrabalho

    if (!isStageComplete) return

    inputEvaluationProactiveTimerRef.current = setTimeout(() => {
      if (currentStage !== 'input-evaluation' || inputEvaluationStageCompletionShown) return

      const proactiveMessage: Message = {
        id: `input-evaluation-complete-${Date.now()}`,
        role: 'assistant',
        content: `✅ **Informações básicas configuradas!**

Detectei:
• **Cargo:** ${basicInfoFields.cargo}
• **Local:** ${basicInfoFields.localidade}
• **Modelo:** ${basicInfoFields.modeloTrabalho}

Quer que eu avance para a etapa de **Enriquecimento da Vaga**, onde vou analisar dados de mercado e sugerir melhorias? Ou prefere ajustar algo antes?`,
        timestamp: new Date(),
        awaitingStageConfirmation: 'jd-enrichment',
      }
      setMessages(prev => [...prev, proactiveMessage])
      setInputEvaluationStageCompletionShown(true)
      setAwaitingStageAdvanceConfirmation('jd-enrichment')
    }, proactiveDelay)

    return () => {
      if (inputEvaluationProactiveTimerRef.current) {
        clearTimeout(inputEvaluationProactiveTimerRef.current)
        inputEvaluationProactiveTimerRef.current = null
      }
    }
  }, [currentStage, basicInfoFields, inputEvaluationStageCompletionShown, proactiveDelay, setMessages])

  useEffect(() => {
    if (competenciesProactiveTimerRef.current) {
      clearTimeout(competenciesProactiveTimerRef.current)
      competenciesProactiveTimerRef.current = null
    }
    if (currentStage !== 'competencies' || competenciesStageCompletionShown) return

    const enabledTechnical = technicalSkills.length
    const enabledBehavioral = behavioralCompetencies.filter(c => c.enabled).length

    const hasMinimumCompetencies = enabledTechnical >= 3 && enabledBehavioral >= 3

    if (!hasMinimumCompetencies) return

    competenciesProactiveTimerRef.current = setTimeout(() => {
      if (currentStage !== 'competencies' || competenciesStageCompletionShown) return
      const proactiveMessage: Message = {
        id: `competencies-complete-${Date.now()}`,
        role: 'assistant',
        content: `✅ **Competências configuradas!**

Detectei:
• **${enabledTechnical} competências técnicas** definidas
• **${enabledBehavioral} competências comportamentais** habilitadas

Quer que eu avance para a etapa de **Perguntas WSI**, ou prefere ajustar algo antes?`,
        timestamp: new Date(),
        awaitingStageConfirmation: 'wsi-questions',
      }
      setMessages(prev => [...prev, proactiveMessage])
      setAwaitingStageAdvanceConfirmation('wsi-questions')
      setCompetenciesStageCompletionShown(true)
    }, proactiveDelay)

    return () => {
      if (competenciesProactiveTimerRef.current) {
        clearTimeout(competenciesProactiveTimerRef.current)
        competenciesProactiveTimerRef.current = null
      }
    }
  }, [currentStage, technicalSkills, behavioralCompetencies, competenciesStageCompletionShown, proactiveDelay, setMessages])

  useEffect(() => {
    if (wsiQuestionsProactiveTimerRef.current) {
      clearTimeout(wsiQuestionsProactiveTimerRef.current)
      wsiQuestionsProactiveTimerRef.current = null
    }
    if (currentStage !== 'wsi-questions' || wsiQuestionsStageCompletionShown) return

    const selectedQuestions = wsiCandidates.filter(q => q.selected).length
    if (selectedQuestions < 3) return

    wsiQuestionsProactiveTimerRef.current = setTimeout(() => {
      if (currentStage !== 'wsi-questions' || wsiQuestionsStageCompletionShown) return
      const selectedTypes = wsiCandidates.filter(q => q.selected)
      const yesNoCount = selectedTypes.filter(q => q.type === 'yes-no').length
      const multipleChoiceCount = selectedTypes.filter(q => q.type === 'multiple-choice').length
      const openCount = selectedTypes.filter(q => q.type === 'open').length
      const numericCount = selectedTypes.filter(q => q.type === 'numeric').length

      const typesSummary: string[] = []
      if (yesNoCount > 0) typesSummary.push(`${yesNoCount} sim/não`)
      if (multipleChoiceCount > 0) typesSummary.push(`${multipleChoiceCount} múltipla escolha`)
      if (openCount > 0) typesSummary.push(`${openCount} aberta${openCount > 1 ? 's' : ''}`)
      if (numericCount > 0) typesSummary.push(`${numericCount} numérica${numericCount > 1 ? 's' : ''}`)

      const proactiveMessage: Message = {
        id: `wsi-questions-complete-${Date.now()}`,
        role: 'assistant',
        content: `✅ **Perguntas de triagem configuradas!**

Detectei:
• **${selectedQuestions} perguntas** selecionadas
• **Tipos:** ${typesSummary.join(', ')}

Essas perguntas serão usadas para avaliar candidatos automaticamente.

Quer que eu avance para a **Revisão Final**, ou prefere ajustar as perguntas?`,
        timestamp: new Date(),
        awaitingStageConfirmation: 'review-publish' as WizardStage,
      }
      setMessages(prev => [...prev, proactiveMessage])
      setWsiQuestionsStageCompletionShown(true)
      setAwaitingStageAdvanceConfirmation('review-publish')
    }, proactiveDelay)

    return () => {
      if (wsiQuestionsProactiveTimerRef.current) {
        clearTimeout(wsiQuestionsProactiveTimerRef.current)
        wsiQuestionsProactiveTimerRef.current = null
      }
    }
  }, [currentStage, wsiCandidates, wsiQuestionsStageCompletionShown, proactiveDelay, setMessages])

  useEffect(() => {
    if (calibrationProactiveTimerRef.current) {
      clearTimeout(calibrationProactiveTimerRef.current)
      calibrationProactiveTimerRef.current = null
    }
    if (currentStage !== 'search-calibration' || calibrationStageCompletionShown) return

    const likedCount = approvedCandidates.length
    const dislikedCount = rejectedCandidates.length
    const totalEvaluated = likedCount + dislikedCount
    const hasMinimumEvaluations = totalEvaluated >= 5
    if (!hasMinimumEvaluations || calibrationComplete) return

    calibrationProactiveTimerRef.current = setTimeout(() => {
      if (currentStage !== 'search-calibration' || calibrationStageCompletionShown) return
      const proactiveMessage: Message = {
        id: `calibration-complete-${Date.now()}`,
        role: 'assistant',
        content: `✅ **Calibração em bom andamento!**

Você avaliou **${totalEvaluated} candidatos**:
• ✓ ${likedCount} aprovados
• ✗ ${dislikedCount} rejeitados

Com base nas suas preferências, estou refinando o perfil ideal de candidato.

Quer **finalizar a calibração** e aplicar o modelo, ou prefere continuar avaliando mais candidatos?`,
        timestamp: new Date(),
        awaitingStageConfirmation: 'calibration-complete' as WizardStage,
      }
      setMessages(prev => [...prev, proactiveMessage])
      setCalibrationStageCompletionShown(true)
      setAwaitingStageAdvanceConfirmation('calibration-complete')
    }, proactiveDelay)

    return () => {
      if (calibrationProactiveTimerRef.current) {
        clearTimeout(calibrationProactiveTimerRef.current)
        calibrationProactiveTimerRef.current = null
      }
    }
  }, [currentStage, approvedCandidates.length, rejectedCandidates.length, calibrationStageCompletionShown, calibrationComplete, proactiveDelay, setMessages])

  useEffect(() => {
    setAwaitingStageAdvanceConfirmation(null)
    if (currentStage !== 'input-evaluation') setInputEvaluationStageCompletionShown(false)
    if (currentStage !== 'salary') setSalaryStageCompletionShown(false)
    if (currentStage !== 'competencies') setCompetenciesStageCompletionShown(false)
    if (currentStage !== 'wsi-questions') setWsiQuestionsStageCompletionShown(false)
    if (currentStage !== 'search-calibration') setCalibrationStageCompletionShown(false)
  }, [currentStage])

  return {
    state: {
      inputEvaluationStageCompletionShown,
      salaryStageCompletionShown,
      competenciesStageCompletionShown,
      wsiQuestionsStageCompletionShown,
      calibrationStageCompletionShown,
      awaitingStageAdvanceConfirmation,
    },
    actions: {
      setInputEvaluationStageCompletionShown,
      setSalaryStageCompletionShown,
      setCompetenciesStageCompletionShown,
      setWsiQuestionsStageCompletionShown,
      setCalibrationStageCompletionShown,
      setAwaitingStageAdvanceConfirmation,
    },
  }
}
