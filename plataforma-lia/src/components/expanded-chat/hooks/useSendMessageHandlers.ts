"use client"

import { useCallback, useEffect } from "react"
import type React from "react"
import type {
  orchestrateWizardMessage,
  orchestratorProcess,
  WizardOrchestratorResponse,
  VacancySearchCriteria,
  VacancyAdjustments,
  liaApi,
} from "@/services/lia-api"
import type { ParecerLIAData } from "@/components/chat/parecer-lia-card"
import type { WizardStage } from "../config"
import type {
  Message,
  WizardMode,
  WizardDraftData,
  FastTrackState,
} from "../types"
import type {
  BasicInfoFields,
  DetectedCriteria,
  TechnicalSkill,
  BehavioralCompetency,
  SalaryInfo,
  WSIQuestion,
} from "../ExpandedChatContext"
import type { WSIQuestionCandidate } from "../types"
import type { useContextSwitching } from "./useContextSwitching"
import type { useConversationMemory } from "./useConversationMemory"
import type { useWizardAnalytics } from "./useWizardAnalytics"
import type { useToolCalling } from "./useToolCalling"
import type { useLearning } from "./useLearning"
import type { ToolCall } from "./useToolCalling"
import type { CompensationAnalysisResult } from "@/components/job-creation/compensation-analysis-panel"
import type { TechnicalSkillSuggestion, BehavioralCompetencySuggestion } from "@/components/job-creation/competencies-chat-message"
import type { JobConfig } from "./usePublishingState"
import type { FieldChange } from "./useChatSync"
import type { VacancySummary } from "@/components/job-creation/vacancy-search-results"
import type { VacancyFullDetails } from "@/components/job-creation/vacancy-full-summary"
import type { EvaluationStepResponse } from "@/hooks/use-job-wizard-backend"
import { useSendMessageInterceptors } from './useSendMessageInterceptors'
import { useSendMessageAPIDispatchers } from './useSendMessageAPIDispatchers'

interface CompetencySuggestions {
  technicalSkills: TechnicalSkillSuggestion[]
  behavioralCompetencies: BehavioralCompetencySuggestion[]
}

export interface SendMessageHandlersContext {
  isOpen: boolean
  onClose: () => void
  isJobCreationMode: boolean
  inline: boolean
  onJobCreated?: (jobId: string, jobData?: Record<string, unknown>) => void
  onOrchestratedMessage?: (msg: string) => Promise<{ content: string; ui_action?: string | null; ui_action_params?: Record<string, unknown> }>
  onMessagesUpdate?: (messages: Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: Date }>) => void
  inputValue: string
  inputRef: React.RefObject<HTMLInputElement | null>
  setInputValue: (value: string) => void
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  isLoading: boolean
  setIsLoading: (val: boolean) => void
  isTypingEffect: boolean
  conversationId: string | null
  setConversationId: (id: string | null) => void
  user: { id?: string; email?: string; company?: string } | null
  resolvedCompanyId: string | null
  currentStage: WizardStage
  setCurrentStage: (stage: WizardStage) => void
  wizardMode: WizardMode
  setWizardMode: (mode: WizardMode) => void
  isInJobCreationMode: boolean
  awaitingStageAdvanceConfirmation: string | null
  setAwaitingStageAdvanceConfirmation: (val: string | null) => void
  awaitingDraftChoice: boolean
  setAwaitingDraftChoice: (val: boolean) => void
  awaitingCalibrationChoice: boolean
  setAwaitingCalibrationChoice: (val: boolean) => void
  activeToolConfirmationMessageId: string | null
  setActiveToolConfirmationMessageId: (val: string | null) => void
  awaitingWSIRegenerationConfirmation: boolean
  setAwaitingWSIRegenerationConfirmation: (val: boolean) => void
  awaitingSensitiveFieldsConfirmation: boolean
  setAwaitingSensitiveFieldsConfirmation: (val: boolean) => void
  pendingDraftData: Partial<WizardDraftData> | null | Record<string, unknown>
  setPendingDraftData: (data: Partial<WizardDraftData> | null) => void
  setHasAppliedRestoredDraft: (val: boolean) => void
  applyPendingDraft: () => void
  clearWizardDraft: () => void
  calibrationComplete: boolean
  setCalibrationComplete: (val: boolean) => void
  approvedCandidates: string[]
  rejectedCandidates: string[]
  setIsPanelOpen: (val: boolean) => void
  localCandidateCount: number
  setShowCalibrationModal: (val: boolean) => void
  fastTrack: ReturnType<typeof import("@/hooks/useFastTrack").useFastTrack>
  fastTrackState: FastTrackState
  setFastTrackState: (state: FastTrackState) => void
  fastTrackSearchResults: VacancySummary[]
  setFastTrackSearchResults: (results: VacancySummary[]) => void
  fastTrackSelectedVacancy: VacancyFullDetails | null
  setFastTrackSelectedVacancy: (vacancy: VacancyFullDetails | null) => void
  fastTrackAdjustments: VacancyAdjustments
  setFastTrackAdjustments: React.Dispatch<React.SetStateAction<VacancyAdjustments>>
  fastTrackSearchCriteria: VacancySearchCriteria
  setFastTrackSearchCriteria: (criteria: VacancySearchCriteria) => void
  isSearchingVacancies: boolean
  setIsSearchingVacancies: (val: boolean) => void
  setWizardFastTrackSourceJobId: (id: string | null) => void
  wizardFastTrackSourceJobId: string | null
  fastTrackSuggestionsShownTracked: boolean
  setAwaitingFastTrackSelection: (val: boolean) => void
  awaitingFastTrackSelection: boolean
  fastTrackAppliedData: { gestor: string; localidade: string; sourceJobTitle: string } | null
  setFastTrackAppliedData: (data: { gestor: string; localidade: string; sourceJobTitle: string } | null) => void
  setFastTrackOriginalCompetencies: (data: { technicalSkillNames: string[]; behavioralCompetencyNames: string[] }) => void
  setWsiRegenerationPrompted: (val: boolean) => void
  setFastTrackMessageSent: (val: boolean) => void
  basicInfoFields: BasicInfoFields
  setBasicInfoFields: React.Dispatch<React.SetStateAction<BasicInfoFields>>
  detectedCriteria: DetectedCriteria
  setDetectedCriteria: React.Dispatch<React.SetStateAction<DetectedCriteria>>
  technicalSkills: TechnicalSkill[]
  setTechnicalSkills: React.Dispatch<React.SetStateAction<TechnicalSkill[]>>
  behavioralCompetencies: BehavioralCompetency[]
  setBehavioralCompetencies: React.Dispatch<React.SetStateAction<BehavioralCompetency[]>>
  salaryInfo: SalaryInfo
  setSalaryInfo: React.Dispatch<React.SetStateAction<SalaryInfo>>
  wsiQuestions: WSIQuestion[]
  setWsiQuestions: React.Dispatch<React.SetStateAction<WSIQuestion[]>>
  wsiCandidates: WSIQuestionCandidate[]
  setWsiCandidates: React.Dispatch<React.SetStateAction<WSIQuestionCandidate[]>>
  setCompetencySuggestions: (val: CompetencySuggestions) => void
  generatedJobDescription: string
  setGeneratedJobDescription: (val: string) => void
  compensationAnalysis: CompensationAnalysisResult | null
  setCompensationAnalysis: (val: CompensationAnalysisResult | null) => void
  setIsLoadingEnrichment: (val: boolean) => void
  setJobConfig: React.Dispatch<React.SetStateAction<JobConfig>>
  setInternalJobCreationMode: (val: boolean) => void
  setDynamicInitialMessage: (val: string | null) => void
  setDisplayedText: (val: string) => void
  buildCollectedData: () => Record<string, unknown>
  processOrchestratorResponse: (result: WizardOrchestratorResponse, processingMessageId: string) => Promise<void>
  generateParecerData: () => ParecerLIAData
  extractCriteriaFromText: (text: string) => DetectedCriteria
  typeText: (text: string, messageId: string) => void
  generateLLMContext: () => string
  goToNextStage: () => void
  handleFastTrackVacancySelect: (vacancyId: string) => Promise<void>
  handleFastTrackSearch: (criteria: VacancySearchCriteria) => Promise<void>
  handleFastTrackPublish: () => Promise<void>
  parseFastTrackAdjustment: (content: string) => VacancyAdjustments | null
  detectFastTrackIntent: (content: string) => "fast_track" | "from_scratch" | "confirm" | "adjust" | "select" | "criteria" | null
  generateCriteriaResponse: (criteria: DetectedCriteria) => string
  callEvaluationStep: (content: string, context?: { job_title?: string; seniority?: string; department?: string; location?: string; work_model?: string; technical_skills?: string[]; behavioral_skills?: string[] }) => Promise<EvaluationStepResponse | null>
  trackFieldChange: (change: Omit<FieldChange, 'id' | 'timestamp'>) => void
  contextSwitching: ReturnType<typeof useContextSwitching>
  conversationMemory: ReturnType<typeof useConversationMemory>
  analytics: ReturnType<typeof useWizardAnalytics>
  toolCalling: ReturnType<typeof useToolCalling>
  learning: ReturnType<typeof useLearning>
}

export function useSendMessageHandlers(ctx: SendMessageHandlersContext) {
  const {
    isOpen,
    onClose,
    inputValue,
    inputRef,
    setInputValue,
    messages,
    setMessages,
    isLoading,
    setIsLoading,
    isTypingEffect,
    isInJobCreationMode,
  } = ctx

  const interceptors = useSendMessageInterceptors(ctx)
  const dispatchers = useSendMessageAPIDispatchers(ctx)

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading || isTypingEffect) return

    interceptors._handleContextSwitch(content)

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setInputValue("")

    if (await interceptors._handleStageAdvanceConfirmation(content)) return
    if (await interceptors._handleDraftChoice(content)) return
    if (await interceptors._handleCalibrationChoice(content)) return
    if (await interceptors._handlePendingToolConfirmation(content)) return
    if (await interceptors._handleWSIRegenConfirmation(content)) return
    if (await interceptors._handleSensitiveFieldsConfirmation(content)) return
    if (await interceptors._handleFastTrackSuggestions(content)) return
    if (await interceptors._handleFastTrackFlow(content)) return
    if (await interceptors._handleCompensationMessage(content)) return
    if (interceptors._handleLocalCommands(content)) return

    const processingMessageId = `processing-${Date.now()}`
    const processingMessage: Message = {
      id: processingMessageId,
      role: 'assistant',
      content: '🧠 Analisando sua mensagem...',
      timestamp: new Date(),
      isProcessing: true,
      processingState: 'thinking'
    }
    setMessages(prev => [...prev, processingMessage])

    if (isInJobCreationMode) {
      await dispatchers._handleWizardAPICall(content, processingMessageId)
      return
    }

    await dispatchers._handleGeneralAPICall(content, processingMessageId)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage(inputValue)
    }
  }

  const handleModalKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape' && isOpen) {
      e.preventDefault()
      onClose()
    }
  }, [isOpen, onClose])

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleModalKeyDown)
      return () => document.removeEventListener('keydown', handleModalKeyDown)
    }
  }, [isOpen, handleModalKeyDown])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      const timer = setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [isOpen, inputRef])

  const handleQuickSuggestion = (suggestion: string) => {
    if (suggestion === "Anexar JD") {
      alert("Funcionalidade de anexar JD será implementada")
    } else if (suggestion === "Usar anterior") {
      alert("Funcionalidade de usar vaga anterior será implementada")
    } else {
      handleSendMessage(suggestion)
    }
  }

  return {
    handleSendMessage,
    handleKeyDown,
    handleQuickSuggestion,
  }
}
