"use client"

import { useCallback, useEffect } from "react"
import type React from "react"
import {
  orchestrateWizardMessage,
  orchestratorProcess,
  type WizardOrchestratorResponse,
  type VacancySearchCriteria,
  type VacancyAdjustments,
  liaApi,
} from "@/services/lia-api"
import type { ParecerLIAData } from "@/components/chat/parecer-lia-card"
import {
  WIZARD_STAGES,
  INITIAL_JOB_CREATION_MESSAGE,
} from "../index"
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
import {
  handleStageAdvanceConfirmation,
  handleFastTrackSuggestions,
  handleFastTrackFlow,
  handleCompensationMessage,
  handleLocalCommands,
} from './useSendMessageHelpers'
import type { CompensationAnalysisResult } from "@/components/job-creation/compensation-analysis-panel"
import type { TechnicalSkillSuggestion, BehavioralCompetencySuggestion } from "@/components/job-creation/competencies-chat-message"
import type { JobConfig } from "./usePublishingState"
import type { FieldChange } from "./useChatSync"
import type { VacancySummary } from "@/components/job-creation/vacancy-search-results"
import type { VacancyFullDetails } from "@/components/job-creation/vacancy-full-summary"
import type { EvaluationStepResponse } from "@/hooks/use-job-wizard-backend"

interface EvaluationStepResult {
  compensation_analysis?: CompensationAnalysisResult
  technical_skills?: Array<{
    name?: string
    level?: string
    weight?: number
    weight_justification?: string
    source?: string
    required?: boolean
    category?: string
  }>
  behavioral_competencies?: Array<{
    name?: string
    weight?: number
    justification?: string
    weight_justification?: string
    source?: string
  }>
  [key: string]: unknown
}

interface CompetencySuggestions {
  technicalSkills: TechnicalSkillSuggestion[]
  behavioralCompetencies: BehavioralCompetencySuggestion[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Context interface — everything the hook needs from the parent component
// ─────────────────────────────────────────────────────────────────────────────

export interface SendMessageHandlersContext {
  // ─── Props ───────────────────────────────────────────────────────────────────
  isOpen: boolean
  onClose: () => void
  isJobCreationMode: boolean
  inline: boolean
  onJobCreated?: (jobId: string, jobData?: Record<string, unknown>) => void
  onOrchestratedMessage?: (msg: string) => Promise<{ content: string; ui_action?: string | null; ui_action_params?: Record<string, unknown> }>
  onMessagesUpdate?: (messages: Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: Date }>) => void

  // ─── Input ───────────────────────────────────────────────────────────────────
  inputValue: string
  inputRef: React.RefObject<HTMLInputElement | null>
  setInputValue: (value: string) => void

  // ─── Messages ────────────────────────────────────────────────────────────────
  messages: Message[]
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
  isLoading: boolean
  setIsLoading: (val: boolean) => void
  isTypingEffect: boolean
  conversationId: string | null
  setConversationId: (id: string | null) => void

  // ─── User ────────────────────────────────────────────────────────────────────
  user: { id?: string; email?: string; company?: string } | null

  // ─── Stage ───────────────────────────────────────────────────────────────────
  currentStage: WizardStage
  setCurrentStage: (stage: WizardStage) => void
  wizardMode: WizardMode
  setWizardMode: (mode: WizardMode) => void
  isInJobCreationMode: boolean

  // ─── Awaiting flags ──────────────────────────────────────────────────────────
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

  // ─── Draft ───────────────────────────────────────────────────────────────────
  pendingDraftData: Partial<WizardDraftData> | null | Record<string, unknown>
  setPendingDraftData: (data: Partial<WizardDraftData> | null) => void
  setHasAppliedRestoredDraft: (val: boolean) => void
  applyPendingDraft: () => void
  clearWizardDraft: () => void

  // ─── Calibration ─────────────────────────────────────────────────────────────
  calibrationComplete: boolean
  setCalibrationComplete: (val: boolean) => void
  approvedCandidates: string[]
  rejectedCandidates: string[]
  setIsPanelOpen: (val: boolean) => void
  localCandidateCount: number
  setShowCalibrationModal: (val: boolean) => void

  // ─── Fast Track ──────────────────────────────────────────────────────────────
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

  // ─── Form fields ─────────────────────────────────────────────────────────────
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

  // ─── Salary / Compensation ───────────────────────────────────────────────────
  compensationAnalysis: CompensationAnalysisResult | null
  setCompensationAnalysis: (val: CompensationAnalysisResult | null) => void
  setIsLoadingEnrichment: (val: boolean) => void

  // ─── Job config ──────────────────────────────────────────────────────────────
  setJobConfig: React.Dispatch<React.SetStateAction<JobConfig>>
  setInternalJobCreationMode: (val: boolean) => void
  setDynamicInitialMessage: (val: string | null) => void

  // ─── UI state ────────────────────────────────────────────────────────────────
  setDisplayedText: (val: string) => void

  // ─── Functions ───────────────────────────────────────────────────────────────
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

  // ─── Hooks ───────────────────────────────────────────────────────────────────
  contextSwitching: ReturnType<typeof useContextSwitching>
  conversationMemory: ReturnType<typeof useConversationMemory>
  analytics: ReturnType<typeof useWizardAnalytics>
  toolCalling: ReturnType<typeof useToolCalling>
  learning: ReturnType<typeof useLearning>
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook
// ─────────────────────────────────────────────────────────────────────────────

export function useSendMessageHandlers(ctx: SendMessageHandlersContext) {
  const {
    isOpen,
    onClose,
    isJobCreationMode,
    onOrchestratedMessage,
    inputValue,
    inputRef,
    setInputValue,
    messages,
    setMessages,
    isLoading,
    setIsLoading,
    isTypingEffect,
    conversationId,
    setConversationId,
    user,
    currentStage,
    setCurrentStage,
    wizardMode,
    setWizardMode,
    isInJobCreationMode,
    awaitingStageAdvanceConfirmation,
    setAwaitingStageAdvanceConfirmation,
    awaitingDraftChoice,
    setAwaitingDraftChoice,
    awaitingCalibrationChoice,
    setAwaitingCalibrationChoice,
    activeToolConfirmationMessageId,
    setActiveToolConfirmationMessageId,
    awaitingWSIRegenerationConfirmation,
    setAwaitingWSIRegenerationConfirmation,
    awaitingSensitiveFieldsConfirmation,
    setAwaitingSensitiveFieldsConfirmation,
    pendingDraftData,
    setPendingDraftData,
    setHasAppliedRestoredDraft,
    applyPendingDraft,
    clearWizardDraft,
    calibrationComplete,
    setCalibrationComplete,
    approvedCandidates,
    rejectedCandidates,
    setIsPanelOpen,
    localCandidateCount,
    setShowCalibrationModal,
    fastTrack,
    fastTrackState,
    setFastTrackState,
    fastTrackSearchResults,
    setFastTrackSearchResults,
    fastTrackSelectedVacancy,
    setFastTrackSelectedVacancy,
    fastTrackAdjustments,
    setFastTrackAdjustments,
    fastTrackSearchCriteria,
    setFastTrackSearchCriteria,
    isSearchingVacancies,
    setIsSearchingVacancies,
    setWizardFastTrackSourceJobId,
    wizardFastTrackSourceJobId,
    fastTrackSuggestionsShownTracked,
    setAwaitingFastTrackSelection,
    awaitingFastTrackSelection,
    fastTrackAppliedData,
    setFastTrackAppliedData,
    setFastTrackOriginalCompetencies,
    setWsiRegenerationPrompted,
    setFastTrackMessageSent,
    basicInfoFields,
    setBasicInfoFields,
    detectedCriteria,
    setDetectedCriteria,
    technicalSkills,
    setTechnicalSkills,
    behavioralCompetencies,
    setBehavioralCompetencies,
    salaryInfo,
    setSalaryInfo,
    wsiQuestions,
    setWsiQuestions,
    wsiCandidates,
    setWsiCandidates,
    setCompetencySuggestions,
    generatedJobDescription,
    setGeneratedJobDescription,
    compensationAnalysis,
    setCompensationAnalysis,
    setIsLoadingEnrichment,
    setJobConfig,
    setInternalJobCreationMode,
    setDynamicInitialMessage,
    setDisplayedText,
    buildCollectedData,
    processOrchestratorResponse,
    generateParecerData,
    extractCriteriaFromText,
    typeText,
    generateLLMContext,
    goToNextStage,
    handleFastTrackVacancySelect,
    handleFastTrackSearch,
    handleFastTrackPublish,
    parseFastTrackAdjustment,
    detectFastTrackIntent,
    generateCriteriaResponse,
    callEvaluationStep,
    trackFieldChange,
    contextSwitching,
    conversationMemory,
    analytics,
    toolCalling,
    learning,
  } = ctx

  // ═══════════════════════════════════════════════════════════════════════════
  // handleSendMessage — Extracted interceptor handlers (Sprint 4.6)
  // Each returns boolean/Promise<boolean>: true = handled, false = continue.
  // ═══════════════════════════════════════════════════════════════════════════

  const _handleContextSwitch = (content: string): void => {
    const detectedContext = contextSwitching.detectContextFromMessage(content)
    if (!detectedContext || detectedContext === contextSwitching.currentContext) return
    if (contextSwitching.isInWizardContext) {
      contextSwitching.saveWizardSnapshot({
        stage: currentStage,
        basicInfoFields: basicInfoFields as unknown as Record<string, unknown>,
        technicalSkills,
        behavioralCompetencies,
        salaryInfo: salaryInfo as unknown as Record<string, unknown>,
        wsiQuestions,
        detectedCriteria: detectedCriteria as unknown as Record<string, unknown>,
        generatedJobDescription,
        fastTrackSourceJobId: wizardFastTrackSourceJobId,
      })
    } else {
      contextSwitching.saveGeneralSnapshot({
        conversationId: conversationMemory.conversationId || conversationId,
        lastMessageIndex: messages.length,
      })
    }
    if (detectedContext === 'wizard') contextSwitching.switchToWizard()
    else if (detectedContext === 'fast_track') contextSwitching.switchToFastTrack()
    else if (detectedContext === 'general') contextSwitching.switchToGeneral()
  }

  const _handleStageAdvanceConfirmation = (content: string) => handleStageAdvanceConfirmation(content, ctx)

  // ── Interceptor 2: awaiting draft choice ──────────────────────────────────
  const _handleDraftChoice = async (content: string): Promise<boolean> => {
    if (!awaitingDraftChoice) return false
    const lowerContent = content.toLowerCase().trim()

    if (lowerContent.includes('continuar') || lowerContent.includes('retomar') ||
        lowerContent.includes('prosseguir') || lowerContent.includes('sim')) {
      applyPendingDraft()
      const currentStageConfig = WIZARD_STAGES.find(s => s.id === pendingDraftData?.currentStage)
      const stageMessage = currentStageConfig?.liaMessage || 'Continuando de onde você parou...'
      const liaMessage: Message = {
        id: `lia-continue-draft-${Date.now()}`,
        role: 'assistant',
        content: `Perfeito! Vou retomar de onde você parou. 📋\n\n${stageMessage}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, liaMessage])
      setIsPanelOpen(true)
      return true
    }

    if (lowerContent.includes('zero') || lowerContent.includes('nova') ||
        lowerContent.includes('novo') || lowerContent.includes('descartar') ||
        lowerContent.includes('limpar') || lowerContent.includes('recomeçar')) {
      clearWizardDraft()
      setPendingDraftData(null)
      setAwaitingDraftChoice(false)
      setHasAppliedRestoredDraft(true)
      setCurrentStage('input-evaluation')
      setBasicInfoFields({ cargo: '', area: '', gestor: '', localidade: '', modeloTrabalho: '', tipoContrato: '' })
      setSalaryInfo({ minSalary: '', maxSalary: '', minBonus: '', maxBonus: '', bonusCriteria: '', benefits: [] })
      setTechnicalSkills([])
      setBehavioralCompetencies([])
      setWsiCandidates([])
      setGeneratedJobDescription('')
      const liaMessage: Message = {
        id: `lia-fresh-start-${Date.now()}`,
        role: 'assistant',
        content: 'Perfeito! Vamos criar uma nova vaga do zero. 🆕\n\nMe conte sobre a posição que você precisa preencher. Pode descrever livremente - cargo, responsabilidades, requisitos, área, modelo de trabalho... Eu vou extrair as informações automaticamente.\n\n💡 **Dica:** Quanto mais detalhes você fornecer, mais precisa será a vaga gerada.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, liaMessage])
      setIsPanelOpen(true)
      setWizardMode('create_from_scratch')
      return true
    }

    const clarifyMessage: Message = {
      id: `lia-clarify-${Date.now()}`,
      role: 'assistant',
      content: 'Não entendi sua escolha. Por favor, digite **"continuar"** para retomar o rascunho, ou **"começar do zero"** para descartar e criar uma nova vaga.',
      timestamp: new Date()
    }
    setMessages(prev => [...prev, clarifyMessage])
    return true
  }

  // ── Interceptor 3: awaiting calibration choice ────────────────────────────
  const _handleCalibrationChoice = async (content: string): Promise<boolean> => {
    if (!awaitingCalibrationChoice || currentStage !== 'search-calibration') return false
    const lowerContent = content.toLowerCase().trim()

    const calibratePatterns = [
      'calibrar', 'calibração', 'calibracao',
      'avaliar candidato', 'avaliar perfis',
      'mostrar candidato', 'mostra candidato', 'ver candidato', 'ver perfis',
      'quero calibrar', 'calibrar agora', 'mostrar perfis', 'avaliar agora'
    ]
    const skipPatterns = [
      'kanban', 'kbn', 'pular', 'direto', 'ir para', 'skip',
      'depois', 'mais tarde', 'funil', 'pipeline',
      'sem calibração', 'sem calibracao', 'calibrar depois',
      'ir pro kanban', 'manda pro funil', 'pode pular',
      'prefiro kanban', 'quero ir pro kanban', 'vai pro kanban',
      'aprendizado natural', 'aprender no kanban'
    ]

    const hasCalibrationIntent = calibratePatterns.some(p => lowerContent.includes(p))
    let hasSkipIntent = skipPatterns.some(p => lowerContent.includes(p))

    if ((lowerContent === 'não' || lowerContent === 'nao') && !hasCalibrationIntent) {
      hasSkipIntent = true
    }

    const explicitRejectCalibration = lowerContent.includes('não') && lowerContent.includes('calibr')
    const hasConflictingIntent = hasCalibrationIntent && hasSkipIntent

    if (hasConflictingIntent) {
      setAwaitingCalibrationChoice(true)
      const conflictClarifyMessage: Message = {
        id: `lia-clarify-conflict-${Date.now()}`,
        role: 'assistant',
        content: `Percebi que você mencionou calibração mas também parece querer deixar para depois. Para confirmar:\n\n• **"Calibrar agora"** - mostro 5 perfis para avaliar rapidamente\n• **"Ir pro kanban"** - adiciono candidatos e você avalia lá\n\nQual prefere?`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, conflictClarifyMessage])
      return true
    }

    if (hasSkipIntent || explicitRejectCalibration) {
      setAwaitingCalibrationChoice(false)
      const skipMessage: Message = {
        id: `lia-skip-calibration-${Date.now()}`,
        role: 'assistant',
        content: `Perfeito! Os candidatos já estão sendo adicionados ao Kanban da vaga. 🎯\n\n**Aprendizado Implícito Ativado:**\nQuando você mover candidatos no Kanban (aprovar → entrevista, reprovar → descartado), eu automaticamente aprendo suas preferências e ajusto as futuras sugestões.\n\n📊 **Candidatos encontrados:** ${localCandidateCount > 0 ? localCandidateCount : 'Buscando...'}\n\nClique no botão abaixo para ir ao Kanban da vaga.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, skipMessage])
      setCalibrationComplete(true)
      return true
    }

    if (hasCalibrationIntent && !hasSkipIntent) {
      setAwaitingCalibrationChoice(false)
      const calibrateMessage: Message = {
        id: `lia-start-calibration-${Date.now()}`,
        role: 'assistant',
        content: `Ótimo! Vou te mostrar 5 perfis para você avaliar rapidamente. 🔍\n\nBasta indicar se cada candidato é **aderente** ou **não aderente** ao perfil da vaga.\n\nCarregando os primeiros perfis...`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, calibrateMessage])
      setShowCalibrationModal(true)
      return true
    }

    const ambiguousAffirmative = ['sim', 'ok', 'pode', 'vamos', 'bora', 'claro', 'beleza'].some(p => lowerContent === p || lowerContent.startsWith(p + ' '))
    if (ambiguousAffirmative) {
      const clarifyAmbiguousMessage: Message = {
        id: `lia-clarify-ambiguous-${Date.now()}`,
        role: 'assistant',
        content: `Ótimo! Só para confirmar, você quer:\n          \n• **"Calibrar"** - eu mostro 5 perfis para você avaliar rapidamente\n• **"Ir pro kanban"** - eu adiciono os candidatos e você avalia lá\n\nQual prefere?`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, clarifyAmbiguousMessage])
      return true
    }

    const clarifyCalibrationMessage: Message = {
      id: `lia-clarify-calibration-${Date.now()}`,
      role: 'assistant',
      content: 'Não entendi sua preferência. Você quer **"calibrar"** (avaliar 5 perfis) ou **"ir pro kanban"** (aprendizado natural)?',
      timestamp: new Date()
    }
    setMessages(prev => [...prev, clarifyCalibrationMessage])
    return true
  }

  // ── Interceptor 4: pending tool call confirmation ─────────────────────────
  const _handlePendingToolConfirmation = async (content: string): Promise<boolean> => {
    if (!toolCalling.hasPendingTool || !activeToolConfirmationMessageId) return false
    const lowerContent = content.toLowerCase().trim()

    const affirmativePatterns = ['sim', 'pode', 'ok', 'claro', 'confirmo', 'confirma', 'prossegue', 'prosseguir', 'fazer', 'execute', 'aceito', 'pode ser', 'beleza', 'manda', 'vai', 'bora']
    const negativePatterns = ['não', 'nao', 'cancela', 'cancelar', 'deixa', 'para', 'espera', 'aguarda', 'negativo', 'desisto']

    const isAffirmative = affirmativePatterns.some(p => lowerContent.includes(p))
    const isNegative = negativePatterns.some(p => lowerContent.includes(p))

    if (isAffirmative && !isNegative) {
      setIsLoading(true)
      try {
        const result = await toolCalling.confirmToolCall()
        const feedbackMessage: Message = {
          id: `tool-feedback-${Date.now()}`,
          role: 'assistant',
          content: result.success ? `✅ ${result.message}` : `❌ ${result.error || result.message}`,
          timestamp: new Date(),
          messageType: 'tool-execution-feedback',
          toolExecutionResult: result,
        }
        setMessages(prev => [...prev, feedbackMessage])
        setActiveToolConfirmationMessageId(null)
        if (result.success) {
          const followUpMessage: Message = {
            id: `tool-followup-${Date.now()}`,
            role: 'assistant',
            content: 'Posso ajudar com mais alguma coisa?',
            timestamp: new Date(),
          }
          setTimeout(() => {
            setMessages(prev => [...prev, followUpMessage])
          }, 500)
        }
      } catch (error) {
        const errorMessage: Message = {
          id: `tool-error-${Date.now()}`,
          role: 'assistant',
          content: 'Tive um problema ao executar a ação. Por favor, tente novamente.',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, errorMessage])
        setActiveToolConfirmationMessageId(null)
      } finally {
        setIsLoading(false)
      }
      return true
    }

    if (isNegative) {
      toolCalling.cancelToolCall()
      setActiveToolConfirmationMessageId(null)
      const cancelMessage: Message = {
        id: `tool-cancel-${Date.now()}`,
        role: 'assistant',
        content: 'Tudo bem, cancelei a ação. Se precisar de algo mais, é só me avisar!',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, cancelMessage])
      return true
    }

    // Unclear — let message flow through to orchestrator
    return false
  }

  // ── Interceptor 5: awaiting WSI regeneration confirmation ─────────────────
  const _handleWSIRegenConfirmation = async (content: string): Promise<boolean> => {
    if (!isInJobCreationMode || !awaitingWSIRegenerationConfirmation) return false
    const lowerContent = content.toLowerCase().trim()

    const affirmativePatterns = ['sim', 'pode', 'atualiz', 'regen', 'ok', 'claro', 'por favor', 'quero']
    const negativePatterns = ['não', 'nao', 'deixa', 'mantém', 'mantem', 'fica', 'assim mesmo']

    const isAffirmative = affirmativePatterns.some(p => lowerContent.includes(p))
    const isNegative = negativePatterns.some(p => lowerContent.includes(p))

    if (isAffirmative && !isNegative) {
      setAwaitingWSIRegenerationConfirmation(false)
      setIsLoading(true)
      try {
        const { regenerateWSIQuestions } = await import('@/services/lia-api')
        const currentQuestions = wsiCandidates.map((q, idx) => ({
          id: q.id || `wsi-${idx}`,
          question_text: q.question,
          question_type: (q.type || 'open') as 'open' | 'yes-no' | 'numeric' | 'multiple-choice',
          competency_validated: q.competency || null,
          competency_type: null as null,
        }))
        const result = await regenerateWSIQuestions({
          company_id: user?.company || 'default',
          job_title: basicInfoFields.cargo,
          current_questions: currentQuestions,
          technical_skills: technicalSkills.map(s => s.name),
          behavioral_competencies: behavioralCompetencies.map(c => c.name),
          seniority: undefined,
          max_questions: 10
        })
        if (result.success && result.questions.length > 0) {
          setWsiCandidates(result.questions.map((q, idx) => ({
            id: `wsi-regen-${idx}-${Date.now()}`,
            question: q.question_text,
            type: (q.question_type || 'open') as WSIQuestion['type'],
            required: true,
            selected: true,
            batch: 0,
            isWSI: true,
            competency: q.competency_validated ?? undefined,
          })))
          analytics.trackSuggestion('fast_track_wsi_regenerated', true)
          const successMessage: Message = {
            id: `wsi-regen-success-${Date.now()}`,
            role: 'assistant',
            content: `Pronto! Gerei **${result.questions.length} novas perguntas WSI** baseadas nas competências atualizadas. Você pode revisar e ajustar no painel ao lado.`,
            timestamp: new Date(),
          }
          setMessages(prev => [...prev, successMessage])
        } else if (!result.success) {
          const warningMessage: Message = {
            id: `wsi-regen-warning-${Date.now()}`,
            role: 'assistant',
            content: 'A regeneração não foi possível. Manterei as perguntas atuais - você pode editá-las manualmente no painel.',
            timestamp: new Date(),
          }
          setMessages(prev => [...prev, warningMessage])
        }
      } catch (error) {
        const errorMessage: Message = {
          id: `wsi-regen-error-${Date.now()}`,
          role: 'assistant',
          content: 'Tive um problema ao regenerar as perguntas. Você pode tentar novamente mais tarde ou editar manualmente.',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, errorMessage])
      } finally {
        setIsLoading(false)
      }
      return true
    }

    if (isNegative) {
      setAwaitingWSIRegenerationConfirmation(false)
      const keepMessage: Message = {
        id: `wsi-keep-${Date.now()}`,
        role: 'assistant',
        content: 'Tudo bem! Manterei as perguntas WSI atuais. Se mudar de ideia, é só me avisar.',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, keepMessage])
      return true
    }

    return false
  }

  // ── Interceptor 6: awaiting sensitive fields confirmation (Fast Track) ─────
  const _handleSensitiveFieldsConfirmation = async (content: string): Promise<boolean> => {
    if (!isInJobCreationMode || !awaitingSensitiveFieldsConfirmation) return false
    const lowerContent = content.toLowerCase().trim()

    const gestorPatterns = [
      /gestor(?:\s+(?:[eé]|vai ser|será))?\s+(?:o\s+|a\s+)?([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+?)(?:\s*[,.]|$)/i,
      /(?:o\s+|a\s+)?([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ]+(?:\s+[A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ]+)*)\s+(?:[eé]\s+)?(?:o\s+)?gestor/i,
      /gestor(?:a)?[:\s]+([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+?)(?:\s*[,.]|$)/i,
    ]
    let extractedGestor = ''
    for (const pattern of gestorPatterns) {
      const match = content.match(pattern)
      if (match && match[1]) {
        extractedGestor = match[1].trim()
        break
      }
    }
    if (lowerContent.includes('mesmo') || lowerContent.includes('anterior') || lowerContent.includes('igual')) {
      if (fastTrackAppliedData?.gestor) extractedGestor = fastTrackAppliedData.gestor
    }

    let extractedLocation = ''
    const locationPatterns = [
      /(?:localiza[çc][aã]o|cidade|local|onde)[:\s]+([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s\-]+?)(?:\s*[,.]|$)/i,
      /(?:em|para)\s+([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s\-]+?)(?:\s*[,.]|$)/i,
    ]
    if ((lowerContent.includes('sim') || lowerContent.includes('mesmo') || lowerContent.includes('continua')) && fastTrackAppliedData?.localidade) {
      extractedLocation = fastTrackAppliedData.localidade
    } else if (lowerContent.includes('remoto') || lowerContent.includes('home office')) {
      extractedLocation = 'Remoto'
    } else {
      for (const pattern of locationPatterns) {
        const match = content.match(pattern)
        if (match && match[1]) {
          extractedLocation = match[1].trim()
          break
        }
      }
    }
    if (!extractedLocation && fastTrackAppliedData?.localidade) {
      extractedLocation = fastTrackAppliedData.localidade
    }

    let isAffirmativeAction = false
    let affirmativeCriteria = ''
    const affirmativeNegativePatterns = [
      /n[aã]o\s+[eé]\s+afirmativa/i,
      /n[aã]o\s+afirmativa/i,
      /n[aã]o,?\s*(?:n[aã]o\s+)?[eé]?\s*afirmativa/i,
    ]
    const affirmativePositivePatterns = [
      /afirmativa\s+(?:para\s+)?(mulheres?|pcd|pessoas?\s+com\s+defici[êe]ncia|negr[oa]s?|lgbtq?\+?|50\+)/i,
      /(?:sim|[eé])\s+afirmativa/i,
      /vaga\s+afirmativa/i,
    ]
    const isNegativeAffirmative = affirmativeNegativePatterns.some(p => p.test(lowerContent))
    if (!isNegativeAffirmative) {
      for (const pattern of affirmativePositivePatterns) {
        const match = content.match(pattern)
        if (match) {
          isAffirmativeAction = true
          if (match[1]) affirmativeCriteria = match[1].trim()
          break
        }
      }
    }

    if (extractedGestor) setBasicInfoFields(prev => ({ ...prev, gestor: extractedGestor }))
    if (extractedLocation) setBasicInfoFields(prev => ({ ...prev, localidade: extractedLocation }))
    if (isAffirmativeAction) {
      setJobConfig(prev => ({ ...prev, isAffirmative: true }))
      if (affirmativeCriteria) setDetectedCriteria(prev => ({ ...prev, affirmativeCriteriaPrimary: affirmativeCriteria }))
    } else if (isNegativeAffirmative) {
      setJobConfig(prev => ({ ...prev, isAffirmative: false }))
    }

    setAwaitingSensitiveFieldsConfirmation(false)
    setFastTrackAppliedData(null)

    const confirmationParts: string[] = []
    if (extractedGestor) confirmationParts.push(`gestor: **${extractedGestor}**`)
    if (extractedLocation) confirmationParts.push(`localização: **${extractedLocation}**`)
    if (isAffirmativeAction) {
      confirmationParts.push(`vaga afirmativa: **Sim${affirmativeCriteria ? ` (${affirmativeCriteria})` : ''}**`)
    } else {
      confirmationParts.push(`vaga afirmativa: **Não**`)
    }

    const confirmMessage: Message = {
      id: `fasttrack-confirm-${Date.now()}`,
      role: 'assistant',
      content: `Perfeito! Registrei ${confirmationParts.join(', ')}.\n\nAgora você pode revisar todos os detalhes no painel lateral e publicar quando estiver pronto!`,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, confirmMessage])
    setCurrentStage('review-publish')
    setWizardMode('create_from_scratch')
    return true
  }

  const _handleFastTrackSuggestions = (content: string) => handleFastTrackSuggestions(content, ctx)

  const _handleFastTrackFlow = (content: string) => handleFastTrackFlow(content, ctx)

  const _handleCompensationMessage = (content: string) => handleCompensationMessage(content, ctx)

  const _handleLocalCommands = (content: string) => handleLocalCommands(content, ctx)

  // ── API dispatch: wizard (smart-orchestrate) ───────────────────────────────
  const _handleWizardAPICall = async (content: string, processingMessageId: string): Promise<void> => {
    setIsLoading(true)

    try {
      setTimeout(() => {
        setMessages(msgs => msgs.map(m =>
          m.id === processingMessageId
            ? { ...m, content: '📊 Consultando LIA...', processingState: 'analyzing' as const }
            : m
        ))
      }, 300)

      const collectedData = buildCollectedData()
      const conversationHistory = messages.slice(-10).map(m => ({ role: m.role, content: m.content }))
      const panelChangesContext = generateLLMContext()
      const enhancedMessage = panelChangesContext ? `${content}\n\n${panelChangesContext}` : content

      if (conversationMemory.conversationId) {
        conversationMemory.addMessage('user', content).catch(() => {})
      }

      const orchestratorResult = await orchestrateWizardMessage({
        message: enhancedMessage,
        current_stage: currentStage,
        collected_data: collectedData,
        conversation_history: conversationHistory,
        conversation_id: conversationMemory.conversationId || undefined,
        company_id: user?.company || undefined,
        user_id: user?.email || undefined
      })

      await processOrchestratorResponse(orchestratorResult, processingMessageId)
      setIsLoading(false)

      if (currentStage === 'input-evaluation' && orchestratorResult.confidence >= 0.7) {
        const evaluationContext = {
          job_title: basicInfoFields.cargo || detectedCriteria.cargo || undefined,
          seniority: detectedCriteria.senioridadeIdiomas || undefined,
          department: basicInfoFields.area || detectedCriteria.departamento || undefined,
          location: basicInfoFields.localidade || detectedCriteria.localizacao || undefined,
          work_model: basicInfoFields.modeloTrabalho || detectedCriteria.modeloTrabalho || undefined,
          technical_skills: technicalSkills.filter(s => s.required).map(s => s.name),
          behavioral_skills: behavioralCompetencies.filter(c => c.enabled).map(c => c.name),
        }
        callEvaluationStep(content, evaluationContext).then((evalResult) => {
          if (evalResult?.compensation_analysis) setCompensationAnalysis(evalResult.compensation_analysis)
          const suggestions = evalResult?.suggestions as EvaluationStepResult | undefined
          if (suggestions?.technical_skills || suggestions?.behavioral_competencies) {
            const technicalSuggestions: TechnicalSkillSuggestion[] = (suggestions.technical_skills || []).map((skill) => ({
              name: skill.name || '', level: (skill.level as TechnicalSkillSuggestion['level']) || 'Intermediário', weight: skill.weight || 3,
              weightJustification: skill.weight_justification || 'Baseado em análise de mercado',
              source: (skill.source as TechnicalSkillSuggestion['source']) || 'market_benchmark', required: skill.required ?? true, category: (skill.category as TechnicalSkillSuggestion['category']) || 'tool'
            }))
            const behavioralSuggestions: BehavioralCompetencySuggestion[] = (suggestions.behavioral_competencies || []).map((comp) => ({
              name: comp.name || '', weight: comp.weight || 3, justification: comp.justification || '',
              weightJustification: comp.weight_justification || 'Baseado em histórico da empresa', source: (comp.source as BehavioralCompetencySuggestion['source']) || 'company_history'
            }))
            if (technicalSuggestions.length > 0 || behavioralSuggestions.length > 0) {
              setCompetencySuggestions({ technicalSkills: technicalSuggestions, behavioralCompetencies: behavioralSuggestions })
              setTimeout(() => {
                const competenciesMessage: Message = {
                  id: `lia-competencies-${Date.now()}`,
                  role: 'assistant',
                  content: '',
                  timestamp: new Date(),
                  messageType: 'competencies',
                  competenciesSuggestions: { technicalSkills: technicalSuggestions, behavioralCompetencies: behavioralSuggestions }
                }
                setMessages(prev => [...prev, competenciesMessage])
              }, 1000)
            }
          }
        }).catch(() => {})
      }
    } catch (error) {
      const newCriteria = extractCriteriaFromText(content)
      const fallbackText = generateCriteriaResponse(newCriteria)
      const fallbackFieldsData: Array<{ label: string; value: string; confidence?: "high" | "medium" | "low" }> = []
      if (newCriteria.cargo) fallbackFieldsData.push({ label: "Cargo", value: newCriteria.cargo, confidence: "high" })
      if (newCriteria.senioridadeIdiomas) fallbackFieldsData.push({ label: "Senioridade", value: newCriteria.senioridadeIdiomas, confidence: "medium" })
      if (newCriteria.modeloTrabalho) fallbackFieldsData.push({ label: "Modelo", value: newCriteria.modeloTrabalho, confidence: "medium" })
      if (newCriteria.localizacao) fallbackFieldsData.push({ label: "Localização", value: newCriteria.localizacao, confidence: "medium" })
      if (newCriteria.competenciasTecnicas?.length > 0) fallbackFieldsData.push({ label: "Skills Técnicas", value: newCriteria.competenciasTecnicas.slice(0, 5).join(", "), confidence: "medium" })
      if (newCriteria.tipoContrato) fallbackFieldsData.push({ label: "Contrato", value: newCriteria.tipoContrato, confidence: "low" })
      setMessages(msgs => msgs.map(m =>
        m.id === processingMessageId
          ? { ...m, content: '✅ Mensagem processada', processingState: 'completed' as const }
          : m
      ))
      const fallbackMessage: Message = {
        id: `fallback-${Date.now()}`,
        role: 'assistant',
        content: fallbackText,
        timestamp: new Date(),
        isTyping: true,
        detectedFieldsData: fallbackFieldsData.length > 0 ? fallbackFieldsData : undefined
      }
      setMessages(msgs => [...msgs, fallbackMessage])
      setDisplayedText("")
      setTimeout(() => { typeText(fallbackText, fallbackMessage.id) }, 300)
      setIsLoading(false)
    }
  }

  // ── API dispatch: general chat (orchestrator) ──────────────────────────────
  const _handleGeneralAPICall = async (content: string, _processingMessageId: string): Promise<void> => {
    setIsLoading(true)
    try {
      let responseText = "Entendi! Estou processando as informações..."

      if (onOrchestratedMessage) {
        const orchestratedResponse = await onOrchestratedMessage(content.trim())
        responseText = orchestratedResponse.content
        if (orchestratedResponse.ui_action === 'start_job_wizard') {
          setInternalJobCreationMode(true)
          setCurrentStage('input-evaluation')
          if (orchestratedResponse.ui_action_params?.['initial_message']) {
            setDynamicInitialMessage(INITIAL_JOB_CREATION_MESSAGE)
          }
        }
      } else {
        if (!conversationMemory.conversationId && user?.email) {
          await conversationMemory.initConversation(user.email, 'general')
        }
        const conversationContext = await conversationMemory.getContext()
        if (conversationMemory.conversationId) {
          conversationMemory.addMessage('user', content.trim()).catch(() => {})
        }
        const orchestratorResponse = await orchestratorProcess({
          user_id: user?.email || 'demo-user',
          message: content.trim(),
          conversation_id: conversationMemory.conversationId || conversationId || undefined,
          context_type: 'general',
          context_id: conversationMemory.conversationId || undefined,
          conversation_context: conversationContext || undefined,
        })

        if (orchestratorResponse.success) {
          if (orchestratorResponse.conversation_id && !conversationId) {
            setConversationId(orchestratorResponse.conversation_id)
          }
          responseText = String(orchestratorResponse.message || orchestratorResponse.result?.message || responseText)
          if (conversationMemory.conversationId) {
            conversationMemory.addMessage('assistant', responseText, orchestratorResponse.intent).catch(() => {})
          }
          const suggestedToolCall = orchestratorResponse.suggested_tool_call || orchestratorResponse.result?.suggested_tool_call
          if (suggestedToolCall) {
            const stc = suggestedToolCall as Record<string, unknown>
            const toolCall: ToolCall = {
              tool_name: String(stc.tool_name),
              parameters: (stc.parameters || {}) as Record<string, unknown>,
              requires_confirmation: stc.requires_confirmation !== false,
              confirmation_message: String(stc.confirmation_message || responseText),
            }
            if (toolCall.requires_confirmation) {
              toolCalling.suggestToolCall(toolCall)
              const confirmationMessageId = `tool-confirm-${Date.now()}`
              setActiveToolConfirmationMessageId(confirmationMessageId)
              const confirmationMessage: Message = {
                id: confirmationMessageId,
                role: 'assistant',
                content: responseText,
                timestamp: new Date(),
                messageType: 'tool-confirmation',
                toolCall: toolCall,
              }
              setMessages(prev => [...prev, confirmationMessage])
              setIsLoading(false)
              return
            } else {
              setIsLoading(true)
              try {
                const result = await toolCalling.executeToolDirectly(toolCall.tool_name, toolCall.parameters)
                const feedbackMessage: Message = {
                  id: `tool-feedback-${Date.now()}`,
                  role: 'assistant',
                  content: result.success ? `✅ ${result.message}` : `❌ ${result.error || result.message}`,
                  timestamp: new Date(),
                  messageType: 'tool-execution-feedback',
                  toolExecutionResult: result,
                }
                setMessages(prev => [...prev, feedbackMessage])
                setIsLoading(false)
                return
              } catch (error) {
              }
            }
          }
        } else {
          const response = await liaApi.sendMessage({
            content: content.trim(),
            conversation_id: conversationId || undefined,
            user_id: 'demo-user'
          })
          if (response.conversation?.id && !conversationId) setConversationId(response.conversation.id)
          responseText = response.message?.content || responseText
        }
      }

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: responseText,
        timestamp: new Date(),
        isTyping: true
      }
      setMessages(prev => [...prev, assistantMessage])
      setDisplayedText("")
      setTimeout(() => { typeText(responseText, assistantMessage.id) }, 300)

    } catch (error) {
      extractCriteriaFromText(content)
      const errorText = "Entendi as informações! Detectei alguns critérios da vaga. Continue adicionando mais detalhes ou avance para a próxima etapa."
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: errorText,
        timestamp: new Date(),
        isTyping: true
      }
      setMessages(prev => [...prev, errorMessage])
      setDisplayedText("")
      setTimeout(() => { typeText(errorText, errorMessage.id) }, 300)
    } finally {
      setIsLoading(false)
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // handleSendMessage — thin dispatcher (Sprint 4.6)
  // ─────────────────────────────────────────────────────────────────────────
  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading || isTypingEffect) return

    // 1. Context switch bookkeeping (no early return)
    _handleContextSwitch(content)

    // 2. Append user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setInputValue("")

    // 3. Interceptors — first match wins
    if (await _handleStageAdvanceConfirmation(content)) return
    if (await _handleDraftChoice(content)) return
    if (await _handleCalibrationChoice(content)) return
    if (await _handlePendingToolConfirmation(content)) return
    if (await _handleWSIRegenConfirmation(content)) return
    if (await _handleSensitiveFieldsConfirmation(content)) return
    if (await _handleFastTrackSuggestions(content)) return
    if (await _handleFastTrackFlow(content)) return
    if (await _handleCompensationMessage(content)) return
    if (_handleLocalCommands(content)) return

    // 4. Normal flow: processing message → API dispatch
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
      await _handleWizardAPICall(content, processingMessageId)
      return
    }

    await _handleGeneralAPICall(content, processingMessageId)
  }


  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage(inputValue)
    }
  }

  // ESC key handler for closing modal - Accessibility (WCAG 2.1)
  const handleModalKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape' && isOpen) {
      e.preventDefault()
      onClose()
    }
  }, [isOpen, onClose])

  // Add ESC key listener for modal
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleModalKeyDown)
      return () => document.removeEventListener('keydown', handleModalKeyDown)
    }
  }, [isOpen, handleModalKeyDown])

  // Auto-focus input when modal opens - Accessibility
  useEffect(() => {
    if (isOpen && inputRef.current) {
      // Small delay to ensure modal is rendered
      const timer = setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
      return () => clearTimeout(timer)
    }
  }, [isOpen])

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
