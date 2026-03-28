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
import { FieldOriginBadge, type FieldOrigin } from "./job-creation/field-origin-badge"
import { ConfidenceIndicator } from "./job-creation/confidence-indicator"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { CompensationChatMessage } from "./job-creation/compensation-chat-message"
import { CompetenciesChatMessage, type TechnicalSkillSuggestion, type BehavioralCompetencySuggestion } from "./job-creation/competencies-chat-message"
import { VacancySearchResults, type VacancySummary } from "./job-creation/vacancy-search-results"
import { VacancyFullSummary, type VacancyFullDetails } from "./job-creation/vacancy-full-summary"
import { type VacancySearchCriteria, type VacancyAdjustments } from "@/services/lia-api"
import { MessageFeedback } from "./chat/message-feedback"
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
} from './expanded-chat'
import { useWizardState, useWSIQualityGates, useWizardNavigation, useChatSync, useToolCalling, useFieldHighlight, useWSIState, useCalibrationState, useSalaryState, useCompetenciesState, usePublishingState, useFastTrackState, type ChatNavigationResult, type GroupedChange, type ToolCall, type ToolExecutionResult } from './expanded-chat/hooks'
import { useSendMessageHandlers, type SendMessageHandlersContext } from './expanded-chat/hooks/useSendMessageHandlers'
import { useWizardPublishHandlers } from './expanded-chat/hooks/useWizardPublishHandlers'
import { useWSIAndCalibrationHandlers } from './expanded-chat/hooks/useWSIAndCalibrationHandlers'
import { useConversationMemory } from './expanded-chat/hooks/useConversationMemory'
import { useLearning } from './expanded-chat/hooks/useLearning'
import { useFastTrack, type FastTrackSuggestion, type FastTrackJobData } from '@/hooks/useFastTrack'
import { FastTrackSuggestions } from './job-wizard/FastTrackSuggestions'
import { FastTrackReviewPanel } from './job-wizard/FastTrackReviewPanel'
import { useWizardAnalytics } from './expanded-chat/hooks/useWizardAnalytics'
import { useContextSwitching, type WizardSnapshot, type GeneralChatSnapshot } from './expanded-chat/hooks/useContextSwitching'
import { ToolConfirmationMessage, ToolExecutionFeedback, ChatMessageList, ExpandedChatInput, WizardRightPanel } from './expanded-chat/components'
import { type EnrichedJDData } from './expanded-chat/stages'
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
} from './expanded-chat/utils'
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
} from './expanded-chat/types'
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
} from './expanded-chat/utils/skill-weight-utils'
import { ClearDraftConfirmModal, EditCriteriaModal, AddTechnicalSkillModal, AddCompetencyModal, AddBenefitModal, SkipCompetenciesWarningModal, CalibrationProfileModal } from './expanded-chat/modals'

function ExpandedChatModalContent({
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
  const checkForExistingDraftSync = useCallback((): { 
    hasDraft: boolean
    stageName: string | null
    draftData: Partial<WizardDraftData> | null 
  } => {
    if (typeof window === 'undefined') return { hasDraft: false, stageName: null, draftData: null }
    try {
      const storedDraft = localStorage.getItem('wizard_draft')
      if (!storedDraft) return { hasDraft: false, stageName: null, draftData: null }
      
      const parsedDraft = JSON.parse(storedDraft) as Partial<WizardDraftData>
      const currentStage = parsedDraft?.currentStage
      
      // Only consider it a meaningful draft if it has progressed beyond initial stage
      const hasMeaningfulDraft = currentStage && !INITIAL_STAGES.includes(currentStage)
      
      if (hasMeaningfulDraft) {
        return { 
          hasDraft: true, 
          stageName: STAGE_DISPLAY_NAMES[currentStage] || currentStage,
          draftData: parsedDraft
        }
      }
      return { hasDraft: false, stageName: null, draftData: null }
    } catch {
      return { hasDraft: false, stageName: null, draftData: null }
    }
  }, [STAGE_DISPLAY_NAMES, INITIAL_STAGES])
  
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
    prefill_data: Record<string, any>
  } | null>(null)
  
  // Track when wizard greeting has been loaded to prevent race conditions
  const [wizardGreetingLoaded, setWizardGreetingLoaded] = useState(false)
  
  // Chat sync for bidirectional panel-chat synchronization (Phase 7)
  const handleProactiveAccept = useCallback(async (actionId: string, messageId: string) => {
    const userId = user?.id || 'default_user'
    try {
      const res = await fetch(`/api/backend-proxy/proactive-actions?path=accept/${actionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      })
      if (res.ok) {
        setMessages(prev => prev.filter(m => m.id !== messageId))
        const confirmMsg: Message = {
          id: `proactive-confirm-${Date.now()}`,
          role: 'assistant',
          content: '✅ Ação aceita! Estou processando...',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, confirmMsg])
      }
    } catch (err) {
    }
  }, [user])

  const handleProactiveReject = useCallback(async (actionId: string, messageId: string) => {
    const userId = user?.id || 'default_user'
    try {
      const res = await fetch(`/api/backend-proxy/proactive-actions?path=reject/${actionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      })
      if (res.ok) {
        setMessages(prev => prev.filter(m => m.id !== messageId))
      }
    } catch (err) {
    }
  }, [user])

  const handleGroupedPanelChange = useCallback((group: GroupedChange) => {
    // Only create system messages for panel changes that users would want to see
    if (group.changes.length === 0) return
    
    // Filter to only panel-initiated changes
    const panelChanges = group.changes.filter(c => c.source === 'panel')
    if (panelChanges.length === 0) return
    
    // Create a subtle assistant message for panel field updates
    const systemMessage: Message = {
      id: `panel-sync-${Date.now()}`,
      role: 'assistant',
      content: `📝 ${group.summary}`,
      timestamp: new Date(),
      messageType: 'text',
      isFieldUpdate: true
    }
    setMessages(prev => [...prev, systemMessage])
  }, [])
  
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
    (syncContext as any)(wizardMode, { skipCallbacks: true, skipSnapshotRestore: true })
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
  useEffect(() => {
    if (!fastTrackOriginalCompetencies || wsiRegenerationPrompted || awaitingWSIRegenerationConfirmation) {
      return
    }
    
    // Get current competency names
    const currentTechnicalSkillNames = technicalSkills.map(s => s.name.toLowerCase())
    const currentBehavioralNames = behavioralCompetencies.map(c => c.name.toLowerCase())
    
    // Check if competencies have changed
    const technicalAdded = currentTechnicalSkillNames.filter(
      n => !fastTrackOriginalCompetencies.technicalSkillNames.includes(n)
    )
    const technicalRemoved = fastTrackOriginalCompetencies.technicalSkillNames.filter(
      n => !currentTechnicalSkillNames.includes(n)
    )
    const behavioralAdded = currentBehavioralNames.filter(
      n => !fastTrackOriginalCompetencies.behavioralCompetencyNames.includes(n)
    )
    const behavioralRemoved = fastTrackOriginalCompetencies.behavioralCompetencyNames.filter(
      n => !currentBehavioralNames.includes(n)
    )
    
    const hasChanges = technicalAdded.length > 0 || technicalRemoved.length > 0 || 
                       behavioralAdded.length > 0 || behavioralRemoved.length > 0
    
    if (hasChanges && currentStage === 'competencies') {
      setWsiRegenerationPrompted(true)
      setAwaitingWSIRegenerationConfirmation(true)
      
      const changesSummary = [
        ...technicalAdded.map(n => `+${n}`),
        ...technicalRemoved.map(n => `-${n}`),
        ...behavioralAdded.map(n => `+${n}`),
        ...behavioralRemoved.map(n => `-${n}`)
      ].slice(0, 5).join(', ')
      
      const wsiRegenMessage: Message = {
        id: `wsi-regen-prompt-${Date.now()}`,
        role: 'assistant',
        content: `Percebi que você alterou algumas competências (${changesSummary}${technicalAdded.length + technicalRemoved.length + behavioralAdded.length + behavioralRemoved.length > 5 ? '...' : ''}).\n\n**Quer que eu atualize as perguntas WSI** para refletir essas mudanças? As perguntas atuais foram geradas com base nas competências anteriores.`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, wsiRegenMessage])
    }
  }, [technicalSkills, behavioralCompetencies, fastTrackOriginalCompetencies, wsiRegenerationPrompted, awaitingWSIRegenerationConfirmation, currentStage])
  
  // Reset message sent flag when suggestions change (new set of suggestions = new prompt)
  const suggestionsKey = fastTrack.suggestions.map(s => s.job_id).join(',')
  const prevSuggestionsKeyRef = useRef(suggestionsKey)
  useEffect(() => {
    if (suggestionsKey !== prevSuggestionsKeyRef.current && suggestionsKey !== '') {
      setFastTrackMessageSent(false)
      prevSuggestionsKeyRef.current = suggestionsKey
    }
  }, [suggestionsKey])
  
  // State to track if learning suggestions have been applied
  const [learningSuggestionsApplied, setLearningSuggestionsApplied] = useState(false)
  
  // Apply learning suggestions to wizard fields when available
  useEffect(() => {
    if (!learning.suggestions || !learning.suggestions.has_suggestions || learningSuggestionsApplied) {
      return
    }
    
    const { salary, skills, behavioral } = learning.suggestions
    
    // Apply salary suggestions if no salary is set
    if (salary?.has_suggestion && salary.min_salary && salary.max_salary) {
      if (!salaryInfo.minSalary && !salaryInfo.maxSalary) {
        setSalaryInfo(prev => ({
          ...prev,
          minSalary: salary.min_salary!.toLocaleString('pt-BR'),
          maxSalary: salary.max_salary!.toLocaleString('pt-BR')
        }))
        analytics.trackFieldUpdate('salario', 'suggestion')
        analytics.trackSuggestion('salary', true)
      }
    }
    
    // Apply skills suggestions if no skills are set
    if (skills?.has_recommendations && skills.recommended_skills?.length && technicalSkills.length === 0) {
      const newSkills: TechnicalSkill[] = skills.recommended_skills.slice(0, 5).map((skill, idx) => ({
        id: `learning-skill-${idx}`,
        name: skill.name,
        level: 'Intermediário' as const,
        required: skill.score > 0.7,
        category: 'tool' as const,
        weight: Math.round(skill.score * 5),
        isWeightInferred: true
      }))
      setTechnicalSkills(newSkills)
      analytics.trackFieldUpdate('technicalSkills', 'suggestion')
      analytics.trackSuggestion('skills', true)
    }
    
    // Apply behavioral suggestions if no behavioral competencies are set
    if (behavioral?.has_recommendations && behavioral.recommended_behavioral?.length && behavioralCompetencies.length === 0) {
      const newBehavioral: BehavioralCompetency[] = behavioral.recommended_behavioral.slice(0, 3).map((comp, idx) => ({
        id: `learning-behavioral-${idx}`,
        name: comp.name,
        weight: Math.round(comp.score * 5),
        justification: 'Sugerido com base em padrões de vagas similares',
        enabled: true,
        isWeightInferred: true
      }))
      setBehavioralCompetencies(newBehavioral)
      analytics.trackFieldUpdate('behavioralCompetencies', 'suggestion')
      analytics.trackSuggestion('behavioral', true)
    }
    
    setLearningSuggestionsApplied(true)
  }, [learning.suggestions, learningSuggestionsApplied, salaryInfo.minSalary, salaryInfo.maxSalary, technicalSkills.length, behavioralCompetencies.length])
  
  // Reset learning suggestions when job title changes
  useEffect(() => {
    setLearningSuggestionsApplied(false)
  }, [detectedCriteria?.cargo])
  
  // Helper to check if a field should be shown (is required based on catalog maturity)
  const isFieldRequiredForWizard = useCallback((fieldName: string): boolean => {
    if (!wizardGreeting?.catalog_status?.required_fields_for_wizard) {
      return true // Show all fields if no data available
    }
    return wizardGreeting.catalog_status.required_fields_for_wizard.includes(fieldName)
  }, [wizardGreeting])
  
  // Effect to auto-collapse sections based on catalog maturity
  useEffect(() => {
    if (wizardGreeting?.catalog_status) {
      const isComplete = wizardGreeting.catalog_status.maturity_level === 'complete'
      const isPartial = wizardGreeting.catalog_status.maturity_level === 'partial'
      
      // For complete/partial maturity, collapse non-required sections by default
      if (isComplete || isPartial) {
        if (!isFieldRequiredForWizard('salario')) {
          setSalaryPanelExpanded(false)
        }
        if (!isFieldRequiredForWizard('competencias')) {
          setCompetenciesPanelExpanded(false)
        }
        // Show notification if any fields were auto-filled
        if (!isFieldRequiredForWizard('salario') || !isFieldRequiredForWizard('competencias')) {
          setShowAutoFilledNotification(true)
          // Auto-hide after 10 seconds
          setTimeout(() => setShowAutoFilledNotification(false), 10000)
        }
      }
    }
  }, [wizardGreeting, isFieldRequiredForWizard])
  
  // Publishing state — company members, languages (from usePublishingState — Sprint 4.2)
  const { companyMembersMap, languagesUserEdited } = publishingState
  const { setCompanyMembersMap, setLanguagesUserEdited } = publishingActions

  // Determine if we're in job creation mode (either from prop or internal state)
  const isInJobCreationMode = isJobCreationMode || internalJobCreationMode

  // Extract languages from conversation messages (only once, when not edited by user)
  useEffect(() => {
    if (languagesUserEdited || jobConfig.languages.length > 0) return // Don't overwrite user edits

    const languagePatterns = [
      { pattern: /ingl[eê]s\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Inglês' },
      { pattern: /espanhol\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Espanhol' },
      { pattern: /franc[eê]s\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Francês' },
      { pattern: /alem[aã]o\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Alemão' },
      { pattern: /italiano\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Italiano' },
      { pattern: /mandarim\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Mandarim' },
      { pattern: /japon[eê]s\s*(fluente|avan[cç]ado|intermedi[aá]rio|b[aá]sico)?/gi, name: 'Japonês' },
    ]

    const allText = messages.map(m => m.content).join(' ').toLowerCase()
    const detectedLanguages: { name: string; level: string }[] = []

    languagePatterns.forEach(({ pattern, name }) => {
      const match = allText.match(pattern)
      if (match) {
        const fullMatch = match[0].toLowerCase()
        let level = 'Intermediário'
        if (fullMatch.includes('fluente') || fullMatch.includes('avançado') || fullMatch.includes('avancado')) {
          level = 'Avançado'
        } else if (fullMatch.includes('básico') || fullMatch.includes('basico')) {
          level = 'Básico'
        }
        detectedLanguages.push({ name, level })
      }
    })

    if (detectedLanguages.length > 0) {
      setJobConfig(prev => ({ ...prev, languages: detectedLanguages }))
    }
  }, [messages, languagesUserEdited, jobConfig.languages.length])
  
  // Check if we have any config data
  const hasConfigData = companyConfig && (
    companyConfig.workModel ||
    (companyConfig.techStack && companyConfig.techStack.length > 0) ||
    (companyConfig.departments && companyConfig.departments.length > 0) ||
    (companyConfig.benefits && companyConfig.benefits.length > 0) ||
    companyConfig.headquarters ||
    (companyConfig.locations && companyConfig.locations.length > 0)
  )
  
  // Check if minimum competencies are met for competencies stage
  const hasMinimumCompetencies = technicalSkills.length >= 3 && behavioralCompetencies.filter(c => c.enabled).length >= 3
  
  // WSI Quality Gates - calculate completeness score
  const wsiQualityGates = useWSIQualityGates({
    technicalSkills: technicalSkills as any,
    behavioralCompetencies: behavioralCompetencies as any,
    detectedCriteria: detectedCriteria as any,
    generatedJobDescription,
    minScoreToAdvance: 70,
  })
  
  // State for draft restoration (must be before hook to avoid race condition)
  const [hasAppliedRestoredDraft, setHasAppliedRestoredDraft] = useState(false)
  
  // State to track if we're awaiting user choice about existing draft
  const [awaitingDraftChoice, setAwaitingDraftChoice] = useState(false)
  const [pendingDraftData, setPendingDraftData] = useState<typeof loadedDraft | null>(null)
  
  // Reset restoration flag when wizard mode changes (for re-entry scenarios)
  useEffect(() => {
    if (!isJobCreationMode) {
      setHasAppliedRestoredDraft(false)
    }
  }, [isJobCreationMode])
  
  // Auto-save hook for wizard draft
  const { isSaving: isAutoSaving, lastSavedAt: autoSaveLastSaved, hasPendingChanges, saveNow: saveWizardDraft, clearDraft: clearWizardDraft, loadedDraft, hasRestoredDraft, hasAttemptedRestore, getLastSavedText } = useWizardAutoSave(
    {
      jobDraftId: wizardDraftId,
      basicInfoFields: {
        jobTitle: basicInfoFields.cargo,
        department: basicInfoFields.area,
        manager: basicInfoFields.gestor,
        locality: basicInfoFields.localidade,
        workModel: basicInfoFields.modeloTrabalho,
        employmentType: basicInfoFields.tipoContrato
      },
      salaryInfo: salaryInfo,
      technicalSkills: technicalSkills as any,
      behavioralCompetencies: behavioralCompetencies as any,
      wsiCandidates: wsiCandidates as any,
      currentStage: currentStage,
      jobDescription: generatedJobDescription || ''
    },
    { enabled: isJobCreationMode, saveInterval: 30000, jobDraftId: wizardDraftId, skipUntilRestored: !hasAppliedRestoredDraft }
  )
  
  useEffect(() => {
    const fetchProactiveSuggestions = async () => {
      try {
        const companyId = user?.company || 'default-company'
        const res = await fetch(`/api/backend-proxy/proactive-actions?path=feed/${companyId}&limit=5`)
        if (!res.ok) return
        const data = await res.json()
        if (!Array.isArray(data) || data.length === 0) return

        const newSuggestions = data.filter((s: any) => !proactiveActionIds.has(s.id))
        if (newSuggestions.length === 0) return

        const newIds = new Set(proactiveActionIds)
        const proactiveMessages: Message[] = newSuggestions.map((s: any) => {
          newIds.add(s.id)
          return {
            id: `proactive-${s.id}`,
            role: 'assistant' as const,
            content: s.message || s.title,
            timestamp: new Date(s.created_at || Date.now()),
            messageType: 'proactive' as const,
            proactiveData: {
              actionId: s.id,
              severity: s.severity || 'info',
              actionLabel: s.action_label || 'Executar',
              suggestedAction: s.suggested_action || {},
            },
          }
        })

        setProactiveActionIds(newIds)
        setMessages(prev => [...prev, ...proactiveMessages])
      } catch (err) {
        // Silent fail - proactive suggestions are non-critical
      }
    }

    const timer = setTimeout(fetchProactiveSuggestions, 10000)
    const interval = setInterval(fetchProactiveSuggestions, 300000)
    return () => {
      clearTimeout(timer)
      clearInterval(interval)
    }
  }, [user, proactiveActionIds])

  // Detect draft and show choice message instead of auto-restoring
  // NOTE: The synchronous check in checkForExistingDraftSync() handles immediate UI feedback
  // This useEffect handles loading draft data from the hook and storing it for restoration
  // It only adds a message if the synchronous check didn't already handle it
  useEffect(() => {
    if (hasRestoredDraft && loadedDraft && !hasAppliedRestoredDraft && isJobCreationMode) {
      // Check if draft has meaningful content (beyond initial stages)
      const currentStage = loadedDraft.currentStage as string
      const hasMeaningfulDraft = currentStage && !INITIAL_STAGES.includes(currentStage)
      
      if (hasMeaningfulDraft) {
        // Always store pending draft data for restoration when user chooses "continue"
        // This ensures the data is available even if sync check already showed the message
        if (!pendingDraftData) {
          setPendingDraftData(loadedDraft)
        }
        
        // Only add the message if we're not already awaiting draft choice
        // (synchronous check in button handler may have already shown the message and set this flag)
        if (!awaitingDraftChoice) {
          setAwaitingDraftChoice(true)
          
          // Use unified stage name mapping
          const stageName = STAGE_DISPLAY_NAMES[currentStage] || currentStage
          
          // Add message asking user what to do
          const draftChoiceMessage: Message = {
            id: `draft-choice-${Date.now()}`,
            role: 'assistant' as const,
            content: DRAFT_DETECTED_MESSAGE(stageName),
            timestamp: new Date()
          }
          setMessages(prev => [...prev, draftChoiceMessage])
        }
        
        // Don't enable auto-save yet - wait for user choice
      } else {
        // No meaningful draft, proceed normally
        setHasAppliedRestoredDraft(true)
      }
    } else if (isJobCreationMode && !hasAppliedRestoredDraft && hasAttemptedRestore && !loadedDraft && !awaitingDraftChoice) {
      // No draft to restore and restore attempt is complete - enable auto-save
      // This handles new sessions without any saved draft
      setHasAppliedRestoredDraft(true)
    }
  }, [hasRestoredDraft, loadedDraft, hasAppliedRestoredDraft, isJobCreationMode, hasAttemptedRestore, awaitingDraftChoice, INITIAL_STAGES, STAGE_DISPLAY_NAMES, pendingDraftData])
  
  // Helper function to apply pending draft data
  const applyPendingDraft = useCallback(() => {
    if (!pendingDraftData) return
    
    // Restore basic info fields
    if (pendingDraftData.basicInfoFields) {
      const bf = pendingDraftData.basicInfoFields
      setBasicInfoFields({
        cargo: bf.jobTitle || '',
        area: bf.department || bf.area || '',
        gestor: bf.manager || '',
        localidade: bf.locality || '',
        modeloTrabalho: bf.workModel || '',
        tipoContrato: bf.employmentType || ''
      })
    }
    
    // Restore salary info
    if (pendingDraftData.salaryInfo) {
      setSalaryInfo(pendingDraftData.salaryInfo)
    }
    
    // Restore technical skills
    if (pendingDraftData.technicalSkills && pendingDraftData.technicalSkills.length > 0) {
      setTechnicalSkills(pendingDraftData.technicalSkills)
    }
    
    // Restore behavioral competencies
    if (pendingDraftData.behavioralCompetencies && pendingDraftData.behavioralCompetencies.length > 0) {
      setBehavioralCompetencies(pendingDraftData.behavioralCompetencies)
    }
    
    // Restore WSI candidates
    if (pendingDraftData.wsiCandidates && pendingDraftData.wsiCandidates.length > 0) {
      setWsiCandidates(pendingDraftData.wsiCandidates)
    }
    
    // Restore current stage
    if (pendingDraftData.currentStage) {
      setCurrentStage(pendingDraftData.currentStage as WizardStage)
    }
    
    // Restore job description
    if (pendingDraftData.jobDescription) {
      setGeneratedJobDescription(pendingDraftData.jobDescription)
    }
    
    // Clear pending state and enable auto-save
    setPendingDraftData(null)
    setAwaitingDraftChoice(false)
    setHasAppliedRestoredDraft(true)
  }, [pendingDraftData])
  
  // Update basic info fields when criteria are detected
  useEffect(() => {
    if (detectedCriteria.cargo && !basicInfoFields.cargo) {
      setBasicInfoFields(prev => ({ ...prev, cargo: detectedCriteria.cargo || '' }))
    }
    if (detectedCriteria.gestorArea && !basicInfoFields.gestor) {
      setBasicInfoFields(prev => ({ ...prev, gestor: detectedCriteria.gestorArea || '' }))
    }
    if (detectedCriteria.localizacao && !basicInfoFields.localidade) {
      setBasicInfoFields(prev => ({ ...prev, localidade: detectedCriteria.localizacao || '' }))
    }
    if (detectedCriteria.modeloTrabalho && !basicInfoFields.modeloTrabalho) {
      setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: detectedCriteria.modeloTrabalho || '' }))
    }
    if (detectedCriteria.tipoContrato && !basicInfoFields.tipoContrato) {
      setBasicInfoFields(prev => ({ ...prev, tipoContrato: detectedCriteria.tipoContrato || '' }))
    }
    if (detectedCriteria.departamento && !basicInfoFields.area) {
      setBasicInfoFields(prev => ({ ...prev, area: detectedCriteria.departamento || '' }))
    }
    
    // Update technical skills when detected
    if (detectedCriteria.competenciasTecnicas.length > 0) {
      const skillCategories: Record<string, 'language' | 'framework' | 'database' | 'tool'> = {
        'Python': 'language', 'JavaScript': 'language', 'TypeScript': 'language', 'Java': 'language',
        'Go': 'language', 'Rust': 'language', 'C#': 'language', 'Ruby': 'language', 'PHP': 'language',
        'Swift': 'language', 'Kotlin': 'language', 'Scala': 'language',
        'React': 'framework', 'Angular': 'framework', 'Vue': 'framework', 'Django': 'framework',
        'FastAPI': 'framework', 'Flask': 'framework', 'Spring': 'framework', 'Rails': 'framework',
        'Laravel': 'framework', 'Express': 'framework', 'Next.js': 'framework', 'Node': 'framework',
        'Nodejs': 'framework', 'React Native': 'framework', 'Flutter': 'framework',
        'PostgreSQL': 'database', 'MySQL': 'database', 'MongoDB': 'database', 'Redis': 'database',
        'Elasticsearch': 'database', 'SQL': 'database', 'Oracle': 'database', 'Cassandra': 'database',
        'Docker': 'tool', 'Kubernetes': 'tool', 'AWS': 'tool', 'Azure': 'tool', 'GCP': 'tool',
        'Git': 'tool', 'Jenkins': 'tool', 'Terraform': 'tool', 'Ansible': 'tool', 'Linux': 'tool',
        'Kafka': 'tool', 'RabbitMQ': 'tool', 'GraphQL': 'tool', 'CI/CD': 'tool',
      }
      
      const baseTs = Date.now()
      const newSkills: TechnicalSkill[] = detectedCriteria.competenciasTecnicas.map((skill, index) => ({
        id: `skill-${baseTs}-${index}-${Math.random().toString(36).slice(2, 6)}`,
        name: skill,
        level: 'Avançado' as const,
        required: index < 3,
        category: skillCategories[skill] || 'tool',
        weight: index < 3 ? 3 : 2
      }))
      
      setTechnicalSkills(prev => {
        const existingNames = prev.map(s => s.name.toLowerCase())
        const filteredNew = newSkills.filter(s => !existingNames.includes(s.name.toLowerCase()))
        return [...prev, ...filteredNew]
      })
      
      // Auto-select department based on detected technical skills
      if (!basicInfoFields.area) {
        const skillsLower = detectedCriteria.competenciasTecnicas.map(s => s.toLowerCase())
        
        // Tech/IT skills
        const techSkills = ['python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue', 'django', 'fastapi', 'flask', 'spring', 'node', 'nodejs', 'go', 'rust', 'c#', '.net', 'ruby', 'rails', 'php', 'swift', 'kotlin', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'devops', 'ci/cd', 'backend', 'frontend', 'full stack', 'fullstack', 'mobile', 'microservices']
        const hasTechSkills = skillsLower.some(s => techSkills.some(ts => s.includes(ts)))
        
        // Data/BI skills - only very specific data roles, NOT generic SQL or "data" which are common in all tech
        const dataSkills = ['data science', 'machine learning', 'power bi', 'tableau', 'data analyst', 'data engineer', 'big data', 'spark', 'hadoop', 'etl', 'data warehouse', 'estatística', 'estatistica', 'cientista de dados', 'engenheiro de dados', 'analista de dados']
        const hasDataSkills = skillsLower.some(s => dataSkills.some(ds => s.includes(ds)))
        
        // Design skills
        const designSkills = ['figma', 'ui', 'ux', 'design', 'photoshop', 'illustrator', 'sketch', 'xd', 'protótipo', 'prototipo', 'wireframe']
        const hasDesignSkills = skillsLower.some(s => designSkills.some(ds => s.includes(ds)))
        
        // Marketing skills
        const marketingSkills = ['marketing', 'seo', 'sem', 'google ads', 'facebook ads', 'analytics', 'mídia', 'midia', 'growth', 'inbound', 'conteúdo', 'conteudo', 'copywriting']
        const hasMarketingSkills = skillsLower.some(s => marketingSkills.some(ms => s.includes(ms)))
        
        // Sales/Commercial skills
        const salesSkills = ['sales', 'vendas', 'salesforce', 'crm', 'hubspot', 'pipedrive', 'prospecção', 'prospeccao', 'negociação', 'negociacao', 'comercial']
        const hasSalesSkills = skillsLower.some(s => salesSkills.some(ss => s.includes(ss)))
        
        // Finance/Operations skills - include excel as a finance indicator
        const financeSkills = ['sap', 'erp', 'oracle', 'totvs', 'contabilidade', 'financeiro', 'fiscal', 'controladoria', 'excel avançado', 'excel']
        const hasFinanceSkills = skillsLower.some(s => financeSkills.some(fs => s.includes(fs)))
        
        // Determine department based on skill priorities
        // IMPORTANT: Tech skills have priority - developers with SQL should still be Tecnologia/TI
        let selectedArea = ''
        if (hasTechSkills) {
          selectedArea = 'Tecnologia/TI'
        } else if (hasDataSkills) {
          // Only Dados/BI if no core tech skills detected
          selectedArea = 'Dados/BI'
        } else if (hasDesignSkills) {
          selectedArea = 'Design'
        } else if (hasMarketingSkills) {
          selectedArea = 'Marketing'
        } else if (hasSalesSkills) {
          selectedArea = 'Comercial'
        } else if (hasFinanceSkills) {
          selectedArea = 'Financeiro'
        }
        
        if (selectedArea) {
          setBasicInfoFields(prev => ({ ...prev, area: selectedArea }))
        }
      }
    }
    
    // Also try to detect area from job title if not yet selected
    if (!basicInfoFields.area && detectedCriteria.cargo) {
      const cargoLower = detectedCriteria.cargo.toLowerCase()
      
      // Map cargo keywords to areas
      const areaKeywords: Record<string, string[]> = {
        'Fiscal/Tributário': ['impostos', 'fiscal', 'tributário', 'tributario', 'tax', 'tributos', 'imposto', 'icms', 'pis', 'cofins', 'irpj', 'csll', 'sped', 'obrigações acessórias', 'obrigacoes acessorias'],
        'Financeiro': ['financeiro', 'financeira', 'finanças', 'financas', 'controladoria', 'contábil', 'contabil', 'tesouraria', 'planejamento financeiro', 'fp&a', 'controller', 'contabilidade'],
        'Recursos Humanos': ['rh', 'recursos humanos', 'people', 'gente', 'talent', 'talentos', 'recrutamento', 'seleção', 'selecao', 'dp', 'departamento pessoal', 'cultura', 'treinamento'],
        'Comercial': ['comercial', 'vendas', 'sales', 'account', 'cliente', 'negócios', 'negocios', 'business'],
        'Marketing': ['marketing', 'comunicação', 'comunicacao', 'branding', 'brand', 'mídia', 'midia', 'digital'],
        'Operações': ['operações', 'operacoes', 'operacional', 'logística', 'logistica', 'supply', 'suprimentos', 'compras', 'procurement'],
        'Jurídico': ['jurídico', 'juridico', 'legal', 'compliance', 'contratos'],
        'Tecnologia/TI': ['tecnologia', 'ti', 'sistemas', 'desenvolvimento', 'software', 'infraestrutura', 'dados', 'data', 'produto', 'product'],
        'Administrativo': ['administrativo', 'administrativa', 'facilities', 'escritório', 'escritorio', 'secretaria'],
        'Qualidade': ['qualidade', 'quality', 'processos', 'melhoria contínua'],
      }
      
      for (const [area, keywords] of Object.entries(areaKeywords)) {
        if (keywords.some(kw => cargoLower.includes(kw))) {
          setBasicInfoFields(prev => ({ ...prev, area }))
          break
        }
      }
    }
  }, [detectedCriteria, basicInfoFields.area, detectedCriteria.cargo])

  const quickSuggestions = [
    "Anexar JD",
    "Usar anterior",
    "Ver exemplos"
  ]

  const suggestionTags = [
    { label: "Criar vaga", icon: Plus, action: "criar_vaga" },
    { label: "Sugerir melhorias", icon: Brain, action: "sugerir_melhorias" },
  ]

  const typeText = useCallback((text: string, messageId: string) => {
    setIsTypingEffect(true)
    let currentIndex = 0
    const speed = 12

    const typeNextChar = () => {
      if (currentIndex < text.length) {
        setDisplayedText(text.slice(0, currentIndex + 1))
        currentIndex++
        typingTimeoutRef.current = setTimeout(typeNextChar, speed)
      } else {
        setIsTypingEffect(false)
        setMessages(prev => prev.map(msg => 
          msg.id === messageId ? { ...msg, isTyping: false } : msg
        ))
      }
    }

    typeNextChar()
  }, [])

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      if (initialMessages && initialMessages.length > 0) {
        const convertedMessages: Message[] = initialMessages.map(m => ({
          id: m.id,
          role: m.role,
          content: m.content,
          timestamp: m.timestamp,
          isTyping: false
        }))
        setMessages(convertedMessages)
        setDisplayedText("")
      } else {
        const messageToShow = isJobCreationMode 
          ? INITIAL_JOB_CREATION_MESSAGE 
          : initialLiaMessage
        
        const initialMsg: Message = {
          id: 'initial-lia',
          role: 'assistant',
          content: messageToShow,
          timestamp: new Date(),
          isTyping: true
        }
        setMessages([initialMsg])
        setDisplayedText("")
        setTimeout(() => {
          typeText(messageToShow, 'initial-lia')
        }, 100)
      }
    }
  }, [isOpen, messages.length, typeText, initialLiaMessage, initialMessages, isJobCreationMode])

  useEffect(() => {
    if (isOpen && initialMessage && messages.length === 1 && !isTypingEffect) {
      setTimeout(() => {
        handleSendMessage(initialMessage)
        setInputValue("")
      }, 500)
    }
  }, [isOpen, initialMessage, messages.length, isTypingEffect])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, displayedText])

  useEffect(() => {
    if (isOpen && !isTypingEffect) {
      inputRef.current?.focus()
    }
  }, [isOpen, isTypingEffect])

  // Sync messages back to parent component for persistence across fullscreen transitions
  // Use ref to avoid infinite loop caused by callback changing on every render
  const onMessagesUpdateRef = useRef(onMessagesUpdate)
  onMessagesUpdateRef.current = onMessagesUpdate
  
  const lastSyncedMessagesRef = useRef<string>('')
  
  useEffect(() => {
    if (messages.length > 0) {
      // Only sync if messages actually changed (avoid infinite loop)
      const messagesKey = messages.map(m => `${m.id}:${m.content.substring(0, 50)}`).join('|')
      if (messagesKey !== lastSyncedMessagesRef.current && onMessagesUpdateRef.current) {
        lastSyncedMessagesRef.current = messagesKey
        const syncMessages = messages.filter(m => m.role !== 'system').map(m => ({
          id: m.id,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          timestamp: m.timestamp
        }))
        onMessagesUpdateRef.current(syncMessages)
      }
    }
  }, [messages])

  // Fetch company configuration when modal opens in job creation mode
  useEffect(() => {
    const fetchCompanyConfig = async () => {
      if (!isOpen || !isInJobCreationMode || configLoaded) return
      
      try {
        const [profileRes, departmentsRes, benefitsRes, greetingRes] = await Promise.all([
          fetch('/api/backend-proxy/company/profile'),
          fetch('/api/backend-proxy/company/departments'),
          fetch('/api/backend-proxy/company/benefits/?company_id=default'),
          fetch('/api/backend-proxy/company/smart-wizard-greeting?company_id=default')
        ])
        
        const config: typeof companyConfig = {}
        const newFieldsFromConfig = new Set<string>()
        
        if (profileRes.ok) {
          const profileData = await profileRes.json()
          if (profileData.work_model) {
            config.workModel = profileData.work_model
          }
          if (profileData.hybrid_days_onsite) {
            config.hybridDaysOnsite = profileData.hybrid_days_onsite
          }
          if (profileData.employment_types && Array.isArray(profileData.employment_types)) {
            config.employmentTypes = profileData.employment_types
          }
          if (profileData.tech_stack && Array.isArray(profileData.tech_stack)) {
            config.techStack = profileData.tech_stack.map((t: string) => {
              const parts = t.split(':')
              return parts.length > 1 ? parts[1] : t
            })
          }
          if (profileData.values) config.values = profileData.values
          if (profileData.coreCompetencies) config.coreCompetencies = profileData.coreCompetencies
          if (profileData.evp_bullets) config.evpBullets = profileData.evp_bullets
          if (profileData.headquarters) config.headquarters = profileData.headquarters
          if (profileData.locations) config.locations = profileData.locations
        }
        
        if (departmentsRes.ok) {
          const departmentsData = await departmentsRes.json()
          if (Array.isArray(departmentsData)) {
            config.departments = departmentsData.map((d: any) => ({
              id: d.id,
              name: d.name
            }))
            
            // Fetch members from each department to build name → email map
            const membersMap = new Map<string, string>()
            try {
              const memberPromises = departmentsData.map(async (dept: any) => {
                try {
                  const membersRes = await fetch(`/api/backend-proxy/company/departments/${dept.id}/members`)
                  if (membersRes.ok) {
                    const members = await membersRes.json()
                    if (Array.isArray(members)) {
                      members.forEach((m: any) => {
                        if (m.name && m.email) {
                          // Store with normalized name (trimmed, lowercase for lookup)
                          membersMap.set(m.name.trim().toLowerCase(), m.email)
                          // Also store with original name
                          membersMap.set(m.name.trim(), m.email)
                        }
                      })
                    }
                  }
                } catch (err) {
                }
              })
              await Promise.all(memberPromises)
              setCompanyMembersMap(membersMap)
            } catch (err) {
            }
          }
        }
        
        if (benefitsRes.ok) {
          const benefitsData = await benefitsRes.json()
          const benefitsList = Array.isArray(benefitsData) ? benefitsData : benefitsData.items || []
          config.benefits = benefitsList.filter((b: any) => b.is_active)
        }
        
        // Fetch and store smart wizard greeting with prefill_data
        if (greetingRes.ok) {
          const greetingData = await greetingRes.json()
          if (greetingData.greeting_message && greetingData.catalog_status) {
            setWizardGreeting(greetingData)
            
            // Use prefill_data to enhance form population for mature catalogs
            const prefillData = greetingData.prefill_data || {}
            
            // Pre-fill departments from prefill_data (if not already set from config)
            if (prefillData.departments && Array.isArray(prefillData.departments) && prefillData.departments.length > 0) {
              if (!config.departments || config.departments.length === 0) {
                config.departments = prefillData.departments.map((d: any, idx: number) => ({
                  id: d.id || `prefill-dept-${idx}`,
                  name: d.name || d
                }))
              }
            }
            
            // Pre-fill benefits from prefill_data (if not already set from config)
            if (prefillData.benefits && Array.isArray(prefillData.benefits) && prefillData.benefits.length > 0) {
              if (!config.benefits || config.benefits.length === 0) {
                config.benefits = prefillData.benefits.map((b: any) => ({
                  id: b.id,
                  name: b.name,
                  value: b.value,
                  is_active: b.is_active ?? true
                }))
              }
            }
            
            // Enhance tech_stack suggestions from prefill_data
            if (prefillData.tech_stack && Array.isArray(prefillData.tech_stack) && prefillData.tech_stack.length > 0) {
              const existingTechStack = config.techStack || []
              const prefillTechStack = prefillData.tech_stack.map((t: string) => {
                const parts = t.split(':')
                return parts.length > 1 ? parts[1] : t
              })
              // Merge prefill tech stack with existing, avoiding duplicates
              const mergedTechStack = [...new Set([...existingTechStack, ...prefillTechStack])]
              config.techStack = mergedTechStack
            }
          }
        }
        
        // Mark wizard greeting as loaded (even if it failed - we have fallback)
        setWizardGreetingLoaded(true)
        
        setCompanyConfig(config)
        
        // Pre-fill fields from company config
        if (config.workModel) {
          const workModelMap: Record<string, string> = {
            'remote': 'Remoto',
            'hybrid': 'Híbrido',
            'onsite': 'Presencial',
            'remoto': 'Remoto',
            'híbrido': 'Híbrido',
            'presencial': 'Presencial'
          }
          const mappedModel = workModelMap[config.workModel.toLowerCase()] || config.workModel
          setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: mappedModel }))
          setDetectedCriteria(prev => ({ ...prev, modeloTrabalho: mappedModel }))
          newFieldsFromConfig.add('modeloTrabalho')
          setFieldOrigins(prev => ({ ...prev, work_model: { source: 'default', confidence: 0.85 } }))
        }
        
        // Pre-fill employment type with first company default
        if (config.employmentTypes && config.employmentTypes.length > 0) {
          setBasicInfoFields(prev => ({ ...prev, tipoContrato: config.employmentTypes![0] }))
          newFieldsFromConfig.add('tipoContrato')
          setFieldOrigins(prev => ({ ...prev, employment_type: { source: 'default', confidence: 0.85 } }))
        }
        
        // Pre-fill hybrid days onsite with company default
        if (config.hybridDaysOnsite) {
          setJobConfig(prev => ({ ...prev, hybridDaysOnsite: config.hybridDaysOnsite }))
        }
        
        if (config.headquarters || (config.locations && config.locations.length > 0)) {
          const location = config.headquarters || config.locations?.[0] || ''
          if (location) {
            setBasicInfoFields(prev => ({ ...prev, localidade: location }))
            setDetectedCriteria(prev => ({ ...prev, localizacao: location }))
            setFieldOrigins(prev => ({ ...prev, location: { source: 'default', confidence: 0.85 } }))
            newFieldsFromConfig.add('localizacao')
          }
        }
        
        // Pre-fill department with first company default
        if (config.departments && config.departments.length > 0 && !basicInfoFields.area) {
          setBasicInfoFields(prev => ({ ...prev, area: config.departments![0].name }))
          newFieldsFromConfig.add('area')
        }
        
        // Pre-fill tech stack
        if (config.techStack && config.techStack.length > 0) {
          const skillCategories: Record<string, 'language' | 'framework' | 'database' | 'tool'> = {
            'Python': 'language', 'JavaScript': 'language', 'TypeScript': 'language', 'Java': 'language',
            'Go': 'language', 'Rust': 'language', 'C#': 'language', 'Ruby': 'language', 'PHP': 'language',
            'Node.js': 'framework', 'React': 'framework', 'Angular': 'framework', 'Vue.js': 'framework',
            'Django': 'framework', 'FastAPI': 'framework', 'Flask': 'framework', 'Spring': 'framework',
            'Next.js': 'framework', 'Express': 'framework', 'React Native': 'framework', 'Flutter': 'framework',
            'PostgreSQL': 'database', 'MySQL': 'database', 'MongoDB': 'database', 'Redis': 'database',
            'Elasticsearch': 'database', 'SQL': 'database', 'Oracle': 'database',
            'Docker': 'tool', 'Kubernetes': 'tool', 'AWS': 'tool', 'Azure': 'tool', 'GCP': 'tool',
            'Git': 'tool', 'Jenkins': 'tool', 'Terraform': 'tool', 'Linux': 'tool',
          }
          
          const configSkills: TechnicalSkill[] = config.techStack.slice(0, 5).map((tech, idx) => ({
            id: `config-skill-${idx}`,
            name: tech,
            level: 'Intermediário' as const,
            required: false,
            category: skillCategories[tech] || 'tool',
            weight: 2
          }))
          
          setTechnicalSkills(prev => {
            const existingNames = prev.map(s => s.name.toLowerCase())
            const newSkills = configSkills.filter(s => !existingNames.includes(s.name.toLowerCase()))
            return [...prev, ...newSkills]
          })
          
          if (configSkills.length > 0) {
            newFieldsFromConfig.add('competenciasTecnicas')
          }
        }
        
        // Pre-fill benefits
        if (config.benefits && config.benefits.length > 0) {
          const configBenefits: Benefit[] = config.benefits.map((b, idx) => ({
            id: `config-benefit-${idx}`,
            name: b.name,
            value: b.value ? `R$ ${b.value}` : undefined,
            enabled: true
          }))
          
          setSalaryInfo(prev => {
            const existingNames = prev.benefits.map(b => b.name.toLowerCase())
            const newBenefits = configBenefits.filter(b => !existingNames.includes(b.name.toLowerCase()))
            return {
              ...prev,
              benefits: [...prev.benefits, ...newBenefits]
            }
          })
          
          if (configBenefits.length > 0) {
            newFieldsFromConfig.add('benefits')
          }
        }
        
        setFieldsFromConfig(newFieldsFromConfig)
        setConfigLoaded(true)
        
      } catch (error) {
        setConfigLoaded(true)
        // Also mark greeting as loaded to prevent blocking (fallback message will be used)
        setWizardGreetingLoaded(true)
      }
    }
    
    fetchCompanyConfig()
  }, [isOpen, isInJobCreationMode, configLoaded, basicInfoFields.modeloTrabalho, basicInfoFields.localidade])

  // Sync company screening questions from settings with companyDefaultQuestions state
  useEffect(() => {
    if (!isLoadingEligibilityQuestions) {
      const mappedQuestions = companyEligibilityQuestions.map(q => ({
        id: q.id,
        question: q.question_text,
        type: 'open' as const,
        enabled: q.is_active,
        fromConfig: true
      }))
      setCompanyDefaultQuestions(mappedQuestions)
    }
  }, [companyEligibilityQuestions, isLoadingEligibilityQuestions])

  // Sync deadlines with SLAs from recruitment stages configuration
  useEffect(() => {
    if (!isLoadingStages && sla) {
      setJobConfig(prev => ({
        ...prev,
        deadlineScreening: sla.calculateDeadline(sla.screeningSLA),
        deadlineShortlist: sla.calculateDeadline(sla.shortlistSLA),
        deadline: sla.calculateDeadline(sla.totalSLA)
      }))
    }
  }, [isLoadingStages, sla])

  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current)
      }
    }
  }, [])

  // Generate job description when entering review stage
  useEffect(() => {
    if (currentStage === 'review-publish' && !jobDescription) {
      generateJobDescription()
    }
  }, [currentStage])

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
          company_id: 'default'
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
  }, [currentStage, basicInfoFields.cargo])

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
    }, PROACTIVE_MESSAGE_DELAY)
    
    return () => {
      if (salaryProactiveTimerRef.current) {
        clearTimeout(salaryProactiveTimerRef.current)
        salaryProactiveTimerRef.current = null
      }
    }
  }, [currentStage, salaryInfo, salaryStageCompletionShown, isFieldRequiredForWizard, PROACTIVE_MESSAGE_DELAY])

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
  }, [currentStage, basicInfoFields, inputEvaluationStageCompletionShown, PROACTIVE_MESSAGE_DELAY])

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
  }, [currentStage, technicalSkills, behavioralCompetencies, competenciesStageCompletionShown, PROACTIVE_MESSAGE_DELAY])

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
  }, [currentStage, wsiCandidates, wsiQuestionsStageCompletionShown, PROACTIVE_MESSAGE_DELAY])

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
  }, [currentStage, approvedCandidates.length, rejectedCandidates.length, calibrationStageCompletionShown, calibrationComplete, PROACTIVE_MESSAGE_DELAY])

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
  }, [currentStage])

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
  }, [isResizing])

  const extractCriteriaFromText = (text: string): DetectedCriteria => {
    const lowerText = text.toLowerCase()
    const newCriteria = { ...detectedCriteria }

    // Character class that includes both lowercase and uppercase Portuguese letters
    const ptLetters = 'a-zA-ZáàâãéèêíïóôõöúçÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇ'
    
    // Common job titles list for direct matching
    const commonJobTitles = [
      'analista contábil', 'analista contabil', 'analista fiscal', 'analista financeiro', 'analista financeira',
      'analista de rh', 'analista de recursos humanos', 'analista de dp', 'analista de departamento pessoal',
      'analista de sistemas', 'analista de dados', 'analista de bi', 'analista de negócios', 'analista de negocios',
      'analista de marketing', 'analista de vendas', 'analista comercial', 'analista tributário', 'analista tributario',
      'analista de compras', 'analista de suprimentos', 'analista de logística', 'analista de logistica',
      'analista de qualidade', 'analista de processos', 'analista de projetos', 'analista de crédito', 'analista de credito',
      'desenvolvedor python', 'desenvolvedor java', 'desenvolvedor javascript', 'desenvolvedor react',
      'desenvolvedor frontend', 'desenvolvedor front-end', 'desenvolvedor backend', 'desenvolvedor back-end',
      'desenvolvedor full stack', 'desenvolvedor fullstack', 'desenvolvedor mobile', 'desenvolvedor web',
      'desenvolvedor .net', 'desenvolvedor dotnet', 'desenvolvedor node', 'desenvolvedor nodejs',
      'desenvolvedor angular', 'desenvolvedor vue', 'desenvolvedor go', 'desenvolvedor golang',
      'engenheiro de software', 'engenheiro de dados', 'engenheiro de machine learning', 'engenheiro devops',
      'engenheiro de qa', 'engenheiro de qualidade', 'engenheiro de produção', 'engenheiro de producao',
      'gerente de projetos', 'gerente de rh', 'gerente financeiro', 'gerente comercial', 'gerente de vendas',
      'gerente de marketing', 'gerente de operações', 'gerente de operacoes', 'gerente de ti', 'gerente de tecnologia',
      'gerente de produto', 'gerente de produção', 'gerente de producao', 'gerente administrativo',
      'coordenador de rh', 'coordenador financeiro', 'coordenador de projetos', 'coordenador de ti',
      'coordenador comercial', 'coordenador de marketing', 'coordenador de operações', 'coordenador de operacoes',
      'supervisor de produção', 'supervisor de producao', 'supervisor de vendas', 'supervisor de operações',
      'diretor financeiro', 'diretor de rh', 'diretor de ti', 'diretor comercial', 'diretor de operações',
      'cfo', 'cto', 'coo', 'cmo', 'cpo', 'ceo', 'chro',
      'product manager', 'product owner', 'scrum master', 'agile coach', 'tech lead', 'tech leader',
      'ux designer', 'ui designer', 'ux/ui designer', 'product designer', 'designer gráfico', 'designer grafico',
      'assistente administrativo', 'assistente financeiro', 'assistente de rh', 'assistente comercial',
      'auxiliar administrativo', 'auxiliar financeiro', 'auxiliar de escritório', 'auxiliar de escritorio',
      'contador', 'contadora', 'controller', 'tesoureiro', 'tesoureira',
      'cientista de dados', 'data scientist', 'data analyst', 'data engineer', 'machine learning engineer',
      'devops engineer', 'sre', 'site reliability engineer', 'cloud engineer', 'arquiteto de software',
      'arquiteto de soluções', 'arquiteto de solucoes', 'arquiteto cloud', 'arquiteto de sistemas',
      'consultor sap', 'consultor oracle', 'consultor de ti', 'consultor financeiro', 'consultor tributário',
      'advogado', 'advogada', 'advogado trabalhista', 'advogado tributário', 'advogado empresarial',
      'recrutador', 'recrutadora', 'talent acquisition', 'headhunter', 'business partner de rh', 'bp de rh',
      'vendedor', 'vendedora', 'executivo de vendas', 'executivo de contas', 'key account manager',
      'comprador', 'compradora', 'buyer', 'strategic buyer'
    ]
    
    // Try to match common job titles first (more accurate)
    for (const title of commonJobTitles) {
      const titlePattern = new RegExp(`\\b${title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?:\\s+(?:s[eê]nior|sr\\.?|pleno|pl\\.?|j[uú]nior|jr\\.?))?\\b`, 'i')
      const match = text.match(titlePattern)
      if (match) {
        newCriteria.cargo = match[0].split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
        break
      }
    }
    
    // If no common title found, try patterns
    if (!newCriteria.cargo) {
      const cargoPatterns = [
        // "preciso de um X", "busco X", "contratando X"
        new RegExp(`(?:preciso\\s+de\\s+(?:um|uma)?|busco\\s+(?:um|uma)?|contratando|procuro\\s+(?:um|uma)?)\\s+([${ptLetters}\\s]+?)(?:\\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr))?(?:\\s+(?:para|que|com|\\.|,|$))`, 'i'),
        // "vaga de X", "vaga para X"
        new RegExp(`vaga\\s+(?:de|para)\\s+([${ptLetters}\\s]+?)(?:\\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr))?(?:\\s+(?:que|para\\s+a|com\\s+experi[êe]ncia|na|no|em|,|\\.|$))`, 'i'),
        // "cargo: X", "posição: X", "função: X"
        new RegExp(`(?:cargo|posi[çc][aã]o|fun[çc][aã]o)\\s*[:\\-]?\\s*([${ptLetters}\\s]+?)(?:\\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr))?(?:\\s+(?:que|para|com|,|\\.|$))`, 'i'),
        // Specific role patterns - capture the full role
        /\b(desenvolvedor[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr|que|para|com|na|no|,|\.|$))/i,
        /\b(analista\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr|que|para|com|na|no|,|\.|$))/i,
        /\b(gerente\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
        /\b(coordenador[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
        /\b(diretor[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
        /\b(engenheiro[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr|que|para|com|na|no|,|\.|$))/i,
        /\b(especialista\s+(?:em\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:s[eê]nior|sr|que|para|com|na|no|,|\.|$))/i,
        /\b(arquiteto[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:s[eê]nior|sr|que|para|com|na|no|,|\.|$))/i,
        /\b(head\s+(?:de\s+|of\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
        /\b(l[ií]der\s+(?:de\s+|t[eé]cnico\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
        /\b(product\s+(?:manager|owner))(?:\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr))?/i,
        /\b(tech\s+lead(?:er)?)(?:\s+(?:s[eê]nior|sr))?/i,
        /\b(designer\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]*)(?=\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr|que|para|com|,|\.|$))/i,
        /\b(consultor[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:s[eê]nior|sr|pleno|pl|j[uú]nior|jr|que|para|com|na|no|,|\.|$))/i,
        /\b(supervisor[a]?\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
        /\b(assistente\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i,
        /\b(auxiliar\s+(?:de\s+)?[a-záàâãéèêíïóôõöúç\s]+?)(?=\s+(?:que|para|com|na|no|,|\.|$))/i
      ]
      
      const stopWords = ['que', 'para', 'com', 'experiência', 'experiencia', 'na', 'no', 'em', 'da', 'do', 'base', 'localizado', 'localizada', 'atuando', 'trabalhar', 'vai', 'será', 'sera', 'deve', 'precisa']
      
      for (const pattern of cargoPatterns) {
        const match = text.match(pattern)
        if (match) {
          let cargo = match[1] || match[0]
          cargo = cargo.replace(/^(?:vaga\s+(?:de|para)\s+|cargo\s*[:\-]?\s*|posi[çc][aã]o\s*[:\-]?\s*|fun[çc][aã]o\s*[:\-]?\s*|preciso\s+de\s+(?:um|uma)?\s*|busco\s+(?:um|uma)?\s*|contratando\s*|procuro\s+(?:um|uma)?\s*)/i, '')
          
          const words = cargo.split(/\s+/)
          const cleanWords: string[] = []
          for (const word of words) {
            if (stopWords.includes(word.toLowerCase())) break
            cleanWords.push(word)
          }
          cargo = cleanWords.join(' ').trim()
          
          if (cargo.length > 2 && cargo.length < 60) {
            newCriteria.cargo = cargo.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ').trim()
            break
          }
        }
      }
    }
    
    // ========== AREA/DEPARTMENT DETECTION ==========
    const areaPatterns = [
      /\b(?:área|area|departamento|setor)\s*(?:de|do|da)?\s*[:\-]?\s*([a-záàâãéèêíïóôõöúç\s\/]+?)(?:\s*[,.\-]|\s+(?:com|para|que|na|no|em|$))/i,
      /\b(?:time|equipe)\s+(?:de|do|da)\s+([a-záàâãéèêíïóôõöúç\s\/]+?)(?:\s*[,.\-]|\s+(?:com|para|que|$))/i,
      /\bpara\s+(?:o|a)?\s*(?:área|area|departamento|time|equipe)\s+(?:de|do|da)?\s*([a-záàâãéèêíïóôõöúç\s\/]+?)(?:\s*[,.\-]|\s+(?:com|que|$))/i
    ]
    
    const areaKeywordMap: Record<string, string> = {
      'ti': 'Tecnologia/TI', 'tecnologia': 'Tecnologia/TI', 'sistemas': 'Tecnologia/TI', 'desenvolvimento': 'Tecnologia/TI',
      'financeiro': 'Financeiro', 'finanças': 'Financeiro', 'financas': 'Financeiro', 'controladoria': 'Financeiro',
      'contábil': 'Contábil', 'contabil': 'Contábil', 'contabilidade': 'Contábil',
      'fiscal': 'Fiscal/Tributário', 'tributário': 'Fiscal/Tributário', 'tributario': 'Fiscal/Tributário', 'impostos': 'Fiscal/Tributário',
      'rh': 'Recursos Humanos', 'recursos humanos': 'Recursos Humanos', 'gente e gestão': 'Recursos Humanos', 'people': 'Recursos Humanos',
      'dp': 'Departamento Pessoal', 'departamento pessoal': 'Departamento Pessoal', 'folha': 'Departamento Pessoal',
      'comercial': 'Comercial', 'vendas': 'Comercial', 'sales': 'Comercial',
      'marketing': 'Marketing', 'comunicação': 'Marketing', 'comunicacao': 'Marketing', 'growth': 'Marketing',
      'operações': 'Operações', 'operacoes': 'Operações', 'produção': 'Operações', 'producao': 'Operações',
      'logística': 'Logística', 'logistica': 'Logística', 'supply': 'Logística', 'suprimentos': 'Logística',
      'compras': 'Compras', 'procurement': 'Compras',
      'jurídico': 'Jurídico', 'juridico': 'Jurídico', 'legal': 'Jurídico',
      'qualidade': 'Qualidade', 'qa': 'Qualidade',
      'dados': 'Dados/BI', 'bi': 'Dados/BI', 'analytics': 'Dados/BI', 'data': 'Dados/BI',
      'design': 'Design', 'ux': 'Design', 'ui': 'Design', 'produto': 'Produto', 'product': 'Produto',
      'administrativo': 'Administrativo', 'admin': 'Administrativo'
    }
    
    // Try to detect area from explicit patterns
    for (const pattern of areaPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const areaText = match[1].trim().toLowerCase()
        // Check if it matches a known area
        for (const [key, value] of Object.entries(areaKeywordMap)) {
          if (areaText.includes(key)) {
            newCriteria.departamento = value
            break
          }
        }
        if (newCriteria.departamento) break
        // If not a known keyword, use the detected text directly
        if (areaText.length > 1 && areaText.length < 40) {
          newCriteria.departamento = match[1].trim().split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
          break
        }
      }
    }
    
    // Also try to detect area from cargo if not found
    if (!newCriteria.departamento && newCriteria.cargo) {
      const cargoLower = newCriteria.cargo.toLowerCase()
      for (const [key, value] of Object.entries(areaKeywordMap)) {
        if (cargoLower.includes(key)) {
          newCriteria.departamento = value
          break
        }
      }
    }

    const gestorPatterns = [
      // Formato direto com dois pontos: "gestor: carlos silva", "gestor: ti"
      new RegExp(`gestor(?:a)?[:\\s]+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
      // Formato direto com dois pontos: "área: tecnologia", "departamento: ti"
      new RegExp(`(?:área|area|departamento|setor)[:\\s]+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
      // Formato com barra: "gestor: carlos silva/departamento de ti" - captura antes da barra
      new RegExp(`gestor(?:a)?[:\\s]+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})(?:\\/|$)`, 'i'),
      // Reporta para
      new RegExp(`reporta(?:r[áa])?\\s+(?:para|ao?|diretamente\\s+ao?)\\s+(?:o\\s+|a\\s+)?([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
      // Equipe do/da
      new RegExp(`equipe\\s+d[oa]\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,2})`, 'i'),
      // Time do/da
      new RegExp(`time\\s+d[oa]\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,2})`, 'i'),
      // Supervisão/liderança/gestão de
      new RegExp(`(?:sob\\s+)?(?:supervisão|liderança|gestão)\\s+(?:do?a?\\s+)?([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,2})`, 'i'),
      // Gestor de [área]
      new RegExp(`gestor(?:a)?\\s+de\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
      // Área/departamento/setor de [nome]
      new RegExp(`(?:área|departamento|setor)\\s+de\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
      // Gestão de [área]
      new RegExp(`gestão\\s+de\\s+([${ptLetters}]+(?:\\s+[${ptLetters}]+){0,3})`, 'i'),
    ]
    
    const invalidGestorTerms = ['de', 'da', 'do', 'para', 'com', 'nivel', 'nível', 'senior', 'sênior', 'pleno', 'junior', 'júnior', 'vagas', 'vaga', 'posição', 'posicao', 'cargo', 'responsabilidades']
    
    for (const pattern of gestorPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const name = match[1].trim()
        const firstWord = name.split(' ')[0].toLowerCase()
        if (name.length > 2 && !invalidGestorTerms.includes(firstWord)) {
          newCriteria.gestorArea = name.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
          break
        }
      }
    }

    const techSkills = [
      // Tech/IT
      'python', 'javascript', 'react', 'node', 'nodejs', 'django', 'fastapi', 'java', 'typescript', 
      'angular', 'vue', 'sql', 'aws', 'docker', 'kubernetes', 'data science', 'machine learning',
      'flask', 'spring', 'go', 'golang', 'rust', 'c#', '.net', 'dotnet', 'ruby', 'rails', 'php',
      'laravel', 'swift', 'kotlin', 'flutter', 'react native', 'mongodb', 'postgresql', 'mysql',
      'redis', 'elasticsearch', 'kafka', 'rabbitmq', 'graphql', 'rest api', 'microservices',
      'devops', 'ci/cd', 'jenkins', 'terraform', 'ansible', 'azure', 'gcp', 'linux', 'git',
      'infraestrutura', 'cybersegurança', 'segurança da informação', 'sre', 'site reliability',
      'engenharia de software', 'implantação', 'sistemas', 'redes', 'cloud', 'nuvem',
      'banco de dados', 'backend', 'frontend', 'full stack', 'fullstack', 'mobile',
      'scrum', 'agile', 'kanban', 'jira', 'figma', 'ux', 'ui', 'product', 'analytics',
      'power bi', 'tableau', 'excel avançado', 'sap', 'salesforce', 'crm', 'erp',
      // Fiscal/Tributário/Contábil
      'ifrs', 'impostos diretos', 'impostos indiretos', 'compliance', 'obrigações acessórias',
      'obrigacoes acessorias', 'sped', 'ecf', 'ecd', 'reinf', 'dctf', 'per/dcomp', 'perdcomp',
      'icms', 'ipi', 'pis', 'cofins', 'irpj', 'csll', 'iss', 'inss', 'fgts',
      'legislação tributária', 'legislacao tributaria', 'planejamento tributário', 'planejamento tributario',
      'contabilidade', 'controladoria', 'auditoria', 'cpc', 'gaap', 'usgaap',
      'conciliação contábil', 'conciliacao contabil', 'fechamento contábil', 'fechamento contabil',
      'análise fiscal', 'analise fiscal', 'apuração de impostos', 'apuracao de impostos',
      'transfer pricing', 'preços de transferência', 'precos de transferencia',
      'lucro real', 'lucro presumido', 'simples nacional', 'regime tributário', 'regime tributario',
      // Financeiro
      'fp&a', 'tesouraria', 'fluxo de caixa', 'dre', 'balanço patrimonial', 'balanco patrimonial',
      'orçamento', 'orcamento', 'budget', 'forecast', 'valuation', 'm&a', 'due diligence',
      'análise financeira', 'analise financeira', 'modelagem financeira', 'excel financeiro',
      // RH/DP
      'folha de pagamento', 'e-social', 'esocial', 'clt', 'legislação trabalhista', 
      'recrutamento e seleção', 'r&s', 'treinamento e desenvolvimento', 't&d',
      'avaliação de desempenho', 'clima organizacional', 'cargos e salários',
      // Jurídico
      'direito tributário', 'direito trabalhista', 'direito empresarial', 'direito societário',
      'contratos', 'lgpd', 'due diligence jurídico'
    ]
    const foundTechSkills: string[] = []
    techSkills.forEach(skill => {
      const skillPattern = new RegExp(`\\b${skill.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
      if (skillPattern.test(lowerText)) {
        foundTechSkills.push(skill.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '))
      }
    })
    
    // Also detect when user explicitly lists skills with pattern "competências técnicas: X, Y, Z"
    const explicitSkillsPatterns = [
      /compet[êe]ncias?\s+t[ée]cnicas?\s*[:\-]\s*([^.]+)/i,
      /skills?\s+t[ée]cnic[oa]s?\s*[:\-]\s*([^.]+)/i,
      /requisitos?\s+t[ée]cnicos?\s*[:\-]\s*([^.]+)/i,
      /conhecimentos?\s*[:\-]\s*([^.]+)/i
    ]
    
    for (const pattern of explicitSkillsPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        const skillsList = match[1].split(/[,;e]/).map(s => s.trim()).filter(s => s.length > 1)
        skillsList.forEach(skill => {
          if (skill && skill.length > 1 && !['e', 'ou', 'com', 'de', 'para'].includes(skill.toLowerCase())) {
            foundTechSkills.push(skill.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' '))
          }
        })
      }
    }
    
    if (foundTechSkills.length > 0) {
      // Case-insensitive deduplication for technical skills
      const existingLower = new Set((newCriteria.competenciasTecnicas || []).map(s => s.toLowerCase()))
      const uniqueNewSkills = foundTechSkills.filter(s => !existingLower.has(s.toLowerCase()))
      newCriteria.competenciasTecnicas = [...(newCriteria.competenciasTecnicas || []), ...uniqueNewSkills]
    }

    const softSkills = [
      'liderança', 'lideranca', 'gestão de pessoas', 'gestao de pessoas', 'comunicação', 'comunicacao',
      'trabalho em equipe', 'proatividade', 'pro-atividade', 'organização', 'organizacao',
      'negociação', 'negociacao', 'resiliência', 'resiliencia', 'empatia', 'criatividade',
      'pensamento crítico', 'resolução de problemas', 'adaptabilidade', 'flexibilidade',
      'autonomia', 'iniciativa', 'colaboração', 'colaboracao', 'foco em resultados',
      'orientação para resultados', 'relacionamento interpessoal', 'inteligência emocional',
      'tomada de decisão', 'visão estratégica', 'visao estrategica', 'gestão de conflitos',
      'mentoria', 'coaching', 'feedback', 'influência', 'influencia', 'persuasão', 'persuasao'
    ]
    const foundSoftSkills: string[] = []
    softSkills.forEach(skill => {
      if (lowerText.includes(skill)) {
        foundSoftSkills.push(skill.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '))
      }
    })
    if (foundSoftSkills.length > 0) {
      // Case-insensitive deduplication for behavioral skills
      const existingLower = new Set((newCriteria.competenciasComportamentais || []).map(s => s.toLowerCase()))
      const uniqueNewComps = foundSoftSkills.filter(s => !existingLower.has(s.toLowerCase()))
      newCriteria.competenciasComportamentais = [...(newCriteria.competenciasComportamentais || []), ...uniqueNewComps]
      // Sincronizar com behavioralCompetencies para persistir no painel visual
      setBehavioralCompetencies(prev => {
        const existingNames = prev.map(c => c.name.toLowerCase())
        const newCompetencies = foundSoftSkills.filter(skill => !existingNames.includes(skill.toLowerCase()))
        if (newCompetencies.length === 0) return prev
        return [
          ...prev,
          ...newCompetencies.map((name, idx) => ({
            id: `detected-${Date.now()}-${idx}`,
            name,
            description: `Competência detectada: ${name}`,
            justification: `Detectada automaticamente no texto da vaga`,
            weight: 3,
            enabled: true,
            source: 'detected' as const
          }))
        ]
      })
    }

    // ========== IDIOMAS DETECTION ==========
    const idiomasPatterns = [
      // "inglês avançado", "inglês fluente", "inglês intermediário"
      /\b(ingl[eê]s|english)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
      /\b(espanhol|spanish)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
      /\b(franc[eê]s|french)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
      /\b(alem[aã]o|german)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
      /\b(italiano|italian)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
      /\b(portugu[eê]s|portuguese)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
      /\b(mandarim|chin[eê]s|chinese)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
      /\b(japon[eê]s|japanese)\s+(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)/gi,
      // Padrões inversos: "fluente em inglês", "avançado em espanhol"
      /\b(avan[çc]ado|fluente|intermedi[aá]rio|b[aá]sico|nativo)\s+(?:em\s+)?(ingl[eê]s|espanhol|franc[eê]s|alem[aã]o|italiano|mandarim|chin[eê]s|japon[eê]s)/gi,
      // Padrões com nível: "inglês nível avançado", "inglês C1", "inglês B2"
      /\b(ingl[eê]s|espanhol|franc[eê]s|alem[aã]o|italiano|mandarim|chin[eê]s|japon[eê]s)\s+(?:n[ií]vel\s+)?(C1|C2|B1|B2|A1|A2)/gi,
    ]
    
    const foundIdiomas: string[] = []
    const idiomasNormalize: Record<string, string> = {
      'ingles': 'Inglês', 'inglês': 'Inglês', 'english': 'Inglês',
      'espanhol': 'Espanhol', 'spanish': 'Espanhol',
      'frances': 'Francês', 'francês': 'Francês', 'french': 'Francês',
      'alemao': 'Alemão', 'alemão': 'Alemão', 'german': 'Alemão',
      'italiano': 'Italiano', 'italian': 'Italiano',
      'portugues': 'Português', 'português': 'Português', 'portuguese': 'Português',
      'mandarim': 'Mandarim', 'chines': 'Chinês', 'chinês': 'Chinês', 'chinese': 'Chinês',
      'japones': 'Japonês', 'japonês': 'Japonês', 'japanese': 'Japonês',
    }
    const nivelNormalize: Record<string, string> = {
      'avancado': 'Avançado', 'avançado': 'Avançado',
      'fluente': 'Fluente', 'nativo': 'Nativo',
      'intermediario': 'Intermediário', 'intermediário': 'Intermediário',
      'basico': 'Básico', 'básico': 'Básico',
      'c1': 'C1', 'c2': 'C2', 'b1': 'B1', 'b2': 'B2', 'a1': 'A1', 'a2': 'A2',
    }
    
    for (const pattern of idiomasPatterns) {
      const regex = new RegExp(pattern.source, pattern.flags)
      let match
      while ((match = regex.exec(text)) !== null) {
        const idioma = idiomasNormalize[match[1].toLowerCase()] || match[1]
        const nivel = nivelNormalize[match[2]?.toLowerCase()] || match[2] || ''
        const formatted = nivel ? `${idioma} ${nivel}` : idioma
        if (!foundIdiomas.some(i => i.toLowerCase() === formatted.toLowerCase())) {
          foundIdiomas.push(formatted)
        }
      }
    }
    
    if (foundIdiomas.length > 0) {
      newCriteria.idiomas = [...new Set([...newCriteria.idiomas, ...foundIdiomas])]
    }

    const seniorityMatch = text.match(/\b(júnior|junior|jr|pleno|pl|sênior|senior|sr|especialista|trainee|estagiário|estagiario|estágio|estagio)\b/i)
    if (seniorityMatch) {
      let seniority = seniorityMatch[1].toLowerCase()
      const seniorityMap: Record<string, string> = {
        'junior': 'Júnior', 'júnior': 'Júnior', 'jr': 'Júnior',
        'pleno': 'Pleno', 'pl': 'Pleno',
        'senior': 'Sênior', 'sênior': 'Sênior', 'sr': 'Sênior',
        'especialista': 'Especialista',
        'trainee': 'Trainee',
        'estagiário': 'Estagiário', 'estagiario': 'Estagiário', 'estágio': 'Estágio', 'estagio': 'Estágio'
      }
      newCriteria.senioridadeIdiomas = seniorityMap[seniority] || seniority.charAt(0).toUpperCase() + seniority.slice(1)
    }

    const modeloMatch = text.match(/\b(remoto|100%\s*remoto|totalmente\s*remoto|híbrido|hibrido|presencial|home\s*office|trabalho\s*remoto)\b/i)
    if (modeloMatch) {
      let modelo = modeloMatch[1].toLowerCase()
      if (modelo.includes('remoto') || modelo.includes('home')) {
        newCriteria.modeloTrabalho = 'Remoto'
      } else if (modelo.includes('híbrido') || modelo.includes('hibrido')) {
        newCriteria.modeloTrabalho = 'Híbrido'
      } else if (modelo.includes('presencial')) {
        newCriteria.modeloTrabalho = 'Presencial'
      }
    }

    const knownCities: Record<string, string> = {
      'são paulo': 'São Paulo, SP',
      'sao paulo': 'São Paulo, SP',
      'rio de janeiro': 'Rio de Janeiro, RJ',
      'belo horizonte': 'Belo Horizonte, MG',
      'curitiba': 'Curitiba, PR',
      'porto alegre': 'Porto Alegre, RS',
      'brasília': 'Brasília, DF',
      'brasilia': 'Brasília, DF',
      'salvador': 'Salvador, BA',
      'recife': 'Recife, PE',
      'fortaleza': 'Fortaleza, CE',
      'campinas': 'Campinas, SP',
      'florianópolis': 'Florianópolis, SC',
      'florianopolis': 'Florianópolis, SC',
      'goiânia': 'Goiânia, GO',
      'goiania': 'Goiânia, GO',
      'manaus': 'Manaus, AM',
      'belém': 'Belém, PA',
      'belem': 'Belém, PA',
      'vitória': 'Vitória, ES',
      'vitoria': 'Vitória, ES',
      'natal': 'Natal, RN',
      'joão pessoa': 'João Pessoa, PB',
      'joao pessoa': 'João Pessoa, PB',
      'maceió': 'Maceió, AL',
      'maceio': 'Maceió, AL',
      'cuiabá': 'Cuiabá, MT',
      'cuiaba': 'Cuiabá, MT',
      'campo grande': 'Campo Grande, MS',
      'teresina': 'Teresina, PI',
      'são luís': 'São Luís, MA',
      'sao luis': 'São Luís, MA',
      'aracaju': 'Aracaju, SE',
      'ribeirão preto': 'Ribeirão Preto, SP',
      'ribeirao preto': 'Ribeirão Preto, SP',
      'santos': 'Santos, SP',
      'sorocaba': 'Sorocaba, SP',
      'são josé dos campos': 'São José dos Campos, SP',
      'sao jose dos campos': 'São José dos Campos, SP',
      'londrina': 'Londrina, PR',
      'joinville': 'Joinville, SC',
      'blumenau': 'Blumenau, SC',
      'uberlândia': 'Uberlândia, MG',
      'uberlandia': 'Uberlândia, MG'
    }
    
    const stateAbbrev: Record<string, string> = {
      'sp': 'São Paulo, SP', 'rj': 'Rio de Janeiro, RJ', 'mg': 'Belo Horizonte, MG',
      'pr': 'Curitiba, PR', 'rs': 'Porto Alegre, RS', 'df': 'Brasília, DF',
      'ba': 'Salvador, BA', 'pe': 'Recife, PE', 'ce': 'Fortaleza, CE',
      'sc': 'Florianópolis, SC', 'go': 'Goiânia, GO', 'am': 'Manaus, AM',
      'pa': 'Belém, PA', 'es': 'Vitória, ES', 'rn': 'Natal, RN'
    }
    
    for (const [cityKey, cityFormatted] of Object.entries(knownCities)) {
      const cityPattern = new RegExp(`\\b${cityKey.replace(/\s+/g, '\\s+')}\\b`, 'i')
      if (cityPattern.test(lowerText)) {
        newCriteria.localizacao = cityFormatted
        break
      }
    }
    
    if (!newCriteria.localizacao) {
      const locationPatterns = [
        /(?:base\s+(?:em|no|na)\s+)([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,\-]\s*([A-Z]{2}))?(?:\s*[,.;]|\s+(?:modelo|remoto|híbrido|presencial)|$)/i,
        /(?:localização|localizacao|cidade|local)\s*[:\-]?\s*([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,\-]\s*([A-Z]{2}))?(?:\s*[,.;]|$)/i,
        /\b([A-Z][a-záàâãéèêíïóôõöúç]+(?:\s+[A-Z]?[a-záàâãéèêíïóôõöúç]+)*)\s*[,\-]\s*([A-Z]{2})\b/
      ]
      
      for (const pattern of locationPatterns) {
        const match = text.match(pattern)
        if (match && match[1]) {
          let location = match[1].trim()
          const state = match[2]?.toUpperCase()
          
          const commonWords = ['empresa', 'vaga', 'equipe', 'time', 'área', 'area', 'modelo', 'trabalho', 'contrato', 'salário', 'salario']
          if (commonWords.some(w => location.toLowerCase().includes(w))) continue
          
          if (stateAbbrev[location.toLowerCase()]) {
            location = stateAbbrev[location.toLowerCase()]
          } else {
            location = location.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ')
            if (state) {
              location = `${location}, ${state}`
            }
          }
          
          if (location.length > 2 && location.length < 50) {
            newCriteria.localizacao = location
            break
          }
        }
      }
    }

    const contratoMatch = text.match(/\b(clt|pj|pessoa\s*jurídica|pessoa\s*juridica|terceirizado|freelancer|temporário|temporario|efetivo|contrato\s*fixo|contratação\s*clt|contratacao\s*clt)\b/i)
    if (contratoMatch) {
      let contrato = contratoMatch[1].toLowerCase()
      if (contrato.includes('clt') || contrato.includes('efetivo')) {
        newCriteria.tipoContrato = 'CLT'
      } else if (contrato.includes('pj') || contrato.includes('jurídica') || contrato.includes('juridica')) {
        newCriteria.tipoContrato = 'PJ'
      } else if (contrato.includes('temporário') || contrato.includes('temporario')) {
        newCriteria.tipoContrato = 'Temporário'
      } else if (contrato.includes('freelancer')) {
        newCriteria.tipoContrato = 'Freelancer'
      } else if (contrato.includes('terceirizado')) {
        newCriteria.tipoContrato = 'Terceirizado'
      }
    }

    // ========== RESPONSABILIDADES DETECTION ==========
    const responsibilityPatterns = [
      // "vai ser responsável por gestão de times, consolidações, reports"
      /(?:vai\s+ser|será|serás?|sendo|é|era|foi)\s+respons[áa]vel\s+por\s+([^.!?]+)/i,
      // "responsável por: X, Y, Z"
      /respons[áa]vel\s+por\s*[:\-]?\s*([^.!?]+)/i,
      // "responsabilidade como X, Y, Z" ou "responsabilidades como X, Y, Z"
      /responsabilidades?\s+como\s+([^.!?]+)/i,
      // "responsabilidades: X, Y, Z"
      /responsabilidades?\s*[:\-]\s*([^.!?]+)/i,
      // "principais atribuições: X, Y, Z"
      /(?:principais\s+)?atribui[çc][õo]es?\s*[:\-]\s*([^.!?]+)/i,
      // "atividades: X, Y, Z"
      /atividades?\s*[:\-]\s*([^.!?]+)/i,
      // "vai liderar projetos de X, desenvolver Y, mentorar Z"
      /vai\s+(liderar|gerenciar|coordenar|supervisionar|desenvolver|implementar|criar|construir|mentorar|treinar)\s+([^.!?]+)/i,
      // "irá liderar pessoas, gerir a área"
      /ir[áa]\s+(liderar|gerenciar|coordenar|supervisionar|desenvolver|implementar|criar|construir|mentorar|treinar|gerir)\s+([^.!?]+)/i,
      // "além de gestão de equipe"
      /al[ée]m\s+(?:de|da|do|das|dos)\s+([^.!?,]+)/i,
    ]
    
    const foundResponsibilities: string[] = []
    for (const pattern of responsibilityPatterns) {
      const match = text.match(pattern)
      if (match) {
        const matchedText = match[1] || match[2] || ''
        // Split by comma, "e", or semicolon
        const items = matchedText.split(/[,;]|\s+e\s+/).map(s => s.trim()).filter(s => {
          // Filter out empty, too short, or common words
          if (s.length < 3) return false
          const stopWords = ['o', 'a', 'os', 'as', 'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'para', 'com', 'por']
          return !stopWords.includes(s.toLowerCase())
        })
        items.forEach(item => {
          if (item.length > 3 && item.length < 100) {
            // Capitalize first letter
            const formatted = item.charAt(0).toUpperCase() + item.slice(1).toLowerCase()
            if (!foundResponsibilities.includes(formatted)) {
              foundResponsibilities.push(formatted)
            }
          }
        })
      }
    }
    if (foundResponsibilities.length > 0) {
      const existingNotPartial = newCriteria.responsabilidades.filter(existing => {
        return !foundResponsibilities.some(newResp => 
          newResp.toLowerCase().startsWith(existing.toLowerCase()) ||
          existing.toLowerCase().startsWith(newResp.toLowerCase())
        )
      })
      newCriteria.responsabilidades = [...new Set([...existingNotPartial, ...foundResponsibilities])]
    }

    const parseSalaryValue = (value: string): number | null => {
      if (!value) return null
      let cleaned = value.toLowerCase().trim()
      
      let multiplier = 1
      if (cleaned.includes('k')) {
        multiplier = 1000
        cleaned = cleaned.replace(/k/gi, '')
      } else if (cleaned.includes('mil')) {
        multiplier = 1000
        cleaned = cleaned.replace(/mil/gi, '')
      }
      
      cleaned = cleaned.replace(/[^\d.,]/g, '')
      cleaned = cleaned.replace(/\./g, '').replace(',', '.')
      
      const num = parseFloat(cleaned)
      if (isNaN(num)) return null
      
      return Math.round(num * multiplier)
    }
    
    const salarioPatterns = [
      // "salário entre 20 e 25 mil reais" - PRIORITY PATTERN
      /sal[áa]rio\s+entre\s+([\d.,]+)\s*(?:mil)?\s*(?:reais?)?\s*(?:e|a|até|-)\s*([\d.,]+)\s*(?:mil|k)?\s*(?:reais?)?/i,
      // "entre 20 e 25 mil" without "salário" prefix
      /entre\s+([\d.,]+)\s*(?:mil)?\s*(?:reais?)?\s*(?:e|a|até|-)\s*([\d.,]+)\s*(?:mil|k)\s*(?:reais?)?/i,
      // "de 20 a 25 mil reais"
      /(?:de\s+)?([\d.,]+)\s*(?:a|até|-)\s*([\d.,]+)\s*(?:mil|k)\s*(?:reais?)?/i,
      // Standard patterns with R$
      /sal[áa]rio\s*(?:de)?\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)\s*(?:a|até|-)\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)/i,
      /(?:r\$)\s*([\d.,]+\s*(?:k|mil)?)\s*(?:a|até|-)\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)/i,
      /faixa\s*(?:salarial)?\s*(?:de)?\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)\s*(?:a|até|-)\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)/i,
      /remunera[çc][ãa]o\s*(?:de)?\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)\s*(?:a|até|-)\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)/i,
      /([\d]{1,3}(?:[.,][\d]{3})*)\s*(?:a|até|-)\s*([\d]{1,3}(?:[.,][\d]{3})*)/i,
      /sal[áa]rio\s*(?:de)?\s*(?:r\$)?\s*([\d.,]+\s*(?:k|mil)?)/i,
      /(?:r\$)\s*([\d.,]+\s*(?:k|mil)?)/i
    ]
    
    for (const pattern of salarioPatterns) {
      const match = text.match(pattern)
      if (match) {
        let minValue = parseSalaryValue(match[1])
        let maxValue = match[2] ? parseSalaryValue(match[2]) : null
        
        // Handle case like "entre 20 e 25 mil" where only max has "mil"
        // If minValue is small (< 100) and maxValue is large (> 10000), apply multiplier to min
        if (minValue && maxValue && minValue < 100 && maxValue >= 1000) {
          minValue = minValue * 1000
        }
        // Handle case where both values are small but text contains "mil"
        if (minValue && minValue < 100 && (lowerText.includes('mil') || lowerText.includes('k '))) {
          minValue = minValue * 1000
        }
        if (maxValue && maxValue < 100 && (lowerText.includes('mil') || lowerText.includes('k '))) {
          maxValue = maxValue * 1000
        }
        
        if (minValue && minValue >= 1000) {
          if (maxValue && maxValue >= minValue) {
            newCriteria.salario = `R$ ${minValue.toLocaleString('pt-BR')} - R$ ${maxValue.toLocaleString('pt-BR')}`
            setSalaryInfo(prev => ({
              ...prev,
              minSalary: minValue!.toString(),
              maxSalary: maxValue!.toString()
            }))
          } else {
            newCriteria.salario = `R$ ${minValue.toLocaleString('pt-BR')}`
            setSalaryInfo(prev => ({
              ...prev,
              minSalary: minValue!.toString()
            }))
          }
          break
        }
      }
    }

    // ========== VAGA AFIRMATIVA DETECTION ==========
    const affirmativePatterns = [
      // "não é afirmativa", "não é vaga afirmativa", "vaga não afirmativa"
      /(?:n[aã]o\s+[eé]\s+(?:uma?\s+)?(?:vaga\s+)?afirmativa|vaga\s+n[aã]o\s+afirmativa|n[aã]o\s+afirmativa)/i,
      // "é vaga afirmativa", "é afirmativa", "vaga afirmativa"
      /(?:[eé]\s+(?:uma?\s+)?(?:vaga\s+)?afirmativa|vaga\s+afirmativa|exclusiva\s+para)/i,
    ]
    
    // Check for negative pattern first (more specific)
    const negativeAffirmativeMatch = text.match(affirmativePatterns[0])
    if (negativeAffirmativeMatch) {
      newCriteria.isAffirmative = false
    } else {
      // Check for positive pattern
      const positiveAffirmativeMatch = text.match(affirmativePatterns[1])
      if (positiveAffirmativeMatch) {
        newCriteria.isAffirmative = true
      }
    }

    // ========== CRITÉRIOS AFIRMATIVOS ESPECÍFICOS ==========
    const affirmativeCriteriaPatterns = [
      /(?:exclusiv[oa]\s+para|voltad[oa]\s+para|destinad[oa]\s+(?:a|para))\s+(mulheres?|pcd|pessoas?\s+com\s+defici[êe]ncia|negr[oa]s?|lgbtq?\+?|50\+|idosos?|trans)/gi,
      /(?:vaga\s+)?(?:afirmativa|exclusiva)\s+(?:para\s+)?(mulheres?|pcd|pessoas?\s+com\s+defici[êe]ncia|negr[oa]s?|lgbtq?\+?|50\+|idosos?|trans)/gi,
    ]
    for (const pattern of affirmativeCriteriaPatterns) {
      const matches = text.matchAll(pattern)
      for (const match of matches) {
        if (match[1]) {
          const criterio = match[1].toLowerCase()
          if (criterio.includes('mulher')) {
            newCriteria.affirmativeCriteriaPrimary = newCriteria.affirmativeCriteriaPrimary || 'Mulheres'
          } else if (criterio.includes('pcd') || criterio.includes('defici')) {
            if (!newCriteria.affirmativeCriteriaPrimary) newCriteria.affirmativeCriteriaPrimary = 'PCD'
            else newCriteria.affirmativeCriteriaSecondary = 'PCD'
          } else if (criterio.includes('negr')) {
            if (!newCriteria.affirmativeCriteriaPrimary) newCriteria.affirmativeCriteriaPrimary = 'Pessoas Negras'
            else newCriteria.affirmativeCriteriaSecondary = 'Pessoas Negras'
          } else if (criterio.includes('lgbtq') || criterio.includes('trans')) {
            if (!newCriteria.affirmativeCriteriaPrimary) newCriteria.affirmativeCriteriaPrimary = 'LGBTQ+'
            else newCriteria.affirmativeCriteriaSecondary = 'LGBTQ+'
          } else if (criterio.includes('50') || criterio.includes('idoso')) {
            if (!newCriteria.affirmativeCriteriaPrimary) newCriteria.affirmativeCriteriaPrimary = '50+'
            else newCriteria.affirmativeCriteriaSecondary = '50+'
          }
          newCriteria.isAffirmative = true
        }
      }
    }

    // ========== EXPERIÊNCIA MÍNIMA ==========
    const experienciaPatterns = [
      /(\d+)\s*(?:\+\s*)?anos?\s+(?:de\s+)?experi[êe]ncia/i,
      /experi[êe]ncia\s+(?:m[íi]nima\s+)?(?:de\s+)?(\d+)\s*(?:\+\s*)?anos?/i,
      /m[íi]nimo\s+(?:de\s+)?(\d+)\s*(?:\+\s*)?anos?\s+(?:de\s+)?experi[êe]ncia/i,
      /(?:pelo\s+menos|no\s+m[íi]nimo)\s+(\d+)\s*anos?\s+(?:de\s+)?experi[êe]ncia/i,
    ]
    for (const pattern of experienciaPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        newCriteria.experienciaMinima = `${match[1]} anos`
        break
      }
    }

    // ========== FORMAÇÃO ACADÊMICA ==========
    const formacaoPatterns = [
      /(?:gradua[çc][ãa]o|graduado|bacharelado|bacharel|licenciatura|tecnólogo|tecnologo)\s+em\s+([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,.\-;]|\s+(?:ou|e|com|$))/gi,
      /(?:forma[çc][ãa]o)\s+em\s+([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,.\-;]|\s+(?:ou|e|com|$))/gi,
      /(?:p[óo]s[- ]?gradua[çc][ãa]o|mba|mestrado|doutorado|especializa[çc][ãa]o)\s+em\s+([a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,.\-;]|\s+(?:ou|e|com|$))/gi,
      /\b(ensino\s+(?:superior|m[ée]dio|t[ée]cnico)(?:\s+completo)?)\b/gi,
      /\b(curso\s+(?:superior|t[ée]cnico)\s+em\s+[a-záàâãéèêíïóôõöúç\s]+?)(?:\s*[,.\-;]|$)/gi,
    ]
    const invalidFormacaoTerms = ['nivel', 'nível', 'senior', 'sênior', 'pleno', 'junior', 'júnior', 'de', 'da', 'do']
    const foundFormacao: string[] = []
    for (const pattern of formacaoPatterns) {
      const regex = new RegExp(pattern.source, pattern.flags)
      let match
      while ((match = regex.exec(text)) !== null) {
        const formacao = (match[1] || match[0]).trim()
        const firstWord = formacao.split(' ')[0].toLowerCase()
        if (formacao.length > 3 && formacao.length < 60 && !invalidFormacaoTerms.includes(firstWord)) {
          foundFormacao.push(formacao.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' '))
        }
      }
    }
    if (foundFormacao.length > 0) {
      newCriteria.formacao = [...new Set([...newCriteria.formacao, ...foundFormacao])]
    }

    // ========== CERTIFICAÇÕES ==========
    const certificacoesPatterns = [
      /certifica[çc][ãa]o\s+(?:em\s+)?([a-záàâãéèêíïóôõöúç\s\-]+?)(?:\s*[,.\-;]|\s+(?:ou|e|$))/gi,
      /certificado\s+(?:em\s+|de\s+)?([a-záàâãéèêíïóôõöúç\s\-]+?)(?:\s*[,.\-;]|\s+(?:ou|e|$))/gi,
    ]
    const knownCertifications = [
      'aws', 'azure', 'gcp', 'google cloud', 'pmp', 'scrum master', 'csm', 'psm', 'safe', 'itil',
      'cissp', 'cisa', 'ceh', 'comptia', 'ccna', 'ccnp', 'oracle', 'java certified', 'microsoft certified',
      'cpa', 'cpa-10', 'cpa-20', 'cga', 'crc', 'oab', 'cfc', 'crea', 'cfp', 'cea', 'cnpi',
      'iso 9001', 'iso 27001', 'six sigma', 'lean', 'green belt', 'black belt', 'yellow belt',
      'tableau certified', 'salesforce certified', 'hubspot', 'google analytics', 'meta blueprint',
    ]
    const foundCertificacoes: string[] = []
    // Check for known certifications
    knownCertifications.forEach(cert => {
      const certPattern = new RegExp(`\\b${cert.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
      if (certPattern.test(lowerText)) {
        foundCertificacoes.push(cert.toUpperCase())
      }
    })
    // Check for patterns
    for (const pattern of certificacoesPatterns) {
      const regex = new RegExp(pattern.source, pattern.flags)
      let match
      while ((match = regex.exec(text)) !== null) {
        if (match[1] && match[1].length > 2 && match[1].length < 40) {
          foundCertificacoes.push(match[1].trim())
        }
      }
    }
    if (foundCertificacoes.length > 0) {
      newCriteria.certificacoes = [...new Set([...newCriteria.certificacoes, ...foundCertificacoes])]
    }

    // ========== FERRAMENTAS ESPECÍFICAS ==========
    const knownTools = [
      'jira', 'confluence', 'trello', 'asana', 'monday', 'notion', 'slack', 'microsoft teams', 'zoom',
      'figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator', 'indesign', 'premiere', 'after effects',
      'sap', 'oracle', 'totvs', 'protheus', 'senior sistemas', 'sankhya', 'omie', 'conta azul', 'bling',
      'salesforce', 'hubspot', 'pipedrive', 'rd station', 'mailchimp', 'active campaign',
      'google analytics', 'google ads', 'facebook ads', 'meta ads', 'tiktok ads', 'linkedin ads',
      'excel', 'google sheets', 'power bi', 'tableau', 'looker', 'metabase', 'qlik',
      'git', 'github', 'gitlab', 'bitbucket', 'jenkins', 'circleci', 'travis',
      'vs code', 'visual studio', 'intellij', 'eclipse', 'pycharm', 'webstorm',
      'postman', 'insomnia', 'swagger', 'docker desktop', 'kubernetes dashboard',
    ]
    const foundFerramentas: string[] = []
    knownTools.forEach(tool => {
      const toolPattern = new RegExp(`\\b${tool.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'i')
      if (toolPattern.test(lowerText)) {
        foundFerramentas.push(tool.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '))
      }
    })
    if (foundFerramentas.length > 0) {
      newCriteria.ferramentas = [...new Set([...newCriteria.ferramentas, ...foundFerramentas])]
    }

    // ========== DIAS PRESENCIAIS (HÍBRIDO) ==========
    if (newCriteria.modeloTrabalho === 'Híbrido') {
      const diasPatterns = [
        /(\d+)\s*(?:dias?\s+)?(?:por\s+semana\s+)?(?:no\s+)?(?:escrit[óo]rio|presencial)/i,
        /(\d+)x\s*(?:por\s+)?semana\s*(?:no\s+)?(?:escrit[óo]rio|presencial)?/i,
        /presencial\s+(\d+)\s*(?:dias?\s+)?(?:por\s+)?semana/i,
        /(\d+)\s*dias?\s+presenciais?/i,
      ]
      for (const pattern of diasPatterns) {
        const match = text.match(pattern)
        if (match && match[1]) {
          const dias = parseInt(match[1])
          if (dias >= 1 && dias <= 5) {
            newCriteria.diasPresenciais = dias
            break
          }
        }
      }
    }

    // ========== BENEFÍCIOS MENCIONADOS ==========
    const beneficiosKeywords = [
      { pattern: /\b(vale\s+refei[çc][ãa]o)\b/i, name: 'Vale Refeição' },
      { pattern: /\b(vale\s+alimenta[çc][ãa]o)\b/i, name: 'Vale Alimentação' },
      { pattern: /\b(vale\s+transporte)\b/i, name: 'Vale Transporte' },
      { pattern: /\b(plano\s+(?:de\s+)?sa[úu]de)\b/i, name: 'Plano de Saúde' },
      { pattern: /\b(plano\s+odontol[óo]gico)\b/i, name: 'Plano Odontológico' },
      { pattern: /\b(seguro\s+(?:de\s+)?vida)\b/i, name: 'Seguro de Vida' },
      { pattern: /\b(gympass|totalpass|wellhub)\b/i, name: 'Gympass/TotalPass' },
      { pattern: /\b(aux[íi]lio\s+home\s*office|aux[íi]lio\s+trabalho\s+remoto)\b/i, name: 'Auxílio Home Office' },
      { pattern: /\b(aux[íi]lio\s+(?:educa[çc][ãa]o|estudos?))\b/i, name: 'Auxílio Educação' },
      { pattern: /\b(aux[íi]lio\s+creche)\b/i, name: 'Auxílio Creche' },
      { pattern: /\b(day\s*off\s*(?:de\s+)?anivers[áa]rio)\b/i, name: 'Day Off Aniversário' },
      { pattern: /\b(stock\s*options?|a[çc][õo]es\s+(?:da\s+)?empresa)\b/i, name: 'Stock Options' },
      { pattern: /\b(participa[çc][ãa]o\s+nos?\s+lucros?|plr)\b/i, name: 'PLR' },
      { pattern: /\b(previdencia\s+privada)\b/i, name: 'Previdência Privada' },
      { pattern: /\b(licen[çc]a\s+maternidade\s+estendida)\b/i, name: 'Licença Maternidade Estendida' },
      { pattern: /\b(licen[çc]a\s+paternidade\s+estendida)\b/i, name: 'Licença Paternidade Estendida' },
    ]
    const foundBeneficios: string[] = []
    beneficiosKeywords.forEach(({ pattern, name }) => {
      if (pattern.test(text)) {
        foundBeneficios.push(name)
      }
    })
    if (foundBeneficios.length > 0) {
      newCriteria.beneficiosMencionados = [...new Set([...newCriteria.beneficiosMencionados, ...foundBeneficios])]
    }

    // ========== BÔNUS ==========
    const bonusPatterns = [
      /b[ôo]nus\s+(?:de\s+)?(?:at[ée]\s+)?(\d+)\s*(?:sal[áa]rios?)?/i,
      /b[ôo]nus\s+(?:de\s+)?(?:r\$\s*)?([\d.,]+\s*(?:k|mil)?)/i,
      /plr\s+(?:de\s+)?(?:at[ée]\s+)?(\d+)\s*sal[áa]rios?/i,
      /(\d+)\s*sal[áa]rios?\s+(?:de\s+)?b[ôo]nus/i,
    ]
    for (const pattern of bonusPatterns) {
      const match = text.match(pattern)
      if (match && match[1]) {
        newCriteria.bonus = match[0].trim()
        break
      }
    }

    // ========== VIAGENS FREQUENTES ==========
    const viagensPatterns = [
      /viagens?\s+frequentes?/i,
      /disponibilidade\s+para\s+viag(?:ar|ens?)/i,
      /(?:requer|exige|necessita)\s+viagens?/i,
      /viagens?\s+(?:a\s+)?(?:trabalho|nacionais?|internacionais?)/i,
    ]
    for (const pattern of viagensPatterns) {
      if (pattern.test(text)) {
        newCriteria.viagensFrequentes = true
        break
      }
    }

    // ========== DISPONIBILIDADE/INÍCIO ==========
    const disponibilidadePatterns = [
      /in[íi]cio\s+imediato/i,
      /dispon[íi]vel\s+(?:para\s+)?(?:come[çc]ar\s+)?imediatamente/i,
      /come[çc]ar\s+(?:em\s+)?(?:at[ée]\s+)?(\d+)\s*dias?/i,
      /in[íi]cio\s+(?:em\s+|para\s+)?([a-záàâãéèêíïóôõöúç]+(?:\s+de\s+\d{4})?)/i,
      /a\s+partir\s+de\s+([a-záàâãéèêíïóôõöúç]+)/i,
    ]
    for (const pattern of disponibilidadePatterns) {
      const match = text.match(pattern)
      if (match) {
        if (match[0].toLowerCase().includes('imediato') || match[0].toLowerCase().includes('imediatamente')) {
          newCriteria.disponibilidade = 'Imediato'
        } else if (match[1]) {
          newCriteria.disponibilidade = match[1].charAt(0).toUpperCase() + match[1].slice(1)
        }
        break
      }
    }

    // ========== CNH ==========
    const cnhPatterns = [
      /cnh\s*(?:categoria\s+)?([A-E](?:\s*[,\/e]\s*[A-E])*)/i,
      /habilita[çc][ãa]o\s*(?:categoria\s+)?([A-E](?:\s*[,\/e]\s*[A-E])*)/i,
      /carteira\s+(?:de\s+)?habilita[çc][ãa]o\s*(?:categoria\s+)?([A-E](?:\s*[,\/e]\s*[A-E])*)?/i,
      /\bcnh\s+([A-E])\b/i,
      /\bcnh\b/i,
    ]
    for (const pattern of cnhPatterns) {
      const match = text.match(pattern)
      if (match) {
        if (match[1]) {
          newCriteria.cnh = `CNH ${match[1].toUpperCase()}`
        } else {
          newCriteria.cnh = 'CNH (categoria não especificada)'
        }
        break
      }
    }

    // ========== HORÁRIO DE TRABALHO ==========
    const horarioPatterns = [
      /hor[áa]rio\s+flex[íi]vel/i,
      /jornada\s+flex[íi]vel/i,
      /turno\s+(noturno|diurno|matutino|vespertino)/i,
      /(\d{1,2})[h:]\s*(?:[àa]s?\s*)?(\d{1,2})h?/i,
      /das\s+(\d{1,2})h?\s+[àa]s?\s+(\d{1,2})h?/i,
      /hor[áa]rio\s+comercial/i,
    ]
    for (const pattern of horarioPatterns) {
      const match = text.match(pattern)
      if (match) {
        if (match[0].toLowerCase().includes('flex')) {
          newCriteria.horario = 'Flexível'
        } else if (match[0].toLowerCase().includes('comercial')) {
          newCriteria.horario = 'Comercial'
        } else if (match[1] && match[2]) {
          newCriteria.horario = `${match[1]}h às ${match[2]}h`
        } else if (match[1]) {
          newCriteria.horario = `Turno ${match[1].charAt(0).toUpperCase() + match[1].slice(1)}`
        }
        break
      }
    }

    setDetectedCriteria(newCriteria)
    return newCriteria
  }

  // State for validation error display
  const [validationError, setValidationError] = useState<string | null>(null)

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

  const {
    generateCriteriaResponse,
    generateParecerData,
    generateCompetencyAnalysisMessage,
    generateWSIExplanationMessage,
    handleAcceptSuggestions,
    handleSkipSuggestions,
    handleClearDraftAndReset,
    handlePublishJob,
    buildCandidateSearchQuery,
    generateJobDescription,
    startLocalSearch,
    startGlobalSearch,
  } = useWizardPublishHandlers({
    detectedCriteria,
    setDetectedCriteria,
    basicInfoFields,
    setBasicInfoFields,
    technicalSkills,
    setTechnicalSkills,
    behavioralCompetencies,
    setBehavioralCompetencies,
    salaryInfo,
    setSalaryInfo,
    messages,
    setMessages,
    currentStage,
    setCurrentStage,
    publishingPlatforms,
    jobConfig,
    setJobDescription,
    setIsGeneratingDescription,
    setPublishedJobId,
    setAwaitingCalibrationChoice,
    setSearchPhase,
    setLocalCandidateCount,
    setGlobalCandidateCount,
    preferredCandidateCount,
    selectedSuggestedTechnical,
    selectedSuggestedBehavioral,
    setShowCompetenciesSuggestionsModal,
    clearWizardDraft,
    setHasAppliedRestoredDraft,
    setShowClearDraftConfirm,
    setWsiCandidates,
    setGeneratedJobDescription,
    companyConfig,
    interviewStages,
    companyMembersMap,
    companyDefaultQuestions,
    wsiCandidates,
    user,
    wizardFastTrackSourceJobId,
    setWizardFastTrackSourceJobId,
    conversationId,
    learning,
    setIsLoading,
    proceedToNextStage,
  })

  // Stage validation function
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

  // Navigation functions for wizard
  const goToNextStage = () => {
    // Validate current stage before proceeding
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

      // Show loading state during transition
      setStageTransition('loading')

      // Intercept transition from salary to competencies to show LIA analysis
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
        }).catch((error) => {
          setMessages(prev => prev.filter(m => m.id !== thinkingMessage.id))
          setStageTransition('idle')
          proceedToNextStage()
        })
        return
      }

      // Intercept transition from competencies to wsi-questions to show LIA message
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

      // Default: proceed directly
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

  const addNewSkill = (name: string) => {
    if (!name.trim()) return
    const newSkill: TechnicalSkill = {
      id: `skill-${Date.now()}`,
      name: name.trim(),
      level: 'Intermediário',
      required: false,
      category: newSkillCategory,
      weight: 2
    }
    setTechnicalSkills(prev => [...prev, newSkill])
    setShowAddSkillModal(false)
    setNewSkillName('')
  }

  const addNewBenefit = () => {
    if (!newBenefitName.trim()) return
    const newBenefit: Benefit = {
      id: `benefit-${Date.now()}`,
      name: newBenefitName.trim(),
      value: newBenefitValue.trim() || undefined,
      enabled: true
    }
    setSalaryInfo(prev => ({
      ...prev,
      benefits: [...prev.benefits, newBenefit]
    }))
    setShowAddBenefitModal(false)
    setNewBenefitName('')
    setNewBenefitValue('')
  }

  const addNewCompetency = () => {
    if (!newCompetencyName.trim()) return
    const newCompetency: BehavioralCompetency = {
      id: `comp-${Date.now()}`,
      name: newCompetencyName.trim(),
      weight: 3,
      justification: newCompetencyJustification.trim() || 'Competência adicionada pelo recrutador',
      enabled: true
    }
    setBehavioralCompetencies(prev => [...prev, newCompetency])
    setShowAddCompetencyModal(false)
    setNewCompetencyName('')
    setNewCompetencyJustification('')
  }

  const {
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
  } = useWSIAndCalibrationHandlers({
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
    messages,
    setMessages,
    currentStage,
    setCurrentStage,
    wsiCandidates,
    setWsiCandidates,
    wsiGenerationBatch,
    setWsiGenerationBatch,
    isGeneratingWSI,
    setIsGeneratingWSI,
    wsiHasGenerated,
    setWsiHasGenerated,
    setWsiQuestions,
    customQuestionText,
    customQuestionType,
    customQuestionRequired,
    setShowCustomQuestionForm,
    setCustomQuestionText,
    setCustomQuestionType,
    setCustomQuestionRequired,
    calibrationCandidates,
    setCalibrationCandidates,
    currentCalibrationIndex,
    setCurrentCalibrationIndex,
    approvedCandidates,
    setApprovedCandidates,
    rejectedCandidates,
    setRejectedCandidates,
    calibrationComplete,
    setCalibrationComplete,
    isLoadingCalibration,
    setIsLoadingCalibration,
    showCalibrationModal,
    setShowCalibrationModal,
    calibrationSessionId,
    setCalibrationSessionId,
    calibrationComment,
    setCalibrationComment,
    publishedJobId,
    setPublishedJobId,
    calibrationCriteria,
    setCalibrationCriteria,
    postCalibrationComplete,
    setPostCalibrationComplete,
    hasAttemptedCalibrationGeneration,
    setHasAttemptedCalibrationGeneration,
    setSearchPhase,
    setLocalCandidateCount,
    setGlobalCandidateCount,
    preferredCandidateCount,
    awaitingCalibrationChoice,
    setAwaitingCalibrationChoice,
    fastTrackState,
    setFastTrackState,
    fastTrackSelectedVacancy,
    setFastTrackSelectedVacancy,
    fastTrackAdjustments,
    setFastTrackAdjustments,
    fastTrackSearchResults,
    setFastTrackSearchResults,
    isSearchingVacancies,
    setIsSearchingVacancies,
    wizardFastTrackSourceJobId,
    setWizardFastTrackSourceJobId,
    setWizardMode,
    isLoading,
    setIsLoading,
    setJobConfig,
    setEnrichedJDData,
    setIsLoadingEnrichment,
    setCompensationAnalysis,
    setDisplayedText,
    user,
    conversationMemory,
    highlightField,
    typeText,
    inputEvaluationStageCompletionShown,
    awaitingStageAdvanceConfirmation,
    setAwaitingStageAdvanceConfirmation,
    onJobCreated,
  })


  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadedFile(file)
      setShowUploadModal(true)
    }
  }

  const handleFileAnalysisComplete = (result: AnalysisResult, type: AnalysisType) => {
    setFileAnalysisResult(result)
    setFileAnalysisType(type)
    setShowUploadModal(false)
    
    let analysisMessage = ''
    if (type === 'resume') {
      const resumeResult = result as ResumeAnalysisResponse
      analysisMessage = `📄 **Análise de Currículo**\n\n**Candidato:** ${resumeResult.candidate_name || 'Não identificado'}\n**Qualidade do Layout:** ${resumeResult.layout_score}%\n\n${resumeResult.improvement_suggestions.length > 0 ? `**Sugestões de Melhoria:**\n${resumeResult.improvement_suggestions.map(s => `• ${s}`).join('\n')}` : '✅ Currículo bem estruturado!'}`
    } else if (type === 'image') {
      analysisMessage = `🖼️ **Análise de Imagem**\n\n${(result as any).analysis || 'Análise concluída.'}`
    } else {
      analysisMessage = `📑 **Análise de Documento**\n\n${(result as any).text_content?.substring(0, 500) || 'Documento analisado com sucesso.'}`
    }
    
    const analysisMsg: Message = {
      id: `analysis-${Date.now()}`,
      role: 'assistant',
      content: analysisMessage,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, analysisMsg])
    setUploadedFile(null)
  }

  const handleFileAnalysisError = (error: string) => {
    const errorMsg: Message = {
      id: `error-${Date.now()}`,
      role: 'assistant',
      content: `❌ **Erro ao analisar arquivo:** ${error}`,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, errorMsg])
    setUploadedFile(null)
    setShowUploadModal(false)
  }

  const handleVoiceResponse = (response: { text: string; audio?: string }) => {
    const voiceMsg: Message = {
      id: `voice-${Date.now()}`,
      role: 'assistant',
      content: response.text,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, voiceMsg])
  }

  const { handleSendMessage, handleKeyDown, handleQuickSuggestion } = useSendMessageHandlers({
    isOpen,
    onClose,
    isJobCreationMode,
    inline,
    onJobCreated,
    onOrchestratedMessage,
    onMessagesUpdate,
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
  })


  const getCriteriaStatus = (value: string | string[] | null) => {
    if (Array.isArray(value)) {
      return value.length > 0
    }
    return value !== null && value !== ''
  }

  const getUnifiedCargoLabel = () => {
    const cargo = detectedCriteria.cargo
    const seniority = detectedCriteria.senioridadeIdiomas
    if (cargo && seniority) {
      return `${cargo} ${seniority}`
    }
    return cargo || null
  }

  const detectedCriteriaItems = [
    { key: 'cargo', label: 'Cargo + Senioridade', value: getUnifiedCargoLabel() },
    { key: 'gestorArea', label: 'Gestor/Área', value: detectedCriteria.gestorArea },
    { key: 'responsabilidades', label: 'Principais responsabilidades', value: detectedCriteria.responsabilidades },
    { key: 'competenciasTecnicas', label: 'Competências técnicas (mín. 3)', value: detectedCriteria.competenciasTecnicas },
    { key: 'competenciasComportamentais', label: 'Comp. comportamentais (mín. 3)', value: detectedCriteria.competenciasComportamentais },
    { key: 'salario', label: 'Faixa salarial', value: detectedCriteria.salario },
    { key: 'isAffirmative', label: 'Vaga Afirmativa', value: detectedCriteria.isAffirmative !== null ? (detectedCriteria.isAffirmative ? 'Sim' : 'Não') : null },
  ]

  const companyDefaultsItems = [
    { key: 'modeloTrabalho', label: 'Modelo de trabalho', value: detectedCriteria.modeloTrabalho },
    { key: 'localizacao', label: 'Localização', value: detectedCriteria.localizacao },
    { key: 'tipoContrato', label: 'Tipo de contrato', value: detectedCriteria.tipoContrato },
  ]

  const criteriaItems = [...detectedCriteriaItems]

  if (!isOpen) return null

  const containerClasses = inline
    ? cn(
        "flex flex-col bg-white dark:bg-gray-800 overflow-hidden rounded-md border border-gray-200 dark:border-gray-700 transition-all duration-300 ease-in-out",
        isFullscreen 
          ? "fixed inset-4 z-50 animate-in zoom-in-95 duration-200" 
          : "h-full"
      )
    : cn(
        "fixed inset-0 z-50 bg-black/50 flex items-center justify-center",
        "animate-in fade-in-0 duration-200"
      )

  const contentClasses = inline
    ? "flex-1 flex flex-col bg-white min-h-0 h-full transition-all duration-300"
    : cn(
        "bg-white w-full rounded-md flex flex-col overflow-hidden border border-gray-900 dark:border-gray-50 transition-all duration-300 ease-in-out",
        "animate-in fade-in-0 zoom-in-95 duration-300",
        isFullscreen 
          ? "max-w-[98vw] h-[95vh]" 
          : "max-w-5xl h-[85vh]"
      )

  return (
    <div 
      className={containerClasses}
      onClick={(e) => {
        // Close modal when clicking backdrop (only for non-inline mode)
        if (!inline && e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      <div 
        className={contentClasses}
        role="dialog"
        aria-modal="true"
        aria-labelledby="wizard-title"
        aria-describedby="wizard-description"
      >
        {/* Hidden description for screen readers */}
        <span id="wizard-description" className="sr-only">
          {isJobCreationMode 
            ? 'Diálogo de criação de vaga com a assistente LIA. Use Tab para navegar, Enter para enviar mensagens, e Escape para fechar.'
            : 'Chat com a assistente LIA. Use Tab para navegar, Enter para enviar mensagens, e Escape para fechar.'
          }
        </span>
        <>
        {/* Header - Apenas botões de controle à direita */}
        {/* Header com botões de busca e fullscreen - sempre visível */}
        <div className="px-4 py-2 flex-shrink-0 bg-white">
            <div className="flex items-center justify-end">
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 text-gray-400 hover:text-gray-500 hover:bg-gray-100"
                  aria-label="Buscar"
                >
                  <Search className="w-3.5 h-3.5" />
                </Button>
                {inline ? (
                  <>
                    {onReturnToLateral && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => onReturnToLateral(messages.filter(m => m.role !== 'system').map(m => ({
                          id: m.id,
                          role: m.role as 'user' | 'assistant',
                          content: m.content,
                          timestamp: m.timestamp
                        })))}
                        className="h-6 w-6 text-gray-400 hover:text-gray-500 hover:bg-gray-100"
                        title="Voltar para prompt lateral"
                        aria-label="Voltar para prompt lateral"
                      >
                        <ChevronLeft className="w-3.5 h-3.5" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setIsFullscreen(!isFullscreen)}
                      className="h-6 w-6 text-gray-400 hover:text-gray-500 hover:bg-gray-100"
                      title={isFullscreen ? "Reduzir" : "Expandir tela cheia"}
                      aria-label={isFullscreen ? "Reduzir diálogo" : "Expandir para tela cheia"}
                    >
                      {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={onClose}
                      className="h-6 w-6 text-gray-400 hover:text-gray-500 hover:bg-gray-100"
                      title="Fechar"
                      aria-label="Fechar diálogo"
                    >
                      <X className="w-3.5 h-3.5" />
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setIsFullscreen(!isFullscreen)}
                      className="h-6 w-6 text-gray-400 hover:text-gray-500 hover:bg-gray-100"
                      title={isFullscreen ? "Reduzir" : "Expandir tela cheia"}
                      aria-label={isFullscreen ? "Reduzir diálogo" : "Expandir para tela cheia"}
                    >
                      {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                    </Button>
                    {onMinimize && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={onMinimize}
                        className="h-6 w-6 text-gray-400 hover:text-gray-500 hover:bg-gray-100"
                        aria-label="Minimizar diálogo"
                      >
                        <Minimize2 className="w-3.5 h-3.5" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={onClose}
                      className="h-6 w-6 text-gray-400 hover:text-gray-500 hover:bg-gray-100"
                      aria-label="Fechar diálogo"
                    >
                      <X className="w-3.5 h-3.5" />
                    </Button>
                  </>
                )}
              </div>
            </div>
          </div>

        {/* Main Content - Split for job-creation, Full for general */}
        <div className="flex-1 flex overflow-hidden bg-white min-h-0 h-full">
          {/* Chat Section */}
          <div className={cn(
            "flex flex-col transition-all duration-300 h-full min-h-0",
            isInJobCreationMode 
              ? "flex-1" 
              : "w-full"
          )}>
            {/* Messages Area - Scrollable, preenche o espaço disponível */}
            <div 
              className={cn(
                "flex-1 overflow-y-auto overflow-x-hidden px-4 min-h-0",
                isInJobCreationMode ? "pt-6 pb-3" : "py-3"
              )}
              role="region"
              aria-label="Conversa com a LIA"
              aria-live="polite"
            >
              <ChatMessageList
                messages={messages}
                isTypingEffect={isTypingEffect}
                displayedText={displayedText}
                conversationId={conversationId}
                inputRef={inputRef}
                isSearchingVacancies={isSearchingVacancies}
                onSetInputValue={setInputValue}
                onSetMessages={setMessages}
                onSetIsLoading={setIsLoading}
                onSetActiveToolConfirmationMessageId={setActiveToolConfirmationMessageId}
                onSetFastTrackState={setFastTrackState}
                onSetCompetencySuggestions={setCompetencySuggestions}
                onFastTrackVacancySelect={handleFastTrackVacancySelect}
                onProactiveAccept={handleProactiveAccept}
                onProactiveReject={handleProactiveReject}
                toolCalling={toolCalling}
              />

              {/* Typing Indicator */}
              {(isLoading || isTypingEffect) && (
                <div 
                  className="flex items-start gap-2.5 mt-3 animate-in fade-in-0 duration-300"
                  role="status"
                  aria-live="polite"
                  aria-label="LIA está digitando"
                >
                  <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
                  </div>
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-1.5 px-1">
                      <span className="text-xs font-bold text-gray-800" style={{ fontFamily: '"Inter", sans-serif' }}>LIA</span>
                    </div>
                    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-[14px] rounded-bl-[4px] p-3 inline-block">
                      <div className="flex items-center gap-1">
                        <span className="w-1.5 h-1.5 bg-chat-cyan rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-1.5 h-1.5 bg-chat-cyan rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-1.5 h-1.5 bg-chat-cyan rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area - Fixo na parte inferior, compacto (estilo Claude/ChatGPT) */}
            <ExpandedChatInput
              inputValue={inputValue}
              isLoading={isLoading}
              isTypingEffect={isTypingEffect}
              hideModeButtons={hideModeButtons}
              activeInputTab={activeInputTab}
              conversationId={conversationId}
              showMoreIdeas={showMoreIdeas}
              wizardGreeting={wizardGreeting}
              inputRef={inputRef}
              fileInputRef={fileInputRef}
              extractCriteriaDebounceRef={extractCriteriaDebounceRef}
              extractCriteriaFromText={extractCriteriaFromText}
              checkForExistingDraftSync={checkForExistingDraftSync}
              typeText={typeText}
              onInputValueChange={setInputValue}
              onKeyDown={handleKeyDown}
              onSendMessage={handleSendMessage}
              onFileSelect={handleFileSelect}
              onVoiceTranscription={(text) => setInputValue(prev => prev ? `${prev} ${text}` : text)}
              onVoiceResponse={handleVoiceResponse}
              onVoiceError={(error) => {
                const errorMsg: Message = {
                  id: `voice-error-${Date.now()}`,
                  role: 'assistant',
                  content: `⚠️ ${error}`,
                  timestamp: new Date()
                }
                setMessages(prev => [...prev, errorMsg])
              }}
              onSetActiveInputTab={setActiveInputTab}
              onSetMessages={setMessages}
              onSetInputValue={setInputValue}
              onSetShowMoreIdeas={setShowMoreIdeas}
              onSetDisplayedText={setDisplayedText}
              onSetInternalJobCreationMode={setInternalJobCreationMode}
              onSetPendingDraftData={setPendingDraftData as (data: any) => void}
              onSetAwaitingDraftChoice={setAwaitingDraftChoice}
              onSetDynamicInitialMessage={setDynamicInitialMessage}
            />
          </div>

          {/* Botão para reabrir painel de etapas (quando fechado) */}
          {isInJobCreationMode && !isPanelOpen && wizardMode === 'create_from_scratch' && (
            <div className="flex items-start pt-4 px-1 flex-shrink-0 ml-auto pr-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsPanelOpen(true)}
                className="h-7 px-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 gap-1"
                title="Mostrar painel de etapas"
                aria-label="Mostrar painel de etapas do wizard"
              >
                <FileText className="w-4 h-4" />
                <span className="text-xs font-medium">Mostrar etapas</span>
              </Button>
            </div>
          )}

          {/* Right: Dynamic Panel (changes based on wizard stage) */}
          {isInJobCreationMode && isPanelOpen && (
            <WizardRightPanel
              panelWidth={panelWidth}
              resizeRef={resizeRef}
              currentStage={currentStage}
              currentStageIndex={currentStageIndex}
              currentStageConfig={currentStageConfig}
              stageTransition={stageTransition}
              isFullscreen={isFullscreen}
              catalogStatus={wizardGreeting?.catalog_status}
              isAutoSaving={isAutoSaving}
              autoSaveLastSaved={autoSaveLastSaved}
              hasPendingChanges={hasPendingChanges}
              hasRestoredDraft={hasRestoredDraft}
              getLastSavedText={getLastSavedText}
              wsiQualityGates={wsiQualityGates}
              configLoaded={configLoaded}
              hasConfigData={!!hasConfigData}
              criteriaItems={criteriaItems}
              isHighlighted={isHighlighted}
              hasFastTrackSuggestions={fastTrack.hasSuggestions}
              fastTrackIsLoading={fastTrack.isLoading}
              fastTrackSuggestions={fastTrack.suggestions}
              fastTrackSelectedJob={fastTrack.selectedJob}
              fastTrackSuggestionsShownTracked={fastTrackSuggestionsShownTracked}
              onFastTrackSelectJob={(job) => fastTrack.selectJob(job)}
              onFastTrackDismiss={() => {
                if (fastTrackSuggestionsShownTracked) {
                  analytics.trackSuggestion('fast_track_rejected', false)
                }
                fastTrack.clearSuggestions()
                setAwaitingFastTrackSelection(false)
              }}
              enrichedJDData={enrichedJDData}
              isLoadingEnrichment={isLoadingEnrichment}
              detectedCriteria={detectedCriteria}
              onAcceptEnrichedSuggestion={(suggestionId) => {
                setEnrichedJDData(prev => {
                  if (!prev) return prev
                  return {
                    ...prev,
                    sections: prev.sections.map(section => ({
                      ...section,
                      suggestions: section.suggestions.map(s =>
                        s.id === suggestionId ? { ...s, accepted: true } : s
                      ),
                    })),
                  }
                })
              }}
              onRejectEnrichedSuggestion={(suggestionId) => {
                setEnrichedJDData(prev => {
                  if (!prev) return prev
                  return {
                    ...prev,
                    sections: prev.sections.map(section => ({
                      ...section,
                      suggestions: section.suggestions.filter(s => s.id !== suggestionId),
                    })),
                  }
                })
              }}
              onAcceptAllEnrichedSuggestions={() => {
                setEnrichedJDData(prev => {
                  if (!prev) return prev
                  return {
                    ...prev,
                    sections: prev.sections.map(section => ({
                      ...section,
                      suggestions: section.suggestions.map(s => ({ ...s, accepted: true })),
                    })),
                  }
                })
              }}
              technicalSkills={technicalSkills}
              behavioralCompetencies={behavioralCompetencies}
              highlightedFields={highlightedFields}
              basicInfoFields={basicInfoFields}
              companyConfig={companyConfig}
              inferSkillWeight={inferSkillWeight}
              competenciesPanelExpanded={competenciesPanelExpanded}
              isFieldRequiredForWizard={isFieldRequiredForWizard}
              onSetTechnicalSkills={(newSkills) => {
                const prevNames = new Set(technicalSkills.map(s => s.name))
                const newNames = new Set(newSkills.map(s => s.name))
                newSkills.forEach(skill => {
                  if (!prevNames.has(skill.name)) {
                    trackFieldChange({ field: 'technicalSkill', oldValue: null, newValue: skill, source: 'panel' })
                  }
                })
                technicalSkills.forEach(skill => {
                  if (!newNames.has(skill.name)) {
                    trackFieldChange({ field: 'technicalSkill', oldValue: skill, newValue: null, source: 'panel' })
                  }
                })
                setTechnicalSkills(newSkills)
              }}
              onSetBehavioralCompetencies={(newComps) => {
                const prevNames = new Set(behavioralCompetencies.filter(c => c.enabled).map(c => c.name))
                const newNames = new Set(newComps.filter(c => c.enabled).map(c => c.name))
                newComps.forEach(comp => {
                  if (comp.enabled && !prevNames.has(comp.name)) {
                    trackFieldChange({ field: 'behavioralCompetency', oldValue: null, newValue: comp, source: 'panel' })
                  }
                })
                behavioralCompetencies.forEach(comp => {
                  if (comp.enabled && !newNames.has(comp.name)) {
                    trackFieldChange({ field: 'behavioralCompetency', oldValue: comp, newValue: null, source: 'panel' })
                  }
                })
                setBehavioralCompetencies(newComps)
              }}
              onExpandEditCompetencies={() => setCompetenciesPanelExpanded(!competenciesPanelExpanded)}
              onShowAddSkillModal={(category) => { if (category !== 'general') setNewSkillCategory(category); setShowAddSkillModal(true) }}
              onShowAddCompetencyModal={() => setShowAddCompetencyModal(true)}
              onEditCompetency={setEditingCompetency}
              salaryInfo={salaryInfo}
              salaryBenchmark={salaryBenchmark as any}
              isLoadingBenchmark={isLoadingBenchmark}
              salaryPanelExpanded={salaryPanelExpanded}
              onSalaryChange={(info) => {
                Object.entries(info).forEach(([key, value]) => {
                  const oldValue = salaryInfo[key as keyof typeof salaryInfo]
                  if (oldValue !== value) {
                    trackFieldChange({ field: key, oldValue, newValue: value, source: 'panel' })
                  }
                })
                setSalaryInfo(prev => ({ ...prev, ...info }))
              }}
              onExpandEditSalary={() => setSalaryPanelExpanded(!salaryPanelExpanded)}
              onShowAddBenefitModal={() => setShowAddBenefitModal(true)}
              wsiCandidates={wsiCandidates}
              companyDefaultQuestions={companyDefaultQuestions as any}
              isGeneratingWSI={isGeneratingWSI}
              showCustomQuestionForm={showCustomQuestionForm}
              customQuestionText={customQuestionText}
              customQuestionType={customQuestionType}
              customQuestionRequired={customQuestionRequired}
              onSetCompanyDefaultQuestions={setCompanyDefaultQuestions as any}
              onToggleQuestionSelection={toggleWSIQuestionSelection}
              onDeleteQuestion={deleteWSIQuestion}
              onUpdateExpectedAnswer={updateWSIQuestionExpectedAnswer}
              onUpdateCorrectOption={updateWSIQuestionCorrectOption}
              onGenerateWSIQuestions={generateWSIQuestions}
              onSetShowCustomQuestionForm={setShowCustomQuestionForm}
              onSetCustomQuestionText={setCustomQuestionText}
              onSetCustomQuestionType={setCustomQuestionType}
              onSetCustomQuestionRequired={setCustomQuestionRequired}
              onAddCustomQuestion={addCustomQuestion}
              wsiQuestions={wsiQuestions}
              jobDescription={jobDescription}
              isGeneratingDescription={isGeneratingDescription}
              publishingPlatforms={publishingPlatforms}
              jobConfig={jobConfig}
              publishedJobId={publishedJobId}
              onGoToStage={setCurrentStage}
              onSetCompetenciesTab={setCompetenciesTab}
              onSetPublishingPlatforms={setPublishingPlatforms}
              onSetJobConfig={setJobConfig}
              onSetDetectedCriteria={setDetectedCriteria}
              onUpdateLanguages={updateLanguages}
              onGenerateJobDescription={generateJobDescription}
              searchPhase={searchPhase}
              calibrationCandidates={calibrationCandidates}
              calibrationComplete={calibrationComplete}
              isLoadingCalibration={isLoadingCalibration}
              hasAttemptedCalibrationGeneration={hasAttemptedCalibrationGeneration}
              approvedCandidates={approvedCandidates}
              showCalibrationModal={showCalibrationModal}
              localCandidateCount={localCandidateCount}
              globalCandidateCount={globalCandidateCount}
              globalSearchAuthorized={globalSearchAuthorized}
              preferredCandidateCount={preferredCandidateCount}
              onSetPreferredCandidateCount={setPreferredCandidateCount}
              onSetGlobalSearchAuthorized={setGlobalSearchAuthorized}
              onSetSearchPhase={setSearchPhase}
              onSetHasAttemptedCalibrationGeneration={setHasAttemptedCalibrationGeneration}
              onSetCalibrationComplete={setCalibrationComplete}
              onSetShowCalibrationModal={setShowCalibrationModal}
              onGenerateCalibrationCandidates={generateCalibrationCandidates}
              onStartGlobalSearch={startGlobalSearch}
              onJobCreated={onJobCreated}
              onClose={onClose}
              onResizeStart={() => setIsResizing(true)}
              onPanelClose={() => setIsPanelOpen(false)}
              onFullscreenChange={(fullscreen) => {
                setIsFullscreen(fullscreen)
                onFullscreenChange?.(fullscreen)
              }}
              onClearDraft={() => setShowClearDraftConfirm(true)}
              onGoToNextStage={goToNextStage}
              onGoToPreviousStage={goToPreviousStage}
              onPublishJob={handlePublishJob}
              canAdvanceToNextStage={canAdvanceToNextStage}
            />
          )}
        </div>
        </>
      </div>

      {/* Modal: Add Technical Skill */}
      <AddTechnicalSkillModal
        show={showAddSkillModal}
        skillCategory={newSkillCategory}
        skillName={newSkillName}
        onSkillNameChange={setNewSkillName}
        onAdd={addNewSkill}
        onCancel={() => { setShowAddSkillModal(false); setNewSkillName('') }}
      />

      {/* Modal: Add Behavioral Competency */}
      <AddCompetencyModal
        show={showAddCompetencyModal}
        companySuggestions={getBehavioralCompetencies()}
        competencyName={newCompetencyName}
        competencyJustification={newCompetencyJustification}
        onCompetencyNameChange={setNewCompetencyName}
        onCompetencyJustificationChange={setNewCompetencyJustification}
        onAdd={addNewCompetency}
        onCancel={() => { setShowAddCompetencyModal(false); setNewCompetencyName(''); setNewCompetencyJustification('') }}
      />

      {/* Modal: Add Benefit */}
      <AddBenefitModal
        show={showAddBenefitModal}
        benefitName={newBenefitName}
        benefitValue={newBenefitValue}
        onBenefitNameChange={setNewBenefitName}
        onBenefitValueChange={setNewBenefitValue}
        onAdd={addNewBenefit}
        onCancel={() => { setShowAddBenefitModal(false); setNewBenefitName(''); setNewBenefitValue('') }}
      />

      {/* Modal: Skip Competencies Warning */}
      <SkipCompetenciesWarningModal
        show={showSkipCompetenciesWarning}
        technicalSkillsCount={technicalSkills.length}
        behavioralCompetenciesCount={behavioralCompetencies.filter(c => c.enabled).length}
        onClose={() => setShowSkipCompetenciesWarning(false)}
        onConfirm={() => { setShowSkipCompetenciesWarning(false); goToNextStage() }}
      />

      {/* Modal: Clear Draft Confirmation */}
      <ClearDraftConfirmModal
        open={showClearDraftConfirm}
        onClose={() => setShowClearDraftConfirm(false)}
        onConfirm={handleClearDraftAndReset}
      />

      {/* Modal: Calibration Profile Review */}
      <CalibrationProfileModal
        show={showCalibrationModal}
        candidates={calibrationCandidates}
        currentIndex={currentCalibrationIndex}
        profileTab={candidateProfileTab}
        comment={calibrationComment}
        approvedCount={approvedCandidates.length}
        onSetCurrentIndex={setCurrentCalibrationIndex}
        onSetProfileTab={setCandidateProfileTab}
        onSetComment={setCalibrationComment}
        onApprove={handleApproveCandidate}
        onReject={handleRejectCandidate}
        onClose={() => setShowCalibrationModal(false)}
        onOpenEditCriteria={() => setShowEditCriteriaModal(true)}
      />

      {/* Modal: Edit Criteria */}
      <EditCriteriaModal
        open={showEditCriteriaModal}
        criteria={calibrationCriteria}
        onClose={() => setShowEditCriteriaModal(false)}
        onAddCriterion={addCalibrationCriterion}
        onRemoveCriterion={removeCalibrationCriterion}
      />

      {/* File Upload Modal */}
      <AlertDialog open={showUploadModal} onOpenChange={setShowUploadModal}>
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              Analisar Arquivo
            </AlertDialogTitle>
            <AlertDialogDescription>
              Selecione um arquivo para análise automática pela LIA.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <MultimodalUpload
              onAnalysisComplete={handleFileAnalysisComplete}
              onError={handleFileAnalysisError}
              analysisType="auto"
              autoAnalyze={false}
            />
          </div>
          <AlertDialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowUploadModal(false)
                setUploadedFile(null)
              }}
            >
              Cancelar
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export function ExpandedChatModal(props: ExpandedChatModalProps) {
  const wizardState = useWizardState({
    initialStage: 'input-evaluation',
    onStageChange: () => {},
    onPendingChanges: () => {}
  })
  
  return (
    <ExpandedChatProvider value={wizardState}>
      <ExpandedChatModalContent {...props} />
    </ExpandedChatProvider>
  )
}
