"use client"

import { useState, useRef } from "react"
import { useAuth } from "@/contexts/auth-context"
import { useCompanyId } from "@/hooks/useCompanyId"
import { useCompanyEligibilityQuestions } from "@/hooks/use-company-eligibility-questions"
import { useCompanyLiaInstructions } from "@/hooks/use-company-lia-instructions"
import { useRecruitmentStages } from "@/hooks/use-recruitment-stages"
import { type AnalysisResult, type AnalysisType } from "@/components/chat/multimodal-upload"
import { type FieldOrigin } from "../../job-creation/field-origin-badge"
import {
  type DetectedCriteria,
  type BasicInfoFields,
  type WizardStage,
  WIZARD_STAGES,
  PRE_WIZARD_MESSAGE,
  INITIAL_GENERAL_MESSAGE,
} from '..'
import {
  useWSIState, useCalibrationState, useSalaryState,
  useCompetenciesState, usePublishingState, useFastTrackState,
} from '.'
import { useCheckForExistingDraftSync } from "./useExpandedChatCallbacks"
import { useChatStateStore } from '@/stores/chat-state-store'
import { useWizardStageConstants } from './useWizardStageConstants'
import { useExpandedChatPanelState } from "./useExpandedChatPanelState"
import { type EnrichedJDData } from '../stages'
import { type Message } from '../types'

export function useExpandedChatCoreState(mode: string = 'general') {
  const { user } = useAuth()
  const { companyId: resolvedCompanyId } = useCompanyId()
  const { questions: companyEligibilityQuestions, isLoading: isLoadingEligibilityQuestions } = useCompanyEligibilityQuestions()
  const { interviewStages, sla, isLoading: isLoadingStages } = useRecruitmentStages()
  const { getBehavioralCompetencies, isLoading: isLoadingCompanyConfig } = useCompanyLiaInstructions()
  const isJobCreationMode = mode === 'job-creation'

  const wsiHook = useWSIState()
  const calibrationHook = useCalibrationState()
  const salaryHook = useSalaryState()
  const competenciesHook = useCompetenciesState()
  const publishingHook = usePublishingState()
  const fastTrackHook = useFastTrackState()

  const { state: wsiState, actions: wsiActions } = wsiHook
  const { state: calibrationState, actions: calibrationActions, postCalibrationFlowStartedRef } = calibrationHook
  const { state: salaryState, actions: salaryActions } = salaryHook
  const { state: competenciesState, actions: competenciesActions } = competenciesHook
  const { state: publishingState, actions: publishingActions } = publishingHook
  const { state: fastTrackHookState, actions: fastTrackActions } = fastTrackHook

  const [dynamicInitialMessage, setDynamicInitialMessage] = useState<string | null>(null)
  const initialLiaMessage = dynamicInitialMessage || (isJobCreationMode ? PRE_WIZARD_MESSAGE : INITIAL_GENERAL_MESSAGE)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [fileAnalysisResult, setFileAnalysisResult] = useState<AnalysisResult | null>(null)
  const [fileAnalysisType, setFileAnalysisType] = useState<AnalysisType | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [activeTab, setActiveTab] = useState<'conversa' | 'contexto'>('conversa')
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [proactiveActionIds, setProactiveActionIds] = useState<Set<string>>(new Set())
  const [displayedText, setDisplayedText] = useState("")
  const [isTypingEffect, setIsTypingEffect] = useState(false)
  const [detectedCriteria, setDetectedCriteria] = useState<DetectedCriteria>({
    cargo: null, gestorArea: null, responsabilidades: [], competenciasTecnicas: [],
    competenciasComportamentais: [], idiomas: [], senioridadeIdiomas: null,
    modeloTrabalho: null, localizacao: null, tipoContrato: null, salario: null,
    departamento: null, isAffirmative: null, affirmativeCriteriaPrimary: null,
    affirmativeCriteriaSecondary: null, affirmativeDescription: null,
    experienciaMinima: null, formacao: [], certificacoes: [], ferramentas: [],
    diasPresenciais: null, beneficiosMencionados: [], bonus: null,
    viagensFrequentes: null, disponibilidade: null, cnh: null, horario: null
  })

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const extractCriteriaDebounceRef = useRef<NodeJS.Timeout | null>(null)
  const salaryProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const competenciesProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const inputEvaluationProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const wsiQuestionsProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const calibrationProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const [showMoreIdeas, setShowMoreIdeas] = useState(false)
  const [activeInputTab, setActiveInputTab] = useState<'ia-natural' | 'job-description' | 'templates'>('ia-natural')
  const [internalJobCreationMode, setInternalJobCreationMode] = useState(false)
  const [generatedJobDescription, setGeneratedJobDescription] = useState<string>('')

  const { wizardMode, fastTrackState, fastTrackSearchResults, fastTrackSelectedVacancy, fastTrackAdjustments, fastTrackSearchCriteria, isSearchingVacancies, wizardFastTrackSourceJobId } = fastTrackHookState
  const { setWizardMode, setFastTrackState, setFastTrackSearchResults, setFastTrackSelectedVacancy, setFastTrackAdjustments, setFastTrackSearchCriteria, setIsSearchingVacancies, setWizardFastTrackSourceJobId } = fastTrackActions

  const panelState = useExpandedChatPanelState({ isJobCreationMode, wizardMode })
  const { panelWidth, setPanelWidth, isResizing, setIsResizing, resizeRef, isPanelOpen, setIsPanelOpen, stageTransition, setStageTransition, isFullscreen, setIsFullscreen } = panelState

  const [activeToolConfirmationMessageId, setActiveToolConfirmationMessageId] = useState<string | null>(null)
  const [currentStage, setCurrentStage] = useState<WizardStage>('input-evaluation')
  const currentStageConfig = WIZARD_STAGES.find(s => s.id === currentStage) || WIZARD_STAGES[0]
  const currentStageIndex = WIZARD_STAGES.findIndex(s => s.id === currentStage)

  const [wizardDraftId] = useState(() => {
    const store = useChatStateStore.getState()
    const existingId = store.wizardDraftId
    if (existingId) return existingId
    const newId = `draft-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    useChatStateStore.getState().setWizardDraftId(newId)
    return newId
  })

  const { STAGE_DISPLAY_NAMES, INITIAL_STAGES } = useWizardStageConstants()
  const { checkForExistingDraftSync, checkForExistingDraftFromBackend } = useCheckForExistingDraftSync({ STAGE_DISPLAY_NAMES, INITIAL_STAGES })

  const [basicInfoFields, setBasicInfoFields] = useState<BasicInfoFields>({
    cargo: '', area: '', gestor: '', localidade: '', modeloTrabalho: '', tipoContrato: ''
  })

  const { technicalSkills, behavioralCompetencies } = competenciesState
  const { setTechnicalSkills, setBehavioralCompetencies } = competenciesActions
  const { salaryInfo } = salaryState
  const { setSalaryInfo } = salaryActions

  const [enrichedJDData, setEnrichedJDData] = useState<EnrichedJDData | null>(null)
  const [isLoadingEnrichment, setIsLoadingEnrichment] = useState(false)
  const [inputEvaluationStageCompletionShown, setInputEvaluationStageCompletionShown] = useState(false)
  const [salaryStageCompletionShown, setSalaryStageCompletionShown] = useState(false)
  const [competenciesStageCompletionShown, setCompetenciesStageCompletionShown] = useState(false)
  const [wsiQuestionsStageCompletionShown, setWsiQuestionsStageCompletionShown] = useState(false)
  const [calibrationStageCompletionShown, setCalibrationStageCompletionShown] = useState(false)
  const [awaitingStageAdvanceConfirmation, setAwaitingStageAdvanceConfirmation] = useState<string | null>(null)
  const PROACTIVE_MESSAGE_DELAY = 6000

  const { wsiQuestions, wsiCandidates, wsiGenerationBatch, isGeneratingWSI, wsiHasGenerated, useCompanyQuestions, companyDefaultQuestions, showCustomQuestionForm, customQuestionText, customQuestionType, customQuestionRequired } = wsiState
  const { setWsiQuestions, setWsiCandidates, setWsiGenerationBatch, setIsGeneratingWSI, setWsiHasGenerated, setUseCompanyQuestions, setCompanyDefaultQuestions, setShowCustomQuestionForm, setCustomQuestionText, setCustomQuestionType, setCustomQuestionRequired } = wsiActions
  const { showAddCompetencyModal, newCompetencyName, newCompetencyJustification, newSkillName, editingCompetency, showAddSkillModal, newSkillCategory, showSkipCompetenciesWarning, competenciesPanelExpanded, showCompetenciesSuggestionsModal, suggestedTechnicalSkills, suggestedBehavioralSkills, selectedSuggestedTechnical, selectedSuggestedBehavioral, showCompetenciesInChat, competenciesChatLoading, competencySuggestions, competenciesTab } = competenciesState
  const { setShowAddCompetencyModal, setNewCompetencyName, setNewCompetencyJustification, setNewSkillName, setEditingCompetency, setShowAddSkillModal, setNewSkillCategory, setShowSkipCompetenciesWarning, setCompetenciesPanelExpanded, setShowCompetenciesSuggestionsModal, setSuggestedTechnicalSkills, setSuggestedBehavioralSkills, setSelectedSuggestedTechnical, setSelectedSuggestedBehavioral, setShowCompetenciesInChat, setCompetenciesChatLoading, setCompetencySuggestions, setCompetenciesTab } = competenciesActions
  const { showAddBenefitModal, newBenefitName, newBenefitValue, salaryPanelExpanded, showAutoFilledNotification } = salaryState
  const { setShowAddBenefitModal, setNewBenefitName, setNewBenefitValue, setSalaryPanelExpanded, setShowAutoFilledNotification } = salaryActions
  const { calibrationCandidates, currentCalibrationIndex, approvedCandidates, rejectedCandidates, calibrationComplete, isLoadingCalibration, showCalibrationModal, calibrationSessionId, awaitingCalibrationChoice, showEditCriteriaModal, candidateProfileTab, calibrationComment, publishedJobId, calibrationCriteria, postCalibrationProcessing, localCandidateCount, globalSearchAuthorized, postCalibrationComplete, hasAttemptedCalibrationGeneration, searchPhase, globalCandidateCount, preferredCandidateCount, showClearDraftConfirm } = calibrationState
  const { setCalibrationCandidates, setCurrentCalibrationIndex, setApprovedCandidates, setRejectedCandidates, setCalibrationComplete, setIsLoadingCalibration, setShowCalibrationModal, setCalibrationSessionId, setAwaitingCalibrationChoice, setShowEditCriteriaModal, setCandidateProfileTab, setCalibrationComment, setPublishedJobId, setCalibrationCriteria, setPostCalibrationProcessing, setLocalCandidateCount, setGlobalSearchAuthorized, setPostCalibrationComplete, setHasAttemptedCalibrationGeneration, setSearchPhase, setGlobalCandidateCount, setPreferredCandidateCount, setShowClearDraftConfirm } = calibrationActions

  const [fieldOrigins, setFieldOrigins] = useState<Record<string, { source: FieldOrigin; confidence: number }>>({})
  const { salaryBenchmark, isLoadingBenchmark, compensationAnalysis } = salaryState
  const { setSalaryBenchmark, setIsLoadingBenchmark, setCompensationAnalysis } = salaryActions

  const { publishingPlatforms, jobConfig, jobDescription, isGeneratingDescription } = publishingState
  const { setPublishingPlatforms, setJobConfig, setJobDescription, setIsGeneratingDescription, updateLanguages } = publishingActions

  const [companyConfig, setCompanyConfig] = useState<{
    workModel?: string; hybridDaysOnsite?: number; employmentTypes?: string[];
    techStack?: string[]; values?: string[]; coreCompetencies?: string[];
    departments?: { id: string, name: string }[];
    benefits?: { name: string, category: string, value?: number, is_active: boolean }[];
    evpBullets?: string[]; headquarters?: string; locations?: string[];
  } | null>(null)
  const [configLoaded, setConfigLoaded] = useState(false)
  const [fieldsFromConfig, setFieldsFromConfig] = useState<Set<string>>(new Set())

  const [wizardGreeting, setWizardGreeting] = useState<{
    greeting_message: string;
    catalog_status: {
      company_id: string; maturity_score: number;
      maturity_level: 'complete' | 'partial' | 'minimal';
      maturity_factors: string[]; smart_start_enabled: boolean;
      required_fields_for_wizard: string[];
      available_data_summary: string[];
      counts: Record<string, number>; recommendations: string[];
    };
    prefill_data: Record<string, unknown>;
  } | null>(null)
  const [wizardGreetingLoaded, setWizardGreetingLoaded] = useState(false)

  const { fastTrackMessageSent, fastTrackSuggestionsShownTracked, awaitingFastTrackSelection, awaitingSensitiveFieldsConfirmation, fastTrackAppliedData, fastTrackOriginalCompetencies, wsiRegenerationPrompted, awaitingWSIRegenerationConfirmation } = fastTrackHookState
  const { setFastTrackMessageSent, setFastTrackSuggestionsShownTracked, setAwaitingFastTrackSelection, setAwaitingSensitiveFieldsConfirmation, setFastTrackAppliedData, setFastTrackOriginalCompetencies, setWsiRegenerationPrompted, setAwaitingWSIRegenerationConfirmation, resetFastTrackConversationState } = fastTrackActions

  return {
    user, resolvedCompanyId, companyEligibilityQuestions, isLoadingEligibilityQuestions,
    interviewStages, sla, isLoadingStages,
    getBehavioralCompetencies, isLoadingCompanyConfig,
    isJobCreationMode, postCalibrationFlowStartedRef,
    publishingState, publishingActions,
    dynamicInitialMessage, setDynamicInitialMessage, initialLiaMessage,
    messages, setMessages, inputValue, setInputValue,
    isLoading, setIsLoading, uploadedFile, setUploadedFile,
    fileAnalysisResult, setFileAnalysisResult, fileAnalysisType, setFileAnalysisType,
    showUploadModal, setShowUploadModal, fileInputRef,
    activeTab, setActiveTab, conversationId, setConversationId,
    proactiveActionIds, setProactiveActionIds,
    displayedText, setDisplayedText, isTypingEffect, setIsTypingEffect,
    detectedCriteria, setDetectedCriteria,
    messagesEndRef, inputRef, typingTimeoutRef, extractCriteriaDebounceRef,
    salaryProactiveTimerRef, competenciesProactiveTimerRef,
    inputEvaluationProactiveTimerRef, wsiQuestionsProactiveTimerRef,
    calibrationProactiveTimerRef,
    showMoreIdeas, setShowMoreIdeas,
    activeInputTab, setActiveInputTab,
    internalJobCreationMode, setInternalJobCreationMode,
    generatedJobDescription, setGeneratedJobDescription,
    wizardMode, fastTrackState, fastTrackSearchResults, fastTrackSelectedVacancy,
    fastTrackAdjustments, fastTrackSearchCriteria, isSearchingVacancies, wizardFastTrackSourceJobId,
    setWizardMode, setFastTrackState, setFastTrackSearchResults, setFastTrackSelectedVacancy,
    setFastTrackAdjustments, setFastTrackSearchCriteria, setIsSearchingVacancies, setWizardFastTrackSourceJobId,
    panelWidth, setPanelWidth, isResizing, setIsResizing, resizeRef,
    isPanelOpen, setIsPanelOpen, stageTransition, setStageTransition,
    isFullscreen, setIsFullscreen,
    activeToolConfirmationMessageId, setActiveToolConfirmationMessageId,
    currentStage, setCurrentStage, currentStageConfig, currentStageIndex,
    wizardDraftId, STAGE_DISPLAY_NAMES, INITIAL_STAGES, checkForExistingDraftSync, checkForExistingDraftFromBackend,
    basicInfoFields, setBasicInfoFields,
    technicalSkills, setTechnicalSkills,
    behavioralCompetencies, setBehavioralCompetencies,
    salaryInfo, setSalaryInfo,
    enrichedJDData, setEnrichedJDData,
    isLoadingEnrichment, setIsLoadingEnrichment,
    inputEvaluationStageCompletionShown, setInputEvaluationStageCompletionShown,
    salaryStageCompletionShown, setSalaryStageCompletionShown,
    competenciesStageCompletionShown, setCompetenciesStageCompletionShown,
    wsiQuestionsStageCompletionShown, setWsiQuestionsStageCompletionShown,
    calibrationStageCompletionShown, setCalibrationStageCompletionShown,
    awaitingStageAdvanceConfirmation, setAwaitingStageAdvanceConfirmation,
    PROACTIVE_MESSAGE_DELAY,
    wsiQuestions, setWsiQuestions, wsiCandidates, setWsiCandidates,
    wsiGenerationBatch, setWsiGenerationBatch,
    isGeneratingWSI, setIsGeneratingWSI, wsiHasGenerated, setWsiHasGenerated,
    useCompanyQuestions, setUseCompanyQuestions,
    companyDefaultQuestions, setCompanyDefaultQuestions,
    showCustomQuestionForm, setShowCustomQuestionForm,
    customQuestionText, setCustomQuestionText,
    customQuestionType, setCustomQuestionType,
    customQuestionRequired, setCustomQuestionRequired,
    showAddCompetencyModal, setShowAddCompetencyModal,
    newCompetencyName, setNewCompetencyName,
    newCompetencyJustification, setNewCompetencyJustification,
    newSkillName, setNewSkillName, editingCompetency, setEditingCompetency,
    showAddSkillModal, setShowAddSkillModal,
    newSkillCategory, setNewSkillCategory,
    showSkipCompetenciesWarning, setShowSkipCompetenciesWarning,
    competenciesPanelExpanded, setCompetenciesPanelExpanded,
    showCompetenciesSuggestionsModal, setShowCompetenciesSuggestionsModal,
    suggestedTechnicalSkills, setSuggestedTechnicalSkills,
    suggestedBehavioralSkills, setSuggestedBehavioralSkills,
    selectedSuggestedTechnical, setSelectedSuggestedTechnical,
    selectedSuggestedBehavioral, setSelectedSuggestedBehavioral,
    showCompetenciesInChat, setShowCompetenciesInChat,
    competenciesChatLoading, setCompetenciesChatLoading,
    competencySuggestions, setCompetencySuggestions,
    competenciesTab, setCompetenciesTab,
    showAddBenefitModal, setShowAddBenefitModal,
    newBenefitName, setNewBenefitName,
    newBenefitValue, setNewBenefitValue,
    salaryPanelExpanded, setSalaryPanelExpanded,
    showAutoFilledNotification, setShowAutoFilledNotification,
    calibrationCandidates, setCalibrationCandidates,
    currentCalibrationIndex, setCurrentCalibrationIndex,
    approvedCandidates, setApprovedCandidates,
    rejectedCandidates, setRejectedCandidates,
    calibrationComplete, setCalibrationComplete,
    isLoadingCalibration, setIsLoadingCalibration,
    showCalibrationModal, setShowCalibrationModal,
    calibrationSessionId, setCalibrationSessionId,
    awaitingCalibrationChoice, setAwaitingCalibrationChoice,
    showEditCriteriaModal, setShowEditCriteriaModal,
    candidateProfileTab, setCandidateProfileTab,
    calibrationComment, setCalibrationComment,
    publishedJobId, setPublishedJobId,
    calibrationCriteria, setCalibrationCriteria,
    postCalibrationProcessing, setPostCalibrationProcessing,
    localCandidateCount, setLocalCandidateCount,
    globalSearchAuthorized, setGlobalSearchAuthorized,
    postCalibrationComplete, setPostCalibrationComplete,
    hasAttemptedCalibrationGeneration, setHasAttemptedCalibrationGeneration,
    searchPhase, setSearchPhase,
    globalCandidateCount, setGlobalCandidateCount,
    preferredCandidateCount, setPreferredCandidateCount,
    showClearDraftConfirm, setShowClearDraftConfirm,
    fieldOrigins, setFieldOrigins,
    salaryBenchmark, setSalaryBenchmark,
    isLoadingBenchmark, setIsLoadingBenchmark,
    compensationAnalysis, setCompensationAnalysis,
    publishingPlatforms, setPublishingPlatforms,
    jobConfig, setJobConfig,
    jobDescription, setJobDescription,
    isGeneratingDescription, setIsGeneratingDescription,
    updateLanguages,
    companyConfig, setCompanyConfig,
    configLoaded, setConfigLoaded,
    fieldsFromConfig, setFieldsFromConfig,
    wizardGreeting, setWizardGreeting,
    wizardGreetingLoaded, setWizardGreetingLoaded,
    fastTrackMessageSent, setFastTrackMessageSent,
    fastTrackSuggestionsShownTracked, setFastTrackSuggestionsShownTracked,
    awaitingFastTrackSelection, setAwaitingFastTrackSelection,
    awaitingSensitiveFieldsConfirmation, setAwaitingSensitiveFieldsConfirmation,
    fastTrackAppliedData, setFastTrackAppliedData,
    fastTrackOriginalCompetencies, setFastTrackOriginalCompetencies,
    wsiRegenerationPrompted, setWsiRegenerationPrompted,
    awaitingWSIRegenerationConfirmation, setAwaitingWSIRegenerationConfirmation,
    resetFastTrackConversationState,
  }
}
