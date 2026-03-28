"use client"

import { useCallback, useEffect } from "react"
import type React from "react"
import {
  orchestrateWizardMessage,
  getConversationalResponse,
  orchestratorProcess,
  interpretMessage,
  type WizardOrchestratorResponse,
  type VacancySearchCriteria,
  type VacancyAdjustments,
  liaApi,
} from "@/services/lia-api"
import type { ParecerLIAData } from "@/components/chat/parecer-lia-card"
import {
  WIZARD_STAGES,
  getStageTransitionMessage,
  FROM_SCRATCH_ORIENTATION_MESSAGE,
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
} from "../ExpandedChatContext"
import type { FastTrackSuggestion, FastTrackJobData } from "@/hooks/useFastTrack"
import type { useContextSwitching } from "./useContextSwitching"
import type { useConversationMemory } from "./useConversationMemory"
import type { useWizardAnalytics } from "./useWizardAnalytics"
import type { useToolCalling } from "./useToolCalling"
import type { useLearning } from "./useLearning"
import type { ToolCall } from "./useToolCalling"
import { parseSalaryValue, applySalaryUpdate, addSkillIfNotExists, removeSkillByName, parseCommand, getStageLabel } from "../utils"
import type { ParsedNavigationCommand, ParsedEditCommand } from "../utils"

// ─────────────────────────────────────────────────────────────────────────────
// Context interface — everything the hook needs from the parent component
// ─────────────────────────────────────────────────────────────────────────────

export interface SendMessageHandlersContext {
  // ─── Props ───────────────────────────────────────────────────────────────────
  isOpen: boolean
  onClose: () => void
  isJobCreationMode: boolean
  inline: boolean
  onJobCreated?: (...args: any[]) => void
  onOrchestratedMessage?: (msg: string) => Promise<{ content: string; ui_action?: string | null; ui_action_params?: Record<string, unknown> }>
  onMessagesUpdate?: (...args: any[]) => void

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
  pendingDraftData: Partial<WizardDraftData> | null | any
  setPendingDraftData: (data: any) => void
  setHasAppliedRestoredDraft: (val: boolean) => void
  applyPendingDraft: () => void
  clearWizardDraft: () => void

  // ─── Calibration ─────────────────────────────────────────────────────────────
  calibrationComplete: boolean
  setCalibrationComplete: (val: boolean) => void
  approvedCandidates: any[]
  rejectedCandidates: any[]
  setIsPanelOpen: (val: boolean) => void
  localCandidateCount: number
  setShowCalibrationModal: (val: boolean) => void

  // ─── Fast Track ──────────────────────────────────────────────────────────────
  fastTrack: ReturnType<typeof import("@/hooks/useFastTrack").useFastTrack>
  fastTrackState: FastTrackState
  setFastTrackState: (state: FastTrackState) => void
  fastTrackSearchResults: any[]
  setFastTrackSearchResults: (results: any[]) => void
  fastTrackSelectedVacancy: any | null
  setFastTrackSelectedVacancy: (vacancy: any | null) => void
  fastTrackAdjustments: any | null
  setFastTrackAdjustments: React.Dispatch<React.SetStateAction<any>>
  fastTrackSearchCriteria: any | null
  setFastTrackSearchCriteria: (criteria: any | null) => void
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
  wsiQuestions: any[]
  setWsiQuestions: React.Dispatch<React.SetStateAction<any[]>>
  wsiCandidates: any[]
  setWsiCandidates: React.Dispatch<React.SetStateAction<any[]>>
  setCompetencySuggestions: (val: any) => void
  generatedJobDescription: string
  setGeneratedJobDescription: (val: string) => void

  // ─── Salary / Compensation ───────────────────────────────────────────────────
  compensationAnalysis: any | null
  setCompensationAnalysis: (val: any | null) => void
  setIsLoadingEnrichment: (val: boolean) => void

  // ─── Job config ──────────────────────────────────────────────────────────────
  setJobConfig: React.Dispatch<React.SetStateAction<any>>
  setInternalJobCreationMode: (val: boolean) => void
  setDynamicInitialMessage: (val: string | null) => void

  // ─── UI state ────────────────────────────────────────────────────────────────
  setDisplayedText: (val: string) => void

  // ─── Functions ───────────────────────────────────────────────────────────────
  buildCollectedData: () => any
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
  callEvaluationStep: (content: string, context: any) => Promise<any>
  trackFieldChange: (change: any) => void

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

  // ── Interceptor 1: awaiting stage advance confirmation ────────────────────
  const _handleStageAdvanceConfirmation = async (content: string): Promise<boolean> => {
    if (!awaitingStageAdvanceConfirmation) return false
    const lowerMessage = content.toLowerCase().trim()
    const originalMessage = content.trim()

    const adjustmentPatterns = [
      'ajust', 'alter', 'mud', 'troc', 'edit', 'corrig', 'revis',
      'quero', 'preciso', 'falta', 'adiciona', 'remov', 'exclui',
      'não', 'nao', 'errad', 'outr', 'diferent'
    ]
    const isAdjustmentRequest = adjustmentPatterns.some(p => lowerMessage.includes(p))

    const shortConfirmPatterns = [
      /^sim$/i, /^pode$/i, /^vamos$/i, /^ok$/i, /^beleza$/i, /^bora$/i,
      /^perfeito$/i, /^show$/i, /^massa$/i, /^confirmo$/i, /^confirma$/i,
      /^tá bom$/i, /^ta bom$/i, /^está bom$/i, /^ta certo$/i, /^tá certo$/i,
      /^pode ser$/i, /^pode sim$/i, /^sim,? pode$/i, /^vamos lá$/i,
      /^vamos sim$/i, /^avança$/i, /^avançar$/i, /^próxima$/i, /^proxima$/i,
      /^seguir$/i, /^segue$/i, /^prosseguir$/i, /^continuar$/i,
      /^sim,?\s*(pode|vamos|avança|ok|beleza)$/i,
      /^(pode|vamos|ok),?\s*sim$/i
    ]

    const isShortMessage = originalMessage.length <= 30
    const isStandaloneConfirmation = shortConfirmPatterns.some(p => p.test(lowerMessage))
    const isClearConfirmation = (isShortMessage && isStandaloneConfirmation && !isAdjustmentRequest)

    if (isClearConfirmation) {
      console.log('[ProactiveConfirmation] Detected clear confirmation:', lowerMessage)

      if (awaitingStageAdvanceConfirmation === 'calibration-complete') {
        setCalibrationComplete(true)
        const totalEvaluated = approvedCandidates.length + rejectedCandidates.length
        const completeMsg: Message = {
          id: `calibration-finished-${Date.now()}`,
          role: 'assistant',
          content: `🎯 **Calibração finalizada!**\n\nO modelo de busca foi ajustado com base nas suas ${totalEvaluated} avaliações. Agora as próximas buscas vão priorizar candidatos similares aos que você aprovou.`,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, completeMsg])
        setAwaitingStageAdvanceConfirmation(null)
        return true
      }

      const nextStage = awaitingStageAdvanceConfirmation

      if (nextStage === 'jd-enrichment') {
        console.log('[ProactiveConfirmation] Transitioning to jd-enrichment, calling smart-orchestrate')
        setAwaitingStageAdvanceConfirmation(null)
        setIsLoadingEnrichment(true)
        const loadingMsg: Message = {
          id: `jd-enrichment-loading-${Date.now()}`,
          role: 'assistant',
          content: '🔍 **Analisando dados de mercado...**\n\nEstou consultando benchmarks salariais, catálogo de competências e histórico da empresa para preparar sugestões personalizadas.',
          timestamp: new Date(),
          isProcessing: true,
          processingState: 'analyzing'
        }
        setMessages(prev => [...prev, loadingMsg])
        setCurrentStage('jd-enrichment' as WizardStage)
        const collectedData = buildCollectedData()
        orchestrateWizardMessage({
          message: content,
          current_stage: 'input-evaluation',
          collected_data: collectedData,
          conversation_history: messages.slice(-10).map(m => ({ role: m.role, content: m.content })),
          conversation_id: conversationMemory.conversationId || undefined,
          company_id: user?.company || undefined,
          user_id: user?.email || undefined
        }).then(async result => {
          setMessages(prev => prev.filter(m => m.id !== loadingMsg.id))
          await processOrchestratorResponse(result, loadingMsg.id)
          setIsLoadingEnrichment(false)
          setTimeout(() => {
            const parecerData = generateParecerData()
            const parecerMsg: Message = {
              id: `parecer-lia-${Date.now()}`,
              role: 'assistant',
              content: `Preparei uma análise completa da sua vaga. Revise o parecer abaixo e ajuste o que desejar antes de avançarmos para **Remuneração**.`,
              timestamp: new Date(),
              messageType: 'parecer-lia',
              parecerData
            }
            setMessages(prev => [...prev, parecerMsg])
            setAwaitingStageAdvanceConfirmation('salary')
          }, 1000)
        }).catch(error => {
          console.error('[ProactiveConfirmation] Failed to get enriched JD:', error)
          setMessages(prev => prev.filter(m => m.id !== loadingMsg.id))
          setIsLoadingEnrichment(false)
          const errorMsg: Message = {
            id: `jd-enrichment-error-${Date.now()}`,
            role: 'assistant',
            content: '❌ Não consegui buscar as sugestões de mercado. Você pode continuar preenchendo manualmente ou tentar novamente.',
            timestamp: new Date()
          }
          setMessages(prev => [...prev, errorMsg])
        })
        return true
      }

      const transitionMsg: Message = {
        id: `stage-transition-${Date.now()}`,
        role: 'assistant',
        content: getStageTransitionMessage(nextStage, {}),
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, transitionMsg])
      setCurrentStage(nextStage as WizardStage)
      setAwaitingStageAdvanceConfirmation(null)
      if (nextStage === 'salary') {
        setTimeout(() => {
          const parecerData = generateParecerData()
          const parecerMsg: Message = {
            id: `parecer-lia-${Date.now()}`,
            role: 'assistant',
            content: `Preparei uma análise completa da sua vaga antes de configurar a remuneração.`,
            timestamp: new Date(),
            messageType: 'parecer-lia',
            parecerData
          }
          setMessages(prev => [...prev, parecerMsg])
        }, 500)
      }
      return true
    }

    // Not a clear confirmation — clear state and fall through to backend
    console.log('[ProactiveConfirmation] Not a clear confirmation, routing to backend:', lowerMessage)
    setAwaitingStageAdvanceConfirmation(null)
    return false
  }

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
        console.error('[ToolCalling] Error executing tool:', error)
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
        const currentQuestions = wsiCandidates.map(q => ({
          question: q.question,
          type: q.type || 'open',
          required: q.required !== false,
          competency_validated: q.competency
        }))
        const result = await regenerateWSIQuestions({
          company_id: user?.company || 'default',
          job_title: basicInfoFields.cargo,
          current_questions: currentQuestions as any,
          technical_skills: technicalSkills.map(s => s.name),
          behavioral_competencies: behavioralCompetencies.map(c => c.name),
          seniority: undefined,
          max_questions: 10
        })
        if (result.success && result.questions.length > 0) {
          setWsiCandidates(result.questions.map((q: any, idx: number) => ({
            id: `wsi-regen-${idx}-${Date.now()}`,
            question: q.question,
            type: q.type || 'open',
            required: q.required !== false,
            selected: true,
            batch: 0,
            isWSI: true,
            competency: q.competency_validated,
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
        console.error('WSI regeneration failed:', error)
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

  // ── Interceptor 7: Fast Track suggestions (hasSuggestions gate) ───────────
  const _handleFastTrackSuggestions = async (content: string): Promise<boolean> => {
    if (!isInJobCreationMode || !fastTrack.hasSuggestions) return false
    const lowerContent = content.toLowerCase().trim()

    const numberMatch = lowerContent.match(/\b([1-5])\b|primeira|segunda|terceira|quarta|quinta/)
    const hasExplicitSelection = numberMatch !== null

    const affirmativePatterns = [
      'sim', 'usa', 'usar', 'ok', 'vamos', 'pode ser', 'pode', 'essa', 'essa mesmo',
      'top', 'bora', 'beleza', 'perfeito', 'ótimo', 'legal', 'certo', 'fechou'
    ]
    const negativePatterns = [
      'não', 'nao', 'zero', 'nova', 'novo', 'criar', 'comecar', 'começar',
      'do zero', 'outra', 'diferente', 'prefiro não'
    ]

    const isAffirmative = affirmativePatterns.some(p => lowerContent.includes(p))
    const isNegative = negativePatterns.some(p => lowerContent.includes(p))

    if ((isAffirmative || hasExplicitSelection) && !isNegative) {
      if (awaitingFastTrackSelection && !numberMatch) {
        const reaskMessage: Message = {
          id: `fasttrack-reask-${Date.now()}`,
          role: 'assistant',
          content: 'Qual das vagas você quer usar? Diga o número (1, 2, 3...) ou "primeira", "segunda", etc.',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, reaskMessage])
        return true
      }

      if (fastTrack.suggestions.length > 1 && !numberMatch && !fastTrack.selectedJob) {
        const clarifyMessage: Message = {
          id: `fasttrack-clarify-${Date.now()}`,
          role: 'assistant',
          content: `Tenho ${fastTrack.suggestions.length} vagas similares. Qual você quer usar?\n\n${fastTrack.suggestions.slice(0, 5).map((s, i) => `${i + 1}. ${s.job_title}${s.department ? ` (${s.department})` : ''} - ${Math.round(s.similarity_score * 100)}% similar`).join('\n')}\n\nDiga o número ou "primeira", "segunda", etc.`,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, clarifyMessage])
        setAwaitingFastTrackSelection(true)
        return true
      }

      let jobToApply: FastTrackSuggestion | null = null
      if (numberMatch) {
        const indexMap: Record<string, number> = {
          '1': 0, 'primeira': 0, '2': 1, 'segunda': 1, '3': 2, 'terceira': 2,
          '4': 3, 'quarta': 3, '5': 4, 'quinta': 4
        }
        const index = indexMap[numberMatch[0].toLowerCase()] ?? 0
        if (index < fastTrack.suggestions.length) jobToApply = fastTrack.suggestions[index]
      } else if (fastTrack.selectedJob) {
        jobToApply = fastTrack.selectedJob
      } else if (fastTrack.suggestions.length === 1) {
        jobToApply = fastTrack.suggestions[0]
      }

      if (!jobToApply) return true

      let fastTrackData: FastTrackJobData | null = null
      try {
        fastTrackData = await fastTrack.applyFastTrack(jobToApply)
      } catch (error) {
        console.error('Fast Track apply failed:', error)
        setAwaitingFastTrackSelection(false)
        const errorMessage: Message = {
          id: `fasttrack-error-${Date.now()}`,
          role: 'assistant',
          content: 'Ops! Tive um problema ao aplicar os dados. Quer tentar novamente ou criar do zero?',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, errorMessage])
        return true
      }

      if (fastTrackData) {
        setBasicInfoFields({
          cargo: fastTrackData.basicInfo.cargo || '',
          area: fastTrackData.basicInfo.area || '',
          gestor: fastTrackData.basicInfo.gestor || '',
          localidade: fastTrackData.basicInfo.localidade || '',
          modeloTrabalho: fastTrackData.basicInfo.modeloTrabalho || '',
          tipoContrato: fastTrackData.basicInfo.tipoContrato || '',
        })
        setTechnicalSkills(fastTrackData.technicalSkills)
        setBehavioralCompetencies(fastTrackData.behavioralCompetencies)
        setSalaryInfo({
          minSalary: fastTrackData.salaryInfo.minSalary || '',
          maxSalary: fastTrackData.salaryInfo.maxSalary || '',
          minBonus: fastTrackData.salaryInfo.minBonus || '',
          maxBonus: fastTrackData.salaryInfo.maxBonus || '',
          bonusCriteria: fastTrackData.salaryInfo.bonusCriteria || '',
          benefits: fastTrackData.salaryInfo.benefits || [],
        })
        if (fastTrackData.wsiQuestions.length > 0) {
          setWsiCandidates(fastTrackData.wsiQuestions.map(q => ({
            ...q, selected: true, batch: 0, isWSI: true,
          })))
        }
        if (fastTrackData.generatedDescription) setGeneratedJobDescription(fastTrackData.generatedDescription)
        setDetectedCriteria(prev => ({ ...prev, ...fastTrackData.detectedCriteria }))
        setWizardFastTrackSourceJobId(fastTrackData.sourceJobId)
        setFastTrackOriginalCompetencies({
          technicalSkillNames: fastTrackData.technicalSkills.map(s => s.name.toLowerCase()),
          behavioralCompetencyNames: fastTrackData.behavioralCompetencies.map(c => c.name.toLowerCase())
        })
        setWsiRegenerationPrompted(false)
        setAwaitingFastTrackSelection(false)
        setFastTrackAppliedData({
          gestor: fastTrackData.basicInfo.gestor || '',
          localidade: fastTrackData.basicInfo.localidade || '',
          sourceJobTitle: jobToApply.job_title || ''
        })
        setAwaitingSensitiveFieldsConfirmation(true)
        analytics.trackSuggestion('fast_track_accepted', true)

        const localidadeInfo = fastTrackData.basicInfo.localidade
          ? `A localização continua sendo **${fastTrackData.basicInfo.localidade}**?`
          : 'Qual será a localidade da vaga?'
        const sensitiveFieldsMessage: Message = {
          id: `fasttrack-sensitive-${Date.now()}`,
          role: 'assistant',
          content: `Copiei todos os dados da vaga "${jobToApply.job_title}"! Só preciso confirmar alguns detalhes:\n\n1. **Quem é o gestor** responsável por esta vaga?\n2. ${localidadeInfo}\n3. **Essa vaga é afirmativa** para algum grupo (PcD, mulheres, pessoas negras, LGBTQ+, 50+)?`,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, sensitiveFieldsMessage])
        setIsPanelOpen(true)
      } else {
        setAwaitingFastTrackSelection(false)
        const errorMessage: Message = {
          id: `fasttrack-null-${Date.now()}`,
          role: 'assistant',
          content: 'Não consegui carregar os dados dessa vaga. Quer tentar outra ou criar do zero?',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, errorMessage])
      }
      return true
    }

    if (isNegative) {
      fastTrack.clearSuggestions()
      setFastTrackMessageSent(false)
      setAwaitingFastTrackSelection(false)
      analytics.trackSuggestion('fast_track_rejected', false)
      const liaMessage: Message = {
        id: `fasttrack-declined-${Date.now()}`,
        role: 'assistant',
        content: 'Tudo bem! Vamos criar uma nova vaga do zero. Me conta mais sobre a vaga que você precisa.',
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, liaMessage])
      return true
    }

    return false
  }

  // ── Interceptor 8: Fast Track flow (pre_wizard / fast_track mode) ──────────
  const _handleFastTrackFlow = async (content: string): Promise<boolean> => {
    if (!isInJobCreationMode || (wizardMode !== 'pre_wizard' && wizardMode !== 'fast_track')) return false

    const intent = detectFastTrackIntent(content)

    if (wizardMode === 'pre_wizard') {
      if (intent === 'fast_track') {
        setWizardMode('fast_track')
        setFastTrackState('collecting_criteria')
        setIsPanelOpen(false)
        const liaMessage: Message = {
          id: `lia-fasttrack-${Date.now()}`,
          role: 'assistant',
          content: '🚀 **Ótima escolha!** Vou buscar suas vagas anteriores.\n\nPara encontrar a vaga certa, me diga pelo menos 2 critérios:\n- Cargo (ex: "Desenvolvedor Python")\n- Área ou departamento\n- Gestor responsável\n- Período aproximado\n\n**Exemplo:** "Desenvolvedor Python da equipe de dados do João"',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, liaMessage])
        return true
      }

      if (intent === 'from_scratch') {
        setWizardMode('create_from_scratch')
        setIsPanelOpen(true)
        if (fastTrackSuggestionsShownTracked) analytics.trackSuggestion('fast_track_rejected', false)
        const liaMessage: Message = {
          id: `lia-scratch-${Date.now()}`,
          role: 'assistant',
          content: FROM_SCRATCH_ORIENTATION_MESSAGE,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, liaMessage])
        return true
      }

      // No clear choice — use AI to respond conversationally
      setIsLoading(true)
      try {
        const conversationalResponse = await getConversationalResponse({
          message: content,
          mode: 'job_creation',
          context: 'pre_wizard'
        })
        if (conversationalResponse.suggested_action === 'from_scratch') {
          setWizardMode('create_from_scratch')
          setIsPanelOpen(true)
          if (fastTrackSuggestionsShownTracked) analytics.trackSuggestion('fast_track_rejected', false)
          const liaMessage: Message = {
            id: `lia-scratch-ai-${Date.now()}`,
            role: 'assistant',
            content: FROM_SCRATCH_ORIENTATION_MESSAGE,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, liaMessage])
          setIsLoading(false)
          return true
        }
        if (conversationalResponse.suggested_action === 'fast_track') {
          setWizardMode('fast_track')
          setFastTrackState('collecting_criteria')
          setIsPanelOpen(false)
          const liaMessage: Message = {
            id: `lia-fasttrack-ai-${Date.now()}`,
            role: 'assistant',
            content: '🚀 **Ótima escolha!** Vou buscar suas vagas anteriores.\n\nPara encontrar a vaga certa, me diga pelo menos 2 critérios:\n- Cargo (ex: "Desenvolvedor Python")\n- Área ou departamento\n- Gestor responsável\n- Período aproximado\n\n**Exemplo:** "Desenvolvedor Python da equipe de dados do João"',
            timestamp: new Date()
          }
          setMessages(prev => [...prev, liaMessage])
          setIsLoading(false)
          return true
        }
        const liaMessage: Message = {
          id: `lia-conversational-${Date.now()}`,
          role: 'assistant',
          content: conversationalResponse.response,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, liaMessage])
      } catch (error) {
        console.error('Error getting conversational response:', error)
        const liaMessage: Message = {
          id: `lia-guidance-fallback-${Date.now()}`,
          role: 'assistant',
          content: 'Sou a LIA, sua assistente de recrutamento! Aqui posso te ajudar a:\n\n• **Criar uma nova vaga** do zero com toda inteligência da plataforma\n• **Reutilizar uma vaga anterior** para publicar rapidamente\n\nComo gostaria de começar?',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, liaMessage])
      } finally {
        setIsLoading(false)
      }
      return true
    }

    // fast_track mode
    if (intent === 'confirm' && fastTrackState === 'reviewing') {
      await handleFastTrackPublish()
      return true
    }
    if (intent === 'adjust' && (fastTrackState === 'reviewing' || fastTrackState === 'adjusting')) {
      const adjustments = parseFastTrackAdjustment(content)
      if (adjustments) {
        setFastTrackAdjustments(prev => ({ ...prev, ...adjustments }))
        setFastTrackState('adjusting')
        if (fastTrackSelectedVacancy) {
          const updatedVacancy = { ...fastTrackSelectedVacancy }
          if (adjustments.salary_min) updatedVacancy.salary_range.min = adjustments.salary_min
          if (adjustments.salary_max) updatedVacancy.salary_range.max = adjustments.salary_max
          if (adjustments.work_model) updatedVacancy.work_model = adjustments.work_model
          if (adjustments.location) updatedVacancy.location = adjustments.location
          setFastTrackSelectedVacancy(updatedVacancy)
          const liaMessage: Message = {
            id: `lia-adjust-${Date.now()}`,
            role: 'assistant',
            content: `✅ **Ajuste aplicado!**\n\nAtualizei os valores conforme solicitado. Revise o resumo atualizado:\n\n• Salário: R$ ${updatedVacancy.salary_range.min.toLocaleString('pt-BR')} - R$ ${updatedVacancy.salary_range.max.toLocaleString('pt-BR')}\n• Modelo: ${updatedVacancy.work_model}\n• Local: ${updatedVacancy.location}\n\nSe quiser fazer mais ajustes, me diga. Quando estiver pronto, digite **"confirmar"** para publicar.`,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, liaMessage])
          setFastTrackState('reviewing')
        }
      } else {
        const liaMessage: Message = {
          id: `lia-adjust-error-${Date.now()}`,
          role: 'assistant',
          content: 'Não consegui entender o ajuste solicitado. Por favor, seja mais específico.\n\n**Exemplos:**\n• "salário para 15 a 20k"\n• "modelo híbrido"\n• "local para São Paulo"',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, liaMessage])
      }
      return true
    }
    if (intent === 'select' && fastTrackState === 'selecting') {
      const numMatch = content.match(/(\d+)/)
      const numberWords: Record<string, number> = { 'um': 1, 'dois': 2, 'três': 3, 'quatro': 4, 'cinco': 5, 'seis': 6, 'sete': 7, 'oito': 8, 'nove': 9, 'dez': 10 }
      let index = -1
      if (numMatch) {
        index = parseInt(numMatch[1]) - 1
      } else {
        const word = content.toLowerCase().trim()
        if (numberWords[word]) index = numberWords[word] - 1
      }
      if (index >= 0 && index < fastTrackSearchResults.length) {
        const selectedVacancy = fastTrackSearchResults[index]
        setFastTrackState('reviewing')
        await handleFastTrackVacancySelect(selectedVacancy.id)
      } else {
        const liaMessage: Message = {
          id: `lia-select-error-${Date.now()}`,
          role: 'assistant',
          content: `Número inválido. Por favor, escolha um número de 1 a ${fastTrackSearchResults.length}.`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, liaMessage])
      }
      return true
    }
    if (intent === 'criteria' || fastTrackState === 'collecting_criteria') {
      const criteria: VacancySearchCriteria = {}
      const wantsToListAll = /(?:lista|listar|mostrar|ver|quais|todas|exibir|apresentar)\s*(?:as|as\s+vagas|vagas|anteriores|recentes|últimas|existentes)?/i.test(content)
      const titleMatch = content.match(/(?:desenvolvedor|analista|gerente|coordenador|engenheiro|designer|product|ux|ui|frontend|backend|fullstack|devops|data|cientista|tech lead|architect)[^\s,.]*/gi)
      if (titleMatch) criteria.title = titleMatch[0]
      const managerMatch = content.match(/(?:do|da|equipe do|equipe da|gestor)\s+([A-Z][a-zà-ú]+(?:\s+[A-Z][a-zà-ú]+)?)/i)
      if (managerMatch) criteria.manager = managerMatch[1]
      const deptMatch = content.match(/(?:área|departamento|setor|time|equipe)\s+(?:de\s+)?([A-Za-zà-ú\s]+)/i)
      if (deptMatch) criteria.department = deptMatch[1].trim()
      setFastTrackSearchCriteria(criteria)

      if (Object.keys(criteria).length > 0 || wantsToListAll) {
        const liaMessage: Message = {
          id: `lia-searching-${Date.now()}`,
          role: 'assistant',
          content: wantsToListAll && Object.keys(criteria).length === 0
            ? '🔍 Buscando suas vagas mais recentes...'
            : '🔍 Buscando vagas anteriores...',
          timestamp: new Date(),
          isProcessing: true,
          processingState: 'searching'
        }
        setMessages(prev => [...prev, liaMessage])
        await handleFastTrackSearch(criteria)
        setMessages(prev => prev.filter(m => m.id !== liaMessage.id))
      } else {
        const liaMessage: Message = {
          id: `lia-criteria-help-${Date.now()}`,
          role: 'assistant',
          content: 'Preciso de mais informações para buscar. Me diga:\n\n• **Cargo** - "Desenvolvedor Python", "Analista de Dados"\n• **Gestor** - "equipe do João", "área do Ricardo"\n• **Departamento** - "área de tecnologia", "time de produto"\n\nOu digite **"listar todas"** para ver as vagas mais recentes.',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, liaMessage])
      }
      return true
    }
    if (intent === 'from_scratch') {
      setWizardMode('create_from_scratch')
      setIsPanelOpen(true)
      const liaMessage: Message = {
        id: `lia-switch-${Date.now()}`,
        role: 'assistant',
        content: FROM_SCRATCH_ORIENTATION_MESSAGE,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, liaMessage])
      return true
    }

    return false
  }

  // ── Interceptor 9: compensation message handling ───────────────────────────
  const _handleCompensationMessage = async (content: string): Promise<boolean> => {
    const lowerContent = content.toLowerCase().trim()
    const hasCompensationMessage = messages.some(m => m.messageType === 'compensation')
    if (!hasCompensationMessage) return false

    const thinkingId = `thinking-interpret-${Date.now()}`
    const thinkingMessage: Message = {
      id: thinkingId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      processingState: 'thinking' as const
    }
    setMessages(prev => [...prev, thinkingMessage])

    try {
      const interpretation = await interpretMessage({
        message: content,
        current_stage: currentStage,
        context: {
          filled_fields: Object.keys(detectedCriteria).filter(k => (detectedCriteria as Record<string, any>)[k]),
          has_compensation: true,
          salary_min: salaryInfo.minSalary,
          salary_max: salaryInfo.maxSalary
        }
      })

      setMessages(prev => prev.filter(m => m.id !== thinkingId))
      console.log('AI Interpretation:', interpretation)

      const MIN_CONFIDENCE = 0.65
      const isHighConfidence = interpretation.confidence >= MIN_CONFIDENCE

      if (isHighConfidence && (interpretation.action === 'confirm' || interpretation.action === 'advance_stage' || interpretation.should_advance)) {
        if (interpretation.extracted_entities && Object.keys(interpretation.extracted_entities).length > 0) {
          if (interpretation.extracted_entities.salario_min) {
            setSalaryInfo(prev => ({ ...prev, minSalary: interpretation.extracted_entities!.salario_min.toString() }))
          }
          if (interpretation.extracted_entities.salario_max) {
            setSalaryInfo(prev => ({ ...prev, maxSalary: interpretation.extracted_entities!.salario_max.toString() }))
          }
        }
        const minSal = parseInt(salaryInfo.minSalary) || 0
        const maxSal = parseInt(salaryInfo.maxSalary) || 0
        if (!(minSal > 0 && maxSal > 0)) {
          const askSalaryMsg: Message = {
            id: `ask-salary-${Date.now()}`,
            role: 'assistant',
            content: '💰 Antes de avançar, preciso confirmar a faixa salarial. Qual é o salário mínimo e máximo para esta vaga?',
            timestamp: new Date()
          }
          setMessages(prev => [...prev, askSalaryMsg])
          return true
        }
        if (minSal > maxSal) {
          const warningMsg: Message = {
            id: `salary-order-warning-${Date.now()}`,
            role: 'assistant',
            content: '⚠️ O salário mínimo não pode ser maior que o máximo. Por favor, corrija os valores.',
            timestamp: new Date()
          }
          setMessages(prev => [...prev, warningMsg])
          return true
        }
        setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
        setCompensationAnalysis(null)
        const confirmMessage: Message = {
          id: `confirm-compensation-${Date.now()}`,
          role: 'assistant',
          content: interpretation.lia_response || '✅ **Valores de remuneração confirmados!**\n\nAvançando para a próxima etapa...',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, confirmMessage])
        setTimeout(() => { goToNextStage() }, 1500)
        return true
      }

      if (isHighConfidence && (interpretation.action === 'update_field' || interpretation.action === 'provide_data')) {
        if (interpretation.extracted_entities) {
          const newMin = interpretation.extracted_entities.salario_min
          const newMax = interpretation.extracted_entities.salario_max
          if (newMin || newMax) {
            const minVal = newMin || parseInt(salaryInfo.minSalary) || 0
            const maxVal = newMax || parseInt(salaryInfo.maxSalary) || 0
            if (minVal > 0 && maxVal > 0 && minVal > maxVal) {
              const warningMessage: Message = {
                id: `salary-warning-${Date.now()}`,
                role: 'assistant',
                content: '⚠️ O salário mínimo não pode ser maior que o máximo. Por favor, informe os valores corretos.',
                timestamp: new Date()
              }
              setMessages(prev => [...prev, warningMessage])
              return true
            }
            if (newMin) setSalaryInfo(prev => ({ ...prev, minSalary: newMin.toString() }))
            if (newMax) setSalaryInfo(prev => ({ ...prev, maxSalary: newMax.toString() }))
            setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
            setCompensationAnalysis(null)
            const formatCurrency = (value: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0 }).format(value)
            const updateMessage: Message = {
              id: `update-salary-${Date.now()}`,
              role: 'assistant',
              content: `✅ **Valores atualizados!**\n\n• Mínimo: ${formatCurrency(minVal)}\n• Máximo: ${formatCurrency(maxVal)}\n\nVocê pode confirmar ou ajustar novamente.`,
              timestamp: new Date()
            }
            setMessages(prev => [...prev, updateMessage])
            return true
          }
        }
      }

      if (interpretation.action === 'reject') {
        const rejectMessage: Message = {
          id: `reject-${Date.now()}`,
          role: 'assistant',
          content: interpretation.lia_response || 'Entendido. O que você gostaria de ajustar?',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, rejectMessage])
        return true
      }

      if (interpretation.action === 'help') {
        const helpMessage: Message = {
          id: `help-${Date.now()}`,
          role: 'assistant',
          content: interpretation.lia_response || '💡 **Ajuda - Etapa de Remuneração**\n\nVocê pode:\n• **Confirmar** os valores atuais\n• **Aceitar sugestões** de mercado\n• **Ajustar** para novos valores (ex: "quero salário de 10 a 15 mil")\n• Pedir para **avançar** para próxima etapa',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, helpMessage])
        return true
      }

      if (interpretation.clarification_needed && interpretation.clarification_question) {
        const clarifyMessage: Message = {
          id: `clarify-${Date.now()}`,
          role: 'assistant',
          content: interpretation.clarification_question,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, clarifyMessage])
        return true
      }

      // action === 'ask_question' or low confidence — fall through to fallback patterns

    } catch (error) {
      console.error('AI interpretation failed, using fallback:', error)
      setMessages(prev => prev.filter(m => m.id !== thinkingId))
    }

    // Fallback pattern matching
    const isConfirmCommand = lowerContent === 'confirmar' || lowerContent.includes('confirmo') ||
      lowerContent.includes('manter valores') || lowerContent.includes('manter atual') ||
      lowerContent.includes('próximo') || lowerContent.includes('proximo') ||
      lowerContent.includes('continuar') || lowerContent.includes('avançar') ||
      lowerContent.includes('avancar') || lowerContent.includes('próximo passo') ||
      lowerContent.includes('proximo passo') || lowerContent.includes('prosseguir') ||
      lowerContent.includes('vamos para') || lowerContent.includes('pode avançar') ||
      lowerContent.includes('ok') || lowerContent === 'sim' || lowerContent === 'ok'

    if (isConfirmCommand) {
      const minSal = parseInt(salaryInfo.minSalary) || 0
      const maxSal = parseInt(salaryInfo.maxSalary) || 0
      if (!(minSal > 0 && maxSal > 0)) {
        const askSalaryMsg: Message = {
          id: `ask-salary-fallback-${Date.now()}`,
          role: 'assistant',
          content: '💰 Antes de continuar, preciso da faixa salarial completa. Qual é o salário mínimo e máximo para esta vaga?',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, askSalaryMsg])
        return true
      }
      if (minSal > maxSal) {
        const warningMsg: Message = {
          id: `salary-order-fallback-${Date.now()}`,
          role: 'assistant',
          content: '⚠️ O salário mínimo não pode ser maior que o máximo. Por favor, corrija os valores.',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, warningMsg])
        return true
      }
      setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
      setCompensationAnalysis(null)
      const confirmMessage: Message = {
        id: `confirm-compensation-fallback-${Date.now()}`,
        role: 'assistant',
        content: '✅ **Valores de remuneração confirmados!**\n\nAvançando para a próxima etapa...',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, confirmMessage])
      setTimeout(() => { goToNextStage() }, 1500)
      return true
    }

    if (lowerContent.includes('aceitar sugest') || lowerContent.includes('aplicar sugest')) {
      const analysis = compensationAnalysis
      if (analysis) {
        if (analysis.salary.suggestion) {
          setSalaryInfo(prev => ({
            ...prev,
            minSalary: analysis.salary.suggestion!.min.toString(),
            maxSalary: analysis.salary.suggestion!.max.toString()
          }))
        }
        if (analysis.bonus.suggestion) {
          setSalaryInfo(prev => ({
            ...prev,
            minBonus: analysis.bonus.suggestion!.toString(),
            maxBonus: analysis.bonus.suggestion!.toString()
          }))
        }
        if (analysis.benefits.missingFromStandard && analysis.benefits.missingFromStandard.length > 0) {
          const newBenefits = analysis.benefits.missingFromStandard.map(b => ({ id: b.id, name: b.name, value: b.value, enabled: true }))
          setSalaryInfo(prev => ({
            ...prev,
            benefits: [...prev.benefits, ...newBenefits.filter(nb => !prev.benefits.some(pb => pb.id === nb.id))]
          }))
        }
      }
      setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
      setCompensationAnalysis(null)
      const confirmMessage: Message = {
        id: `apply-suggestions-${Date.now()}`,
        role: 'assistant',
        content: '✅ **Sugestões aplicadas!**\n\nOs valores foram atualizados conforme as recomendações de mercado.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, confirmMessage])
      setTimeout(() => { goToNextStage() }, 1500)
      return true
    }

    const adjustMatch = lowerContent.match(/ajust(?:ar|e)?\s*(?:para)?\s*(?:r\$?\s*)?(\d+[\d.,]*)\s*(?:a|até|-|–|\/)\s*(?:r\$?\s*)?(\d+[\d.,]*)/i)
    if (adjustMatch) {
      const minValue = parseInt(adjustMatch[1].replace(/[.,]/g, ''))
      const maxValue = parseInt(adjustMatch[2].replace(/[.,]/g, ''))
      setSalaryInfo(prev => ({ ...prev, minSalary: minValue.toString(), maxSalary: maxValue.toString() }))
      setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
      setCompensationAnalysis(null)
      const formatCurrency = (value: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0 }).format(value)
      const confirmMessage: Message = {
        id: `adjust-salary-fallback-${Date.now()}`,
        role: 'assistant',
        content: `✅ **Faixa salarial atualizada!**\n\n• Mínimo: ${formatCurrency(minValue)}\n• Máximo: ${formatCurrency(maxValue)}\n\nVocê pode confirmar ou ajustar novamente.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, confirmMessage])
      return true
    }

    return false
  }

  // ── Interceptor 10: local command handling (navigation & edit) ─────────────
  const _handleLocalCommands = (content: string): boolean => {
    if (!isInJobCreationMode || wizardMode !== 'create_from_scratch' || currentStage === 'input-evaluation') return false

    const parsedCommand = parseCommand(content)

    if (parsedCommand.type === 'navigate') {
      const navCommand = parsedCommand as ParsedNavigationCommand
      const targetStage = navCommand.target
      const targetStageIndex = WIZARD_STAGES.findIndex(s => s.id === targetStage)
      const currentStageIndex = WIZARD_STAGES.findIndex(s => s.id === currentStage)

      if (targetStage === currentStage) {
        const alreadyHereMessage: Message = {
          id: `nav-already-here-${Date.now()}`,
          role: 'assistant',
          content: `Você já está na etapa de **${getStageLabel(targetStage)}**. Como posso ajudar?`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, alreadyHereMessage])
        return true
      }
      if (targetStageIndex < currentStageIndex) {
        setCurrentStage(targetStage)
        const navSuccessMessage: Message = {
          id: `nav-success-${Date.now()}`,
          role: 'assistant',
          content: `✅ Navegando para a etapa de **${getStageLabel(targetStage)}**.\n\nVocê pode revisar e ajustar os campos conforme necessário.`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, navSuccessMessage])
        return true
      }
      const stageConfig = WIZARD_STAGES.find(s => s.id === currentStage)
      if (stageConfig) {
        setCurrentStage(targetStage)
        const navForwardMessage: Message = {
          id: `nav-forward-${Date.now()}`,
          role: 'assistant',
          content: `✅ Navegando para a etapa de **${getStageLabel(targetStage)}**.\n\n💡 *Dica: Lembre-se de revisar as etapas anteriores antes de finalizar.*`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, navForwardMessage])
        return true
      }
    }

    if (parsedCommand.type === 'edit') {
      const editCommand = parsedCommand as ParsedEditCommand

      if (editCommand.field === 'salary' && editCommand.value) {
        const salaryResult = parseSalaryValue(String(editCommand.value))
        if (salaryResult.isValid) {
          const { updated, changes } = applySalaryUpdate(salaryInfo, salaryResult)
          if (updated.minSalary !== salaryInfo.minSalary) {
            trackFieldChange({ field: 'minSalary', oldValue: salaryInfo.minSalary, newValue: updated.minSalary, source: 'chat' })
          }
          if (updated.maxSalary !== salaryInfo.maxSalary) {
            trackFieldChange({ field: 'maxSalary', oldValue: salaryInfo.maxSalary, newValue: updated.maxSalary, source: 'chat' })
          }
          setSalaryInfo(updated)
          setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
          setCompensationAnalysis(null)
          const confirmMessage: Message = {
            id: `edit-salary-${Date.now()}`,
            role: 'assistant',
            content: `✅ **Salário atualizado!**\n\n${changes.length > 0 ? changes.join('\n') : `Faixa salarial definida: ${salaryResult.formatted}`}\n\n*Você pode confirmar ou ajustar novamente.*`,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, confirmMessage])
          if (currentStage !== 'salary') setCurrentStage('salary')
          return true
        } else {
          const errorMessage: Message = {
            id: `edit-salary-error-${Date.now()}`,
            role: 'assistant',
            content: `❌ Não consegui entender o valor do salário. Por favor, use formatos como:\n• "15k" (para R$ 15.000)\n• "R$ 10.000 a R$ 15.000"\n• "10k a 15k"`,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, errorMessage])
          return true
        }
      }

      if (editCommand.field === 'skill' && editCommand.value) {
        const skillName = String(editCommand.value)
        if (editCommand.action === 'add') {
          const result = addSkillIfNotExists(technicalSkills, skillName)
          if (result.added) {
            trackFieldChange({ field: 'technicalSkill', oldValue: null, newValue: { name: skillName }, source: 'chat' })
            setTechnicalSkills(result.skills)
          }
          const confirmMessage: Message = {
            id: `edit-skill-add-${Date.now()}`,
            role: 'assistant',
            content: result.added
              ? `✅ **Skill adicionada:** ${skillName}\n\n*A nova skill aparece no painel de competências.*`
              : `ℹ️ ${result.message}`,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, confirmMessage])
          if (currentStage !== 'competencies') setCurrentStage('competencies')
          return true
        }
        if (editCommand.action === 'remove') {
          const result = removeSkillByName(technicalSkills, skillName)
          if (result.removed) {
            trackFieldChange({ field: 'technicalSkill', oldValue: { name: skillName }, newValue: null, source: 'chat' })
            setTechnicalSkills(result.skills)
          }
          const confirmMessage: Message = {
            id: `edit-skill-remove-${Date.now()}`,
            role: 'assistant',
            content: result.removed
              ? `✅ **Skill removida:** ${skillName}`
              : `ℹ️ ${result.message}`,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, confirmMessage])
          if (currentStage !== 'competencies') setCurrentStage('competencies')
          return true
        }
      }
    }

    return false
  }

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

      console.log('[SmartOrchestrate] Using smart-orchestrate response (confidence:', orchestratorResult.confidence, ')')
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
          const evalResultAny = evalResult as any
          if (evalResultAny?.technical_skills || evalResultAny?.behavioral_competencies) {
            const technicalSuggestions = (evalResultAny.technical_skills || []).map((skill: any) => ({
              name: skill.name || skill, level: skill.level || 'Intermediário', weight: skill.weight || 3,
              weightJustification: skill.weight_justification || 'Baseado em análise de mercado',
              source: skill.source || 'market_benchmark', required: skill.required ?? true, category: skill.category || 'tool'
            }))
            const behavioralSuggestions = (evalResultAny.behavioral_competencies || []).map((comp: any) => ({
              name: comp.name || comp, weight: comp.weight || 3, justification: comp.justification || '',
              weightJustification: comp.weight_justification || 'Baseado em histórico da empresa', source: comp.source || 'company_history'
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
        }).catch((err) => { console.error('Error calling evaluation step:', err) })
      }
    } catch (error) {
      console.error('Error in wizard step:', error)
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
          if ((orchestratedResponse.ui_action_params as any)?.initial_message) {
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
          responseText = orchestratorResponse.message || orchestratorResponse.result?.message || responseText
          if (conversationMemory.conversationId) {
            conversationMemory.addMessage('assistant', responseText, orchestratorResponse.intent).catch(() => {})
          }
          const suggestedToolCall = orchestratorResponse.suggested_tool_call || orchestratorResponse.result?.suggested_tool_call
          if (suggestedToolCall) {
            const toolCall: ToolCall = {
              tool_name: suggestedToolCall.tool_name,
              parameters: suggestedToolCall.parameters || {},
              requires_confirmation: suggestedToolCall.requires_confirmation !== false,
              confirmation_message: suggestedToolCall.confirmation_message || responseText,
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
                console.error('[ToolCalling] Error executing tool directly:', error)
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
      console.error('Error sending message:', error)
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
