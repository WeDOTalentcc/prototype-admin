"use client"

  
import React, { useState, useRef, useEffect, useCallback, useMemo } from "react"
import { X, Send, Search, Paperclip, Minimize2, Maximize2, Loader2, Check, Clock, FileText, ChevronRight, ChevronLeft, MessageSquare, ArrowUp, Lightbulb, Brain, Plus, Briefcase, Users, BarChart3, ChevronDown, Target, BookTemplate, Upload, History, Building2, MapPin, DollarSign, GraduationCap, Languages, Laptop, Code, Database, Wrench, Edit2, Star, MessageCircle, CheckCircle2, AlertCircle, Rocket, Eye, Phone, Circle, Settings, AlertTriangle, RefreshCw, Globe, Calendar, Bell, ExternalLink, Info, Heart, TrendingUp, User } from "lucide-react"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { Button } from "@/components/ui/button"
import { VoiceChatButton } from "@/components/chat/voice-chat-button"
import { MultimodalUpload, type AnalysisResult, type AnalysisType } from "@/components/chat/multimodal-upload"
import { ResumeAnalysisResult } from "@/components/chat/resume-analysis-result"
import { ActionResultCard } from "@/components/chat/action-result-card"
import { DetectedFieldsCard } from "@/components/chat/detected-fields-card"
import { ParecerLIACard, type ParecerLIAData } from "@/components/chat/parecer-lia-card"
import { type ResumeAnalysisResponse } from "@/services/lia-api"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { cn } from "@/lib/utils"
import { liaApi, CalibrationCandidate as ApiCalibrationCandidate, interpretMessage, getConversationalResponse, orchestrateWizardMessage, orchestratorProcess, type WizardOrchestratorResponse } from "@/services/lia-api"
import { textStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"
import { useAuth } from "@/components/auth-context"
import { LIASimpleProcessing, LIAFeedbackButtons, LIAProcessingCard, type LIATaskStep as LIATaskStepType } from "@/components/lia-processing-card"
import { LiaVacancyQueriesGuide } from "@/components/ui/lia-vacancy-queries-guide"
import { useJobWizard } from "@/hooks/use-lia-suggestions"
import { useCompanyEligibilityQuestions } from "@/hooks/use-company-eligibility-questions"
import { useCompanyLiaInstructions } from "@/hooks/use-company-lia-instructions"
import { useRecruitmentStages } from "@/hooks/use-recruitment-stages"
import { useJobWizardBackend } from "@/hooks/use-job-wizard-backend"
import { useWizardAutoSave } from "@/hooks/use-wizard-auto-save"
import { FieldOriginBadge, type FieldOrigin } from "../../job-creation/field-origin-badge"
import { ConfidenceIndicator } from "../../job-creation/confidence-indicator"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { CompensationChatMessage } from "../../job-creation/compensation-chat-message"
import { CompetenciesChatMessage, type TechnicalSkillSuggestion, type BehavioralCompetencySuggestion } from "../../job-creation/competencies-chat-message"
import { VacancySearchResults, type VacancySummary } from "../../job-creation/vacancy-search-results"
import { VacancyFullSummary, type VacancyFullDetails } from "../../job-creation/vacancy-full-summary"
import { type VacancySearchCriteria, type VacancyAdjustments } from "@/services/lia-api"
import { MessageFeedback } from "../../chat/message-feedback"
import {
  ExpandedChatProvider,
  useExpandedChatContext,
  type TechnicalSkill,
  type BehavioralCompetency,
  type Benefit,
  type SalaryInfo,
  type WSIQuestion,
  type DetectedCriteria,
  type BasicInfoFields,
  type WizardStage,
  type WizardPhase,
  type WizardPhaseConfig,
  type ExtendedWizardStageConfig,
  WIZARD_PHASES,
  WIZARD_STAGES,
  FRONTEND_TO_BACKEND_STAGE,
  BACKEND_TO_FRONTEND_STAGE,
  getBackendStageNumber,
  getFrontendStageFromBackend,
  getStageTransitionMessage,
  getMissingCriticalFields,
  generateMissingFieldsMessage,
  PRE_WIZARD_MESSAGE,
  DRAFT_DETECTED_MESSAGE,
  INITIAL_JOB_CREATION_MESSAGE,
  FROM_SCRATCH_ORIENTATION_MESSAGE,
  INITIAL_GENERAL_MESSAGE,
} from '..'
import { useWizardState, useWSIQualityGates, useWizardNavigation, useChatSync, useToolCalling, useFieldHighlight, useWSIState, useCalibrationState, useSalaryState, useCompetenciesState, usePublishingState, useFastTrackState, type ChatNavigationResult, type GroupedChange, type ToolCall, type ToolExecutionResult } from '.'
import { useSendMessageHandlers, type SendMessageHandlersContext } from './useSendMessageHandlers'
import { useWizardPublishHandlers } from './useWizardPublishHandlers'
import { useWSIAndCalibrationHandlers } from './useWSIAndCalibrationHandlers'
import { useConversationMemory } from './useConversationMemory'
import { useLearning } from './useLearning'
import { useFastTrack, type FastTrackSuggestion, type FastTrackJobData } from '@/hooks/useFastTrack'
import { FastTrackSuggestions } from '../../job-wizard/FastTrackSuggestions'
import { extractCriteriaFromText as _extractCriteria } from "./expandedChatCriteriaExtractor"
import { useProactiveHandlers, useGroupedPanelChangeHandler, useCheckForExistingDraftSync } from "./useExpandedChatCallbacks"
import { useExpandedChatEffects } from "./useExpandedChatEffects"
import { useExpandedChatSubHooks } from "./useExpandedChatSubHooks"
import { FastTrackReviewPanel } from '../../job-wizard/FastTrackReviewPanel'
import { useWizardAnalytics } from './useWizardAnalytics'
import { useContextSwitching, type WizardSnapshot, type GeneralChatSnapshot } from './useContextSwitching'
import { ToolConfirmationMessage, ToolExecutionFeedback, ChatMessageList, ExpandedChatInput, WizardRightPanel } from '../components'
import { type EnrichedJDData } from '../stages'
import {
  parseCommand,
  isLocalCommand,
  getStageLabel,
  parseSalaryValue,
  applySalaryUpdate,
  addSkillIfNotExists,
  removeSkillByName,
  createTechnicalSkill,
  generateUpdateConfirmation,
  type ParsedCommand,
  type ParsedNavigationCommand,
  type ParsedEditCommand,
} from '../utils'
import {
  type WSIQuestionCandidate,
  type CalibrationCandidateExperience,
  type CalibrationCandidateEducation,
  type CalibrationMatchCriteria,
  type CalibrationCandidate,
  type WizardDraftData,
  type Message,
  type WizardMode,
  type FastTrackState,
  type ExpandedChatModalProps,
} from '../types'
import {
  inferSkillWeight,
  inferTechnicalSkillWeight,
  inferBehavioralSkillWeight,
  detectAreaFromRole,
  getSkillSuggestions,
  detectSeniorityLevel,
  isLeadershipRole,
  isCommercialRole,
  isTechnicalRole,
  getCoreSkillsForRole,
} from '../utils/skill-weight-utils'
import { ClearDraftConfirmModal, EditCriteriaModal, AddTechnicalSkillModal, AddCompetencyModal, AddBenefitModal, SkipCompetenciesWarningModal, CalibrationProfileModal } from '../modals'


  export function useExpandedChatModalCore({
    isOpen,
    onClose,
    onMinimize,
    initialMessage,
    initialMessages,
    contextTitle = "Criação de Vaga",
    inline = false,
    mode = 'general',
    onJobCreated,
    onReturnToLateral,
    hideModeButtons = false,
    onOrchestratedMessage,
    onFullscreenChange,
    onMessagesUpdate
  }: ExpandedChatModalProps) {
    const { user } = useAuth()
  const { questions: companyEligibilityQuestions, isLoading: isLoadingEligibilityQuestions } = useCompanyEligibilityQuestions()
  const { interviewStages, sla, isLoading: isLoadingStages } = useRecruitmentStages()
  const { getBehavioralCompetencies, isLoading: isLoadingCompanyConfig } = useCompanyLiaInstructions()
  const isJobCreationMode = mode === 'job-creation'
  // ─── Domain state hooks (Sprint 4.2) ────────────────────────────────────────
  const wsiHook = useWSIState()
  const calibrationHook = useCalibrationState()
  const salaryHook = useSalaryState()
  const competenciesHook = useCompetenciesState()
  const publishingHook = usePublishingState()
  const fastTrackHook = useFastTrackState()

  // Destructure for backwards-compatible access throughout this component
  const { state: wsiState, actions: wsiActions } = wsiHook
  const { state: calibrationState, actions: calibrationActions, postCalibrationFlowStartedRef } = calibrationHook
  const { state: salaryState, actions: salaryActions } = salaryHook
  const { state: competenciesState, actions: competenciesActions } = competenciesHook
  const { state: publishingState, actions: publishingActions } = publishingHook
  const { state: fastTrackHookState, actions: fastTrackActions } = fastTrackHook
  // ────────────────────────────────────────────────────────────────────────────

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
    cargo: null,
    gestorArea: null,
    responsabilidades: [],
    competenciasTecnicas: [],
    competenciasComportamentais: [],
    idiomas: [],
    senioridadeIdiomas: null,
    modeloTrabalho: null,
    localizacao: null,
    tipoContrato: null,
    salario: null,
    departamento: null,
    isAffirmative: null,
    affirmativeCriteriaPrimary: null,
    affirmativeCriteriaSecondary: null,
    affirmativeDescription: null,
    experienciaMinima: null,
    formacao: [],
    certificacoes: [],
    ferramentas: [],
    diasPresenciais: null,
    beneficiosMencionados: [],
    bonus: null,
    viagensFrequentes: null,
    disponibilidade: null,
    cnh: null,
    horario: null
  })
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const extractCriteriaDebounceRef = useRef<NodeJS.Timeout | null>(null)
  
  // Refs para controlar timers de mensagem proativa (evita sobreposição de timers)
  const salaryProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const competenciesProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const inputEvaluationProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const wsiQuestionsProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const calibrationProactiveTimerRef = useRef<NodeJS.Timeout | null>(null)
  const [showMoreIdeas, setShowMoreIdeas] = useState(false)
  
  // Panel resize state
  const [panelWidth, setPanelWidth] = useState(42) // percentage
  const [isResizing, setIsResizing] = useState(false)
  const resizeRef = useRef<HTMLDivElement>(null)
  const [isPanelOpen, setIsPanelOpen] = useState(true) // Controls right panel visibility
  const [stageTransition, setStageTransition] = useState<'idle' | 'loading' | 'waiting-response'>('idle') // Controls panel loading state during stage transitions
  const [activeInputTab, setActiveInputTab] = useState<'ia-natural' | 'job-description' | 'templates'>('ia-natural')
  const [internalJobCreationMode, setInternalJobCreationMode] = useState(false)
  const [generatedJobDescription, setGeneratedJobDescription] = useState<string>('')
  
  // Fast Track state (from useFastTrackState — Sprint 4.2)
  const { wizardMode, fastTrackState, fastTrackSearchResults, fastTrackSelectedVacancy, fastTrackAdjustments, fastTrackSearchCriteria, isSearchingVacancies, wizardFastTrackSourceJobId } = fastTrackHookState
  const { setWizardMode, setFastTrackState, setFastTrackSearchResults, setFastTrackSelectedVacancy, setFastTrackAdjustments, setFastTrackSearchCriteria, setIsSearchingVacancies, setWizardFastTrackSourceJobId } = fastTrackActions
  const [isFullscreen, setIsFullscreen] = useState(false)
  
  // Control panel visibility based on wizard mode
  useEffect(() => {
    if (isJobCreationMode) {
      // Hide panel for pre_wizard, fast_track, and general modes
      // Show panel only for create_from_scratch mode
      if (wizardMode === 'pre_wizard' || wizardMode === 'fast_track' || wizardMode === 'general') {
        setIsPanelOpen(false)
      } else if (wizardMode === 'create_from_scratch') {
        setIsPanelOpen(true)
      }
    }
  }, [isJobCreationMode, wizardMode])
  
  // Job Wizard hook - integrates with backend LIA agent
  const jobWizard = useJobWizard()
  
  // Fast Track hook - semantic search for similar jobs
  // Note: Using consistent companyId with other hooks (default-company placeholder until multi-tenant is implemented)
  const fastTrack = useFastTrack({
    companyId: 'default-company',
    debounceMs: 600,
    minSimilarity: 0.70,
  })
  
  // Tool Calling hook - executes tools via chat with confirmation flow
  const toolCalling = useToolCalling({
    onToolExecuted: (result) => {
    },
    onToolError: (error, toolName) => {
    },
  })
  
  // Conversation Memory hook - persists conversation context for AI memory
  const conversationMemory = useConversationMemory({
    summaryThreshold: 10,
    maxMessages: 50,
    onError: (error) => {
    },
    onConversationLoaded: (conv) => {
    },
  })
  
  // State for tracking active tool confirmation message ID
  const [activeToolConfirmationMessageId, setActiveToolConfirmationMessageId] = useState<string | null>(null)
  
  // Wizard stage state
  const [currentStage, setCurrentStage] = useState<WizardStage>('input-evaluation')
  const currentStageConfig = WIZARD_STAGES.find(s => s.id === currentStage) || WIZARD_STAGES[0]
  const currentStageIndex = WIZARD_STAGES.findIndex(s => s.id === currentStage)
  
  // Stable draft ID for auto-save (persisted in localStorage for session restoration)
  const [wizardDraftId] = useState(() => {
    const DRAFT_ID_KEY = 'wizard_draft_id'
    if (typeof window !== 'undefined') {
      const existingId = localStorage.getItem(DRAFT_ID_KEY)
      if (existingId) {
        return existingId
      }
      const newId = `draft-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      localStorage.setItem(DRAFT_ID_KEY, newId)
      return newId
    }
    return `draft-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  })
  
  // Unified stage name mapping used by both sync check and useEffect
  const STAGE_DISPLAY_NAMES: Record<string, string> = useMemo(() => ({
    'assessment': 'Avaliação',
    'input-evaluation': 'Avaliação',
    'jd-enrichment': 'Enriquecimento',
    'salary': 'Remuneração',
    'competencies': 'Competências',
    'wsi-questions': 'Triagem WSI',
    'review': 'Revisão',
    'review-publish': 'Revisão',
    'search': 'Busca',
    'search-calibration': 'Busca'
  }), [])
  
  // Initial stages that don't count as meaningful progress
  const INITIAL_STAGES = useMemo(() => ['assessment', 'input-evaluation'], [])
  
  // Helper function to check for existing draft synchronously (before showing initial message)
  // Returns both draft info and the parsed draft data for restoration
  const { checkForExistingDraftSync } = useCheckForExistingDraftSync({ STAGE_DISPLAY_NAMES, INITIAL_STAGES })
  
  // Basic info form fields (Stage 2)
  const [basicInfoFields, setBasicInfoFields] = useState<BasicInfoFields>({
    cargo: '',
    area: '',
    gestor: '',
    localidade: '',
    modeloTrabalho: '',
    tipoContrato: ''
  })
  
  // Technical skills & Behavioral competencies (from useCompetenciesState — Sprint 4.2)
  const { technicalSkills, behavioralCompetencies } = competenciesState
  const { setTechnicalSkills, setBehavioralCompetencies } = competenciesActions

  // Salary info (from useSalaryState — Sprint 4.2)
  const { salaryInfo } = salaryState
  const { setSalaryInfo } = salaryActions
  
  // Enriched JD Data (JD Enrichment Stage)
  const [enrichedJDData, setEnrichedJDData] = useState<EnrichedJDData | null>(null)
  const [isLoadingEnrichment, setIsLoadingEnrichment] = useState(false)
  
  // Proactive stage completion detection flags
  const [inputEvaluationStageCompletionShown, setInputEvaluationStageCompletionShown] = useState(false)
  const [salaryStageCompletionShown, setSalaryStageCompletionShown] = useState(false)
  const [competenciesStageCompletionShown, setCompetenciesStageCompletionShown] = useState(false)
  const [wsiQuestionsStageCompletionShown, setWsiQuestionsStageCompletionShown] = useState(false)
  const [calibrationStageCompletionShown, setCalibrationStageCompletionShown] = useState(false)
  
  // State to track if we're awaiting confirmation for stage advance (conversational flow)
  const [awaitingStageAdvanceConfirmation, setAwaitingStageAdvanceConfirmation] = useState<string | null>(null)
  
  // Delay before showing proactive message (ms) - 6 seconds of no edits
  // Timer is now managed via refs (salaryProactiveTimerRef, etc.) and useEffect cleanup
  const PROACTIVE_MESSAGE_DELAY = 6000
  
  // WSI Questions (Stage 6)
  // WSI Questions state (from useWSIState — Sprint 4.2)
  const { wsiQuestions, wsiCandidates, wsiGenerationBatch, isGeneratingWSI, wsiHasGenerated, useCompanyQuestions, companyDefaultQuestions, showCustomQuestionForm, customQuestionText, customQuestionType, customQuestionRequired } = wsiState
  const { setWsiQuestions, setWsiCandidates, setWsiGenerationBatch, setIsGeneratingWSI, setWsiHasGenerated, setUseCompanyQuestions, setCompanyDefaultQuestions, setShowCustomQuestionForm, setCustomQuestionText, setCustomQuestionType, setCustomQuestionRequired } = wsiActions

  // Competencies state — modal forms, suggestions (from useCompetenciesState — Sprint 4.2)
  const { showAddCompetencyModal, newCompetencyName, newCompetencyJustification, newSkillName, editingCompetency, showAddSkillModal, newSkillCategory, showSkipCompetenciesWarning, competenciesPanelExpanded, showCompetenciesSuggestionsModal, suggestedTechnicalSkills, suggestedBehavioralSkills, selectedSuggestedTechnical, selectedSuggestedBehavioral, showCompetenciesInChat, competenciesChatLoading, competencySuggestions, competenciesTab } = competenciesState
  const { setShowAddCompetencyModal, setNewCompetencyName, setNewCompetencyJustification, setNewSkillName, setEditingCompetency, setShowAddSkillModal, setNewSkillCategory, setShowSkipCompetenciesWarning, setCompetenciesPanelExpanded, setShowCompetenciesSuggestionsModal, setSuggestedTechnicalSkills, setSuggestedBehavioralSkills, setSelectedSuggestedTechnical, setSelectedSuggestedBehavioral, setShowCompetenciesInChat, setCompetenciesChatLoading, setCompetencySuggestions, setCompetenciesTab } = competenciesActions

  // Salary state — benefit modal forms, benchmark (from useSalaryState — Sprint 4.2)
  const { showAddBenefitModal, newBenefitName, newBenefitValue, salaryPanelExpanded, showAutoFilledNotification } = salaryState
  const { setShowAddBenefitModal, setNewBenefitName, setNewBenefitValue, setSalaryPanelExpanded, setShowAutoFilledNotification } = salaryActions

  // Calibration state (from useCalibrationState — Sprint 4.2)
  const { calibrationCandidates, currentCalibrationIndex, approvedCandidates, rejectedCandidates, calibrationComplete, isLoadingCalibration, showCalibrationModal, calibrationSessionId, awaitingCalibrationChoice, showEditCriteriaModal, candidateProfileTab, calibrationComment, publishedJobId, calibrationCriteria, postCalibrationProcessing, localCandidateCount, globalSearchAuthorized, postCalibrationComplete, hasAttemptedCalibrationGeneration, searchPhase, globalCandidateCount, preferredCandidateCount, showClearDraftConfirm } = calibrationState
  const { setCalibrationCandidates, setCurrentCalibrationIndex, setApprovedCandidates, setRejectedCandidates, setCalibrationComplete, setIsLoadingCalibration, setShowCalibrationModal, setCalibrationSessionId, setAwaitingCalibrationChoice, setShowEditCriteriaModal, setCandidateProfileTab, setCalibrationComment, setPublishedJobId, setCalibrationCriteria, setPostCalibrationProcessing, setLocalCandidateCount, setGlobalSearchAuthorized, setPostCalibrationComplete, setHasAttemptedCalibrationGeneration, setSearchPhase, setGlobalCandidateCount, setPreferredCandidateCount, setShowClearDraftConfirm } = calibrationActions
  
  // Field origins state to track where each value came from (backend integration)
  const [fieldOrigins, setFieldOrigins] = useState<Record<string, { source: FieldOrigin; confidence: number }>>({})

  // Salary benchmark + compensation analysis (from useSalaryState — Sprint 4.2)
  const { salaryBenchmark, isLoadingBenchmark, compensationAnalysis } = salaryState
  const { setSalaryBenchmark, setIsLoadingBenchmark, setCompensationAnalysis } = salaryActions
  
  // Job Wizard Backend integration
  const { 
    processStep: processBackendStep, 
    isProcessing: isBackendProcessing, 
    lastResponse: lastBackendResponse,
    callEvaluationStep,
    isEvaluating,
    evaluationResult,
    clearEvaluationResult,
    fetchDeduplicatedSkills,
    filterSkillSuggestions,
    isFetchingSkills
  } = useJobWizardBackend({
    companyId: 'default',
    onCriteriaDetected: (criteria, origins) => {
      // Apply detected criteria to state
      if (criteria.job_title) {
        const jobTitle = criteria.job_title
        setDetectedCriteria(prev => ({ ...prev, cargo: jobTitle }))
        setBasicInfoFields(prev => ({ ...prev, cargo: jobTitle }))
        
        // Trigger Fast Track semantic search for similar jobs
        fastTrack.searchWithDebounce(jobTitle, criteria.department)
      }
      if (criteria.seniority) {
        const seniority = criteria.seniority
        setDetectedCriteria(prev => ({ ...prev, senioridadeIdiomas: seniority }))
      }
      if (criteria.technical_skills) {
        const skills = criteria.technical_skills
        setDetectedCriteria(prev => ({ 
          ...prev, 
          competenciasTecnicas: skills 
        }))
      }
      if (criteria.behavioral_skills) {
        const behaviors = criteria.behavioral_skills
        setDetectedCriteria(prev => ({ 
          ...prev, 
          competenciasComportamentais: behaviors 
        }))
      }
      if (criteria.salary_min || criteria.salary_max) {
        setDetectedCriteria(prev => ({ 
          ...prev, 
          salario: `R$ ${criteria.salary_min?.toLocaleString() || '?'} - R$ ${criteria.salary_max?.toLocaleString() || '?'}` 
        }))
      }
      if (criteria.location) {
        setBasicInfoFields(prev => ({ ...prev, localidade: criteria.location! }))
      }
      if (criteria.work_model) {
        setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: criteria.work_model! }))
      }
      
      // Store field origins from backend
      const newOrigins: Record<string, { source: FieldOrigin; confidence: number }> = {}
      for (const [field, data] of Object.entries(origins)) {
        newOrigins[field] = {
          source: (data as { source?: FieldOrigin; confidence?: number }).source || 'detected',
          confidence: (data as { source?: FieldOrigin; confidence?: number }).confidence || 0.7
        }
      }
      setFieldOrigins(prev => ({ ...prev, ...newOrigins }))
    },
    onError: (error) => {
    }
  })
  
  // Publishing state (from usePublishingState — Sprint 4.2)
  const { publishingPlatforms, jobConfig, jobDescription, isGeneratingDescription } = publishingState
  const { setPublishingPlatforms, setJobConfig, setJobDescription, setIsGeneratingDescription, updateLanguages } = publishingActions
  
  // Company configuration state (fetched from settings)
  const [companyConfig, setCompanyConfig] = useState<{
    workModel?: string
    hybridDaysOnsite?: number
    employmentTypes?: string[]
    techStack?: string[]
    values?: string[]
    coreCompetencies?: string[]
    departments?: {id: string, name: string}[]
    benefits?: {name: string, category: string, value?: number, is_active: boolean}[]
    evpBullets?: string[]
    headquarters?: string
    locations?: string[]
  } | null>(null)
  const [configLoaded, setConfigLoaded] = useState(false)
  const [fieldsFromConfig, setFieldsFromConfig] = useState<Set<string>>(new Set())
  
  // Smart wizard greeting state (from catalog status endpoint)
  const [wizardGreeting, setWizardGreeting] = useState<{
    greeting_message: string
    catalog_status: {
      company_id: string
      maturity_score: number
      maturity_level: 'complete' | 'partial' | 'minimal'
      maturity_factors: string[]
      smart_start_enabled: boolean
      required_fields_for_wizard: string[]
      available_data_summary: string[]
      counts: Record<string, number>
      recommendations: string[]
    }
    prefill_data: Record<string, unknown>
  } | null>(null)
  
  // Track when wizard greeting has been loaded to prevent race conditions
  const [wizardGreetingLoaded, setWizardGreetingLoaded] = useState(false)
  
  // Chat sync for bidirectional panel-chat synchronization (Phase 7)
  // Proactive handlers and grouped panel change handler extracted to useExpandedChatCallbacks
  const { handleProactiveAccept, handleProactiveReject } = useProactiveHandlers({ user, setMessages })
  const { handleGroupedPanelChange } = useGroupedPanelChangeHandler({ setMessages })
  
  const {
    trackFieldChange,
    generateLLMContext,
    clearChanges: clearChatSyncChanges,
  } = useChatSync({
    debounceMs: 800,
    groupingWindowMs: 1500,
    onGroupedChange: handleGroupedPanelChange,
  })
  
  // Field highlight hook for visual feedback when fields are updated via chat/orchestrator
  const {
    highlightField,
    isHighlighted,
    highlightedFields,
    clearAllHighlights,
  } = useFieldHighlight({ highlightDurationMs: 2000 })
  
  // Learning and Analytics hooks for Phase 8
  const learning = useLearning()
  const analytics = useWizardAnalytics('default-company', 'default-recruiter')
  
  // Context switching hook for wizard/general mode transitions
  const contextSwitching = useContextSwitching({
    autoDetectIntent: true,
    onContextSwitch: (from, to) => {
      if (to === 'wizard') {
        setWizardMode('pre_wizard')
      } else if (to === 'general') {
        setWizardMode('general')
      } else if (to === 'fast_track') {
        setWizardMode('fast_track')
      }
    },
    onWizardRestore: (snapshot: WizardSnapshot) => {
      if (snapshot.stage) {
        setCurrentStage(snapshot.stage as WizardStage)
      }
      if (snapshot.basicInfoFields) {
        setBasicInfoFields(snapshot.basicInfoFields as unknown as BasicInfoFields)
      }
      if (snapshot.technicalSkills && Array.isArray(snapshot.technicalSkills)) {
        setTechnicalSkills(snapshot.technicalSkills as TechnicalSkill[])
      }
      if (snapshot.behavioralCompetencies && Array.isArray(snapshot.behavioralCompetencies)) {
        setBehavioralCompetencies(snapshot.behavioralCompetencies as BehavioralCompetency[])
      }
      if (snapshot.salaryInfo) {
        setSalaryInfo(snapshot.salaryInfo as unknown as SalaryInfo)
      }
      if (snapshot.wsiQuestions && Array.isArray(snapshot.wsiQuestions)) {
        setWsiQuestions(snapshot.wsiQuestions as WSIQuestion[])
      }
      if (snapshot.generatedJobDescription) {
        setGeneratedJobDescription(snapshot.generatedJobDescription)
      }
      if (snapshot.fastTrackSourceJobId) {
        setWizardFastTrackSourceJobId(snapshot.fastTrackSourceJobId)
      }
    },
    onGeneralRestore: (snapshot: GeneralChatSnapshot) => {
      // Restore conversationId from snapshot
      if (snapshot.conversationId) {
        setConversationId(snapshot.conversationId)
        
        // Re-initialize conversation memory with the stored conversation ID
        // This will reload messages and context from the backend
        // Use a non-blocking async IIFE to avoid making the callback async
        if (user?.email) {
          (async () => {
            try {
              await conversationMemory.initConversation(user.email, 'general')
              
              // After reloading, the conversationMemory.messages will have the history
              // Convert backend messages to UI Message format if needed
              if (conversationMemory.messages.length > 0) {
                const restoredMessages: Message[] = conversationMemory.messages.map(m => ({
                  id: m.id || `restored-${Date.now()}-${Math.random()}`,
                  role: m.role as 'user' | 'assistant',
                  content: m.content,
                  timestamp: m.created_at ? new Date(m.created_at) : new Date(),
                }))
                
                // Prepend initial LIA message if not present
                const hasInitialMessage = restoredMessages.some(m => 
                  m.role === 'assistant' && m.content.includes('Olá!')
                )
                if (!hasInitialMessage) {
                  const initialMessage: Message = {
                    id: 'initial-restored',
                    role: 'assistant',
                    content: INITIAL_GENERAL_MESSAGE,
                    timestamp: new Date(Date.now() - 1000),
                  }
                  setMessages([initialMessage, ...restoredMessages])
                } else {
                  setMessages(restoredMessages)
                }
              }
            } catch (error) {
            }
          })()
        }
      }
      // Scroll to the last message index when restoring general context
      if (snapshot.lastMessageIndex > 0) {
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
        }, 0)
      }
    },
  })
  
  // Sync context switching hook with wizardMode changes
  // Use skipCallbacks to prevent infinite loops: wizardMode change → syncContext → onContextSwitch → setWizardMode → loop
  // The callbacks are already triggered by switchTo* methods when context changes internally
  // Note: Extract syncContext function to avoid re-running when entire hook object changes
  const { syncContext } = contextSwitching
  useEffect(() => {
    (syncContext as (mode: unknown, opts: Record<string, unknown>) => void)(wizardMode, { skipCallbacks: true, skipSnapshotRestore: true })
  }, [wizardMode, syncContext])
  
  // Start analytics session when wizard opens
  // Use refs to avoid infinite loops from function dependencies
  const { startSession, trackStageChange, completeSession } = analytics
  const startSessionRef = useRef(startSession)
  const trackStageChangeRef = useRef(trackStageChange)
  const completeSessionRef = useRef(completeSession)
  const analyticsInitializedRef = useRef(false)
  
  // Keep refs updated
  startSessionRef.current = startSession
  trackStageChangeRef.current = trackStageChange
  completeSessionRef.current = completeSession
  
  useEffect(() => {
    // Only initialize once per modal open to prevent loops
    if (isOpen && mode === 'job-creation' && !analyticsInitializedRef.current) {
      analyticsInitializedRef.current = true
      const sessionId = startSessionRef.current()
      if (sessionId) {
        trackStageChangeRef.current('input-evaluation')
      }
    }
    
    // Reset flag when modal closes
    if (!isOpen) {
      analyticsInitializedRef.current = false
    }
    
    return () => {
      if (mode === 'job-creation' && analyticsInitializedRef.current) {
        completeSessionRef.current()
      }
    }
  }, [isOpen, mode])
  
  // Initialize conversation memory when wizard opens
  // Use refs to avoid infinite loops from function dependencies
  const initConversationRef = useRef(conversationMemory.initConversation)
  const updateSummaryRef = useRef(conversationMemory.updateSummary)
  const conversationInitializedRef = useRef(false)
  
  // Keep refs updated
  useEffect(() => {
    initConversationRef.current = conversationMemory.initConversation
    updateSummaryRef.current = conversationMemory.updateSummary
  }, [conversationMemory.initConversation, conversationMemory.updateSummary])
  
  useEffect(() => {
    // Only initialize once per modal open
    if (isOpen && mode === 'job-creation' && user?.email && !conversationInitializedRef.current) {
      conversationInitializedRef.current = true
      initConversationRef.current(
        user.email,
        'wizard',
        wizardDraftId
      ).catch(() => {
        // Silently ignore initialization errors - conversation is optional
      })
    }
    
    // Reset flag when modal closes
    if (!isOpen) {
      conversationInitializedRef.current = false
    }
    
    return () => {
      if (mode === 'job-creation' && conversationInitializedRef.current) {
        updateSummaryRef.current(true).catch(() => {})
      }
    }
  }, [isOpen, mode, user?.email, wizardDraftId])
  
  // Fetch learning suggestions when job title changes
  // Note: Extract function to avoid infinite loop from hook object dependency
  const { fetchWizardSuggestions } = learning
  useEffect(() => {
    if (detectedCriteria?.cargo && mode === 'job-creation') {
      fetchWizardSuggestions({
        companyId: 'default-company',
        jobTitle: detectedCriteria.cargo,
        department: detectedCriteria.departamento || undefined,
        seniority: undefined
      })
    }
  }, [detectedCriteria?.cargo, detectedCriteria?.departamento, mode, fetchWizardSuggestions])
  
  // Fast Track conversation state (from useFastTrackState — Sprint 4.2)
  const { fastTrackMessageSent, fastTrackSuggestionsShownTracked, awaitingFastTrackSelection, awaitingSensitiveFieldsConfirmation, fastTrackAppliedData, fastTrackOriginalCompetencies, wsiRegenerationPrompted, awaitingWSIRegenerationConfirmation } = fastTrackHookState
  const { setFastTrackMessageSent, setFastTrackSuggestionsShownTracked, setAwaitingFastTrackSelection, setAwaitingSensitiveFieldsConfirmation, setFastTrackAppliedData, setFastTrackOriginalCompetencies, setWsiRegenerationPrompted, setAwaitingWSIRegenerationConfirmation, resetFastTrackConversationState } = fastTrackActions
  
  // Note: Extract functions to avoid stale closure issues and infinite loops
  const { 
    clearSuggestions: clearFastTrackSuggestions, 
    hasSuggestions: fastTrackHasSuggestions,
    suggestions: fastTrackSuggestions,
    getLiaMessage: getFastTrackLiaMessage
  } = fastTrack
  
  // Send LIA message when Fast Track suggestions are found
  useEffect(() => {
    if (fastTrackHasSuggestions && !fastTrackMessageSent && mode === 'job-creation' && currentStage === 'input-evaluation') {
      const liaMessage = getFastTrackLiaMessage(fastTrackSuggestions)
      if (liaMessage) {
        const fastTrackMessage = {
          id: `fasttrack-${Date.now()}`,
          role: 'assistant' as const,
          content: liaMessage,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, fastTrackMessage])
        setFastTrackMessageSent(true)
        
        // Analytics: Track Fast Track suggestion shown (only once per session)
        if (!fastTrackSuggestionsShownTracked) {
          analytics.trackSuggestion('fast_track_suggestion_shown', false)
          setFastTrackSuggestionsShownTracked(true)
        }
      }
    }
  }, [fastTrackHasSuggestions, fastTrackSuggestions, fastTrackMessageSent, mode, currentStage, analytics, fastTrackSuggestionsShownTracked, getFastTrackLiaMessage])
  
  // Reset Fast Track message flag when starting new job creation
  useEffect(() => {
    if (!isOpen || mode !== 'job-creation') {
      resetFastTrackConversationState()
      clearFastTrackSuggestions()
    }
  }, [isOpen, mode, clearFastTrackSuggestions, resetFastTrackConversationState])
  
  // Clear awaiting state when suggestions disappear (centralized cleanup)
  useEffect(() => {
    if (!fastTrackHasSuggestions) {
      setAwaitingFastTrackSelection(false)
      setFastTrackMessageSent(false)
      // Note: Don't clear awaitingSensitiveFieldsConfirmation here
      // as it's used after suggestions are applied (cleared)
    }
  }, [fastTrackHasSuggestions])
  
  // Detect competency changes after Fast Track and prompt for WSI regeneration

  // === Effects and lifecycle logic ===
  const effectsResult = useExpandedChatEffects({
    INITIAL_STAGES, PROACTIVE_MESSAGE_DELAY, analytics, approvedCandidates,
    awaitingWSIRegenerationConfirmation, basicInfoFields, behavioralCompetencies, calibrationComplete, calibrationProactiveTimerRef,
    calibrationStageCompletionShown, checkForExistingDraftSync, companyConfig, companyDefaultQuestions, competenciesProactiveTimerRef,
    competenciesStageCompletionShown, configLoaded, currentStage, detectedCriteria, displayedText,
    fastTrack, fastTrackOriginalCompetencies, generatedJobDescription, initialLiaMessage,
    initialMessages, inputEvaluationProactiveTimerRef, inputEvaluationStageCompletionShown, inputRef, internalJobCreationMode,
    isJobCreationMode, isOpen, isResizing, isTypingEffect, jobConfig,
    jobDescription, learning, messages, messagesEndRef,
    mode, proactiveActionIds, rejectedCandidates,
    resizeRef, salaryBenchmark, salaryInfo, salaryProactiveTimerRef, salaryStageCompletionShown,
    setAwaitingStageAdvanceConfirmation, setAwaitingWSIRegenerationConfirmation, setBasicInfoFields, setBehavioralCompetencies,
    setCalibrationStageCompletionShown, setCompanyConfig, setCompanyDefaultQuestions, setCompetenciesPanelExpanded, setCompetenciesStageCompletionShown,
    setConfigLoaded, setCurrentStage, setDetectedCriteria, setDisplayedText, setFastTrackMessageSent,
    setFieldOrigins, setFieldsFromConfig, setGeneratedJobDescription, setInputEvaluationStageCompletionShown, setInputValue,
    setIsLoadingBenchmark, setIsResizing, setIsTypingEffect, setJobConfig, setMessages,
    setPanelWidth, setProactiveActionIds, setSalaryBenchmark, setSalaryInfo, setSalaryPanelExpanded,
    setSalaryStageCompletionShown, setShowAutoFilledNotification, setTechnicalSkills, setWizardGreeting, setWizardGreetingLoaded,
    setWsiCandidates, setWsiQuestionsStageCompletionShown, setWsiRegenerationPrompted, sla,
    technicalSkills, typingTimeoutRef, user,
    wizardGreeting, wsiCandidates, wsiQuestionsProactiveTimerRef, wsiQuestionsStageCompletionShown, wsiRegenerationPrompted,
    publishingState, publishingActions, wizardDraftId, STAGE_DISPLAY_NAMES, onMessagesUpdate,
    isLoadingEligibilityQuestions, companyEligibilityQuestions, isLoadingStages,
  })
  const {
    typeText, isFieldRequiredForWizard, hasConfigData, isInJobCreationMode,
    wsiQualityGates, applyPendingDraft,
    companyMembersMap, languagesUserEdited, setCompanyMembersMap, setLanguagesUserEdited,
    hasAppliedRestoredDraft, setHasAppliedRestoredDraft,
    awaitingDraftChoice, setAwaitingDraftChoice,
    pendingDraftData, setPendingDraftData,
    saveWizardDraft, clearWizardDraft, loadedDraft, hasRestoredDraft,
    hasAttemptedRestore, isAutoSaving, autoSaveLastSaved, hasPendingChanges, getLastSavedText,
    hasMinimumCompetencies,
  } = effectsResult

  const extractCriteriaFromText = (text: string) => {
    const result = _extractCriteria(text, detectedCriteria)
    setDetectedCriteria(result)
    return result
  }


  // Proceed to next stage (called after modal or directly if no suggestions)
  // Defined before hook so it can be passed as context
  const proceedToNextStage = () => {
    const nextIndex = currentStageIndex + 1
    if (nextIndex < WIZARD_STAGES.length) {
      const currentStageConfig = WIZARD_STAGES[currentStageIndex] as ExtendedWizardStageConfig
      const nextStage = WIZARD_STAGES[nextIndex] as ExtendedWizardStageConfig

      // Generate transition message from current stage
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

      // Check for missing recommended fields and add gentle reminders
      const missingFields = getMissingCriticalFields(currentStageConfig.id, detectedCriteria)
      if (missingFields.recommended.length > 0) {
        transitionContent += `\n\n📝 *Campos opcionais não preenchidos: ${missingFields.recommended.join(', ')}*`
      }

      // Add transition message first
      if (transitionContent) {
        const transitionMessage: Message = {
          id: `transition-${currentStageConfig.id}-${Date.now()}`,
          role: 'assistant',
          content: transitionContent,
          timestamp: new Date(),
          isTyping: true
        }
        setMessages(prev => [...prev, transitionMessage])

        // Type transition message, then after delay add next stage message
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
        }, 2000) // Wait 2 seconds for transition message to be read
      } else {
        // No transition config, proceed directly
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
  }

  // === Sub-hook calls ===
  const subHooksResult = useExpandedChatSubHooks({
    activeToolConfirmationMessageId, analytics, applyPendingDraft, approvedCandidates, awaitingCalibrationChoice,
    awaitingDraftChoice, awaitingFastTrackSelection, awaitingSensitiveFieldsConfirmation, awaitingStageAdvanceConfirmation, awaitingWSIRegenerationConfirmation,
    basicInfoFields, behavioralCompetencies, calibrationCandidates, calibrationComment, calibrationComplete,
    calibrationCriteria, calibrationSessionId, callEvaluationStep, clearWizardDraft, companyConfig,
    companyDefaultQuestions, companyMembersMap, compensationAnalysis, contextSwitching, conversationId,
    conversationMemory, currentCalibrationIndex, currentStage, currentStageConfig, currentStageIndex,
    customQuestionRequired, customQuestionText, customQuestionType, detectedCriteria, extractCriteriaFromText,
    fastTrack, fastTrackAdjustments, fastTrackAppliedData, fastTrackSearchCriteria, fastTrackSearchResults,
    fastTrackSelectedVacancy, fastTrackState, fastTrackSuggestionsShownTracked, fetchDeduplicatedSkills, generateLLMContext,
    generatedJobDescription, hasAttemptedCalibrationGeneration, highlightField, inputEvaluationStageCompletionShown, inputRef,
    inputValue, interviewStages, isFullscreen, isGeneratingWSI, isInJobCreationMode,
    isJobCreationMode, isLoading, isLoadingCalibration, isOpen, isSearchingVacancies,
    isTypingEffect, jobConfig, learning, localCandidateCount,
    messages, newBenefitName, newBenefitValue, newCompetencyJustification, newCompetencyName,
    newSkillCategory, onClose, onJobCreated, pendingDraftData, postCalibrationComplete,
    preferredCandidateCount, proceedToNextStage, publishedJobId, publishingPlatforms,
    rejectedCandidates, salaryInfo, saveWizardDraft, selectedSuggestedBehavioral, selectedSuggestedTechnical,
    setActiveToolConfirmationMessageId, setApprovedCandidates, setAwaitingCalibrationChoice, setAwaitingFastTrackSelection,
    setAwaitingSensitiveFieldsConfirmation, setAwaitingStageAdvanceConfirmation, setAwaitingWSIRegenerationConfirmation, setBasicInfoFields, setBehavioralCompetencies,
    setCalibrationCandidates, setCalibrationComment, setCalibrationComplete, setCalibrationCriteria, setCalibrationSessionId,
    setCompensationAnalysis, setCompetencySuggestions, setConversationId, setCurrentCalibrationIndex, setCurrentStage,
    setCustomQuestionRequired, setCustomQuestionText, setCustomQuestionType, setDetectedCriteria, setDisplayedText,
    setDynamicInitialMessage, setEnrichedJDData, setFastTrackAdjustments, setFastTrackAppliedData, setFastTrackMessageSent,
    setFastTrackOriginalCompetencies, setFastTrackSearchCriteria, setFastTrackSearchResults, setFastTrackSelectedVacancy, setFastTrackState,
    setFileAnalysisResult, setFileAnalysisType, setGeneratedJobDescription, setGlobalCandidateCount, setHasAttemptedCalibrationGeneration,
    setInputValue, setInternalJobCreationMode, setIsGeneratingDescription, setIsGeneratingWSI, setIsLoading,
    setIsLoadingCalibration, setIsLoadingEnrichment, setIsPanelOpen, setIsSearchingVacancies, setJobConfig,
    setJobDescription, setLocalCandidateCount, setMessages, setNewBenefitName, setNewBenefitValue,
    setNewCompetencyJustification, setNewCompetencyName, setNewSkillName, setPostCalibrationComplete, setPublishedJobId,
    setRejectedCandidates, setSalaryInfo, setSearchPhase, setShowAddBenefitModal, setShowAddCompetencyModal,
    setShowAddSkillModal, setShowCalibrationModal, setShowClearDraftConfirm, setShowCompetenciesSuggestionsModal, setShowCustomQuestionForm,
    setShowUploadModal, setStageTransition, setTechnicalSkills, setUploadedFile,
    setWizardFastTrackSourceJobId, setWizardMode, setWsiCandidates, setWsiGenerationBatch, setWsiHasGenerated,
    setWsiQuestions, setWsiRegenerationPrompted, showCalibrationModal,
    technicalSkills, toolCalling, trackFieldChange, typeText, user,
    wizardFastTrackSourceJobId, wizardMode, wsiCandidates, wsiGenerationBatch,
    wsiHasGenerated, wsiQualityGates, wsiQuestions,
    inline, onOrchestratedMessage, onMessagesUpdate,
  })
  const {
    addCalibrationCriterion, addCustomQuestion, addNewBenefit, addNewCompetency, addNewSkill,
    buildCandidateSearchQuery, buildCollectedData, canAdvanceToNextStage, containerClasses, contentClasses,
    criteriaItems, deleteWSIQuestion, detectFastTrackIntent, generateCalibrationCandidates, generateCompetencyAnalysisMessage,
    generateCriteriaResponse, generateJobDescription, generateMoreCalibrationCandidates, generateParecerData,
    generateWSIExplanationMessage, generateWSIQuestions, goToNextStage, goToPreviousStage,
    handleAcceptSuggestions, handleApproveCandidate, handleClearDraftAndReset,
    handleFastTrackPublish, handleFastTrackSearch, handleFastTrackVacancySelect,
    handleFileAnalysisComplete, handleFileAnalysisError, handleFileSelect,
    handleKeyDown, handlePublishJob, handleQuickSuggestion, handleRejectCandidate,
    handleSendMessage, handleSkipSuggestions, handleVoiceResponse,
    initializeCalibrationCriteria, moveToNextCandidate, parseFastTrackAdjustment,
    processOrchestratorResponse, removeCalibrationCriterion,
    reorderCalibrationCriteria, startGlobalSearch, startLocalSearch,
    toggleWSIQuestionSelection, updateWSIQuestionCorrectOption, updateWSIQuestionExpectedAnswer,
  } = subHooksResult

  useEffect(() => {
    if (currentStage === 'review-publish' && !jobDescription) {
      generateJobDescription()
    }
  }, [currentStage])

  useEffect(() => {
    if (isOpen && initialMessage && messages.length === 1 && !isTypingEffect) {
      setTimeout(() => {
        handleSendMessage(initialMessage)
        setInputValue("")
      }, 500)
    }
  }, [isOpen, initialMessage, messages.length, isTypingEffect])

    return {
      activeInputTab,
    addCalibrationCriterion,
    addCustomQuestion,
    addNewBenefit,
    addNewCompetency,
    addNewSkill,
    analytics,
    approvedCandidates,
    autoSaveLastSaved,
    basicInfoFields,
    behavioralCompetencies,
    calibrationCandidates,
    calibrationComment,
    calibrationComplete,
    calibrationCriteria,
    canAdvanceToNextStage,
    candidateProfileTab,
    checkForExistingDraftSync,
    companyConfig,
    companyDefaultQuestions,
    competenciesPanelExpanded,
    configLoaded,
    containerClasses,
    contentClasses,
    conversationId,
    criteriaItems,
    currentCalibrationIndex,
    currentStage,
    currentStageConfig,
    currentStageIndex,
    customQuestionRequired,
    customQuestionText,
    customQuestionType,
    deleteWSIQuestion,
    detectedCriteria,
    displayedText,
    enrichedJDData,
    extractCriteriaDebounceRef,
    extractCriteriaFromText,
    fastTrack,
    fastTrackSuggestionsShownTracked,
    fileInputRef,
    generateCalibrationCandidates,
    generateJobDescription,
    generateWSIQuestions,
    getBehavioralCompetencies,
    getLastSavedText,
    globalCandidateCount,
    globalSearchAuthorized,
    goToNextStage,
    goToPreviousStage,
    handleApproveCandidate,
    handleClearDraftAndReset,
    handleFastTrackVacancySelect,
    handleFileAnalysisComplete,
    handleFileAnalysisError,
    handleFileSelect,
    handleKeyDown,
    handleProactiveAccept,
    handleProactiveReject,
    handlePublishJob,
    handleRejectCandidate,
    handleSendMessage,
    handleVoiceResponse,
    hasAttemptedCalibrationGeneration,
    hasConfigData,
    hasPendingChanges,
    hasRestoredDraft,
    highlightedFields,
    inputRef,
    inputValue,
    isAutoSaving,
    isFieldRequiredForWizard,
    isFullscreen,
    isGeneratingDescription,
    isGeneratingWSI,
    isHighlighted,
    isInJobCreationMode,
    isJobCreationMode,
    isLoading,
    isLoadingBenchmark,
    isLoadingCalibration,
    isLoadingEnrichment,
    isPanelOpen,
    isSearchingVacancies,
    isTypingEffect,
    jobConfig,
    jobDescription,
    localCandidateCount,
    messages,
    messagesEndRef,
    newBenefitName,
    newBenefitValue,
    newCompetencyJustification,
    newCompetencyName,
    newSkillCategory,
    newSkillName,
    panelWidth,
    preferredCandidateCount,
    publishedJobId,
    publishingPlatforms,
    removeCalibrationCriterion,
    resizeRef,
    salaryBenchmark,
    salaryInfo,
    salaryPanelExpanded,
    searchPhase,
    setActiveInputTab,
    setActiveToolConfirmationMessageId,
    setAwaitingDraftChoice,
    setAwaitingFastTrackSelection,
    setBehavioralCompetencies,
    setCalibrationComment,
    setCalibrationComplete,
    setCandidateProfileTab,
    setCompanyDefaultQuestions,
    setCompetenciesPanelExpanded,
    setCompetenciesTab,
    setCompetencySuggestions,
    setCurrentCalibrationIndex,
    setCurrentStage,
    setCustomQuestionRequired,
    setCustomQuestionText,
    setCustomQuestionType,
    setDetectedCriteria,
    setDisplayedText,
    setDynamicInitialMessage,
    setEditingCompetency,
    setEnrichedJDData,
    setFastTrackState,
    setGlobalSearchAuthorized,
    setHasAttemptedCalibrationGeneration,
    setInputValue,
    setInternalJobCreationMode,
    setIsFullscreen,
    setIsLoading,
    setIsPanelOpen,
    setIsResizing,
    setJobConfig,
    setMessages,
    setNewBenefitName,
    setNewBenefitValue,
    setNewCompetencyJustification,
    setNewCompetencyName,
    setNewSkillCategory,
    setNewSkillName,
    setPendingDraftData,
    setPreferredCandidateCount,
    setPublishingPlatforms,
    setSalaryInfo,
    setSalaryPanelExpanded,
    setSearchPhase,
    setShowAddBenefitModal,
    setShowAddCompetencyModal,
    setShowAddSkillModal,
    setShowCalibrationModal,
    setShowClearDraftConfirm,
    setShowCustomQuestionForm,
    setShowEditCriteriaModal,
    setShowMoreIdeas,
    setShowSkipCompetenciesWarning,
    setShowUploadModal,
    setTechnicalSkills,
    setUploadedFile,
    showAddBenefitModal,
    showAddCompetencyModal,
    showAddSkillModal,
    showCalibrationModal,
    showClearDraftConfirm,
    showCustomQuestionForm,
    showEditCriteriaModal,
    showMoreIdeas,
    showSkipCompetenciesWarning,
    showUploadModal,
    stageTransition,
    startGlobalSearch,
    technicalSkills,
    toggleWSIQuestionSelection,
    toolCalling,
    trackFieldChange,
    typeText,
    updateLanguages,
    updateWSIQuestionCorrectOption,
    updateWSIQuestionExpectedAnswer,
    wizardGreeting,
    wizardMode,
    wsiCandidates,
    wsiQualityGates,
    wsiQuestions,
    isOpen,
  }
}
  