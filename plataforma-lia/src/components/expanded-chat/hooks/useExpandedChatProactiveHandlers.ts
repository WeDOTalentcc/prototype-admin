"use client"

import { formatBRL } from "@/lib/pricing"
import { liaApi } from "@/services/lia-api"

import React, { useEffect, useCallback } from "react"
import type { Message } from "../types"
import type { BasicInfoFields, DetectedCriteria, TechnicalSkill, BehavioralCompetency, SalaryInfo } from "../ExpandedChatContext"
import type { WSIQuestionCandidate } from "../types"

export interface ExpandedChatProactiveHandlersContext {
  PROACTIVE_MESSAGE_DELAY: number
  approvedCandidates: string[]
  basicInfoFields: BasicInfoFields
  behavioralCompetencies: BehavioralCompetency[]
  calibrationComplete: boolean
  calibrationProactiveTimerRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>
  calibrationStageCompletionShown: boolean
  competenciesProactiveTimerRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>
  competenciesStageCompletionShown: boolean
  currentStage: string
  inputEvaluationProactiveTimerRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>
  inputEvaluationStageCompletionShown: boolean
  isFieldRequiredForWizard: (fieldName: string) => boolean
  isResizing: boolean
  rejectedCandidates: string[]
  resizeRef: React.RefObject<HTMLDivElement>
  salaryInfo: SalaryInfo
  salaryProactiveTimerRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>
  salaryStageCompletionShown: boolean
  setAwaitingStageAdvanceConfirmation: React.Dispatch<React.SetStateAction<string | null>>
  setCalibrationStageCompletionShown: (val: boolean) => void
  setCompetenciesStageCompletionShown: (val: boolean) => void
  setInputEvaluationStageCompletionShown: (val: boolean) => void
  setIsResizing: (val: boolean) => void
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  setPanelWidth: (val: number) => void
  setSalaryStageCompletionShown: (val: boolean) => void
  setWsiQuestionsStageCompletionShown: (val: boolean) => void
  technicalSkills: TechnicalSkill[]
  wsiCandidates: WSIQuestionCandidate[]
  wsiQuestionsProactiveTimerRef: React.MutableRefObject<ReturnType<typeof setTimeout> | null>
  wsiQuestionsStageCompletionShown: boolean

  salaryBenchmark: unknown
  detectedCriteria: import("../ExpandedChatContext").DetectedCriteria
  setSalaryBenchmark: React.Dispatch<React.SetStateAction<unknown>>
  setSalaryInfo: React.Dispatch<React.SetStateAction<import("../ExpandedChatContext").SalaryInfo>>
  setIsLoadingBenchmark: (val: boolean) => void
}
export function useExpandedChatProactiveHandlers(ctx: ExpandedChatProactiveHandlersContext) {
  // Destructure for direct access (these effects reference variables directly)
  const {
    PROACTIVE_MESSAGE_DELAY,
    approvedCandidates, basicInfoFields, behavioralCompetencies,
    calibrationComplete, calibrationProactiveTimerRef, calibrationStageCompletionShown,
    competenciesProactiveTimerRef, competenciesStageCompletionShown,
    currentStage, inputEvaluationProactiveTimerRef, inputEvaluationStageCompletionShown,
    isFieldRequiredForWizard, isResizing, rejectedCandidates, resizeRef,
    salaryInfo, salaryProactiveTimerRef, salaryStageCompletionShown,
    setAwaitingStageAdvanceConfirmation, setCalibrationStageCompletionShown,
    setCompetenciesStageCompletionShown, setInputEvaluationStageCompletionShown,
    setIsResizing, setMessages, setPanelWidth, setSalaryStageCompletionShown,
    setWsiQuestionsStageCompletionShown, technicalSkills,
    wsiCandidates, wsiQuestionsProactiveTimerRef, wsiQuestionsStageCompletionShown,
    salaryBenchmark, detectedCriteria, setSalaryBenchmark, setSalaryInfo, setIsLoadingBenchmark,
  } = ctx

  // Proactive salary stage completion detection - timer resets on each salaryInfo change
  useEffect(() => {
    // Clear existing timer on every render (before checking conditions)
    if (salaryProactiveTimerRef.current) {
      clearTimeout(salaryProactiveTimerRef.current)
      salaryProactiveTimerRef.current = null
    }
    
    // Only trigger when in salary stage and not already shown
    if (currentStage !== 'salary' || salaryStageCompletionShown) return
    
    // Parse salary values
    const minSalary = parseFloat(salaryInfo.minSalary?.replace(/\./g, '').replace(',', '.') || '0')
    const maxSalary = parseFloat(salaryInfo.maxSalary?.replace(/\./g, '').replace(',', '.') || '0')
    const enabledBenefits = salaryInfo.benefits?.filter(b => b.enabled).length || 0
    
    // Check if salary field is required for this wizard
    const isSalaryRequired = isFieldRequiredForWizard('salario')
    
    // Determine if salary stage is complete based on requirements
    let isStageComplete = false
    
    if (!isSalaryRequired) {
      // If salary is NOT required (pre-configured), stage is complete immediately
      isStageComplete = true
    } else {
      // If salary IS required, need at least min/max salary
      const hasSalaryRange = minSalary > 0 && maxSalary > 0
      isStageComplete = hasSalaryRange
    }
    
    if (!isStageComplete) return // Not enough data yet
    
    // Schedule proactive message after delay (timer resets on each salaryInfo change via cleanup)
    salaryProactiveTimerRef.current = setTimeout(() => {
      // Double-check conditions are still valid (state may have changed)
      if (currentStage !== 'salary' || salaryStageCompletionShown) return
      
      // Build message based on what's filled
      const statusParts: string[] = []
      if (minSalary > 0 && maxSalary > 0) {
        statusParts.push(`**Faixa salarial:** ${formatBRL(minSalary)} - ${formatBRL(maxSalary)}`)
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
    }, PROACTIVE_MESSAGE_DELAY)
    
    return () => {
      if (salaryProactiveTimerRef.current) {
        clearTimeout(salaryProactiveTimerRef.current)
        salaryProactiveTimerRef.current = null
      }
    }
  }, [currentStage, salaryInfo, salaryStageCompletionShown, isFieldRequiredForWizard, PROACTIVE_MESSAGE_DELAY, salaryProactiveTimerRef, setAwaitingStageAdvanceConfirmation, setMessages, setSalaryStageCompletionShown])

  // Salary benchmark loading — moved from useExpandedChatEffects
  // Fetch salary benchmark when entering salary stage
  useEffect(() => {
    const fetchBenchmark = async () => {
      if (currentStage !== 'salary' || !basicInfoFields.cargo) return
      if (salaryBenchmark !== null) return
      
      setIsLoadingBenchmark(true)
      try {
        const benchmarkData = await liaApi.getSalaryBenchmark({
          job_title: basicInfoFields.cargo,
          seniority: detectedCriteria.senioridadeIdiomas || '',
          location: basicInfoFields.localidade,
          department: basicInfoFields.area,
          company_id: (basicInfoFields as unknown as Record<string, unknown>).companyId as string || ''
        })
        
        if (benchmarkData && (benchmarkData.internal || benchmarkData.market)) {
          setSalaryBenchmark(benchmarkData)
          
          if (benchmarkData.combined && !salaryInfo.minSalary && !salaryInfo.maxSalary) {
            setSalaryInfo(prev => ({
              ...prev,
              minSalary: benchmarkData.combined!.min.toLocaleString(),
              maxSalary: benchmarkData.combined!.max.toLocaleString()
            }))
          }
        }
      } catch (error) {
      } finally {
        setIsLoadingBenchmark(false)
      }
    }
    
    fetchBenchmark()
  }, [currentStage, basicInfoFields.cargo, basicInfoFields.area, basicInfoFields.localidade, detectedCriteria, salaryBenchmark, salaryInfo.maxSalary, salaryInfo.minSalary, setIsLoadingBenchmark, setSalaryBenchmark, setSalaryInfo])

  // Proactive input-evaluation stage completion detection - timer resets on each basicInfoFields change
  useEffect(() => {
    // Clear existing timer on every render (before checking conditions)
    if (inputEvaluationProactiveTimerRef.current) {
      clearTimeout(inputEvaluationProactiveTimerRef.current)
      inputEvaluationProactiveTimerRef.current = null
    }
    
    if (currentStage !== 'input-evaluation' || inputEvaluationStageCompletionShown) return
    
    // Check minimum required fields
    const hasCargo = !!basicInfoFields.cargo?.trim()
    const hasLocalidade = !!basicInfoFields.localidade?.trim()
    const hasModeloTrabalho = !!basicInfoFields.modeloTrabalho?.trim()
    
    const isStageComplete = hasCargo && hasLocalidade && hasModeloTrabalho
    
    if (!isStageComplete) return // Not enough data yet
    
    // Schedule proactive message after delay (timer resets on each basicInfoFields change via cleanup)
    inputEvaluationProactiveTimerRef.current = setTimeout(() => {
      // Double-check conditions are still valid (state may have changed)
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
    }, PROACTIVE_MESSAGE_DELAY)
    
    return () => {
      if (inputEvaluationProactiveTimerRef.current) {
        clearTimeout(inputEvaluationProactiveTimerRef.current)
        inputEvaluationProactiveTimerRef.current = null
      }
    }
  }, [currentStage, basicInfoFields, inputEvaluationStageCompletionShown, PROACTIVE_MESSAGE_DELAY, inputEvaluationProactiveTimerRef, setAwaitingStageAdvanceConfirmation, setInputEvaluationStageCompletionShown, setMessages])

  // Proactive competencies stage completion detection - timer resets on each competencies change
  useEffect(() => {
    // Clear existing timer on every render (before checking conditions)
    if (competenciesProactiveTimerRef.current) {
      clearTimeout(competenciesProactiveTimerRef.current)
      competenciesProactiveTimerRef.current = null
    }
    
    if (currentStage !== 'competencies' || competenciesStageCompletionShown) return
    
    const enabledTechnical = technicalSkills.length
    const enabledBehavioral = behavioralCompetencies.filter(c => c.enabled).length
    
    // Check minimum requirements: 3 technical + 3 behavioral
    const hasMinimumCompetencies = enabledTechnical >= 3 && enabledBehavioral >= 3
    
    if (!hasMinimumCompetencies) return // Not enough data yet
    
    // Schedule proactive message after delay (timer resets on each competencies change via cleanup)
    competenciesProactiveTimerRef.current = setTimeout(() => {
      // Double-check conditions are still valid (state may have changed)
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
    }, PROACTIVE_MESSAGE_DELAY)
    
    return () => {
      if (competenciesProactiveTimerRef.current) {
        clearTimeout(competenciesProactiveTimerRef.current)
        competenciesProactiveTimerRef.current = null
      }
    }
  }, [currentStage, technicalSkills, behavioralCompetencies, competenciesStageCompletionShown, PROACTIVE_MESSAGE_DELAY, competenciesProactiveTimerRef, setAwaitingStageAdvanceConfirmation, setCompetenciesStageCompletionShown, setMessages])

  // Proactive wsi-questions stage completion detection - timer resets on each wsiCandidates change
  useEffect(() => {
    // Clear existing timer on every render (before checking conditions)
    if (wsiQuestionsProactiveTimerRef.current) {
      clearTimeout(wsiQuestionsProactiveTimerRef.current)
      wsiQuestionsProactiveTimerRef.current = null
    }
    
    if (currentStage !== 'wsi-questions' || wsiQuestionsStageCompletionShown) return
    
    // Count selected questions
    const selectedQuestions = wsiCandidates.filter(q => q.selected).length
    const hasMinimumQuestions = selectedQuestions >= 3
    
    if (!hasMinimumQuestions) return // Not enough data yet
    
    // Schedule proactive message after delay (timer resets on each wsiCandidates change via cleanup)
    wsiQuestionsProactiveTimerRef.current = setTimeout(() => {
      // Double-check conditions are still valid (state may have changed)
      if (currentStage !== 'wsi-questions' || wsiQuestionsStageCompletionShown) return
      
      // Count question types
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
        awaitingStageConfirmation: 'review-publish',
      }
      setMessages(prev => [...prev, proactiveMessage])
      setWsiQuestionsStageCompletionShown(true)
      setAwaitingStageAdvanceConfirmation('review-publish')
    }, PROACTIVE_MESSAGE_DELAY)
    
    return () => {
      if (wsiQuestionsProactiveTimerRef.current) {
        clearTimeout(wsiQuestionsProactiveTimerRef.current)
        wsiQuestionsProactiveTimerRef.current = null
      }
    }
  }, [currentStage, wsiCandidates, wsiQuestionsStageCompletionShown, PROACTIVE_MESSAGE_DELAY, setAwaitingStageAdvanceConfirmation, setMessages, setWsiQuestionsStageCompletionShown, wsiQuestionsProactiveTimerRef])

  // Proactive calibration stage completion detection - timer resets on each calibration data change
  useEffect(() => {
    // Clear existing timer on every render (before checking conditions)
    if (calibrationProactiveTimerRef.current) {
      clearTimeout(calibrationProactiveTimerRef.current)
      calibrationProactiveTimerRef.current = null
    }
    
    if (currentStage !== 'search-calibration' || calibrationStageCompletionShown) return
    
    // Count evaluated candidates (approved + rejected)
    const likedCount = approvedCandidates.length
    const dislikedCount = rejectedCandidates.length
    const totalEvaluated = likedCount + dislikedCount
    
    const hasMinimumEvaluations = totalEvaluated >= 5
    
    if (!hasMinimumEvaluations || calibrationComplete) return // Not enough data yet or already complete
    
    // Schedule proactive message after delay (timer resets on each calibration data change via cleanup)
    calibrationProactiveTimerRef.current = setTimeout(() => {
      // Double-check conditions are still valid (state may have changed)
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
        awaitingStageConfirmation: 'calibration-complete',
      }
      setMessages(prev => [...prev, proactiveMessage])
      setCalibrationStageCompletionShown(true)
      setAwaitingStageAdvanceConfirmation('calibration-complete')
    }, PROACTIVE_MESSAGE_DELAY)
    
    return () => {
      if (calibrationProactiveTimerRef.current) {
        clearTimeout(calibrationProactiveTimerRef.current)
        calibrationProactiveTimerRef.current = null
      }
    }
  }, [currentStage, approvedCandidates.length, rejectedCandidates.length, calibrationStageCompletionShown, calibrationComplete, PROACTIVE_MESSAGE_DELAY, calibrationProactiveTimerRef, setAwaitingStageAdvanceConfirmation, setCalibrationStageCompletionShown, setMessages])

  // Reset all stage completion flags and confirmation state when stage changes
  useEffect(() => {
    // Reset awaiting confirmation when stage changes (prevents stale confirmations)
    setAwaitingStageAdvanceConfirmation(null)
    
    // Reset individual stage completion flags when leaving each stage
    if (currentStage !== 'input-evaluation') {
      setInputEvaluationStageCompletionShown(false)
    }
    if (currentStage !== 'salary') {
      setSalaryStageCompletionShown(false)
    }
    if (currentStage !== 'competencies') {
      setCompetenciesStageCompletionShown(false)
    }
    if (currentStage !== 'wsi-questions') {
      setWsiQuestionsStageCompletionShown(false)
    }
    if (currentStage !== 'search-calibration') {
      setCalibrationStageCompletionShown(false)
    }
    // Note: Timer refs are automatically reset by useEffect cleanup when stage changes
    // No need for manual timestamp tracking
  }, [currentStage, setAwaitingStageAdvanceConfirmation, setCalibrationStageCompletionShown, setCompetenciesStageCompletionShown, setInputEvaluationStageCompletionShown, setSalaryStageCompletionShown, setWsiQuestionsStageCompletionShown])

  // Panel resize handlers
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing || !resizeRef.current) return
      
      const container = resizeRef.current.parentElement?.parentElement
      if (!container) return
      
      const containerRect = container.getBoundingClientRect()
      const newWidth = ((containerRect.right - e.clientX) / containerRect.width) * 100
      
      // Limit between 25% and 55%
      setPanelWidth(Math.min(55, Math.max(25, newWidth)))
    }
    
    const handleMouseUp = () => {
      setIsResizing(false)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    
    if (isResizing) {
      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing, resizeRef, setIsResizing, setPanelWidth])

}
