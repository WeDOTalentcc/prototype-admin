"use client"

import { formatBRL, CURRENCY_SYMBOL } from "@/lib/pricing"

import React, { useCallback, useEffect } from "react"
import { liaApi, type WizardOrchestratorResponse, type VacancySearchCriteria, type VacancyAdjustments } from "@/services/lia-api"
import {
  type TechnicalSkill,
  type BehavioralCompetency,
  type SalaryInfo,
  type DetectedCriteria,
  type BasicInfoFields,
} from "../ExpandedChatContext"
import { type WizardStage, getFrontendStageFromBackend } from "../config/wizard-config"
import {
  type Message,
  type CalibrationCandidate,
  type WSIQuestionCandidate,
} from "../types"
import { type EnrichedJDData } from "../stages"
import { type WizardMode, type FastTrackState } from "../types"
import { type UseConversationMemoryReturn } from "./useConversationMemory"
import { type JobConfig } from "./usePublishingState"
import { type CompensationAnalysisResult } from "../../job-creation/compensation-analysis-panel"
import type { VacancySummary } from "../../job-creation/vacancy-search-results"

import { useWSIQuestionHandlers } from "./useWSIQuestionHandlers"
import { useCalibrationAndFastTrackHandlers } from "./useCalibrationAndFastTrackHandlers"
export interface WSIAndCalibrationHandlersContext {
  // Basic info and criteria
  basicInfoFields: BasicInfoFields
  setBasicInfoFields: React.Dispatch<React.SetStateAction<BasicInfoFields>>
  detectedCriteria: DetectedCriteria
  setDetectedCriteria: React.Dispatch<React.SetStateAction<DetectedCriteria>>

  // Skills and competencies
  technicalSkills: TechnicalSkill[]
  setTechnicalSkills: React.Dispatch<React.SetStateAction<TechnicalSkill[]>>
  behavioralCompetencies: BehavioralCompetency[]
  setBehavioralCompetencies: React.Dispatch<React.SetStateAction<BehavioralCompetency[]>>

  // Salary
  salaryInfo: SalaryInfo
  setSalaryInfo: React.Dispatch<React.SetStateAction<SalaryInfo>>

  // Messages
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>

  // Stage
  currentStage: WizardStage
  setCurrentStage: React.Dispatch<React.SetStateAction<WizardStage>>

  // WSI state
  wsiCandidates: WSIQuestionCandidate[]
  setWsiCandidates: React.Dispatch<React.SetStateAction<WSIQuestionCandidate[]>>
  wsiGenerationBatch: number
  setWsiGenerationBatch: React.Dispatch<React.SetStateAction<number>>
  isGeneratingWSI: boolean
  setIsGeneratingWSI: React.Dispatch<React.SetStateAction<boolean>>
  wsiHasGenerated: boolean
  setWsiHasGenerated: React.Dispatch<React.SetStateAction<boolean>>
  setWsiQuestions: React.Dispatch<React.SetStateAction<WSIQuestionCandidate[]>>
  customQuestionText: string
  customQuestionType: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  customQuestionRequired: boolean
  setShowCustomQuestionForm: (val: boolean) => void
  setCustomQuestionText: (val: string) => void
  setCustomQuestionType: (val: 'open' | 'yes-no' | 'numeric' | 'multiple-choice') => void
  setCustomQuestionRequired: (val: boolean) => void

  // Calibration state
  calibrationCandidates: CalibrationCandidate[]
  setCalibrationCandidates: React.Dispatch<React.SetStateAction<CalibrationCandidate[]>>
  currentCalibrationIndex: number
  setCurrentCalibrationIndex: React.Dispatch<React.SetStateAction<number>>
  approvedCandidates: string[]
  setApprovedCandidates: React.Dispatch<React.SetStateAction<string[]>>
  rejectedCandidates: string[]
  setRejectedCandidates: React.Dispatch<React.SetStateAction<string[]>>
  calibrationComplete: boolean
  setCalibrationComplete: React.Dispatch<React.SetStateAction<boolean>>
  isLoadingCalibration: boolean
  setIsLoadingCalibration: React.Dispatch<React.SetStateAction<boolean>>
  showCalibrationModal: boolean
  setShowCalibrationModal: React.Dispatch<React.SetStateAction<boolean>>
  calibrationSessionId: string | null
  setCalibrationSessionId: React.Dispatch<React.SetStateAction<string | null>>
  calibrationComment: string
  setCalibrationComment: React.Dispatch<React.SetStateAction<string>>
  publishedJobId: string | null
  setPublishedJobId: React.Dispatch<React.SetStateAction<string | null>>
  calibrationCriteria: Array<{ id: string; text: string; source: 'technical' | 'behavioral' }>
  setCalibrationCriteria: React.Dispatch<React.SetStateAction<Array<{ id: string; text: string; source: 'technical' | 'behavioral' }>>>
  postCalibrationComplete: boolean
  setPostCalibrationComplete: React.Dispatch<React.SetStateAction<boolean>>
  hasAttemptedCalibrationGeneration: boolean
  setHasAttemptedCalibrationGeneration: React.Dispatch<React.SetStateAction<boolean>>
  setSearchPhase: React.Dispatch<React.SetStateAction<'local-searching' | 'local-complete' | 'global-searching' | 'global-complete' | 'idle'>>
  setLocalCandidateCount: (count: number) => void
  setGlobalCandidateCount: (count: number) => void
  preferredCandidateCount: number
  awaitingCalibrationChoice: boolean
  setAwaitingCalibrationChoice: React.Dispatch<React.SetStateAction<boolean>>

  // Fast Track state
  fastTrackState: FastTrackState
  setFastTrackState: React.Dispatch<React.SetStateAction<FastTrackState>>
  fastTrackSelectedVacancy: VacancySummary | null
  setFastTrackSelectedVacancy: (vacancy: VacancySummary | null) => void
  fastTrackAdjustments: VacancyAdjustments
  setFastTrackAdjustments: React.Dispatch<React.SetStateAction<VacancyAdjustments>>
  fastTrackSearchResults: VacancySummary[]
  setFastTrackSearchResults: React.Dispatch<React.SetStateAction<VacancySummary[]>>
  isSearchingVacancies: boolean
  setIsSearchingVacancies: React.Dispatch<React.SetStateAction<boolean>>
  wizardFastTrackSourceJobId: string | null
  setWizardFastTrackSourceJobId: (id: string | null) => void
  setWizardMode: React.Dispatch<React.SetStateAction<WizardMode>>

  // Loading
  isLoading: boolean
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>

  // Job config
  setJobConfig: React.Dispatch<React.SetStateAction<JobConfig>>

  // Enrichment
  setEnrichedJDData: React.Dispatch<React.SetStateAction<EnrichedJDData | null>>
  setIsLoadingEnrichment: React.Dispatch<React.SetStateAction<boolean>>

  // Compensation
  setCompensationAnalysis: React.Dispatch<React.SetStateAction<CompensationAnalysisResult | null>>

  // Display state
  setDisplayedText: React.Dispatch<React.SetStateAction<string>>

  // User
  user: { name?: string; email?: string; company?: string; id?: string } | null
  resolvedCompanyId: string | null

  // Conversation memory
  conversationMemory: UseConversationMemoryReturn

  // UI helpers
  highlightField: (field: string) => void
  typeText: (text: string, messageId: string) => void

  // Proactive confirmation tracking
  inputEvaluationStageCompletionShown: boolean
  awaitingStageAdvanceConfirmation: string | null
  setAwaitingStageAdvanceConfirmation: React.Dispatch<React.SetStateAction<string | null>>

  // Callback from parent
  onJobCreated?: () => void

  // From Extraction 1 — generateParecerData is needed by processOrchestratorResponse callers
  // (not directly by processOrchestratorResponse itself — it uses typeText + setMessages)
}

export function useWSIAndCalibrationHandlers(ctx: WSIAndCalibrationHandlersContext) {

  // WSI question management — extracted to useWSIQuestionHandlers
  const {
    generateWSIQuestions,
    toggleWSIQuestionSelection,
    updateWSIQuestionExpectedAnswer,
    updateWSIQuestionCorrectOption,
    deleteWSIQuestion,
    addCustomQuestion,
  } = useWSIQuestionHandlers({
    basicInfoFields: ctx.basicInfoFields,
    detectedCriteria: ctx.detectedCriteria,
    technicalSkills: ctx.technicalSkills,
    behavioralCompetencies: ctx.behavioralCompetencies,
    wsiCandidates: ctx.wsiCandidates,
    setWsiCandidates: ctx.setWsiCandidates,
    wsiGenerationBatch: ctx.wsiGenerationBatch,
    setWsiGenerationBatch: ctx.setWsiGenerationBatch,
    isGeneratingWSI: ctx.isGeneratingWSI,
    setIsGeneratingWSI: ctx.setIsGeneratingWSI,
    wsiHasGenerated: ctx.wsiHasGenerated,
    setWsiHasGenerated: ctx.setWsiHasGenerated,
    setWsiQuestions: ctx.setWsiQuestions,
    customQuestionText: ctx.customQuestionText,
    customQuestionType: ctx.customQuestionType,
    customQuestionRequired: ctx.customQuestionRequired,
    setShowCustomQuestionForm: ctx.setShowCustomQuestionForm,
    setCustomQuestionText: ctx.setCustomQuestionText,
    setCustomQuestionType: ctx.setCustomQuestionType,
    setCustomQuestionRequired: ctx.setCustomQuestionRequired,
    currentStage: ctx.currentStage,
    setMessages: ctx.setMessages,
  })

  // Initialize calibration criteria from technical skills and behavioral competencies
  // Calibration + Fast Track handlers — extracted to useCalibrationAndFastTrackHandlers
  const {
    initializeCalibrationCriteria,
    generateCalibrationCandidates,
    handleApproveCandidate,
    handleRejectCandidate,
    moveToNextCandidate,
    generateMoreCalibrationCandidates,
    addCalibrationCriterion,
    removeCalibrationCriterion,
    reorderCalibrationCriteria,
    handleFastTrackVacancySelect,
    handleFastTrackSearch,
    handleFastTrackPublish,
    parseFastTrackAdjustment,
  } = useCalibrationAndFastTrackHandlers({
    basicInfoFields: ctx.basicInfoFields,
    detectedCriteria: ctx.detectedCriteria,
    technicalSkills: ctx.technicalSkills,
    behavioralCompetencies: ctx.behavioralCompetencies,
    salaryInfo: ctx.salaryInfo,
    publishedJobId: ctx.publishedJobId,
    calibrationCandidates: ctx.calibrationCandidates,
    setCalibrationCandidates: ctx.setCalibrationCandidates,
    currentCalibrationIndex: ctx.currentCalibrationIndex,
    setCurrentCalibrationIndex: ctx.setCurrentCalibrationIndex,
    approvedCandidates: ctx.approvedCandidates,
    setApprovedCandidates: ctx.setApprovedCandidates,
    rejectedCandidates: ctx.rejectedCandidates,
    setRejectedCandidates: ctx.setRejectedCandidates,
    calibrationComplete: ctx.calibrationComplete,
    setCalibrationComplete: ctx.setCalibrationComplete,
    isLoadingCalibration: ctx.isLoadingCalibration,
    setIsLoadingCalibration: ctx.setIsLoadingCalibration,
    showCalibrationModal: ctx.showCalibrationModal,
    setShowCalibrationModal: ctx.setShowCalibrationModal,
    calibrationSessionId: ctx.calibrationSessionId,
    setCalibrationSessionId: ctx.setCalibrationSessionId,
    calibrationComment: ctx.calibrationComment,
    setCalibrationComment: ctx.setCalibrationComment,
    calibrationCriteria: ctx.calibrationCriteria,
    setCalibrationCriteria: ctx.setCalibrationCriteria,
    postCalibrationComplete: ctx.postCalibrationComplete,
    setPostCalibrationComplete: ctx.setPostCalibrationComplete,
    hasAttemptedCalibrationGeneration: ctx.hasAttemptedCalibrationGeneration,
    setHasAttemptedCalibrationGeneration: ctx.setHasAttemptedCalibrationGeneration,
    setSearchPhase: ctx.setSearchPhase,
    setLocalCandidateCount: ctx.setLocalCandidateCount,
    setGlobalCandidateCount: ctx.setGlobalCandidateCount,
    awaitingCalibrationChoice: ctx.awaitingCalibrationChoice,
    setAwaitingCalibrationChoice: ctx.setAwaitingCalibrationChoice,
    fastTrackState: ctx.fastTrackState,
    setFastTrackState: ctx.setFastTrackState,
    fastTrackSelectedVacancy: ctx.fastTrackSelectedVacancy,
    setFastTrackSelectedVacancy: ctx.setFastTrackSelectedVacancy,
    fastTrackAdjustments: ctx.fastTrackAdjustments,
    setFastTrackAdjustments: ctx.setFastTrackAdjustments,
    fastTrackSearchResults: ctx.fastTrackSearchResults,
    setFastTrackSearchResults: ctx.setFastTrackSearchResults,
    isSearchingVacancies: ctx.isSearchingVacancies,
    setIsSearchingVacancies: ctx.setIsSearchingVacancies,
    wizardFastTrackSourceJobId: ctx.wizardFastTrackSourceJobId,
    setWizardFastTrackSourceJobId: ctx.setWizardFastTrackSourceJobId,
    setWizardMode: ctx.setWizardMode,
    isLoading: ctx.isLoading,
    setIsLoading: ctx.setIsLoading,
    messages: ctx.messages,
    setMessages: ctx.setMessages,
    currentStage: ctx.currentStage,
    user: ctx.user,
    resolvedCompanyId: ctx.resolvedCompanyId as string | null ?? null,
    onJobCreated: ctx.onJobCreated,
  })

  const buildCollectedData = useCallback(() => {
    return {
      title: ctx.basicInfoFields.cargo || ctx.detectedCriteria.cargo || null,
      department: ctx.basicInfoFields.area || ctx.detectedCriteria.departamento || null,
      seniority_level: ctx.detectedCriteria.senioridadeIdiomas || null,
      work_model: ctx.basicInfoFields.modeloTrabalho || ctx.detectedCriteria.modeloTrabalho || null,
      location: ctx.basicInfoFields.localidade || ctx.detectedCriteria.localizacao || null,
      manager: ctx.basicInfoFields.gestor || ctx.detectedCriteria.gestorArea || null,
      salary_min: ctx.salaryInfo.minSalary ? parseInt(ctx.salaryInfo.minSalary) : null,
      salary_max: ctx.salaryInfo.maxSalary ? parseInt(ctx.salaryInfo.maxSalary) : null,
      technical_skills: ctx.technicalSkills.filter(s => s.required).map(s => s.name),
      behavioral_competencies: ctx.behavioralCompetencies.filter(c => c.enabled).map(c => c.name),
      screening_questions: ctx.wsiCandidates.filter(q => q.selected).map(q => ({
        question: q.question,
        category: q.category,
        expected_answer: q.expectedAnswer,
        weight: 5,
        type: q.type
      }))
    }
  }, [ctx.basicInfoFields, ctx.detectedCriteria, ctx.salaryInfo, ctx.technicalSkills, ctx.behavioralCompetencies, ctx.wsiCandidates])

  // Process orchestrator response and apply actions from smart-orchestrate endpoint
  const processOrchestratorResponse = useCallback(async (
    orchestratorResult: WizardOrchestratorResponse,
    processingMessageId: string
  ) => {
    
    // Use new response format from smart-orchestrate endpoint
    const liaMessage = orchestratorResult.lia_message || orchestratorResult.response || ''
    const detectedCriteriaFromBackend = orchestratorResult.detected_criteria || {}
    const nextStage = orchestratorResult.next_stage
    const autoTransition = orchestratorResult.auto_transition
    const toolResults = orchestratorResult.tool_results || []
    
    // Update processing message
    ctx.setMessages(msgs => msgs.map(m => 
      m.id === processingMessageId 
        ? { ...m, content: '✅ Resposta da LIA', processingState: 'completed' as const }
        : m
    ))
    
    // Apply detected_criteria to form fields
    if (detectedCriteriaFromBackend && Object.keys(detectedCriteriaFromBackend).length > 0) {
      
      if (detectedCriteriaFromBackend.job_title || detectedCriteriaFromBackend.title || detectedCriteriaFromBackend.cargo) {
        const title = String(detectedCriteriaFromBackend.job_title || detectedCriteriaFromBackend.title || detectedCriteriaFromBackend.cargo)
        ctx.setBasicInfoFields(prev => ({ ...prev, cargo: title }))
        ctx.setDetectedCriteria(prev => ({ ...prev, cargo: title }))
        ctx.highlightField('cargo')
      }
      
      if (detectedCriteriaFromBackend.department || detectedCriteriaFromBackend.area) {
        const dept = String(detectedCriteriaFromBackend.department || detectedCriteriaFromBackend.area)
        ctx.setBasicInfoFields(prev => ({ ...prev, area: dept }))
        ctx.setDetectedCriteria(prev => ({ ...prev, departamento: dept }))
        ctx.highlightField('departamento')
      }
      
      if (detectedCriteriaFromBackend.seniority || detectedCriteriaFromBackend.seniority_level) {
        const seniority = String(detectedCriteriaFromBackend.seniority || detectedCriteriaFromBackend.seniority_level)
        ctx.setDetectedCriteria(prev => ({ ...prev, senioridadeIdiomas: seniority }))
        ctx.highlightField('senioridade')
      }
      
      if (detectedCriteriaFromBackend.work_model || detectedCriteriaFromBackend.modelo_trabalho) {
        const workModel = String(detectedCriteriaFromBackend.work_model || detectedCriteriaFromBackend.modelo_trabalho)
        ctx.setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: workModel }))
        ctx.setDetectedCriteria(prev => ({ ...prev, modeloTrabalho: workModel }))
        ctx.highlightField('modeloTrabalho')
      }
      
      if (detectedCriteriaFromBackend.location || detectedCriteriaFromBackend.localidade) {
        const location = String(detectedCriteriaFromBackend.location || detectedCriteriaFromBackend.localidade)
        ctx.setBasicInfoFields(prev => ({ ...prev, localidade: location }))
        ctx.setDetectedCriteria(prev => ({ ...prev, localizacao: location }))
        ctx.highlightField('localizacao')
      }
      
      if (detectedCriteriaFromBackend.manager || detectedCriteriaFromBackend.gestor) {
        const manager = String(detectedCriteriaFromBackend.manager || detectedCriteriaFromBackend.gestor)
        ctx.setBasicInfoFields(prev => ({ ...prev, gestor: manager }))
        ctx.setDetectedCriteria(prev => ({ ...prev, gestorArea: manager }))
        ctx.highlightField('gestor')
      }
      
      // Salary
      if (detectedCriteriaFromBackend.salary_min || detectedCriteriaFromBackend.min_salary) {
        const minSalary = detectedCriteriaFromBackend.salary_min || detectedCriteriaFromBackend.min_salary
        ctx.setSalaryInfo(prev => ({ ...prev, minSalary: String(minSalary) }))
        ctx.highlightField('minSalary')
      }
      if (detectedCriteriaFromBackend.salary_max || detectedCriteriaFromBackend.max_salary) {
        const maxSalary = detectedCriteriaFromBackend.salary_max || detectedCriteriaFromBackend.max_salary
        ctx.setSalaryInfo(prev => ({ ...prev, maxSalary: String(maxSalary) }))
        ctx.highlightField('maxSalary')
      }

      if (ctx.currentStage === 'salary') {
        const salaryDetectedFields: Array<{ label: string; value: string; confidence?: "high" | "medium" | "low" }> = []
        const detectedMin = detectedCriteriaFromBackend.salary_min || detectedCriteriaFromBackend.min_salary
        const detectedMax = detectedCriteriaFromBackend.salary_max || detectedCriteriaFromBackend.max_salary
        if (detectedMin) salaryDetectedFields.push({ label: "Salário Mínimo", value: `${formatBRL(Number(detectedMin))}`, confidence: "high" })
        if (detectedMax) salaryDetectedFields.push({ label: "Salário Máximo", value: `${formatBRL(Number(detectedMax))}`, confidence: "high" })
        if (detectedCriteriaFromBackend.bonus_min) salaryDetectedFields.push({ label: "Bônus Mínimo", value: `${detectedCriteriaFromBackend.bonus_min}%`, confidence: "medium" })
        if (detectedCriteriaFromBackend.bonus_max) salaryDetectedFields.push({ label: "Bônus Máximo", value: `${detectedCriteriaFromBackend.bonus_max}%`, confidence: "medium" })

        if (salaryDetectedFields.length > 0) {
          const salaryDetectedMsg: Message = {
            id: `salary-detected-${Date.now()}`,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            messageType: 'detected-fields',
            detectedFields: salaryDetectedFields
          }
          ctx.setMessages(prev => [...prev, salaryDetectedMsg])
        }
      }
      
      // Technical skills
      if (detectedCriteriaFromBackend.technical_skills && Array.isArray(detectedCriteriaFromBackend.technical_skills)) {
        const newSkills = detectedCriteriaFromBackend.technical_skills as string[]
        newSkills.forEach((skill: string, index: number) => {
          if (!ctx.technicalSkills.find(s => s.name.toLowerCase() === skill.toLowerCase())) {
            ctx.setTechnicalSkills(prev => [
              ...prev,
              {
                id: `smart-skill-${Date.now()}-${index}`,
                name: skill,
                level: 'Intermediário' as const,
                required: true,
                category: 'tool' as const,
                weight: 3
              }
            ])
          }
        })
        if (newSkills.length > 0) {
          ctx.highlightField('skills')
        }
      }
      
      // Behavioral competencies
      if (detectedCriteriaFromBackend.behavioral_competencies && Array.isArray(detectedCriteriaFromBackend.behavioral_competencies)) {
        const newComps = detectedCriteriaFromBackend.behavioral_competencies as string[]
        newComps.forEach((comp: string) => {
          const existing = ctx.behavioralCompetencies.find(c => c.name.toLowerCase() === comp.toLowerCase())
          if (existing && !existing.enabled) {
            ctx.setBehavioralCompetencies(prev => prev.map(c => 
              c.name.toLowerCase() === comp.toLowerCase() ? { ...c, enabled: true } : c
            ))
          }
        })
        if (newComps.length > 0) {
          ctx.highlightField('competencias')
        }
      }

      if (ctx.currentStage === 'competencies') {
        const compDetectedFields: Array<{ label: string; value: string; confidence?: "high" | "medium" | "low" }> = []
        const detectedTechSkills = detectedCriteriaFromBackend.technical_skills || detectedCriteriaFromBackend.required_skills || detectedCriteriaFromBackend.competenciasTecnicas || []
        const detectedBehavSkills = detectedCriteriaFromBackend.behavioral_competencies || detectedCriteriaFromBackend.competenciasComportamentais || []

        if (Array.isArray(detectedTechSkills) && detectedTechSkills.length > 0) {
          compDetectedFields.push({ label: "Skills Técnicas", value: detectedTechSkills.slice(0, 5).join(", "), confidence: "high" })
        }
        if (Array.isArray(detectedBehavSkills) && detectedBehavSkills.length > 0) {
          compDetectedFields.push({ label: "Competências Comportamentais", value: detectedBehavSkills.slice(0, 3).join(", "), confidence: "medium" })
        }

        if (compDetectedFields.length > 0) {
          const compDetectedMsg: Message = {
            id: `comp-detected-${Date.now()}`,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            messageType: 'detected-fields',
            detectedFields: compDetectedFields
          }
          ctx.setMessages(prev => [...prev, compDetectedMsg])
        }
      }
      
      if (detectedCriteriaFromBackend.is_affirmative !== undefined) {
        const isAffirmative = detectedCriteriaFromBackend.is_affirmative as boolean
        ctx.setDetectedCriteria(prev => ({ ...prev, isAffirmative }))
        ctx.setJobConfig(prev => ({ ...prev, isAffirmative }))
      }
      
      // Responsibilities / Responsabilidades
      if (detectedCriteriaFromBackend.responsibilities && Array.isArray(detectedCriteriaFromBackend.responsibilities)) {
        const newResponsibilities = detectedCriteriaFromBackend.responsibilities as string[]
        if (newResponsibilities.length > 0) {
          ctx.setDetectedCriteria(prev => ({
            ...prev,
            responsabilidades: [...new Set([...(prev.responsabilidades || []), ...newResponsibilities])]
          }))
          ctx.highlightField('responsabilidades')
        }
      }
      
      // Helper function for case-insensitive deduplication while preserving original casing
      const deduplicateCaseInsensitive = (existing: string[], newItems: string[]): string[] => {
        const seen = new Map<string, string>()
        // Add existing items first
        existing.forEach(item => {
          const key = item.toLowerCase()
          if (!seen.has(key)) seen.set(key, item)
        })
        // Add new items only if not already present (case-insensitive)
        newItems.forEach(item => {
          const key = item.toLowerCase()
          if (!seen.has(key)) seen.set(key, item)
        })
        return Array.from(seen.values())
      }
      
      // Required skills (also maps to technical skills)
      if (detectedCriteriaFromBackend.required_skills && Array.isArray(detectedCriteriaFromBackend.required_skills)) {
        const newSkills = detectedCriteriaFromBackend.required_skills as string[]
        newSkills.forEach((skill: string, index: number) => {
          if (!ctx.technicalSkills.find(s => s.name.toLowerCase() === skill.toLowerCase())) {
            ctx.setTechnicalSkills(prev => [
              ...prev,
              {
                id: `smart-skill-${Date.now()}-${index}`,
                name: skill,
                level: 'Intermediário' as const,
                required: true,
                category: 'tool' as const,
                weight: 3
              }
            ])
          }
        })
        // Also update detected criteria for panel display
        if (newSkills.length > 0) {
          ctx.setDetectedCriteria(prev => ({
            ...prev,
            competenciasTecnicas: deduplicateCaseInsensitive(prev.competenciasTecnicas || [], newSkills)
          }))
          ctx.highlightField('skills')
        }
      }
      
      // Soft skills (also maps to behavioral competencies display)
      if (detectedCriteriaFromBackend.soft_skills && Array.isArray(detectedCriteriaFromBackend.soft_skills)) {
        const newComps = detectedCriteriaFromBackend.soft_skills as string[]
        if (newComps.length > 0) {
          ctx.setDetectedCriteria(prev => ({
            ...prev,
            competenciasComportamentais: deduplicateCaseInsensitive(prev.competenciasComportamentais || [], newComps)
          }))
          ctx.highlightField('competencias')
        }
      }
    }
    
    // Process tool_results if present (e.g., salary benchmark, skills suggestions)
    if (toolResults.length > 0) {
      (toolResults as Array<{ tool: string; result?: { skills?: { name?: string; level?: string; required?: boolean; category?: string; weight?: number }[]; [key: string]: unknown }; [key: string]: unknown }>).forEach((toolResult) => {
        if (toolResult.tool === 'salary_benchmark' && toolResult.result) {
          ctx.setCompensationAnalysis(toolResult.result as unknown as CompensationAnalysisResult)
        }
        if (toolResult.tool === 'skills_suggestion' && toolResult.result?.skills) {
          const suggestedSkills = toolResult.result.skills
          suggestedSkills.forEach((skill, index: number) => {
            if (!ctx.technicalSkills.find(s => s.name.toLowerCase() === skill.name?.toLowerCase())) {
              ctx.setTechnicalSkills(prev => [...prev, {
                  id: `tool-skill-${Date.now()}-${index}`,
                  name: skill.name || '',
                  level: ((skill.level === 'Expert' ? 'Avançado' : skill.level) || 'Intermediário') as 'Básico' | 'Intermediário' | 'Avançado',
                  required: skill.required ?? true,
                  category: ((['language', 'framework', 'database', 'tool', 'general'] as string[]).includes(skill.category || '') ? (skill.category as 'language' | 'framework' | 'database' | 'tool' | 'general') : 'tool'),
                  weight: skill.weight || 3
                }
              ])
            }
          })
        }
        // Process JD enrichment data
        if (toolResult.tool === 'generate_enriched_jd' && toolResult.result) {
          const er = toolResult.result as Record<string, unknown>
          const enrichedData: EnrichedJDData = {
            sections: (er.sections || []) as EnrichedJDData['sections'],
            compensation: er.compensation as EnrichedJDData['compensation'],
            wsiQualityScore: (er.wsi_quality_score ?? er.wsiQualityScore ?? 0) as number,
            overallCompleteness: (er.overall_completeness ?? er.overallCompleteness ?? 0) as number,
            totalSuggestions: (er.total_suggestions ?? er.totalSuggestions ?? 0) as number
          }
          ctx.setEnrichedJDData(enrichedData)
          ctx.setIsLoadingEnrichment(false)
        }
      })
    }
    
    // Handle action results from WizardActionExecutor
    if (orchestratorResult.action_executed && orchestratorResult.action_type) {
      
      // Apply draft_updates to form fields if present
      if (orchestratorResult.draft_updates && Object.keys(orchestratorResult.draft_updates).length > 0) {
        const updates = orchestratorResult.draft_updates as Record<string, unknown>
        if (updates.cargo || updates.job_title || updates.title) {
          const title = String(updates.cargo || updates.job_title || updates.title)
          ctx.setBasicInfoFields(prev => ({ ...prev, cargo: title }))
          ctx.highlightField('cargo')
        }
        if (updates.area || updates.department) {
          const dept = String(updates.area || updates.department)
          ctx.setBasicInfoFields(prev => ({ ...prev, area: dept }))
          ctx.highlightField('departamento')
        }
        if (updates.localidade || updates.location) {
          const location = String(updates.localidade || updates.location)
          ctx.setBasicInfoFields(prev => ({ ...prev, localidade: location }))
          ctx.highlightField('localizacao')
        }
        if (updates.modeloTrabalho || updates.work_model) {
          const workModel = String(updates.modeloTrabalho || updates.work_model)
          ctx.setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: workModel }))
          ctx.highlightField('modeloTrabalho')
        }
        if (updates.gestor || updates.manager) {
          const manager = String(updates.gestor || updates.manager)
          ctx.setBasicInfoFields(prev => ({ ...prev, gestor: manager }))
          ctx.highlightField('gestor')
        }
      }
      
      // Add action result message to chat
      const actionResultMsg: Message = {
        id: `action-result-${Date.now()}`,
        role: 'assistant',
        content: liaMessage,
        timestamp: new Date(),
        messageType: 'action-result',
        actionType: orchestratorResult.action_type,
        actionResult: (orchestratorResult.action_result || {}) as Record<string, unknown>,
        isTyping: true
      }
      
      if (ctx.conversationMemory.conversationId) {
        ctx.conversationMemory.addMessage('assistant', liaMessage).catch(() => {})
      }
      
      setTimeout(() => {
        ctx.setMessages(prev => [...prev, actionResultMsg])
        ctx.typeText(liaMessage, actionResultMsg.id)
      }, 200)
      
      return
    }
    
    // Handle automatic stage transition
    if (autoTransition && nextStage) {
      const frontendStage = getFrontendStageFromBackend(nextStage)
      if (frontendStage && frontendStage !== ctx.currentStage) {
        setTimeout(() => {
          ctx.setCurrentStage(frontendStage as WizardStage)
        }, 1500)
      }
    }
    
    // Handle awaiting_confirmation from backend - show proactive message asking to advance
    const awaitingConfirmation = orchestratorResult.awaiting_confirmation
    const shouldShowProactiveConfirmation = awaitingConfirmation && 
      ctx.currentStage === 'input-evaluation' && 
      !ctx.awaitingStageAdvanceConfirmation && // Not already awaiting confirmation
      Object.keys(detectedCriteriaFromBackend).length > 0 // Has detected criteria
    
    if (shouldShowProactiveConfirmation) {
      
      // Build summary of detected fields (support both snake_case and camelCase)
      const detectedFields: string[] = []
      const title = detectedCriteriaFromBackend.job_title || detectedCriteriaFromBackend.title || detectedCriteriaFromBackend.cargo
      const seniority = detectedCriteriaFromBackend.seniority || detectedCriteriaFromBackend.senioridade
      const department = detectedCriteriaFromBackend.department || detectedCriteriaFromBackend.departamento || detectedCriteriaFromBackend.area
      const techSkills = detectedCriteriaFromBackend.technical_skills || detectedCriteriaFromBackend.competenciasTecnicas || detectedCriteriaFromBackend.required_skills || []
      const salaryMin = detectedCriteriaFromBackend.salary_min || detectedCriteriaFromBackend.salarioMin
      const salaryMax = detectedCriteriaFromBackend.salary_max || detectedCriteriaFromBackend.salarioMax
      
      if (title) detectedFields.push(`Cargo: **${title}**`)
      if (seniority) detectedFields.push(`Senioridade: **${seniority}**`)
      if (department) detectedFields.push(`Departamento: **${department}**`)
      if ((techSkills as unknown[])?.length > 0) detectedFields.push(`Skills Técnicas: **${(techSkills as string[]).slice(0, 3).join(', ')}**`)
      if (salaryMin && salaryMax) {
        const minFormatted = typeof salaryMin === 'number' ? formatBRL(salaryMin) : `${CURRENCY_SYMBOL} ${salaryMin}`
        const maxFormatted = typeof salaryMax === 'number' ? formatBRL(salaryMax) : `${CURRENCY_SYMBOL} ${salaryMax}`
        detectedFields.push(`Faixa Salarial: **${minFormatted} - ${maxFormatted}**`)
      }
      
      const summaryText = detectedFields.length > 0 
        ? `\n\n📋 **Critérios detectados:**\n${detectedFields.map(f => `• ${f}`).join('\n')}`
        : ''
      
      // Append proactive question to LIA's response
      const enhancedMessage = `${liaMessage}${summaryText}\n\n✨ Quer que eu avance para a etapa de **Enriquecimento da Vaga**, onde vou analisar dados de mercado e sugerir melhorias para a descrição?`
      
      // Build structured detected fields for DetectedFieldsCard
      const detectedFieldsStructured: Array<{ label: string; value: string; confidence?: "high" | "medium" | "low" }> = []
      if (title) detectedFieldsStructured.push({ label: "Cargo", value: String(title), confidence: "high" })
      if (seniority) detectedFieldsStructured.push({ label: "Senioridade", value: String(seniority), confidence: "high" })
      if (department) detectedFieldsStructured.push({ label: "Departamento", value: String(department), confidence: "medium" })
      if ((techSkills as unknown[])?.length > 0) detectedFieldsStructured.push({ label: "Skills Técnicas", value: (techSkills as string[]).slice(0, 5).join(", "), confidence: "high" })
      if (salaryMin && salaryMax) {
        const minF = typeof salaryMin === 'number' ? formatBRL(salaryMin) : `${CURRENCY_SYMBOL} ${salaryMin}`
        const maxF = typeof salaryMax === 'number' ? formatBRL(salaryMax) : `${CURRENCY_SYMBOL} ${salaryMax}`
        detectedFieldsStructured.push({ label: "Faixa Salarial", value: `${minF} - ${maxF}`, confidence: "medium" })
      }

      // Set awaiting confirmation state
      ctx.setAwaitingStageAdvanceConfirmation('jd-enrichment')
      
      // Show enhanced message with proactive question
      const proactiveMsg: Message = {
        id: `lia-orchestrator-${Date.now()}`,
        role: 'assistant',
        content: enhancedMessage,
        timestamp: new Date(),
        isTyping: true,
        awaitingStageConfirmation: 'jd-enrichment',
        detectedFieldsData: detectedFieldsStructured
      }
      
      if (ctx.conversationMemory.conversationId) {
        ctx.conversationMemory.addMessage('assistant', enhancedMessage).catch(() => {})
      }
      
      setTimeout(() => {
        ctx.setMessages(prev => [...prev, proactiveMsg])
        ctx.typeText(enhancedMessage, proactiveMsg.id)
      }, 200)
      
      return // Show enhanced message instead of normal response
    }
    
    // Show orchestrator response
    const assistantMessage: Message = {
      id: `lia-orchestrator-${Date.now()}`,
      role: 'assistant',
      content: liaMessage,
      timestamp: new Date(),
      isTyping: true
    }
    
    // Save assistant message to conversation memory
    if (ctx.conversationMemory.conversationId) {
      ctx.conversationMemory.addMessage('assistant', liaMessage).catch(() => {})
    }
    
    setTimeout(() => {
      ctx.setMessages(prev => [...prev, assistantMessage])
      ctx.typeText(liaMessage, assistantMessage.id)
    }, 200)
  }, [ctx])

  // Fast Track: Detect ctx.user intent from message
  const detectFastTrackIntent = (content: string): 'fast_track' | 'from_scratch' | 'confirm' | 'adjust' | 'select' | 'criteria' | null => {
    const lowerContent = content.toLowerCase()
    
    // Detect confirmation
    if (lowerContent.includes('confirmar') || lowerContent.includes('publicar') || lowerContent === 'sim') {
      return 'confirm'
    }
    
    // Detect fast track intent
    if (lowerContent.includes('aproveitar') || lowerContent.includes('anterior') || 
        lowerContent.includes('reutilizar') || lowerContent.includes('copiar') ||
        lowerContent.includes('usar vaga') || lowerContent.includes('vaga passada')) {
      return 'fast_track'
    }
    
    // Detect create from scratch
    if (lowerContent.includes('do zero') || lowerContent.includes('criar nova') || 
        lowerContent.includes('nova vaga') || lowerContent.includes('começar')) {
      return 'from_scratch'
    }
    
    // Detect selection by number
    if (/^[1-9]$/.test(content.trim()) || /^(um|dois|três|quatro|cinco|seis|sete|oito|nove|dez)$/i.test(content.trim())) {
      return 'select'
    }
    
    // Detect adjustment request
    if (lowerContent.includes('mudar') || lowerContent.includes('alterar') || 
        lowerContent.includes('ajustar') || lowerContent.includes('salário para') ||
        lowerContent.includes('modelo') || lowerContent.includes('local para')) {
      return 'adjust'
    }
    
    // Check if it contains search criteria (title, department, manager)
    if (ctx.fastTrackState === 'collecting_criteria' || ctx.fastTrackState === 'initial') {
      return 'criteria'
    }
    
    return null
  }

  return {
    generateWSIQuestions,
    toggleWSIQuestionSelection,
    updateWSIQuestionExpectedAnswer,
    updateWSIQuestionCorrectOption,
    deleteWSIQuestion,
    addCustomQuestion,
    initializeCalibrationCriteria,
    generateCalibrationCandidates,
    handleApproveCandidate,
    handleRejectCandidate,
    moveToNextCandidate,
    generateMoreCalibrationCandidates,
    addCalibrationCriterion,
    removeCalibrationCriterion,
    reorderCalibrationCriteria,
    handleFastTrackVacancySelect,
    handleFastTrackSearch,
    handleFastTrackPublish,
    parseFastTrackAdjustment,
    buildCollectedData,
    processOrchestratorResponse,
    detectFastTrackIntent,
  }
}
