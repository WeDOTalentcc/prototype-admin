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
import { useConversationMemory } from './expanded-chat/hooks/useConversationMemory'
import { useLearning } from './expanded-chat/hooks/useLearning'
import { useFastTrack, type FastTrackSuggestion, type FastTrackJobData } from '@/hooks/useFastTrack'
import { FastTrackSuggestions } from './job-wizard/FastTrackSuggestions'
import { FastTrackReviewPanel } from './job-wizard/FastTrackReviewPanel'
import { useWizardAnalytics } from './expanded-chat/hooks/useWizardAnalytics'
import { useContextSwitching, type WizardSnapshot, type GeneralChatSnapshot } from './expanded-chat/hooks/useContextSwitching'
import { WizardHeader, WSIQualityBar, ToolConfirmationMessage, ToolExecutionFeedback, ChatMessageList } from './expanded-chat/components'
import { SalaryStage, CompetenciesStage, WSIQuestionsStage, EnrichedJDStage, SearchCalibrationStage, SearchCalibrationNavButtons, ReviewPublishStage, InputEvaluationStage, type EnrichedJDData } from './expanded-chat/stages'
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
import { ClearDraftConfirmModal, EditCriteriaModal } from './expanded-chat/modals'

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
      console.log('[ToolCalling] Tool executed:', result.tool_name, result.success ? 'success' : 'failed')
    },
    onToolError: (error, toolName) => {
      console.error('[ToolCalling] Tool error:', toolName, error)
    },
  })
  
  // Conversation Memory hook - persists conversation context for AI memory
  const conversationMemory = useConversationMemory({
    summaryThreshold: 10,
    maxMessages: 50,
    onError: (error) => {
      console.warn('[ConversationMemory] Error:', error.message)
    },
    onConversationLoaded: (conv) => {
      console.log('[ConversationMemory] Conversation loaded:', conv.id, 'messages:', conv.message_count)
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
      console.error('Backend wizard error:', error)
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
      console.error('Failed to accept proactive action:', err)
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
      console.error('Failed to reject proactive action:', err)
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
      console.log(`[ContextSwitch] ${from} → ${to}`)
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
              console.warn('[onGeneralRestore] Failed to restore conversation:', error)
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
      technicalSkills: technicalSkills,
      behavioralCompetencies: behavioralCompetencies,
      wsiCandidates: wsiCandidates,
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
                  console.warn(`Failed to fetch members for department ${dept.id}:`, err)
                }
              })
              await Promise.all(memberPromises)
              setCompanyMembersMap(membersMap)
            } catch (err) {
              console.warn('Failed to fetch company members:', err)
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
        console.error('Error fetching company config:', error)
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
        console.error('Failed to fetch salary benchmark:', error)
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

  const generateCriteriaResponse = (criteria: DetectedCriteria): string => {
    const detected: string[] = []
    const missing: string[] = []
    
    if (criteria.cargo) detected.push(`**Cargo**: ${criteria.cargo}`)
    else missing.push('cargo')
    
    if (criteria.gestorArea) detected.push(`**Gestor**: ${criteria.gestorArea}`)
    
    if (criteria.responsabilidades.length > 0) {
      detected.push(`**Responsabilidades**: ${criteria.responsabilidades.slice(0, 4).join(', ')}${criteria.responsabilidades.length > 4 ? ` (+${criteria.responsabilidades.length - 4})` : ''}`)
    }
    
    if (criteria.competenciasTecnicas.length > 0) {
      detected.push(`**Skills técnicos**: ${criteria.competenciasTecnicas.slice(0, 5).join(', ')}${criteria.competenciasTecnicas.length > 5 ? ` (+${criteria.competenciasTecnicas.length - 5})` : ''}`)
    } else {
      missing.push('competências técnicas')
    }
    
    if (criteria.competenciasComportamentais.length > 0) {
      detected.push(`**Competências comportamentais**: ${criteria.competenciasComportamentais.slice(0, 3).join(', ')}`)
    }
    
    if (criteria.idiomas && criteria.idiomas.length > 0) {
      detected.push(`**Idiomas**: ${criteria.idiomas.join(', ')}`)
    }
    
    if (criteria.senioridadeIdiomas) detected.push(`**Senioridade**: ${criteria.senioridadeIdiomas}`)
    else missing.push('senioridade')
    
    if (criteria.modeloTrabalho) {
      let modeloText = `**Modelo**: ${criteria.modeloTrabalho}`
      if (criteria.diasPresenciais) {
        modeloText += ` (${criteria.diasPresenciais}x por semana no escritório)`
      }
      detected.push(modeloText)
    }
    if (criteria.localizacao) detected.push(`**Local**: ${criteria.localizacao}`)
    if (criteria.tipoContrato) detected.push(`**Contrato**: ${criteria.tipoContrato}`)
    if (criteria.salario) detected.push(`**Salário**: ${criteria.salario}`)
    if (criteria.bonus) detected.push(`**Bônus**: ${criteria.bonus}`)
    if (criteria.isAffirmative !== null) {
      let affirmText = `**Vaga Afirmativa**: ${criteria.isAffirmative ? 'Sim' : 'Não'}`
      if (criteria.affirmativeCriteriaPrimary) {
        affirmText += ` (${criteria.affirmativeCriteriaPrimary}${criteria.affirmativeCriteriaSecondary ? `, ${criteria.affirmativeCriteriaSecondary}` : ''})`
      }
      detected.push(affirmText)
    }
    
    // Novos campos detectáveis
    if (criteria.experienciaMinima) detected.push(`**Experiência**: ${criteria.experienciaMinima}`)
    if (criteria.formacao && criteria.formacao.length > 0) {
      detected.push(`**Formação**: ${criteria.formacao.join(', ')}`)
    }
    if (criteria.certificacoes && criteria.certificacoes.length > 0) {
      detected.push(`**Certificações**: ${criteria.certificacoes.join(', ')}`)
    }
    if (criteria.ferramentas && criteria.ferramentas.length > 0) {
      detected.push(`**Ferramentas**: ${criteria.ferramentas.slice(0, 5).join(', ')}${criteria.ferramentas.length > 5 ? ` (+${criteria.ferramentas.length - 5})` : ''}`)
    }
    if (criteria.beneficiosMencionados && criteria.beneficiosMencionados.length > 0) {
      detected.push(`**Benefícios**: ${criteria.beneficiosMencionados.slice(0, 4).join(', ')}${criteria.beneficiosMencionados.length > 4 ? ` (+${criteria.beneficiosMencionados.length - 4})` : ''}`)
    }
    if (criteria.viagensFrequentes) detected.push(`**Viagens**: Sim`)
    if (criteria.disponibilidade) detected.push(`**Início**: ${criteria.disponibilidade}`)
    if (criteria.cnh) detected.push(`**CNH**: ${criteria.cnh}`)
    if (criteria.horario) detected.push(`**Horário**: ${criteria.horario}`)
    
    let response = ''
    
    if (detected.length > 0) {
      response = `Detectei os seguintes critérios:\n\n${detected.map(d => `- ${d}`).join('\n')}`
      
      if (missing.length > 0 && missing.length <= 2) {
        response += `\n\nPara completar, informe: **${missing.join('** e **')}**.`
      } else if (detected.length >= 3) {
        response += `\n\nÓtimo progresso! Você pode adicionar mais detalhes para enriquecer a vaga.`
      }
    } else {
      response = 'Não consegui detectar critérios específicos. Tente descrever o cargo, senioridade, skills técnicos e modelo de trabalho.'
    }
    
    return response
  }

  const generateParecerData = useCallback((): ParecerLIAData => {
    const sections: Array<{ title: string; status: "good" | "attention" | "missing"; items: string[]; suggestions?: string[] }> = []
    
    const descItems: string[] = []
    const descSuggestions: string[] = []
    if (detectedCriteria.cargo) descItems.push(`Cargo: ${detectedCriteria.cargo}`)
    if (detectedCriteria.senioridadeIdiomas) descItems.push(`Senioridade: ${detectedCriteria.senioridadeIdiomas}`)
    if (detectedCriteria.departamento) descItems.push(`Departamento: ${detectedCriteria.departamento}`)
    if (detectedCriteria.modeloTrabalho) descItems.push(`Modelo: ${detectedCriteria.modeloTrabalho}`)
    if (detectedCriteria.localizacao) descItems.push(`Local: ${detectedCriteria.localizacao}`)
    if (!detectedCriteria.senioridadeIdiomas) descSuggestions.push("Adicionar senioridade para melhor calibração de candidatos")
    if (!detectedCriteria.modeloTrabalho) descSuggestions.push("Definir modelo de trabalho (remoto, híbrido, presencial)")
    sections.push({
      title: "Descrição da Vaga",
      status: descItems.length >= 4 ? "good" : descItems.length >= 2 ? "attention" : "missing",
      items: descItems,
      suggestions: descSuggestions.length > 0 ? descSuggestions : undefined
    })

    const respItems = detectedCriteria.responsabilidades || []
    sections.push({
      title: "Responsabilidades",
      status: respItems.length >= 3 ? "good" : respItems.length >= 1 ? "attention" : "missing",
      items: respItems.length > 0 ? respItems.slice(0, 5) : ["Nenhuma responsabilidade identificada"],
      suggestions: respItems.length < 3 ? ["Adicionar pelo menos 3 responsabilidades principais"] : undefined
    })

    const techItems = technicalSkills.map(s => `${s.name} (${s.level})`)
    const techFromCriteria = detectedCriteria.competenciasTecnicas || []
    const techDisplay = techItems.length > 0 ? techItems : techFromCriteria.map(s => s)
    sections.push({
      title: "Competências Técnicas",
      status: techDisplay.length >= 3 ? "good" : techDisplay.length >= 1 ? "attention" : "missing",
      items: techDisplay.length > 0 ? techDisplay.slice(0, 6) : ["Nenhuma competência técnica identificada"],
      suggestions: techDisplay.length < 3 ? ["Incluir pelo menos 3 skills técnicos para melhor triagem WSI"] : undefined
    })

    const behavItems = behavioralCompetencies.filter(c => c.enabled).map(c => c.name)
    const behavFromCriteria = detectedCriteria.competenciasComportamentais || []
    const behavDisplay = behavItems.length > 0 ? behavItems : behavFromCriteria
    sections.push({
      title: "Competências Comportamentais",
      status: behavDisplay.length >= 2 ? "good" : behavDisplay.length >= 1 ? "attention" : "missing",
      items: behavDisplay.length > 0 ? behavDisplay.slice(0, 5) : ["Nenhuma competência comportamental identificada"],
      suggestions: behavDisplay.length < 2 ? ["Definir competências comportamentais para avaliação cultural"] : undefined
    })

    const salaryItems: string[] = []
    const salarySuggestions: string[] = []
    if (salaryInfo.minSalary && salaryInfo.maxSalary) {
      salaryItems.push(`Faixa: R$ ${salaryInfo.minSalary} - R$ ${salaryInfo.maxSalary}`)
    }
    if (salaryInfo.minBonus || salaryInfo.maxBonus) {
      salaryItems.push(`Bônus: ${salaryInfo.minBonus || '0'}% - ${salaryInfo.maxBonus || '0'}%`)
    }
    const enabledBenefits = salaryInfo.benefits?.filter(b => b.enabled) || []
    if (enabledBenefits.length > 0) {
      salaryItems.push(`${enabledBenefits.length} benefício(s) definido(s)`)
    }
    if (!salaryInfo.minSalary) salarySuggestions.push("Definir faixa salarial para atrair candidatos adequados")
    sections.push({
      title: "Remuneração",
      status: salaryItems.length >= 2 ? "good" : salaryItems.length >= 1 ? "attention" : "missing",
      items: salaryItems.length > 0 ? salaryItems : ["Remuneração ainda não definida"],
      suggestions: salarySuggestions.length > 0 ? salarySuggestions : undefined
    })

    const marketComparisons: Array<{ field: string; yourValue: string; marketValue: string; status: "above" | "aligned" | "below" }> = []
    if (learning.suggestions?.salary?.has_suggestion && salaryInfo.minSalary) {
      const yourMin = parseFloat(salaryInfo.minSalary.replace(/\./g, '').replace(',', '.')) || 0
      const marketMin = learning.suggestions.salary.min_salary || 0
      const marketMax = learning.suggestions.salary.max_salary || 0
      if (marketMin > 0) {
        marketComparisons.push({
          field: "Faixa Salarial",
          yourValue: `R$ ${salaryInfo.minSalary} - ${salaryInfo.maxSalary}`,
          marketValue: `R$ ${marketMin.toLocaleString('pt-BR')} - ${marketMax.toLocaleString('pt-BR')}`,
          status: yourMin > marketMax ? "above" : yourMin < marketMin * 0.8 ? "below" : "aligned"
        })
      }
    }

    let timeToFillEstimate: ParecerLIAData['timeToFillEstimate']
    if (learning.suggestions?.time_to_fill?.has_prediction) {
      const ttf = learning.suggestions.time_to_fill
      timeToFillEstimate = {
        days: ttf.estimated_days || ttf.median_days || 30,
        rangeMin: ttf.range_min || 20,
        rangeMax: ttf.range_max || 45,
        confidence: ttf.confidence || 0.5
      }
    }

    const sectionScores = sections.map(s => s.status === "good" ? 1 : s.status === "attention" ? 0.5 : 0)
    const overallScore = Math.round((sectionScores.reduce((a, b) => a + b, 0) / sectionScores.length) * 100)
    
    const totalFields = 10
    const filledFields = [
      detectedCriteria.cargo,
      detectedCriteria.senioridadeIdiomas,
      detectedCriteria.departamento,
      detectedCriteria.modeloTrabalho,
      detectedCriteria.localizacao,
      (detectedCriteria.responsabilidades?.length || 0) > 0,
      techDisplay.length > 0,
      behavDisplay.length > 0,
      salaryInfo.minSalary,
      detectedCriteria.gestorArea
    ].filter(Boolean).length
    const completenessScore = Math.round((filledFields / totalFields) * 100)

    const recommendations: string[] = []
    sections.forEach(s => {
      if (s.suggestions) {
        s.suggestions.forEach(sug => recommendations.push(sug))
      }
    })
    if (recommendations.length === 0) {
      recommendations.push("A vaga está bem estruturada! Revise os detalhes e avance para a próxima etapa.")
    }

    const dataSourcesUsed: string[] = ["Critérios informados pelo recrutador"]
    if (learning.suggestions?.has_suggestions) {
      dataSourcesUsed.push(`${learning.suggestions.total_samples || 0} vagas similares`)
      if (learning.suggestions.patterns_found > 0) {
        dataSourcesUsed.push(`${learning.suggestions.patterns_found} padrões identificados`)
      }
    }

    return {
      overallScore,
      completenessScore,
      sections,
      marketComparisons: marketComparisons.length > 0 ? marketComparisons : undefined,
      timeToFillEstimate,
      similarJobsCount: learning.suggestions?.total_samples,
      dataSourcesUsed,
      recommendations
    }
  }, [detectedCriteria, technicalSkills, behavioralCompetencies, salaryInfo, learning.suggestions])

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

  // State for validation error display
  const [validationError, setValidationError] = useState<string | null>(null)

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
        // Add LIA thinking message
        const thinkingMessage: Message = {
          id: `lia-thinking-${Date.now()}`,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          processingState: 'thinking' as const
        }
        setMessages(prev => [...prev, thinkingMessage])
        
        // Use backend deduplication API for better suggestions
        const alreadySelectedSkills = [
          ...technicalSkills.map(s => s.name),
          ...behavioralCompetencies.filter(c => c.enabled).map(c => c.name)
        ]
        
        fetchDeduplicatedSkills(
          basicInfoFields.cargo || 'profissional',
          alreadySelectedSkills,
          detectedCriteria.senioridadeIdiomas || undefined
        ).then(deduplicatedSkills => {
          // Remove thinking message
          setMessages(prev => prev.filter(m => m.id !== thinkingMessage.id))
          
          // Extract skill names from deduplicated skills
          const skillNames = deduplicatedSkills.map(s => s.name)
          
          // Generate LIA analysis message with competency suggestions
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
          
          // Type the analysis message
          setTimeout(() => {
            typeText(analysisContent, analysisMessage.id)
          }, 200)
          
          // Proceed to next stage after brief delay
          setTimeout(() => {
            setStageTransition('idle')
            proceedToNextStage()
          }, 500)
        }).catch((error) => {
          console.error('Failed to fetch deduplicated skills:', error)
          // Remove thinking message and proceed anyway
          setMessages(prev => prev.filter(m => m.id !== thinkingMessage.id))
          setStageTransition('idle')
          proceedToNextStage()
        })
        return // Don't advance yet, wait for async completion
      }
      
      // Intercept transition from competencies to wsi-questions to show LIA message
      if (currentStage === 'competencies' && nextStage.id === 'wsi-questions') {
        // Add LIA thinking message
        const thinkingMessage: Message = {
          id: `lia-thinking-wsi-${Date.now()}`,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          processingState: 'thinking' as const
        }
        setMessages(prev => [...prev, thinkingMessage])
        
        // Brief delay then show WSI generation message
        setTimeout(() => {
          // Remove thinking message
          setMessages(prev => prev.filter(m => m.id !== thinkingMessage.id))
          
          // Generate WSI explanation message
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
          
          // Proceed to next stage
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
  
  // Generate competency analysis message from LIA
  const generateCompetencyAnalysisMessage = (
    cargo: string | null,
    area: string | null,
    criteria: typeof detectedCriteria,
    deduplicatedSkills?: string[]
  ): string => {
    const role = cargo || 'profissional'
    const department = area || 'a área'
    
    let message = `**Análise de Competências para ${role}**\n\n`
    message += `Com base nas informações da vaga e dados de mercado, preparei sugestões de competências:\n\n`
    
    if (criteria.competenciasTecnicas.length > 0) {
      message += `**Competências Técnicas Identificadas:**\n`
      criteria.competenciasTecnicas.slice(0, 5).forEach(skill => {
        message += `• ${skill}\n`
      })
      message += `\n`
    }
    
    if (criteria.competenciasComportamentais.length > 0) {
      message += `**Competências Comportamentais Sugeridas:**\n`
      criteria.competenciasComportamentais.slice(0, 4).forEach(comp => {
        message += `• ${comp}\n`
      })
      message += `\n`
    }
    
    message += `📊 *Fontes: histórico de vagas similares + dados de mercado*\n\n`
    message += `Me informe aqui no chat se deseja adicionar, remover ou alterar os pesos das competências.`
    
    return message
  }
  
  // Generate WSI explanation message from LIA
  const generateWSIExplanationMessage = (
    technicalSkills: string[],
    behavioralCompetencies: string[],
    cargo: string | null
  ): string => {
    const role = cargo || 'a vaga'
    const totalCompetencies = technicalSkills.length + behavioralCompetencies.length
    
    let message = `**Gerando Perguntas de Triagem WSI**\n\n`
    message += `Vou criar perguntas baseadas na metodologia WSI (Work Sample Interview), que combina:\n\n`
    message += `• **Taxonomia de Bloom** - níveis cognitivos\n`
    message += `• **Modelo Dreyfus** - proficiência técnica\n`
    message += `• **Big Five** - traços comportamentais\n\n`
    
    message += `Considerando as ${totalCompetencies} competências definidas para ${role}, `
    message += `as perguntas avaliarão tanto habilidades técnicas quanto comportamentais.\n\n`
    
    message += `⏳ *Aguarde enquanto gero as perguntas personalizadas...*`
    
    return message
  }
  
  // Proceed to next stage (called after modal or directly if no suggestions)
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
  
  // Handle accepting selected suggestions from the modal
  const handleAcceptSuggestions = () => {
    // Add selected technical skills
    const skillCategories: Record<string, 'language' | 'framework' | 'database' | 'tool'> = {
      'Python': 'language', 'Java': 'language', 'Node.js': 'framework', 'React': 'framework',
      'TypeScript': 'language', 'SQL': 'database', 'Docker': 'tool', 'AWS': 'tool',
      'Git': 'tool', 'Linux': 'tool', 'MongoDB': 'database', 'PostgreSQL': 'database',
      'Kubernetes': 'tool', 'CI/CD': 'tool', 'REST API': 'tool',
      'Excel Avançado': 'tool', 'Power BI': 'tool', 'SAP': 'tool', 'ERP': 'tool'
    }
    
    const newTechnicalSkills: TechnicalSkill[] = Array.from(selectedSuggestedTechnical).map((skill, idx) => ({
      id: `suggested-tech-${Date.now()}-${idx}`,
      name: skill,
      level: 'Intermediário' as const,
      required: idx < 3,
      category: skillCategories[skill] || 'tool',
      weight: idx < 3 ? 3 : 2
    }))
    
    setTechnicalSkills(prev => {
      const existingNames = prev.map(s => s.name.toLowerCase())
      const filteredNew = newTechnicalSkills.filter(s => !existingNames.includes(s.name.toLowerCase()))
      return [...prev, ...filteredNew]
    })
    
    // Add selected behavioral competencies
    const newBehavioralCompetencies: BehavioralCompetency[] = Array.from(selectedSuggestedBehavioral).map((comp, idx) => ({
      id: `suggested-behav-${Date.now()}-${idx}`,
      name: comp,
      weight: 4,
      justification: 'Sugerido pela LIA com base no cargo/área',
      enabled: true
    }))
    
    setBehavioralCompetencies(prev => {
      const existingNames = prev.map(c => c.name.toLowerCase())
      const filteredNew = newBehavioralCompetencies.filter(c => !existingNames.includes(c.name.toLowerCase()))
      return [...prev, ...filteredNew]
    })
    
    // Add feedback message
    const acceptedCount = selectedSuggestedTechnical.size + selectedSuggestedBehavioral.size
    if (acceptedCount > 0) {
      const feedbackMessage: Message = {
        id: `suggestions-accepted-${Date.now()}`,
        role: 'assistant',
        content: `Ótimo! Adicionei **${selectedSuggestedTechnical.size} competências técnicas** e **${selectedSuggestedBehavioral.size} comportamentais** baseadas no perfil da vaga. Me informe aqui no chat se precisar ajustar os pesos e níveis.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, feedbackMessage])
    }
    
    // Close modal and proceed
    setShowCompetenciesSuggestionsModal(false)
    proceedToNextStage()
  }
  
  // Handle skipping suggestions
  const handleSkipSuggestions = () => {
    setShowCompetenciesSuggestionsModal(false)
    proceedToNextStage()
  }

  const goToPreviousStage = () => {
    const prevIndex = currentStageIndex - 1
    if (prevIndex >= 0) {
      const prevStage = WIZARD_STAGES[prevIndex]
      setCurrentStage(prevStage.id)
    }
  }

  const handleClearDraftAndReset = () => {
    clearWizardDraft()
    setMessages([])
    setBasicInfoFields({
      cargo: '',
      area: '',
      gestor: '',
      localidade: '',
      modeloTrabalho: '',
      tipoContrato: ''
    })
    setTechnicalSkills([])
    setBehavioralCompetencies([
      { id: '1', name: 'Comunicação Eficaz', weight: 4, justification: '', enabled: false },
      { id: '2', name: 'Resolução de Problemas', weight: 5, justification: '', enabled: false },
      { id: '3', name: 'Adaptabilidade', weight: 4, justification: '', enabled: false },
      { id: '4', name: 'Trabalho em Equipe', weight: 4, justification: '', enabled: false },
      { id: '5', name: 'Proatividade', weight: 3, justification: '', enabled: false },
    ])
    setSalaryInfo({
      minSalary: '',
      maxSalary: '',
      minBonus: '',
      maxBonus: '',
      bonusCriteria: '',
      benefits: []
    })
    setWsiCandidates([])
    setDetectedCriteria({
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
    setCurrentStage('input-evaluation')
    setGeneratedJobDescription('')
    setHasAppliedRestoredDraft(false)
    setShowClearDraftConfirm(false)
  }

  const canAdvanceToNextStage = (): boolean => {
    switch (currentStage) {
      case 'input-evaluation':
        // User must have sent at least one message before advancing
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
        // User can advance after reviewing enriched JD (at least cargo must be detected)
        return !!detectedCriteria.cargo
      case 'competencies':
        // Require at least one technical skill AND WSI quality gate score >= 70%
        const hasMinimumTechnicalSkills = technicalSkills.length >= 1
        return hasMinimumTechnicalSkills && wsiQualityGates.canAdvance
      case 'salary':
        const hasSalaryRange = !!(salaryInfo.minSalary && salaryInfo.maxSalary && 
          parseFloat(salaryInfo.minSalary.replace(/\./g, '').replace(',', '.')) > 0 && 
          parseFloat(salaryInfo.maxSalary.replace(/\./g, '').replace(',', '.')) > 0)
        // Bonus is optional: only validate if user started filling either field
        const bonusStarted = !!(salaryInfo.minBonus || salaryInfo.maxBonus)
        const bonusValid = !bonusStarted || !!(
          salaryInfo.minBonus && salaryInfo.maxBonus && 
          parseFloat(salaryInfo.minBonus.replace(/\./g, '').replace(',', '.')) > 0 && 
          parseFloat(salaryInfo.maxBonus.replace(/\./g, '').replace(',', '.')) > 0
        )
        const hasAtLeastOneBenefit = salaryInfo.benefits.some(b => b.enabled)
        return hasSalaryRange && bonusValid && hasAtLeastOneBenefit
      case 'wsi-questions':
        // Require at least one question selected AND WSI quality gate score >= 70%
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

  const handlePublishJob = async () => {
    setIsLoading(true)
    
    try {
      // Prepare job vacancy data for API
      const linkedinPlatform = publishingPlatforms.find(p => p.id === 'linkedin')
      const indeedPlatform = publishingPlatforms.find(p => p.id === 'indeed')
      const websitePlatform = publishingPlatforms.find(p => p.id === 'website')
      
      const jobData = {
        title: basicInfoFields.cargo || 'Nova Vaga',
        department: basicInfoFields.area || undefined,
        location: basicInfoFields.localidade || undefined,
        work_model: basicInfoFields.modeloTrabalho || undefined,
        hybrid_days_onsite: basicInfoFields.modeloTrabalho === 'Híbrido' 
          ? (jobConfig.hybridDaysOnsite || companyConfig?.hybridDaysOnsite || 3) 
          : undefined,
        employment_type: basicInfoFields.tipoContrato || 'CLT',
        seniority_level: detectedCriteria.senioridadeIdiomas || 'Pleno',
        description: messages.find(m => m.role === 'user')?.content || `Vaga de ${basicInfoFields.cargo}`,
        requirements: technicalSkills.filter(s => s.required).map(s => s.name),
        technical_requirements: technicalSkills.map(s => ({
          name: s.name,
          level: s.level,
          required: s.required,
          weight: s.weight
        })),
        behavioral_competencies: behavioralCompetencies.filter(c => c.enabled).map(c => ({
          name: c.name,
          weight: c.weight,
          justification: c.justification
        })),
        salary: salaryInfo.minSalary && salaryInfo.maxSalary ? 
          `R$ ${parseInt(salaryInfo.minSalary).toLocaleString('pt-BR')} - R$ ${parseInt(salaryInfo.maxSalary).toLocaleString('pt-BR')}` : undefined,
        salary_range: (salaryInfo.minSalary || salaryInfo.maxSalary || salaryInfo.minBonus || salaryInfo.maxBonus) ? {
          min: salaryInfo.minSalary ? parseInt(salaryInfo.minSalary) : undefined,
          max: salaryInfo.maxSalary ? parseInt(salaryInfo.maxSalary) : undefined,
          currency: 'BRL',
          bonus_min: salaryInfo.minBonus ? parseInt(salaryInfo.minBonus) : undefined,
          bonus_max: salaryInfo.maxBonus ? parseInt(salaryInfo.maxBonus) : undefined
        } : undefined,
        benefits: salaryInfo.benefits.filter(b => b.enabled).map(b => b.name),
        manager: basicInfoFields.gestor || undefined,
        status: 'active' as const,
        recruiter: user?.name || user?.email?.split('@')[0] || 'Recrutador',
        recruiter_email: user?.email || '',
        open_date: new Date().toISOString(),
        // Visible editable fields
        urgency_level: jobConfig.urgencyLevel,
        visibility: jobConfig.visibility,
        is_confidential: jobConfig.isConfidential,
        is_affirmative: jobConfig.isAffirmative,
        affirmative_criteria_primary: detectedCriteria.affirmativeCriteriaPrimary,
        affirmative_criteria_secondary: detectedCriteria.affirmativeCriteriaSecondary,
        affirmative_description: detectedCriteria.affirmativeDescription,
        deadline: jobConfig.deadline,
        deadline_screening: jobConfig.deadlineScreening,
        deadline_shortlist: jobConfig.deadlineShortlist,
        languages: jobConfig.languages.map(l => ({ name: l.name, level: l.level })),
        // Calculated invisible fields (for email/Teams summary)
        stage: 'screening',
        target_audience: jobConfig.visibility === 'internal' || jobConfig.visibility === 'confidential' ? 'internal' : 'external',
        masked_company_name: jobConfig.isConfidential ? 'Empresa Confidencial' : undefined,
        interview_stages: interviewStages.length > 0 
          ? interviewStages.map((stage, index) => ({
              stageName: stage.name,
              order: index + 1,
              type: stage.name.toLowerCase().includes('triagem') ? 'screening' :
                    stage.name.toLowerCase().includes('técnic') ? 'technical' :
                    stage.name.toLowerCase().includes('rh') ? 'interview' :
                    stage.name.toLowerCase().includes('final') || stage.name.toLowerCase().includes('gestor') ? 'final' :
                    'interview',
              sla: stage.sla
            }))
          : [
              { stageName: 'Triagem', order: 1, type: 'screening' },
              { stageName: 'Entrevista RH', order: 2, type: 'interview' },
              { stageName: 'Entrevista Técnica', order: 3, type: 'technical' },
              { stageName: 'Entrevista Final', order: 4, type: 'final' },
            ],
        hiring_process: interviewStages.length > 0 
          ? interviewStages.map(stage => stage.name)
          : ['Triagem', 'Entrevista RH', 'Entrevista Técnica', 'Entrevista Final'],
        // Publishing platforms
        published_linkedin: linkedinPlatform?.enabled || false,
        published_indeed: indeedPlatform?.enabled || false,
        published_website: websitePlatform?.enabled || false,
        eligibility_questions: companyDefaultQuestions.filter(q => q.enabled).map(q => ({
          question: q.question,
          category: 'eligibility',
          type: q.type,
          weight: 3,
          is_eliminatory: true
        })),
        screening_questions: wsiCandidates.filter(q => q.selected).map(q => ({
          question: q.question,
          category: q.category,
          expected_answer: q.expectedAnswer,
          weight: 5,
          type: q.type
        })),
        conversation_id: conversationId || undefined
      }
      
      console.log('Creating job vacancy with data:', jobData)
      
      // Call API to create job vacancy
      const createdJob = await liaApi.createJobVacancy(jobData)
      
      const jobId = (createdJob as any).job_id || createdJob.id
      setPublishedJobId(jobId)
      
      console.log('Job vacancy created successfully:', createdJob)
      
      if (wizardFastTrackSourceJobId && jobId && jobId !== wizardFastTrackSourceJobId) {
        const tenantId = user?.company || 'default'
        liaApi.recordFastTrackUsage({
          company_id: tenantId,
          source_job_id: wizardFastTrackSourceJobId,
          new_job_id: jobId,
          modified_fields: [],
          was_published: true
        }).catch(err => console.error('Non-blocking: Fast Track usage recording failed:', err))
        setWizardFastTrackSourceJobId(null)
      }
      
      // Send workplan notification to recruiter and manager
      try {
        await liaApi.sendJobCreatedNotification({
          job_id: jobId,
          job_title: basicInfoFields.cargo || 'Nova Vaga',
          department: basicInfoFields.area || undefined,
          location: basicInfoFields.localidade || undefined,
          work_model: basicInfoFields.modeloTrabalho || undefined,
          seniority_level: detectedCriteria.senioridadeIdiomas || undefined,
          job_description: messages.find(m => m.role === 'user')?.content || `Vaga de ${basicInfoFields.cargo}`,
          technical_requirements: technicalSkills.map(s => ({
            name: s.name,
            level: s.level,
            required: s.required,
            weight: s.weight
          })),
          behavioral_competencies: behavioralCompetencies.filter(c => c.enabled).map(c => ({
            name: c.name,
            weight: String(c.weight)
          })),
          languages: jobConfig.languages.map(l => ({ name: l.name, level: l.level })),
          salary_range: (salaryInfo.minSalary || salaryInfo.maxSalary) ? {
            min: salaryInfo.minSalary ? parseInt(salaryInfo.minSalary) : undefined,
            max: salaryInfo.maxSalary ? parseInt(salaryInfo.maxSalary) : undefined,
            currency: 'BRL'
          } : undefined,
          benefits: salaryInfo.benefits.filter(b => b.enabled).map(b => b.name),
          deadline_screening: jobConfig.deadlineScreening,
          deadline_shortlist: jobConfig.deadlineShortlist,
          deadline_closing: jobConfig.deadline,
          interview_stages: interviewStages.map((stage, index) => ({
            stageName: stage.name,
            order: index + 1,
            sla: stage.sla
          })),
          publishing_platforms: {
            linkedin: linkedinPlatform?.enabled || false,
            indeed: indeedPlatform?.enabled || false,
            website: websitePlatform?.enabled || false
          },
          urgency_level: jobConfig.urgencyLevel,
          is_confidential: jobConfig.isConfidential,
          is_affirmative: jobConfig.isAffirmative,
          recruiter_email: user?.email || '',
          recruiter_name: user?.name || user?.email?.split('@')[0] || 'Recrutador',
          // Manager notification: lookup email from company members map
          manager_email: basicInfoFields.gestor 
            ? (companyMembersMap.get(basicInfoFields.gestor.trim()) || 
               companyMembersMap.get(basicInfoFields.gestor.trim().toLowerCase()))
            : undefined,
          manager_name: basicInfoFields.gestor || undefined,
          channels: ['email', 'teams']
        })
        console.log('Job created notification sent successfully')
      } catch (notifError) {
        console.error('Failed to send job created notification (non-blocking):', notifError)
        // Non-blocking error - job was created successfully, notification is secondary
      }
      
      // Add publish confirmation message with calibration choice
      const publishMessage: Message = {
        id: `publish-${Date.now()}`,
        role: 'assistant',
        content: `A vaga **${basicInfoFields.cargo || 'Nova Vaga'}** foi criada e publicada com sucesso! 🎉

📋 **ID da Vaga:** ${jobId}
🏢 **Área:** ${basicInfoFields.area || 'A definir'}
📍 **Local:** ${basicInfoFields.localidade || 'A definir'}

---

**Próximo passo: Calibração de Busca**

Posso apresentar alguns candidatos para você avaliar agora. Isso me ajuda a entender melhor o perfil ideal e melhora a precisão das próximas sugestões em até 60%.

**OU** você pode ir direto para o Kanban e eu aprendo naturalmente conforme você move candidatos pelo funil (aprovar → entrevista, reprovar → descartado).

*O que prefere?*
• "Calibrar agora" - mostro 5 perfis rápidos para você avaliar
• "Ir para o kanban" - já adiciono os candidatos e você avalia lá`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, publishMessage])
      
      // Set awaiting calibration choice state
      setAwaitingCalibrationChoice(true)
      
      // Transition to search-calibration stage (unified search and calibration)
      setCurrentStage('search-calibration')
      
      // Clear wizard draft after successful publish
      clearWizardDraft()
      
      // Start local candidate search in background (results used for both paths)
      startLocalSearch()
      
      // NOTE: Do NOT call onJobCreated here - it causes the parent to switch modes and close the wizard.
      // The wizard needs to remain open to show the candidate-search and calibration stages.
      // onJobCreated will be called later when the user explicitly finishes or closes the wizard.
    } catch (error) {
      console.error('Error creating job vacancy:', error)
      
      // Add error message
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Desculpe, ocorreu um erro ao criar a vaga. Por favor, tente novamente.\n\nErro: ${error instanceof Error ? error.message : 'Erro desconhecido'}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const buildCandidateSearchQuery = (): string => {
    const parts: string[] = []
    if (basicInfoFields.cargo) parts.push(basicInfoFields.cargo)
    if (detectedCriteria.senioridadeIdiomas) parts.push(detectedCriteria.senioridadeIdiomas)
    if (basicInfoFields.area) parts.push(basicInfoFields.area)
    const topSkills = technicalSkills.slice(0, 5).map(s => s.name)
    if (topSkills.length > 0) parts.push(topSkills.join(', '))
    if (basicInfoFields.localidade) parts.push(basicInfoFields.localidade)
    return parts.join(' ') || 'profissional'
  }

  const startLocalSearch = async () => {
    setSearchPhase('local-searching')
    try {
      const searchQuery = buildCandidateSearchQuery()
      const response = await liaApi.searchCandidatesLocal({
        query: searchQuery,
        limit: Math.max(20, preferredCandidateCount * 5)
      })
      setLocalCandidateCount(response.total_results || response.candidates?.length || 0)
      setSearchPhase('local-complete')
    } catch (error) {
      console.error('Local search error:', error)
      setLocalCandidateCount(0)
      setSearchPhase('local-complete')
    }
  }

  const startGlobalSearch = async () => {
    setSearchPhase('global-searching')
    try {
      const searchQuery = buildCandidateSearchQuery()
      const response = await liaApi.searchCandidates({
        query: searchQuery,
        search_type: 'fast',
        limit: Math.max(100, preferredCandidateCount * 20)
      })
      setGlobalCandidateCount(response.total_results || response.candidates?.length || 0)
      setSearchPhase('global-complete')
    } catch (error) {
      console.error('Global search error:', error)
      setGlobalCandidateCount(0)
      setSearchPhase('global-complete')
    }
  }

  const generateJobDescription = () => {
    setIsGeneratingDescription(true)
    
    const skills = technicalSkills.slice(0, 5).map(s => s.name).join(', ')
    const competencies = behavioralCompetencies.filter(c => c.enabled).slice(0, 3).map(c => c.name).join(', ')
    const benefits = salaryInfo.benefits.filter(b => b.enabled).slice(0, 4).map(b => b.name).join(', ')
    
    const description = `Estamos em busca de um(a) ${basicInfoFields.cargo || 'profissional'} para integrar nossa equipe de ${basicInfoFields.area || 'alto desempenho'}.

📍 **Local:** ${basicInfoFields.localidade || 'A definir'} | ${basicInfoFields.modeloTrabalho || 'Flexível'}
📝 **Contrato:** ${basicInfoFields.tipoContrato || 'CLT'}

**O que você vai encontrar:**
• Oportunidade de crescimento em ambiente ${companyConfig?.values?.includes('inovação') ? 'inovador' : 'dinâmico'}
• Projetos desafiadores na área de ${basicInfoFields.area || 'tecnologia'}
${benefits ? `• Benefícios: ${benefits}` : '• Pacote de benefícios competitivo'}

**O que buscamos:**
${skills ? `• Experiência com: ${skills}` : '• Conhecimentos técnicos na área'}
${competencies ? `• Perfil: ${competencies}` : '• Profissional colaborativo e proativo'}
• Experiência compatível com a posição

${salaryInfo.minSalary && salaryInfo.maxSalary ? `💰 **Faixa salarial:** R$ ${salaryInfo.minSalary} - R$ ${salaryInfo.maxSalary}` : ''}

Venha fazer parte do nosso time! 🚀`

    setTimeout(() => {
      setJobDescription(description)
      setIsGeneratingDescription(false)
    }, 1200)
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

  const generateWSIQuestions = async (count: number = 7, category: 'technical' | 'behavioral' = 'technical') => {
    setIsGeneratingWSI(true)
    const newBatch = wsiGenerationBatch + 1
    setWsiGenerationBatch(newBatch)
    
    try {
      // Call backend API to generate WSI questions using LLM
      const response = await liaApi.generateJobScreeningQuestions({
        job_title: basicInfoFields.cargo || 'Vaga',
        job_description: detectedCriteria.cargo ? `Vaga de ${detectedCriteria.cargo}` : undefined,
        technical_skills: technicalSkills.filter(s => s.required).map(s => s.name),
        behavioral_competencies: behavioralCompetencies.filter(c => c.enabled).map(c => c.name),
        seniority_level: detectedCriteria.senioridadeIdiomas?.toLowerCase() || 'pleno',
        work_model: basicInfoFields.modeloTrabalho?.toLowerCase(),
        location: basicInfoFields.localidade,
        count: count,
        category: category
      })
      
      // Convert API response to WSIQuestionCandidate format
      const existingTexts = new Set(wsiCandidates.map(q => q.question.toLowerCase()))
      
      const newQuestions: WSIQuestionCandidate[] = response.questions
        .filter(q => !existingTexts.has(q.question.toLowerCase()))
        .map((q) => ({
          id: q.id,
          question: q.question,
          type: q.type as 'open' | 'yes-no' | 'numeric' | 'multiple-choice',
          required: q.required,
          options: q.options,
          expectedAnswer: q.expected_answer,
          correctOptionIndex: q.correct_option_index,
          selected: false,
          batch: newBatch,
          isWSI: true,
          competency: q.competency,
          framework: q.framework,
          category: q.category
        }))
      
      setWsiCandidates(prev => [...prev, ...newQuestions])
      setWsiHasGenerated(true)
      
      // Add LIA feedback message
      const selectedCount = wsiCandidates.filter(q => q.selected).length
      const feedbackMessage: Message = {
        id: `wsi-feedback-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        role: 'assistant',
        content: newBatch === 1 
          ? `Gerei ${newQuestions.length} perguntas de triagem baseadas na **metodologia WSI** (Work Sample Interview) e no perfil da vaga.\n\nAs perguntas foram criadas com base em frameworks científicos:\n- **CBI** (Competency-Based Interviewing)\n- **Dreyfus Model** (Avaliação de Expertise)\n- **Bloom's Taxonomy** (Níveis de Conhecimento)\n\nSelecione **5 perguntas** que melhor se adequam ao processo seletivo. As respostas esperadas já foram definidas pela LIA com base no perfil ideal.`
          : `Adicionei mais ${newQuestions.length} opções de perguntas WSI! Você tem ${selectedCount}/5 selecionadas.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, feedbackMessage])
      
    } catch (error) {
      console.error('Error generating WSI questions:', error)
      
      // Fallback to static questions if API fails
      const baseTs = Date.now()
      const fallbackQuestions: WSIQuestionCandidate[] = [
        { id: `wsi-fallback-${baseTs}-1-${Math.random().toString(36).slice(2, 8)}`, question: 'Qual sua pretensão salarial para regime CLT?', type: 'open', required: true, selected: false, batch: newBatch },
        { id: `wsi-fallback-${baseTs}-2-${Math.random().toString(36).slice(2, 8)}`, question: `Você tem disponibilidade para trabalho ${basicInfoFields.modeloTrabalho || 'híbrido'}${basicInfoFields.localidade ? ` em ${basicInfoFields.localidade}` : ''}?`, type: 'yes-no', required: true, expectedAnswer: true, selected: false, batch: newBatch },
        { id: `wsi-fallback-${baseTs}-3-${Math.random().toString(36).slice(2, 8)}`, question: 'Quantos anos de experiência você tem com a principal tecnologia da vaga?', type: 'numeric', required: true, expectedAnswer: 3, selected: false, batch: newBatch },
        { id: `wsi-fallback-${baseTs}-4-${Math.random().toString(36).slice(2, 8)}`, question: 'Você tem experiência com metodologias ágeis (Scrum, Kanban)?', type: 'yes-no', required: true, expectedAnswer: true, selected: false, batch: newBatch },
        { id: `wsi-fallback-${baseTs}-5-${Math.random().toString(36).slice(2, 8)}`, question: 'Qual seu nível de inglês?', type: 'multiple-choice', options: ['Básico', 'Intermediário', 'Avançado', 'Fluente'], required: true, correctOptionIndex: 2, selected: false, batch: newBatch },
      ]
      
      const existingTexts = new Set(wsiCandidates.map(q => q.question.toLowerCase()))
      const newQuestions = fallbackQuestions.filter(q => !existingTexts.has(q.question.toLowerCase())).slice(0, count)
      
      setWsiCandidates(prev => [...prev, ...newQuestions])
      setWsiHasGenerated(true)
      
      const feedbackMessage: Message = {
        id: `wsi-feedback-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        role: 'assistant',
        content: `Gerei ${newQuestions.length} perguntas de triagem padrão. Selecione **5 perguntas** para a triagem.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, feedbackMessage])
    } finally {
      setIsGeneratingWSI(false)
    }
  }

  const toggleWSIQuestionSelection = (questionId: string) => {
    setWsiCandidates(prev => {
      const currentlySelected = prev.filter(q => q.selected).length
      const question = prev.find(q => q.id === questionId)
      
      if (!question) return prev
      
      // If already at max (5) and trying to select more, don't allow
      if (!question.selected && currentlySelected >= 5) {
        return prev
      }
      
      const updated = prev.map(q => 
        q.id === questionId ? { ...q, selected: !q.selected } : q
      )
      
      // Sync selected questions to wsiQuestions
      const selected = updated.filter(q => q.selected)
      setWsiQuestions(selected.map(({ selected, batch, ...rest }) => rest))
      
      // If reached 5 questions, add confirmation message
      const newCount = question.selected ? currentlySelected - 1 : currentlySelected + 1
      if (newCount === 5) {
        const confirmMessage: Message = {
          id: `wsi-confirm-${Date.now()}`,
          role: 'assistant',
          content: `Perfeito! Você selecionou **5 perguntas** de triagem.\n\nRevise as respostas esperadas no painel e clique em "Confirmar Triagem" quando estiver pronto para a revisão final.`,
          timestamp: new Date()
        }
        setMessages(msgs => [...msgs, confirmMessage])
      }
      
      return updated
    })
  }

  const updateWSIQuestionExpectedAnswer = (questionId: string, answer: string | number | boolean) => {
    setWsiCandidates(prev => {
      const updated = prev.map(q => 
        q.id === questionId ? { ...q, expectedAnswer: answer } : q
      )
      // Sync to wsiQuestions
      const selected = updated.filter(q => q.selected)
      setWsiQuestions(selected.map(({ selected, batch, ...rest }) => rest))
      return updated
    })
  }

  const updateWSIQuestionCorrectOption = (questionId: string, optionIndex: number) => {
    setWsiCandidates(prev => {
      const updated = prev.map(q => 
        q.id === questionId ? { ...q, correctOptionIndex: optionIndex } : q
      )
      // Sync to wsiQuestions
      const selected = updated.filter(q => q.selected)
      setWsiQuestions(selected.map(({ selected, batch, ...rest }) => rest))
      return updated
    })
  }

  const deleteWSIQuestion = (questionId: string) => {
    setWsiCandidates(prev => {
      const updated = prev.filter(q => q.id !== questionId)
      const selected = updated.filter(q => q.selected)
      setWsiQuestions(selected.map(({ selected, batch, ...rest }) => rest))
      return updated
    })
  }

  const addCustomQuestion = () => {
    if (!customQuestionText.trim()) return
    
    const newQuestion: WSIQuestionCandidate = {
      id: `custom-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      question: customQuestionText.trim(),
      type: customQuestionType,
      required: customQuestionRequired,
      selected: false,
      batch: wsiGenerationBatch,
      isWSI: false,
      category: 'technical'
    }
    
    setWsiCandidates(prev => [...prev, newQuestion])
    setShowCustomQuestionForm(false)
    setCustomQuestionText('')
    setCustomQuestionType('open')
    setCustomQuestionRequired(false)
  }

  // Auto-generate WSI questions when entering the stage
  useEffect(() => {
    if (currentStage === 'wsi-questions' && !wsiHasGenerated && !isGeneratingWSI) {
      // Generate technical questions first
      generateWSIQuestions(7, 'technical')
      // Also generate behavioral/fit questions (3-5 based on selected competencies)
      const enabledBehavioralCount = behavioralCompetencies.filter(c => c.enabled).length
      const behavioralQuestionCount = Math.max(3, Math.min(5, enabledBehavioralCount))
      setTimeout(() => {
        generateWSIQuestions(behavioralQuestionCount, 'behavioral')
      }, 1500) // Small delay to avoid race conditions
    }
  }, [currentStage, wsiHasGenerated, isGeneratingWSI])

  // Initialize calibration criteria from technical skills and behavioral competencies
  const initializeCalibrationCriteria = useCallback(() => {
    const criteria: {id: string; text: string; source: 'technical' | 'behavioral'}[] = []
    const baseTs = Date.now()
    
    // Add technical skills as criteria
    technicalSkills.filter(s => s.required).forEach((skill, idx) => {
      criteria.push({
        id: `tech-${baseTs}-${idx}-${skill.name.replace(/\s+/g, '')}`,
        text: `Deve ter experiência com ${skill.name} (${skill.level})`,
        source: 'technical'
      })
    })
    
    // Add behavioral competencies as criteria
    behavioralCompetencies.filter(c => c.enabled && c.weight >= 4).forEach((comp, idx) => {
      criteria.push({
        id: `behav-${baseTs}-${idx}-${comp.name.replace(/\s+/g, '')}`,
        text: `${comp.name} - ${comp.justification}`,
        source: 'behavioral'
      })
    })
    
    setCalibrationCriteria(criteria)
  }, [technicalSkills, behavioralCompetencies])

  // Generate calibration candidates from real API
  const generateCalibrationCandidates = async () => {
    setIsLoadingCalibration(true)
    
    try {
      // Build job description from collected data
      const jobDescription = `
        Cargo: ${basicInfoFields.cargo || detectedCriteria.cargo || 'Vaga'}
        Área: ${basicInfoFields.area || detectedCriteria.gestorArea || ''}
        Localidade: ${basicInfoFields.localidade || detectedCriteria.localizacao || ''}
        Modelo: ${basicInfoFields.modeloTrabalho || detectedCriteria.modeloTrabalho || ''}
        
        Habilidades técnicas: ${technicalSkills.filter(s => s.required).map(s => s.name).join(', ')}
        
        Competências comportamentais: ${behavioralCompetencies.filter(c => c.enabled).map(c => c.name).join(', ')}
      `.trim()
      
      const response = await liaApi.startCalibrationSession({
        job_vacancy_id: publishedJobId || 'temp-' + Date.now(),
        job_description: jobDescription,
        technical_skills: technicalSkills.filter(s => s.required).map(s => s.name),
        behavioral_competencies: behavioralCompetencies.filter(c => c.enabled).map(c => c.name),
        location: basicInfoFields.localidade || detectedCriteria.localizacao || undefined,
        limit: 5
      })
      
      setCalibrationSessionId(response.session_id)
      setCalibrationCandidates(response.candidates as unknown as CalibrationCandidate[])
      setIsLoadingCalibration(false)
      setShowCalibrationModal(true)
      
      // Add LIA feedback message
      const feedbackMessage: Message = {
        id: `calibration-ready-${Date.now()}`,
        role: 'assistant',
        content: `Encontrei **${response.candidates.length} perfis** na base de talentos que correspondem aos critérios da vaga!\n\nVou apresentar cada um para você avaliar. Seu feedback me ajuda a calibrar a busca e ser mais assertiva nas próximas sugestões.\n\nClique em **Aprovar** ou **Reprovar** e adicione comentários se desejar. Após 3 aprovações, inicio a busca em escala.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, feedbackMessage])
      
    } catch (error) {
      console.error('Error fetching calibration candidates:', error)
      setIsLoadingCalibration(false)
      
      // Fallback message
      const errorMessage: Message = {
        id: `calibration-error-${Date.now()}`,
        role: 'assistant',
        content: `Não consegui buscar candidatos no momento. Vamos tentar novamente em instantes.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  // Handle candidate approval
  const handleApproveCandidate = () => {
    const currentCandidate = calibrationCandidates[currentCalibrationIndex]
    if (!currentCandidate) return
    
    const newApproved = [...approvedCandidates, currentCandidate.id]
    setApprovedCandidates(newApproved)
    
    // Save feedback to backend
    if (calibrationSessionId && publishedJobId) {
      liaApi.submitCalibrationFeedback({
        session_id: calibrationSessionId,
        candidate_id: currentCandidate.id,
        job_id: publishedJobId,
        approved: true,
        lia_score: currentCandidate.overallScore,
        feedback_reason: calibrationComment || undefined
      }).catch(err => console.error('Error saving calibration feedback:', err))
    }
    
    // Save comment if any
    if (calibrationComment) {
      console.log(`Comment for ${currentCandidate.name}: ${calibrationComment}`)
      setCalibrationComment('')
    }
    
    // Check if we have 3 approved - only trigger if not already completed
    if (newApproved.length >= 3 && !postCalibrationComplete) {
      setCalibrationComplete(true)
      setShowCalibrationModal(false)
      setPostCalibrationComplete(true)
      
      // Add celebration message
      const celebrationMessage: Message = {
        id: `calibration-complete-${Date.now()}`,
        role: 'assistant',
        content: `Calibração concluída! Agora entendo melhor o perfil que você busca.\n\nEstou iniciando a busca em escala para popular o kanban da vaga. Vou te manter informado sobre os próximos passos.`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, celebrationMessage])
      
      // Stay in search-calibration stage to show next steps (unified stage)
      // setCurrentStage already set to 'search-calibration' after publish
      
      // Start real background search
      setSearchPhase('local-searching')

      const startActiveSearch = async () => {
        try {
          const jobDescription = `${basicInfoFields.cargo || detectedCriteria.cargo} - ${technicalSkills.filter(s => s.required).map(s => s.name).join(', ')}`
          
          const searchResponse = await liaApi.searchCandidatesByJobDescription(
            jobDescription,
            basicInfoFields.localidade || detectedCriteria.localizacao || undefined,
            15
          )
          
          setLocalCandidateCount(searchResponse.total_results)
          setSearchPhase('local-complete')
          
          // Add candidates to pipeline if job was created
          if (publishedJobId && searchResponse.candidates.length > 0) {
            const candidateIds = searchResponse.candidates
              .filter(c => c.id)
              .map(c => c.id as string)
            
            if (candidateIds.length > 0) {
              await liaApi.addCandidatesToPipeline({
                candidate_ids: candidateIds,
                job_vacancy_id: publishedJobId,
                source: 'calibration_search'
              })
              
              // Send notification
              await liaApi.sendNotification({
                user_id: user?.email || 'system',
                title: 'Novos candidatos encontrados',
                message: `${candidateIds.length} candidatos foram adicionados ao pipeline da vaga ${basicInfoFields.cargo || 'Nova Vaga'}`,
                notification_type: 'candidates_added',
                related_job_id: publishedJobId,
                action_url: `/jobs/${publishedJobId}/kanban`
              })
            }
          }
        } catch (error) {
          console.error('Error in active search:', error)
          setSearchPhase('local-complete')
          setLocalCandidateCount(0)
        }
      }

      startActiveSearch()
    } else if (newApproved.length < 3) {
      // Move to next candidate
      moveToNextCandidate()
    }
  }

  // Handle candidate rejection
  const handleRejectCandidate = () => {
    const currentCandidate = calibrationCandidates[currentCalibrationIndex]
    if (!currentCandidate) return
    
    const newRejected = [...rejectedCandidates, currentCandidate.id]
    setRejectedCandidates(newRejected)
    
    // Save feedback to backend
    if (calibrationSessionId && publishedJobId) {
      liaApi.submitCalibrationFeedback({
        session_id: calibrationSessionId,
        candidate_id: currentCandidate.id,
        job_id: publishedJobId,
        approved: false,
        lia_score: currentCandidate.overallScore,
        feedback_reason: calibrationComment || undefined
      }).catch(err => console.error('Error saving calibration feedback:', err))
    }
    
    // Save comment if any
    if (calibrationComment) {
      console.log(`Rejection reason for ${currentCandidate.name}: ${calibrationComment}`)
      setCalibrationComment('')
    }
    
    // Add LIA feedback about adding more candidates
    const needMore = 3 - approvedCandidates.length
    const feedbackMessage: Message = {
      id: `rejection-feedback-${Date.now()}`,
      role: 'assistant',
      content: `Entendido! Vou usar este feedback para refinar a busca.\n\nVocê ainda precisa aprovar mais **${needMore} perfil(s)** para calibração. Vou buscar mais opções que correspondam melhor aos seus critérios.`,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, feedbackMessage])
    
    // Move to next or generate more
    if (currentCalibrationIndex < calibrationCandidates.length - 1) {
      moveToNextCandidate()
    } else {
      // Need to generate more candidates
      generateMoreCalibrationCandidates()
    }
  }

  // Move to next candidate in calibration
  const moveToNextCandidate = () => {
    if (currentCalibrationIndex < calibrationCandidates.length - 1) {
      setCurrentCalibrationIndex(prev => prev + 1)
    }
  }

  // Generate more calibration candidates when needed
  const generateMoreCalibrationCandidates = async () => {
    setIsLoadingCalibration(true)
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // Add one more candidate
    const newCandidate: CalibrationCandidate = {
      id: `calib-${Date.now()}`,
      name: 'Ana Carolina Silva',
      linkedinUrl: 'https://linkedin.com/in/ana-carolina-silva',
      currentRole: 'Marketing Director',
      currentCompany: 'Nubank',
      location: 'São Paulo, Brasil',
      education: 'Fundação Getúlio Vargas (FGV)',
      highlights: [
        { icon: 'rocket', label: 'Startup Unicórnio', value: 'Cresceu time de 5 para 30 pessoas' },
        { icon: 'trophy', label: 'Premiada', value: 'Top 30 under 30 Forbes' }
      ],
      experiences: [
        { id: 'exp-1', company: 'Nubank', role: 'Marketing Director', period: 'Mar 2020 - Presente', duration: '3 anos 9 meses', skills: ['Growth Marketing', 'Brand Building', 'Team Leadership'] }
      ],
      educationHistory: [
        { id: 'edu-1', institution: 'Fundação Getúlio Vargas (FGV)', degree: 'MBA', field: 'Marketing', period: '2016 - 2018' }
      ],
      skillMap: [
        { category: 'Growth', skills: ['Growth Hacking', 'Performance Marketing', 'User Acquisition'] }
      ],
      languages: ['Portuguese', 'English', 'Spanish'],
      additionalSkills: ['Data-Driven Marketing', 'Product Marketing', 'Agile'],
      matchCriteria: [
        { id: 'match-1', criteria: 'Experiência como Marketing Manager em empresa de grande porte', isMatch: true, explanation: 'Experiência como Marketing Director em fintech unicórnio com 5000+ funcionários.', importance: 1 }
      ],
      overallScore: 90,
      averageTenure: '3 anos',
      currentTenure: '3 anos 9 meses',
      totalExperience: '10 anos'
    }
    
    setCalibrationCandidates(prev => [...prev, newCandidate])
    setCurrentCalibrationIndex(prev => prev + 1)
    setIsLoadingCalibration(false)
    
    const feedbackMessage: Message = {
      id: `more-candidates-${Date.now()}`,
      role: 'assistant',
      content: `Encontrei mais 1 perfil que corresponde aos critérios! Avalie este candidato para continuar a calibração.`,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, feedbackMessage])
  }

  // Add/Remove/Reorder calibration criteria
  const addCalibrationCriterion = (text: string) => {
    setCalibrationCriteria(prev => [
      ...prev,
      { id: `custom-${Date.now()}`, text, source: 'behavioral' }
    ])
  }

  const removeCalibrationCriterion = (id: string) => {
    setCalibrationCriteria(prev => prev.filter(c => c.id !== id))
  }

  const reorderCalibrationCriteria = (fromIndex: number, toIndex: number) => {
    setCalibrationCriteria(prev => {
      const result = [...prev]
      const [removed] = result.splice(fromIndex, 1)
      result.splice(toIndex, 0, removed)
      return result
    })
  }

  // Auto-load calibration when entering the stage (only once per stage entry)
  useEffect(() => {
    if (currentStage === 'search-calibration' && calibrationCandidates.length === 0 && !isLoadingCalibration && !hasAttemptedCalibrationGeneration) {
      setHasAttemptedCalibrationGeneration(true)
      initializeCalibrationCriteria()
      generateCalibrationCandidates()
    }
  }, [currentStage, calibrationCandidates.length, isLoadingCalibration, hasAttemptedCalibrationGeneration, initializeCalibrationCriteria])

  // Fast Track: Handle vacancy selection
  const handleFastTrackVacancySelect = async (vacancyId: string) => {
    setIsLoading(true)
    
    try {
      const vacancyDetails = await liaApi.getVacancyFullDetails(vacancyId)
      
      if (vacancyDetails) {
        setFastTrackSelectedVacancy(vacancyDetails)
        
        // Add LIA message with full summary
        const summaryMessage: Message = {
          id: `lia-summary-${Date.now()}`,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          messageType: 'vacancy-summary',
          vacancyFullDetails: vacancyDetails
        }
        setMessages(prev => [...prev, summaryMessage])
      } else {
        // Error loading vacancy
        const errorMessage: Message = {
          id: `lia-error-${Date.now()}`,
          role: 'assistant',
          content: 'Desculpe, não consegui carregar os detalhes dessa vaga. Tente selecionar outra ou digite "criar nova" para iniciar do zero.',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
        setFastTrackState('selecting')
      }
    } catch (error) {
      console.error('Failed to load vacancy details:', error)
      const errorMessage: Message = {
        id: `lia-error-${Date.now()}`,
        role: 'assistant',
        content: 'Ocorreu um erro ao carregar a vaga. Por favor, tente novamente.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }
    
    setIsLoading(false)
  }

  // Fast Track: Search previous vacancies
  const handleFastTrackSearch = async (criteria: VacancySearchCriteria) => {
    setIsSearchingVacancies(true)
    setFastTrackState('searching')
    
    try {
      const response = await liaApi.searchPreviousVacancies(criteria)
      setFastTrackSearchResults(response.vacancies || [])
      
      // Add search results message
      const searchResultsMessage: Message = {
        id: `lia-search-${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        messageType: 'vacancy-search',
        vacancySearchResults: response.vacancies || []
      }
      setMessages(prev => [...prev, searchResultsMessage])
      setFastTrackState('selecting')
    } catch (error) {
      console.error('Failed to search vacancies:', error)
      const errorMessage: Message = {
        id: `lia-error-${Date.now()}`,
        role: 'assistant',
        content: 'Não consegui encontrar vagas anteriores. Podemos criar uma nova vaga do zero. Me diga o cargo que precisa.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      setWizardMode('create_from_scratch')
    }
    
    setIsSearchingVacancies(false)
  }

  // Fast Track: Publish vacancy with adjustments
  const handleFastTrackPublish = async () => {
    if (!fastTrackSelectedVacancy) return
    
    setIsLoading(true)
    setFastTrackState('publishing')
    
    try {
      const result = await liaApi.publishFastTrackVacancy(fastTrackSelectedVacancy.id, fastTrackAdjustments)
      
      if (result.success) {
        const modifiedFields = Object.keys(fastTrackAdjustments).filter(
          key => fastTrackAdjustments[key as keyof VacancyAdjustments] !== undefined
        )
        const tenantId = user?.company || 'default'
        const newJobId = result.vacancy_id
        if (newJobId && newJobId !== fastTrackSelectedVacancy.id) {
          liaApi.recordFastTrackUsage({
            company_id: tenantId,
            source_job_id: fastTrackSelectedVacancy.id,
            new_job_id: newJobId,
            modified_fields: modifiedFields,
            was_published: true
          }).catch(err => console.error('Non-blocking: Fast Track usage recording failed:', err))
        } else {
          console.warn('Fast Track usage not recorded: new_job_id not returned or same as source')
        }
        
        const successMessage: Message = {
          id: `lia-success-${Date.now()}`,
          role: 'assistant',
          content: `🎉 **Vaga publicada com sucesso!**\n\nA vaga "${fastTrackSelectedVacancy.title}" está ativa e já está recebendo candidatos.\n\nVocê pode acompanhar o pipeline de candidatos no Kanban ou me pedir para buscar candidatos compatíveis.`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, successMessage])
        setFastTrackState('completed')
        onJobCreated?.()
      } else {
        const errorMessage: Message = {
          id: `lia-error-${Date.now()}`,
          role: 'assistant',
          content: `Não foi possível publicar a vaga: ${result.message}. Por favor, tente novamente.`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
        setFastTrackState('reviewing')
      }
    } catch (error) {
      console.error('Failed to publish vacancy:', error)
      const errorMessage: Message = {
        id: `lia-error-${Date.now()}`,
        role: 'assistant',
        content: 'Ocorreu um erro ao publicar a vaga. Por favor, tente novamente.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      setFastTrackState('reviewing')
    }
    
    setIsLoading(false)
  }

  // Fast Track: Parse user adjustment request
  const parseFastTrackAdjustment = (content: string): VacancyAdjustments | null => {
    const adjustments: VacancyAdjustments = {}
    const lowerContent = content.toLowerCase()
    
    // Parse salary adjustments
    const salaryMatch = content.match(/sal[aá]rio\s*(?:para|de|:)?\s*(\d+(?:[.,]\d+)?)\s*(?:a|até|-|a)\s*(\d+(?:[.,]\d+)?)/i)
    if (salaryMatch) {
      adjustments.salary_min = parseFloat(salaryMatch[1].replace(',', '.')) * 1000
      adjustments.salary_max = parseFloat(salaryMatch[2].replace(',', '.')) * 1000
    }
    
    // Parse work model
    if (lowerContent.includes('remoto')) {
      adjustments.work_model = 'remote'
    } else if (lowerContent.includes('híbrido') || lowerContent.includes('hibrido')) {
      adjustments.work_model = 'hybrid'
    } else if (lowerContent.includes('presencial')) {
      adjustments.work_model = 'onsite'
    }
    
    // Parse location
    const locationMatch = content.match(/(?:local|localização|cidade)\s*(?:para|:)?\s*([A-Za-zÀ-ÿ\s]+)/i)
    if (locationMatch) {
      adjustments.location = locationMatch[1].trim()
    }
    
    return Object.keys(adjustments).length > 0 ? adjustments : null
  }

  // Build collected data object for orchestrator
  const buildCollectedData = useCallback(() => {
    return {
      title: basicInfoFields.cargo || detectedCriteria.cargo || null,
      department: basicInfoFields.area || detectedCriteria.departamento || null,
      seniority_level: detectedCriteria.senioridadeIdiomas || null,
      work_model: basicInfoFields.modeloTrabalho || detectedCriteria.modeloTrabalho || null,
      location: basicInfoFields.localidade || detectedCriteria.localizacao || null,
      manager: basicInfoFields.gestor || detectedCriteria.gestorArea || null,
      salary_min: salaryInfo.minSalary ? parseInt(salaryInfo.minSalary) : null,
      salary_max: salaryInfo.maxSalary ? parseInt(salaryInfo.maxSalary) : null,
      technical_skills: technicalSkills.filter(s => s.required).map(s => s.name),
      behavioral_competencies: behavioralCompetencies.filter(c => c.enabled).map(c => c.name),
      screening_questions: wsiCandidates.filter(q => q.selected).map(q => ({
        question: q.question,
        category: q.category,
        expected_answer: q.expectedAnswer,
        weight: 5,
        type: q.type
      }))
    }
  }, [basicInfoFields, detectedCriteria, salaryInfo, technicalSkills, behavioralCompetencies, wsiCandidates])

  // Process orchestrator response and apply actions from smart-orchestrate endpoint
  const processOrchestratorResponse = useCallback(async (
    orchestratorResult: WizardOrchestratorResponse,
    processingMessageId: string
  ) => {
    console.log('[SmartOrchestrate] Processing response:', {
      success: orchestratorResult.success,
      auto_transition: orchestratorResult.auto_transition,
      next_stage: orchestratorResult.next_stage,
      detected_criteria: orchestratorResult.detected_criteria
    })
    
    // Use new response format from smart-orchestrate endpoint
    const liaMessage = orchestratorResult.lia_message || orchestratorResult.response || ''
    const detectedCriteriaFromBackend = orchestratorResult.detected_criteria || {}
    const nextStage = orchestratorResult.next_stage
    const autoTransition = orchestratorResult.auto_transition
    const toolResults = orchestratorResult.tool_results || []
    
    // Update processing message
    setMessages(msgs => msgs.map(m => 
      m.id === processingMessageId 
        ? { ...m, content: '✅ Resposta da LIA', processingState: 'completed' as const }
        : m
    ))
    
    // Apply detected_criteria to form fields
    if (detectedCriteriaFromBackend && Object.keys(detectedCriteriaFromBackend).length > 0) {
      console.log('[SmartOrchestrate] Applying detected criteria:', detectedCriteriaFromBackend)
      
      // Job title / cargo
      if (detectedCriteriaFromBackend.job_title || detectedCriteriaFromBackend.title || detectedCriteriaFromBackend.cargo) {
        const title = detectedCriteriaFromBackend.job_title || detectedCriteriaFromBackend.title || detectedCriteriaFromBackend.cargo
        setBasicInfoFields(prev => ({ ...prev, cargo: title }))
        setDetectedCriteria(prev => ({ ...prev, cargo: title }))
        highlightField('cargo')
      }
      
      // Department / area
      if (detectedCriteriaFromBackend.department || detectedCriteriaFromBackend.area) {
        const dept = detectedCriteriaFromBackend.department || detectedCriteriaFromBackend.area
        setBasicInfoFields(prev => ({ ...prev, area: dept }))
        setDetectedCriteria(prev => ({ ...prev, departamento: dept }))
        highlightField('departamento')
      }
      
      // Seniority
      if (detectedCriteriaFromBackend.seniority || detectedCriteriaFromBackend.seniority_level) {
        const seniority = detectedCriteriaFromBackend.seniority || detectedCriteriaFromBackend.seniority_level
        setDetectedCriteria(prev => ({ ...prev, senioridadeIdiomas: seniority }))
        highlightField('senioridade')
      }
      
      // Work model
      if (detectedCriteriaFromBackend.work_model || detectedCriteriaFromBackend.modelo_trabalho) {
        const workModel = detectedCriteriaFromBackend.work_model || detectedCriteriaFromBackend.modelo_trabalho
        setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: workModel }))
        setDetectedCriteria(prev => ({ ...prev, modeloTrabalho: workModel }))
        highlightField('modeloTrabalho')
      }
      
      // Location
      if (detectedCriteriaFromBackend.location || detectedCriteriaFromBackend.localidade) {
        const location = detectedCriteriaFromBackend.location || detectedCriteriaFromBackend.localidade
        setBasicInfoFields(prev => ({ ...prev, localidade: location }))
        setDetectedCriteria(prev => ({ ...prev, localizacao: location }))
        highlightField('localizacao')
      }
      
      // Manager / Gestor
      if (detectedCriteriaFromBackend.manager || detectedCriteriaFromBackend.gestor) {
        const manager = detectedCriteriaFromBackend.manager || detectedCriteriaFromBackend.gestor
        setBasicInfoFields(prev => ({ ...prev, gestor: manager }))
        setDetectedCriteria(prev => ({ ...prev, gestorArea: manager }))
        highlightField('gestor')
      }
      
      // Salary
      if (detectedCriteriaFromBackend.salary_min || detectedCriteriaFromBackend.min_salary) {
        const minSalary = detectedCriteriaFromBackend.salary_min || detectedCriteriaFromBackend.min_salary
        setSalaryInfo(prev => ({ ...prev, minSalary: minSalary.toString() }))
        highlightField('minSalary')
      }
      if (detectedCriteriaFromBackend.salary_max || detectedCriteriaFromBackend.max_salary) {
        const maxSalary = detectedCriteriaFromBackend.salary_max || detectedCriteriaFromBackend.max_salary
        setSalaryInfo(prev => ({ ...prev, maxSalary: maxSalary.toString() }))
        highlightField('maxSalary')
      }

      if (currentStage === 'salary') {
        const salaryDetectedFields: Array<{ label: string; value: string; confidence?: "high" | "medium" | "low" }> = []
        const detectedMin = detectedCriteriaFromBackend.salary_min || detectedCriteriaFromBackend.min_salary
        const detectedMax = detectedCriteriaFromBackend.salary_max || detectedCriteriaFromBackend.max_salary
        if (detectedMin) salaryDetectedFields.push({ label: "Salário Mínimo", value: `R$ ${detectedMin}`, confidence: "high" })
        if (detectedMax) salaryDetectedFields.push({ label: "Salário Máximo", value: `R$ ${detectedMax}`, confidence: "high" })
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
          setMessages(prev => [...prev, salaryDetectedMsg])
        }
      }
      
      // Technical skills
      if (detectedCriteriaFromBackend.technical_skills && Array.isArray(detectedCriteriaFromBackend.technical_skills)) {
        const newSkills = detectedCriteriaFromBackend.technical_skills as string[]
        newSkills.forEach((skill: string, index: number) => {
          if (!technicalSkills.find(s => s.name.toLowerCase() === skill.toLowerCase())) {
            setTechnicalSkills(prev => [
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
          highlightField('skills')
        }
      }
      
      // Behavioral competencies
      if (detectedCriteriaFromBackend.behavioral_competencies && Array.isArray(detectedCriteriaFromBackend.behavioral_competencies)) {
        const newComps = detectedCriteriaFromBackend.behavioral_competencies as string[]
        newComps.forEach((comp: string) => {
          const existing = behavioralCompetencies.find(c => c.name.toLowerCase() === comp.toLowerCase())
          if (existing && !existing.enabled) {
            setBehavioralCompetencies(prev => prev.map(c => 
              c.name.toLowerCase() === comp.toLowerCase() ? { ...c, enabled: true } : c
            ))
          }
        })
        if (newComps.length > 0) {
          highlightField('competencias')
        }
      }

      if (currentStage === 'competencies') {
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
          setMessages(prev => [...prev, compDetectedMsg])
        }
      }
      
      // Affirmative action
      if (detectedCriteriaFromBackend.is_affirmative !== undefined) {
        setDetectedCriteria(prev => ({ ...prev, isAffirmative: detectedCriteriaFromBackend.is_affirmative }))
        setJobConfig(prev => ({ ...prev, isAffirmative: detectedCriteriaFromBackend.is_affirmative }))
      }
      
      // Responsibilities / Responsabilidades
      if (detectedCriteriaFromBackend.responsibilities && Array.isArray(detectedCriteriaFromBackend.responsibilities)) {
        const newResponsibilities = detectedCriteriaFromBackend.responsibilities as string[]
        if (newResponsibilities.length > 0) {
          setDetectedCriteria(prev => ({
            ...prev,
            responsabilidades: [...new Set([...(prev.responsabilidades || []), ...newResponsibilities])]
          }))
          highlightField('responsabilidades')
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
          if (!technicalSkills.find(s => s.name.toLowerCase() === skill.toLowerCase())) {
            setTechnicalSkills(prev => [
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
          setDetectedCriteria(prev => ({
            ...prev,
            competenciasTecnicas: deduplicateCaseInsensitive(prev.competenciasTecnicas || [], newSkills)
          }))
          highlightField('skills')
        }
      }
      
      // Soft skills (also maps to behavioral competencies display)
      if (detectedCriteriaFromBackend.soft_skills && Array.isArray(detectedCriteriaFromBackend.soft_skills)) {
        const newComps = detectedCriteriaFromBackend.soft_skills as string[]
        if (newComps.length > 0) {
          setDetectedCriteria(prev => ({
            ...prev,
            competenciasComportamentais: deduplicateCaseInsensitive(prev.competenciasComportamentais || [], newComps)
          }))
          highlightField('competencias')
        }
      }
    }
    
    // Process tool_results if present (e.g., salary benchmark, skills suggestions)
    if (toolResults.length > 0) {
      console.log('[SmartOrchestrate] Processing tool results:', toolResults)
      toolResults.forEach((toolResult: any) => {
        if (toolResult.tool === 'salary_benchmark' && toolResult.result) {
          setCompensationAnalysis(toolResult.result)
        }
        if (toolResult.tool === 'skills_suggestion' && toolResult.result?.skills) {
          const suggestedSkills = toolResult.result.skills
          suggestedSkills.forEach((skill: any, index: number) => {
            if (!technicalSkills.find(s => s.name.toLowerCase() === skill.name?.toLowerCase())) {
              setTechnicalSkills(prev => [
                ...prev,
                {
                  id: `tool-skill-${Date.now()}-${index}`,
                  name: skill.name,
                  level: skill.level || 'Intermediário',
                  required: skill.required ?? true,
                  category: skill.category || 'tool',
                  weight: skill.weight || 3
                }
              ])
            }
          })
        }
        // Process JD enrichment data
        if (toolResult.tool === 'generate_enriched_jd' && toolResult.result) {
          console.log('[SmartOrchestrate] Processing enriched JD data:', toolResult.result)
          const enrichmentResult = toolResult.result
          // Map backend response to EnrichedJDData format
          const enrichedData: EnrichedJDData = {
            sections: enrichmentResult.sections || [],
            compensation: enrichmentResult.compensation,
            wsiQualityScore: enrichmentResult.wsi_quality_score ?? enrichmentResult.wsiQualityScore ?? 0,
            overallCompleteness: enrichmentResult.overall_completeness ?? enrichmentResult.overallCompleteness ?? 0,
            totalSuggestions: enrichmentResult.total_suggestions ?? enrichmentResult.totalSuggestions ?? 0
          }
          setEnrichedJDData(enrichedData)
          setIsLoadingEnrichment(false)
        }
      })
    }
    
    // Handle action results from WizardActionExecutor
    if (orchestratorResult.action_executed && orchestratorResult.action_type) {
      console.log('[SmartOrchestrate] Action executed:', orchestratorResult.action_type, orchestratorResult.action_result)
      
      // Apply draft_updates to form fields if present
      if (orchestratorResult.draft_updates && Object.keys(orchestratorResult.draft_updates).length > 0) {
        const updates = orchestratorResult.draft_updates as Record<string, any>
        if (updates.cargo || updates.job_title || updates.title) {
          const title = updates.cargo || updates.job_title || updates.title
          setBasicInfoFields(prev => ({ ...prev, cargo: title }))
          highlightField('cargo')
        }
        if (updates.area || updates.department) {
          const dept = updates.area || updates.department
          setBasicInfoFields(prev => ({ ...prev, area: dept }))
          highlightField('departamento')
        }
        if (updates.localidade || updates.location) {
          const location = updates.localidade || updates.location
          setBasicInfoFields(prev => ({ ...prev, localidade: location }))
          highlightField('localizacao')
        }
        if (updates.modeloTrabalho || updates.work_model) {
          const workModel = updates.modeloTrabalho || updates.work_model
          setBasicInfoFields(prev => ({ ...prev, modeloTrabalho: workModel }))
          highlightField('modeloTrabalho')
        }
        if (updates.gestor || updates.manager) {
          const manager = updates.gestor || updates.manager
          setBasicInfoFields(prev => ({ ...prev, gestor: manager }))
          highlightField('gestor')
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
      
      if (conversationMemory.conversationId) {
        conversationMemory.addMessage('assistant', liaMessage).catch(() => {})
      }
      
      setTimeout(() => {
        setMessages(prev => [...prev, actionResultMsg])
        typeText(liaMessage, actionResultMsg.id)
      }, 200)
      
      return
    }
    
    // Handle automatic stage transition
    if (autoTransition && nextStage) {
      console.log('[SmartOrchestrate] Auto-transition to stage:', nextStage)
      const frontendStage = getFrontendStageFromBackend(nextStage)
      if (frontendStage && frontendStage !== currentStage) {
        console.log('[SmartOrchestrate] Mapped to frontend stage:', frontendStage)
        setTimeout(() => {
          setCurrentStage(frontendStage as WizardStage)
        }, 1500)
      }
    }
    
    // Handle awaiting_confirmation from backend - show proactive message asking to advance
    const awaitingConfirmation = orchestratorResult.awaiting_confirmation
    const shouldShowProactiveConfirmation = awaitingConfirmation && 
      currentStage === 'input-evaluation' && 
      !awaitingStageAdvanceConfirmation && // Not already awaiting confirmation
      Object.keys(detectedCriteriaFromBackend).length > 0 // Has detected criteria
    
    if (shouldShowProactiveConfirmation) {
      console.log('[SmartOrchestrate] Backend awaiting confirmation for input-evaluation, showing proactive message')
      
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
      if (techSkills?.length > 0) detectedFields.push(`Skills Técnicas: **${techSkills.slice(0, 3).join(', ')}**`)
      if (salaryMin && salaryMax) {
        const minFormatted = typeof salaryMin === 'number' ? salaryMin.toLocaleString('pt-BR') : salaryMin
        const maxFormatted = typeof salaryMax === 'number' ? salaryMax.toLocaleString('pt-BR') : salaryMax
        detectedFields.push(`Faixa Salarial: **R$ ${minFormatted} - R$ ${maxFormatted}**`)
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
      if (techSkills?.length > 0) detectedFieldsStructured.push({ label: "Skills Técnicas", value: techSkills.slice(0, 5).join(", "), confidence: "high" })
      if (salaryMin && salaryMax) {
        const minF = typeof salaryMin === 'number' ? salaryMin.toLocaleString('pt-BR') : salaryMin
        const maxF = typeof salaryMax === 'number' ? salaryMax.toLocaleString('pt-BR') : salaryMax
        detectedFieldsStructured.push({ label: "Faixa Salarial", value: `R$ ${minF} - R$ ${maxF}`, confidence: "medium" })
      }

      // Set awaiting confirmation state
      setAwaitingStageAdvanceConfirmation('jd-enrichment')
      
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
      
      if (conversationMemory.conversationId) {
        conversationMemory.addMessage('assistant', enhancedMessage).catch(() => {})
      }
      
      setTimeout(() => {
        setMessages(prev => [...prev, proactiveMsg])
        typeText(enhancedMessage, proactiveMsg.id)
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
    if (conversationMemory.conversationId) {
      conversationMemory.addMessage('assistant', liaMessage).catch(() => {})
    }
    
    setTimeout(() => {
      setMessages(prev => [...prev, assistantMessage])
      typeText(liaMessage, assistantMessage.id)
    }, 200)
  }, [typeText, conversationMemory.conversationId, highlightField, currentStage, technicalSkills, behavioralCompetencies, setJobConfig, inputEvaluationStageCompletionShown])

  // Fast Track: Detect user intent from message
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
    if (fastTrackState === 'collecting_criteria' || fastTrackState === 'initial') {
      return 'criteria'
    }
    
    return null
  }

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

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isLoading || isTypingEffect) return
    
    // DEBUG: Log message flow state
    console.log('[DEBUG handleSendMessage] Message received:', content)
    console.log('[DEBUG handleSendMessage] State:', {
      awaitingDraftChoice,
      awaitingCalibrationChoice,
      hasPendingTool: toolCalling.hasPendingTool,
      awaitingWSIRegenerationConfirmation,
      awaitingSensitiveFieldsConfirmation,
      fastTrackHasSuggestions: fastTrack?.hasSuggestions,
      isInJobCreationMode,
      currentStage
    })

    // Detect context switch intent from message
    const detectedContext = contextSwitching.detectContextFromMessage(content)
    if (detectedContext && detectedContext !== contextSwitching.currentContext) {
      // Save current wizard state before switching
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
      
      // Switch context
      if (detectedContext === 'wizard') {
        contextSwitching.switchToWizard()
      } else if (detectedContext === 'fast_track') {
        contextSwitching.switchToFastTrack()
      } else if (detectedContext === 'general') {
        contextSwitching.switchToGeneral()
      }
    }

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue("")

    // Check if we're awaiting stage advance confirmation (conversational flow)
    if (awaitingStageAdvanceConfirmation) {
      console.log('[DEBUG handleSendMessage] INTERCEPTED by awaitingStageAdvanceConfirmation:', awaitingStageAdvanceConfirmation)
      const lowerMessage = content.toLowerCase().trim()
      const originalMessage = content.trim()
      
      // Patterns that indicate adjustment requests (NOT confirmations)
      // These keywords mean the user wants to change something, not confirm
      const adjustmentPatterns = [
        'ajust', 'alter', 'mud', 'troc', 'edit', 'corrig', 'revis',
        'quero', 'preciso', 'falta', 'adiciona', 'remov', 'exclui',
        'não', 'nao', 'errad', 'outr', 'diferent'
      ]
      
      const isAdjustmentRequest = adjustmentPatterns.some(p => lowerMessage.includes(p))
      
      // Short standalone confirmations (regex patterns for exact/near-exact matches)
      // These only match when the ENTIRE message is a confirmation phrase
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
      
      // Check if it's a short standalone confirmation AND not an adjustment request
      const isShortMessage = originalMessage.length <= 30
      const isStandaloneConfirmation = shortConfirmPatterns.some(p => p.test(lowerMessage))
      
      // Only treat as confirmation if:
      // 1. Short message AND matches standalone pattern AND no adjustment keywords
      const isClearConfirmation = (isShortMessage && isStandaloneConfirmation && !isAdjustmentRequest)
      
      if (isClearConfirmation) {
        console.log('[ProactiveConfirmation] Detected clear confirmation:', lowerMessage)
        
        // Special handling for calibration completion (not a stage transition)
        if (awaitingStageAdvanceConfirmation === 'calibration-complete') {
          setCalibrationComplete(true)
          const totalEvaluated = approvedCandidates.length + rejectedCandidates.length
          const completeMsg: Message = {
            id: `calibration-finished-${Date.now()}`,
            role: 'assistant',
            content: `🎯 **Calibração finalizada!**

O modelo de busca foi ajustado com base nas suas ${totalEvaluated} avaliações. Agora as próximas buscas vão priorizar candidatos similares aos que você aprovou.`,
            timestamp: new Date(),
          }
          setMessages(prev => [...prev, completeMsg])
          setAwaitingStageAdvanceConfirmation(null)
          return // Don't process further
        }
        
        // Advance to next stage (normal stage transitions)
        const nextStage = awaitingStageAdvanceConfirmation
        
        // Special handling for jd-enrichment: call smart-orchestrate to get enriched data
        if (nextStage === 'jd-enrichment') {
          console.log('[ProactiveConfirmation] Transitioning to jd-enrichment, calling smart-orchestrate')
          setAwaitingStageAdvanceConfirmation(null)
          setIsLoadingEnrichment(true)
          
          // Show loading message
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
          
          // Call smart-orchestrate with CONFIRM intent to trigger generate_enriched_jd
          const collectedData = buildCollectedData()
          orchestrateWizardMessage({
            message: content, // User's confirmation message
            current_stage: 'input-evaluation', // Coming from input-evaluation
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
            
            // Show error message
            const errorMsg: Message = {
              id: `jd-enrichment-error-${Date.now()}`,
              role: 'assistant',
              content: '❌ Não consegui buscar as sugestões de mercado. Você pode continuar preenchendo manualmente ou tentar novamente.',
              timestamp: new Date()
            }
            setMessages(prev => [...prev, errorMsg])
          })
          return
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
        return // Don't process further
      }
      
      // Not a clear confirmation - could be adjustment request or ambiguous
      // Clear the awaiting state and let the message be processed by smart-orchestrate
      console.log('[ProactiveConfirmation] Not a clear confirmation, routing to backend:', lowerMessage)
      setAwaitingStageAdvanceConfirmation(null)
      // Continue to normal message processing...
    }

    // Handle draft choice if awaiting user decision
    if (awaitingDraftChoice) {
      console.log('[DEBUG handleSendMessage] INTERCEPTED by awaitingDraftChoice')
      const lowerContent = content.toLowerCase().trim()
      
      // Detect "continuar" intent
      if (lowerContent.includes('continuar') || lowerContent.includes('retomar') || 
          lowerContent.includes('prosseguir') || lowerContent.includes('sim')) {
        // Apply the pending draft and show appropriate stage message
        applyPendingDraft()
        
        // Get current stage message
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
        return
      }
      
      // Detect "começar do zero" intent
      if (lowerContent.includes('zero') || lowerContent.includes('nova') || 
          lowerContent.includes('novo') || lowerContent.includes('descartar') ||
          lowerContent.includes('limpar') || lowerContent.includes('recomeçar')) {
        // Clear the draft and start fresh
        clearWizardDraft()
        setPendingDraftData(null)
        setAwaitingDraftChoice(false)
        setHasAppliedRestoredDraft(true)
        
        // Reset all wizard state
        setCurrentStage('input-evaluation')
        setBasicInfoFields({ cargo: '', area: '', gestor: '', localidade: '', modeloTrabalho: '', tipoContrato: '' })
        setSalaryInfo({ minSalary: '', maxSalary: '', minBonus: '', maxBonus: '', bonusCriteria: '', benefits: [] })
        setTechnicalSkills([])
        setBehavioralCompetencies([])
        setWsiCandidates([])
        setGeneratedJobDescription('')
        
        // After clearing draft, ask user to describe the job (NOT repeat greeting with options)
        const liaMessage: Message = {
          id: `lia-fresh-start-${Date.now()}`,
          role: 'assistant',
          content: 'Perfeito! Vamos criar uma nova vaga do zero. 🆕\n\nMe conte sobre a posição que você precisa preencher. Pode descrever livremente - cargo, responsabilidades, requisitos, área, modelo de trabalho... Eu vou extrair as informações automaticamente.\n\n💡 **Dica:** Quanto mais detalhes você fornecer, mais precisa será a vaga gerada.',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, liaMessage])
        setIsPanelOpen(true)
        setWizardMode('create_from_scratch')
        return
      }
      
      // User didn't clearly choose - ask again
      const clarifyMessage: Message = {
        id: `lia-clarify-${Date.now()}`,
        role: 'assistant',
        content: 'Não entendi sua escolha. Por favor, digite **"continuar"** para retomar o rascunho, ou **"começar do zero"** para descartar e criar uma nova vaga.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, clarifyMessage])
      return
    }

    // Handle calibration choice after job publish
    if (awaitingCalibrationChoice && currentStage === 'search-calibration') {
      console.log('[DEBUG handleSendMessage] INTERCEPTED by awaitingCalibrationChoice')
      const lowerContent = content.toLowerCase().trim()
      
      // Explicit patterns for "calibrate now" - requires clear calibration intent
      const calibratePatterns = [
        'calibrar', 'calibração', 'calibracao', 
        'avaliar candidato', 'avaliar perfis', 
        'mostrar candidato', 'mostra candidato', 'ver candidato', 'ver perfis',
        'quero calibrar', 'calibrar agora', 'mostrar perfis', 'avaliar agora'
      ]
      
      // Explicit patterns for "skip to kanban" - requires clear skip intent
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
      
      // Handle clear "não" as skip
      if ((lowerContent === 'não' || lowerContent === 'nao') && !hasCalibrationIntent) {
        hasSkipIntent = true
      }
      
      // Explicit rejection of calibration
      const explicitRejectCalibration = lowerContent.includes('não') && lowerContent.includes('calibr')
      
      // Detect conflict: has both calibration AND skip intent (e.g., "calibrar depois")
      const hasConflictingIntent = hasCalibrationIntent && hasSkipIntent
      
      if (hasConflictingIntent) {
        // Ask for clarification when intent is ambiguous - keep awaiting state true
        setAwaitingCalibrationChoice(true)
        const conflictClarifyMessage: Message = {
          id: `lia-clarify-conflict-${Date.now()}`,
          role: 'assistant',
          content: `Percebi que você mencionou calibração mas também parece querer deixar para depois. Para confirmar:

• **"Calibrar agora"** - mostro 5 perfis para avaliar rapidamente
• **"Ir pro kanban"** - adiciono candidatos e você avalia lá

Qual prefere?`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, conflictClarifyMessage])
        return
      }
      
      if (hasSkipIntent || explicitRejectCalibration) {
        // Skip calibration - go directly to kanban
        setAwaitingCalibrationChoice(false)
        const skipMessage: Message = {
          id: `lia-skip-calibration-${Date.now()}`,
          role: 'assistant',
          content: `Perfeito! Os candidatos já estão sendo adicionados ao Kanban da vaga. 🎯

**Aprendizado Implícito Ativado:**
Quando você mover candidatos no Kanban (aprovar → entrevista, reprovar → descartado), eu automaticamente aprendo suas preferências e ajusto as futuras sugestões.

📊 **Candidatos encontrados:** ${localCandidateCount > 0 ? localCandidateCount : 'Buscando...'}

Clique no botão abaixo para ir ao Kanban da vaga.`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, skipMessage])
        setCalibrationComplete(true)
        return
      }
      
      if (hasCalibrationIntent && !hasSkipIntent) {
        // Start explicit calibration flow
        setAwaitingCalibrationChoice(false)
        const calibrateMessage: Message = {
          id: `lia-start-calibration-${Date.now()}`,
          role: 'assistant',
          content: `Ótimo! Vou te mostrar 5 perfis para você avaliar rapidamente. 🔍

Basta indicar se cada candidato é **aderente** ou **não aderente** ao perfil da vaga.

Carregando os primeiros perfis...`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, calibrateMessage])
        setShowCalibrationModal(true)
        return
      }
      
      // Ambiguous response (like "sim", "ok", "pode") - ask for clarification
      const ambiguousAffirmative = ['sim', 'ok', 'pode', 'vamos', 'bora', 'claro', 'beleza'].some(p => lowerContent === p || lowerContent.startsWith(p + ' '))
      if (ambiguousAffirmative) {
        const clarifyAmbiguousMessage: Message = {
          id: `lia-clarify-ambiguous-${Date.now()}`,
          role: 'assistant',
          content: `Ótimo! Só para confirmar, você quer:
          
• **"Calibrar"** - eu mostro 5 perfis para você avaliar rapidamente
• **"Ir pro kanban"** - eu adiciono os candidatos e você avalia lá

Qual prefere?`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, clarifyAmbiguousMessage])
        return
      }
      
      // Completely unclear - ask again
      const clarifyCalibrationMessage: Message = {
        id: `lia-clarify-calibration-${Date.now()}`,
        role: 'assistant',
        content: 'Não entendi sua preferência. Você quer **"calibrar"** (avaliar 5 perfis) ou **"ir pro kanban"** (aprendizado natural)?',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, clarifyCalibrationMessage])
      return
    }

    // Handle pending tool call confirmation
    if (toolCalling.hasPendingTool && activeToolConfirmationMessageId) {
      console.log('[DEBUG handleSendMessage] INTERCEPTED by hasPendingTool')
      const lowerContent = content.toLowerCase().trim()
      
      const affirmativePatterns = ['sim', 'pode', 'ok', 'claro', 'confirmo', 'confirma', 'prossegue', 'prosseguir', 'fazer', 'execute', 'aceito', 'pode ser', 'beleza', 'manda', 'vai', 'bora']
      const negativePatterns = ['não', 'nao', 'cancela', 'cancelar', 'deixa', 'para', 'espera', 'aguarda', 'negativo', 'desisto']
      
      const isAffirmative = affirmativePatterns.some(p => lowerContent.includes(p))
      const isNegative = negativePatterns.some(p => lowerContent.includes(p))
      
      if (isAffirmative && !isNegative) {
        setIsLoading(true)
        
        try {
          const result = await toolCalling.confirmToolCall()
          
          // Add execution feedback message
          const feedbackMessage: Message = {
            id: `tool-feedback-${Date.now()}`,
            role: 'assistant',
            content: result.success 
              ? `✅ ${result.message}` 
              : `❌ ${result.error || result.message}`,
            timestamp: new Date(),
            messageType: 'tool-execution-feedback',
            toolExecutionResult: result,
          }
          setMessages(prev => [...prev, feedbackMessage])
          setActiveToolConfirmationMessageId(null)
          
          if (result.success) {
            // Add a follow-up message from LIA
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
        return
      } else if (isNegative) {
        toolCalling.cancelToolCall()
        setActiveToolConfirmationMessageId(null)
        
        const cancelMessage: Message = {
          id: `tool-cancel-${Date.now()}`,
          role: 'assistant',
          content: 'Tudo bem, cancelei a ação. Se precisar de algo mais, é só me avisar!',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, cancelMessage])
        return
      }
      // If unclear, let the message flow through to the orchestrator
    }

    // Handle WSI regeneration confirmation
    if (isInJobCreationMode && awaitingWSIRegenerationConfirmation) {
      console.log('[DEBUG handleSendMessage] INTERCEPTED by awaitingWSIRegenerationConfirmation')
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
          
          // Build current questions from wsiCandidates
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
            
            // Analytics: Track WSI regeneration
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
        return
      } else if (isNegative) {
        setAwaitingWSIRegenerationConfirmation(false)
        const keepMessage: Message = {
          id: `wsi-keep-${Date.now()}`,
          role: 'assistant',
          content: 'Tudo bem! Manterei as perguntas WSI atuais. Se mudar de ideia, é só me avisar.',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, keepMessage])
        return
      }
    }

    // Handle sensitive fields confirmation after Fast Track
    if (isInJobCreationMode && awaitingSensitiveFieldsConfirmation) {
      console.log('[DEBUG handleSendMessage] INTERCEPTED by awaitingSensitiveFieldsConfirmation')
      const lowerContent = content.toLowerCase().trim()
      
      // Extract gestor from response
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
      
      // Check for "mesmo da anterior" or similar
      if (lowerContent.includes('mesmo') || lowerContent.includes('anterior') || lowerContent.includes('igual')) {
        if (fastTrackAppliedData?.gestor) {
          extractedGestor = fastTrackAppliedData.gestor
        }
      }
      
      // Extract location from response
      let extractedLocation = ''
      const locationPatterns = [
        /(?:localiza[çc][aã]o|cidade|local|onde)[:\s]+([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s\-]+?)(?:\s*[,.]|$)/i,
        /(?:em|para)\s+([A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s\-]+?)(?:\s*[,.]|$)/i,
      ]
      
      // Check for confirmation of previous location
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
      
      // If no location extracted, keep the original
      if (!extractedLocation && fastTrackAppliedData?.localidade) {
        extractedLocation = fastTrackAppliedData.localidade
      }
      
      // Extract affirmative action from response
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
            if (match[1]) {
              affirmativeCriteria = match[1].trim()
            }
            break
          }
        }
      }
      
      // Update fields with extracted data
      if (extractedGestor) {
        setBasicInfoFields(prev => ({ ...prev, gestor: extractedGestor }))
      }
      if (extractedLocation) {
        setBasicInfoFields(prev => ({ ...prev, localidade: extractedLocation }))
      }
      if (isAffirmativeAction) {
        setJobConfig(prev => ({ ...prev, isAffirmative: true }))
        if (affirmativeCriteria) {
          setDetectedCriteria(prev => ({ ...prev, affirmativeCriteriaPrimary: affirmativeCriteria }))
        }
      } else if (isNegativeAffirmative) {
        setJobConfig(prev => ({ ...prev, isAffirmative: false }))
      }
      
      // Clear state and proceed to review
      setAwaitingSensitiveFieldsConfirmation(false)
      setFastTrackAppliedData(null)
      
      // Build confirmation response
      const confirmationParts: string[] = []
      if (extractedGestor) {
        confirmationParts.push(`gestor: **${extractedGestor}**`)
      }
      if (extractedLocation) {
        confirmationParts.push(`localização: **${extractedLocation}**`)
      }
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
      
      // Now go to review stage
      setCurrentStage('review-publish')
      setWizardMode('create_from_scratch')
      
      return
    }

    // Handle Fast Track semantic suggestions (new hook)
    // Accept responses when suggestions exist - simple gate on hasSuggestions
    if (isInJobCreationMode && fastTrack.hasSuggestions) {
      console.log('[DEBUG handleSendMessage] INTERCEPTED by fastTrack.hasSuggestions')
      const lowerContent = content.toLowerCase().trim()
      
      // Detect specific selection (number or ordinal)
      const numberMatch = lowerContent.match(/\b([1-5])\b|primeira|segunda|terceira|quarta|quinta/)
      const hasExplicitSelection = numberMatch !== null
      
      // Detect affirmative response - user wants to use a suggestion
      const affirmativePatterns = [
        'sim', 'usa', 'usar', 'ok', 'vamos', 'pode ser', 'pode', 'essa', 'essa mesmo',
        'top', 'bora', 'beleza', 'perfeito', 'ótimo', 'legal', 'certo', 'fechou'
      ]
      
      // Detect negative response - user wants to create from scratch
      const negativePatterns = [
        'não', 'nao', 'zero', 'nova', 'novo', 'criar', 'comecar', 'começar',
        'do zero', 'outra', 'diferente', 'prefiro não'
      ]
      
      const isAffirmative = affirmativePatterns.some(p => lowerContent.includes(p))
      const isNegative = negativePatterns.some(p => lowerContent.includes(p))
      
      if ((isAffirmative || hasExplicitSelection) && !isNegative) {
        // If we're awaiting selection and user didn't provide a number, re-prompt
        if (awaitingFastTrackSelection && !numberMatch) {
          const reaskMessage: Message = {
            id: `fasttrack-reask-${Date.now()}`,
            role: 'assistant',
            content: 'Qual das vagas você quer usar? Diga o número (1, 2, 3...) ou "primeira", "segunda", etc.',
            timestamp: new Date(),
          }
          setMessages(prev => [...prev, reaskMessage])
          return
        }
        
        // If multiple suggestions and no explicit selection yet, ask for clarification
        if (fastTrack.suggestions.length > 1 && !numberMatch && !fastTrack.selectedJob) {
          const clarifyMessage: Message = {
            id: `fasttrack-clarify-${Date.now()}`,
            role: 'assistant',
            content: `Tenho ${fastTrack.suggestions.length} vagas similares. Qual você quer usar?\n\n${fastTrack.suggestions.slice(0, 5).map((s, i) => `${i + 1}. ${s.job_title}${s.department ? ` (${s.department})` : ''} - ${Math.round(s.similarity_score * 100)}% similar`).join('\n')}\n\nDiga o número ou "primeira", "segunda", etc.`,
            timestamp: new Date(),
          }
          setMessages(prev => [...prev, clarifyMessage])
          setAwaitingFastTrackSelection(true)
          return
        }
        
        // Determine which job to use - require explicit selection for multiple suggestions
        let jobToApply: FastTrackSuggestion | null = null
        
        if (numberMatch) {
          const indexMap: Record<string, number> = {
            '1': 0, 'primeira': 0,
            '2': 1, 'segunda': 1,
            '3': 2, 'terceira': 2,
            '4': 3, 'quarta': 3,
            '5': 4, 'quinta': 4
          }
          const index = indexMap[numberMatch[0].toLowerCase()] ?? 0
          if (index < fastTrack.suggestions.length) {
            jobToApply = fastTrack.suggestions[index]
          }
        } else if (fastTrack.selectedJob) {
          jobToApply = fastTrack.selectedJob
        } else if (fastTrack.suggestions.length === 1) {
          jobToApply = fastTrack.suggestions[0]
        }
        
        if (!jobToApply) {
          return
        }
        
        // Apply Fast Track data
        let fastTrackData = null
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
          return
        }
        
        if (fastTrackData) {
          // Apply data to wizard fields
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
              ...q,
              selected: true,
              batch: 0,
              isWSI: true,
            })))
          }
          if (fastTrackData.generatedDescription) {
            setGeneratedJobDescription(fastTrackData.generatedDescription)
          }
          setDetectedCriteria(prev => ({
            ...prev,
            ...fastTrackData.detectedCriteria,
          }))
          
          // Store source job ID for learning loop
          setWizardFastTrackSourceJobId(fastTrackData.sourceJobId)
          
          // Store original competencies for WSI regeneration detection
          setFastTrackOriginalCompetencies({
            technicalSkillNames: fastTrackData.technicalSkills.map(s => s.name.toLowerCase()),
            behavioralCompetencyNames: fastTrackData.behavioralCompetencies.map(c => c.name.toLowerCase())
          })
          setWsiRegenerationPrompted(false)
          
          // Clear awaiting selection state
          setAwaitingFastTrackSelection(false)
          
          // Store applied data for sensitive fields confirmation
          setFastTrackAppliedData({
            gestor: fastTrackData.basicInfo.gestor || '',
            localidade: fastTrackData.basicInfo.localidade || '',
            sourceJobTitle: jobToApply.job_title || ''
          })
          
          // Ask for sensitive fields confirmation instead of going directly to review
          setAwaitingSensitiveFieldsConfirmation(true)
          
          // Analytics: Track Fast Track accepted
          analytics.trackSuggestion('fast_track_accepted', true)
          
          // Build sensitive fields question
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
          
          // Open panel but stay at current stage until confirmation
          setIsPanelOpen(true)
        } else {
          // fastTrackData is null - notify user
          setAwaitingFastTrackSelection(false)
          const errorMessage: Message = {
            id: `fasttrack-null-${Date.now()}`,
            role: 'assistant',
            content: 'Não consegui carregar os dados dessa vaga. Quer tentar outra ou criar do zero?',
            timestamp: new Date(),
          }
          setMessages(prev => [...prev, errorMessage])
        }
        return
      }
      
      if (isNegative) {
        // User wants to create from scratch
        fastTrack.clearSuggestions()
        setFastTrackMessageSent(false)
        setAwaitingFastTrackSelection(false)
        
        // Analytics: Track Fast Track rejected
        analytics.trackSuggestion('fast_track_rejected', false)
        
        const liaMessage: Message = {
          id: `fasttrack-declined-${Date.now()}`,
          role: 'assistant',
          content: 'Tudo bem! Vamos criar uma nova vaga do zero. Me conta mais sobre a vaga que você precisa.',
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, liaMessage])
        return
      }
    }

    // Fast Track flow handling
    if (isInJobCreationMode && (wizardMode === 'pre_wizard' || wizardMode === 'fast_track')) {
      const intent = detectFastTrackIntent(content)
      
      // Pre-wizard mode: detect user's choice
      if (wizardMode === 'pre_wizard') {
        if (intent === 'fast_track') {
          setWizardMode('fast_track')
          setFastTrackState('collecting_criteria')
          setIsPanelOpen(false) // Hide right panel for Fast Track
          
          const liaMessage: Message = {
            id: `lia-fasttrack-${Date.now()}`,
            role: 'assistant',
            content: '🚀 **Ótima escolha!** Vou buscar suas vagas anteriores.\n\nPara encontrar a vaga certa, me diga pelo menos 2 critérios:\n- Cargo (ex: "Desenvolvedor Python")\n- Área ou departamento\n- Gestor responsável\n- Período aproximado\n\n**Exemplo:** "Desenvolvedor Python da equipe de dados do João"',
            timestamp: new Date()
          }
          setMessages(prev => [...prev, liaMessage])
          return
        } else if (intent === 'from_scratch') {
          setWizardMode('create_from_scratch')
          setIsPanelOpen(true) // Show right panel for regular wizard
          
          // Analytics: Track implicit rejection if Fast Track suggestions were shown
          if (fastTrackSuggestionsShownTracked) {
            analytics.trackSuggestion('fast_track_rejected', false)
          }
          
          const liaMessage: Message = {
            id: `lia-scratch-${Date.now()}`,
            role: 'assistant',
            content: FROM_SCRATCH_ORIENTATION_MESSAGE,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, liaMessage])
          return
        } else {
          // User hasn't clearly chosen - use AI to respond conversationally
          setIsLoading(true)
          
          try {
            const conversationalResponse = await getConversationalResponse({
              message: content,
              mode: 'job_creation',
              context: 'pre_wizard'
            })
            
            // Check if AI understood an intent that maps to an action
            if (conversationalResponse.suggested_action === 'from_scratch') {
              setWizardMode('create_from_scratch')
              setIsPanelOpen(true)
              
              // Analytics: Track implicit rejection if Fast Track suggestions were shown
              if (fastTrackSuggestionsShownTracked) {
                analytics.trackSuggestion('fast_track_rejected', false)
              }
              
              const liaMessage: Message = {
                id: `lia-scratch-ai-${Date.now()}`,
                role: 'assistant',
                content: FROM_SCRATCH_ORIENTATION_MESSAGE,
                timestamp: new Date()
              }
              setMessages(prev => [...prev, liaMessage])
              setIsLoading(false)
              return
            } else if (conversationalResponse.suggested_action === 'fast_track') {
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
              return
            }
            
            // No specific action - show the AI's conversational response
            const liaMessage: Message = {
              id: `lia-conversational-${Date.now()}`,
              role: 'assistant',
              content: conversationalResponse.response,
              timestamp: new Date()
            }
            setMessages(prev => [...prev, liaMessage])
          } catch (error) {
            console.error('Error getting conversational response:', error)
            // Fallback to helpful guidance
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
          return
        }
      }
      
      // Fast Track mode: handle various states
      if (wizardMode === 'fast_track') {
        if (intent === 'confirm' && fastTrackState === 'reviewing') {
          // User confirmed, publish the vacancy
          await handleFastTrackPublish()
          return
        }
        
        if (intent === 'adjust' && (fastTrackState === 'reviewing' || fastTrackState === 'adjusting')) {
          // User wants to adjust something
          const adjustments = parseFastTrackAdjustment(content)
          if (adjustments) {
            setFastTrackAdjustments(prev => ({ ...prev, ...adjustments }))
            setFastTrackState('adjusting')
            
            // Update the vacancy with adjustments and show confirmation
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
          return
        }
        
        if (intent === 'select' && fastTrackState === 'selecting') {
          // User selected a vacancy by number
          const numMatch = content.match(/(\d+)/)
          const numberWords: Record<string, number> = { 'um': 1, 'dois': 2, 'três': 3, 'quatro': 4, 'cinco': 5, 'seis': 6, 'sete': 7, 'oito': 8, 'nove': 9, 'dez': 10 }
          let index = -1
          
          if (numMatch) {
            index = parseInt(numMatch[1]) - 1
          } else {
            const word = content.toLowerCase().trim()
            if (numberWords[word]) {
              index = numberWords[word] - 1
            }
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
          return
        }
        
        if (intent === 'criteria' || fastTrackState === 'collecting_criteria') {
          // User is providing search criteria
          const criteria: VacancySearchCriteria = {}
          
          // Check if user wants to list all vacancies (generic request without specific criteria)
          const wantsToListAll = /(?:lista|listar|mostrar|ver|quais|todas|exibir|apresentar)\s*(?:as|as\s+vagas|vagas|anteriores|recentes|últimas|existentes)?/i.test(content)
          
          // Extract title/cargo
          const titleMatch = content.match(/(?:desenvolvedor|analista|gerente|coordenador|engenheiro|designer|product|ux|ui|frontend|backend|fullstack|devops|data|cientista|tech lead|architect)[^\s,.]*/gi)
          if (titleMatch) {
            criteria.title = titleMatch[0]
          }
          
          // Extract manager name
          const managerMatch = content.match(/(?:do|da|equipe do|equipe da|gestor)\s+([A-Z][a-zà-ú]+(?:\s+[A-Z][a-zà-ú]+)?)/i)
          if (managerMatch) {
            criteria.manager = managerMatch[1]
          }
          
          // Extract department
          const deptMatch = content.match(/(?:área|departamento|setor|time|equipe)\s+(?:de\s+)?([A-Za-zà-ú\s]+)/i)
          if (deptMatch) {
            criteria.department = deptMatch[1].trim()
          }
          
          setFastTrackSearchCriteria(criteria)
          
          // If user wants to list all OR has specific criteria, proceed with search
          if (Object.keys(criteria).length > 0 || wantsToListAll) {
            // Search with criteria (or empty criteria for "list all")
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
            
            // Remove processing message
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
          return
        }
        
        // Switch to create from scratch if requested
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
          return
        }
      }
    }

    // Handle salary confirmation/adjustment commands when compensation analysis is active
    const lowerContent = content.toLowerCase().trim()
    const hasCompensationMessage = messages.some(m => m.messageType === 'compensation')
    
    // Use AI interpretation when compensation message is active
    if (hasCompensationMessage) {
      // Show thinking message while interpreting
      const thinkingId = `thinking-interpret-${Date.now()}`
      const thinkingMessage: Message = {
        id: thinkingId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        processingState: 'thinking' as const
      }
      setMessages(prev => [...prev, thinkingMessage])
      
      // Call AI interpretation
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
        
        // Remove thinking message
        setMessages(prev => prev.filter(m => m.id !== thinkingId))
        
        console.log('AI Interpretation:', interpretation)
        
        // Only trust AI interpretation if confidence is high enough
        const MIN_CONFIDENCE = 0.65
        const isHighConfidence = interpretation.confidence >= MIN_CONFIDENCE
        
        // Handle based on AI interpretation with confidence gating
        if (isHighConfidence && (interpretation.action === 'confirm' || interpretation.action === 'advance_stage' || interpretation.should_advance)) {
          // Check if user wants to apply suggestions (look for entities)
          if (interpretation.extracted_entities && Object.keys(interpretation.extracted_entities).length > 0) {
            // User might be providing new values, apply them
            if (interpretation.extracted_entities.salario_min) {
              setSalaryInfo(prev => ({
                ...prev,
                minSalary: interpretation.extracted_entities!.salario_min.toString()
              }))
            }
            if (interpretation.extracted_entities.salario_max) {
              setSalaryInfo(prev => ({
                ...prev,
                maxSalary: interpretation.extracted_entities!.salario_max.toString()
              }))
            }
          }
          
          // Validate that we have complete and valid salary data before advancing
          const minSal = parseInt(salaryInfo.minSalary) || 0
          const maxSal = parseInt(salaryInfo.maxSalary) || 0
          const hasSalaryData = minSal > 0 && maxSal > 0
          
          if (!hasSalaryData) {
            const askSalaryMsg: Message = {
              id: `ask-salary-${Date.now()}`,
              role: 'assistant',
              content: '💰 Antes de avançar, preciso confirmar a faixa salarial. Qual é o salário mínimo e máximo para esta vaga?',
              timestamp: new Date()
            }
            setMessages(prev => [...prev, askSalaryMsg])
            return
          }
          
          // Validate min <= max
          if (minSal > maxSal) {
            const warningMsg: Message = {
              id: `salary-order-warning-${Date.now()}`,
              role: 'assistant',
              content: '⚠️ O salário mínimo não pode ser maior que o máximo. Por favor, corrija os valores.',
              timestamp: new Date()
            }
            setMessages(prev => [...prev, warningMsg])
            return
          }
          
          // Remove compensation message
          setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
          setCompensationAnalysis(null)
          
          const confirmMessage: Message = {
            id: `confirm-compensation-${Date.now()}`,
            role: 'assistant',
            content: interpretation.lia_response || '✅ **Valores de remuneração confirmados!**\n\nAvançando para a próxima etapa...',
            timestamp: new Date()
          }
          setMessages(prev => [...prev, confirmMessage])
          
          // Auto advance
          setTimeout(() => {
            goToNextStage()
          }, 1500)
          return
        }
        
        if (isHighConfidence && (interpretation.action === 'update_field' || interpretation.action === 'provide_data')) {
          // User is updating values - apply extracted entities with confidence gating
          if (interpretation.extracted_entities) {
            const newMin = interpretation.extracted_entities.salario_min
            const newMax = interpretation.extracted_entities.salario_max
            
            // Only apply if we have valid salary data extracted
            if (newMin || newMax) {
              const minVal = newMin || parseInt(salaryInfo.minSalary) || 0
              const maxVal = newMax || parseInt(salaryInfo.maxSalary) || 0
              
              // Validate min <= max
              if (minVal > 0 && maxVal > 0 && minVal > maxVal) {
                const warningMessage: Message = {
                  id: `salary-warning-${Date.now()}`,
                  role: 'assistant',
                  content: '⚠️ O salário mínimo não pode ser maior que o máximo. Por favor, informe os valores corretos.',
                  timestamp: new Date()
                }
                setMessages(prev => [...prev, warningMessage])
                return
              }
              
              if (newMin) {
                setSalaryInfo(prev => ({
                  ...prev,
                  minSalary: newMin.toString()
                }))
              }
              if (newMax) {
                setSalaryInfo(prev => ({
                  ...prev,
                  maxSalary: newMax.toString()
                }))
              }
              
              setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
              setCompensationAnalysis(null)
              
              const formatCurrency = (value: number) => new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL',
                minimumFractionDigits: 0
              }).format(value)
              
              const updateMessage: Message = {
                id: `update-salary-${Date.now()}`,
                role: 'assistant',
                content: `✅ **Valores atualizados!**\n\n• Mínimo: ${formatCurrency(minVal)}\n• Máximo: ${formatCurrency(maxVal)}\n\nVocê pode confirmar ou ajustar novamente.`,
                timestamp: new Date()
              }
              setMessages(prev => [...prev, updateMessage])
              return
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
          return
        }
        
        if (interpretation.action === 'ask_question') {
          // Let the question flow through to normal processing
        }
        
        if (interpretation.action === 'help') {
          const helpMessage: Message = {
            id: `help-${Date.now()}`,
            role: 'assistant',
            content: interpretation.lia_response || '💡 **Ajuda - Etapa de Remuneração**\n\nVocê pode:\n• **Confirmar** os valores atuais\n• **Aceitar sugestões** de mercado\n• **Ajustar** para novos valores (ex: "quero salário de 10 a 15 mil")\n• Pedir para **avançar** para próxima etapa',
            timestamp: new Date()
          }
          setMessages(prev => [...prev, helpMessage])
          return
        }
        
        // If AI didn't understand clearly, fall back to normal processing
        if (interpretation.confidence < 0.6 && interpretation.action === 'other') {
          // Continue to fallback pattern matching below
        } else if (interpretation.clarification_needed && interpretation.clarification_question) {
          const clarifyMessage: Message = {
            id: `clarify-${Date.now()}`,
            role: 'assistant',
            content: interpretation.clarification_question,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, clarifyMessage])
          return
        }
        
      } catch (error) {
        console.error('AI interpretation failed, using fallback:', error)
        // Remove thinking message and fall through to fallback
        setMessages(prev => prev.filter(m => m.id !== thinkingId))
      }
      
      // Fallback: Pattern matching for specific commands when AI doesn't resolve
      // This ensures the system still works even if AI interpretation fails or has low confidence
      
      // Check for confirmation/advance commands
      const isConfirmCommand = lowerContent === 'confirmar' || lowerContent.includes('confirmo') || 
        lowerContent.includes('manter valores') || lowerContent.includes('manter atual') ||
        lowerContent.includes('próximo') || lowerContent.includes('proximo') || 
        lowerContent.includes('continuar') || lowerContent.includes('avançar') || 
        lowerContent.includes('avancar') || lowerContent.includes('próximo passo') ||
        lowerContent.includes('proximo passo') || lowerContent.includes('prosseguir') || 
        lowerContent.includes('vamos para') || lowerContent.includes('pode avançar') ||
        lowerContent.includes('ok') || lowerContent === 'sim' || lowerContent === 'ok'
      
      if (isConfirmCommand) {
        // Validate complete salary data exists (min and max)
        const minSal = parseInt(salaryInfo.minSalary) || 0
        const maxSal = parseInt(salaryInfo.maxSalary) || 0
        const hasSalaryData = minSal > 0 && maxSal > 0
        
        if (!hasSalaryData) {
          const askSalaryMsg: Message = {
            id: `ask-salary-fallback-${Date.now()}`,
            role: 'assistant',
            content: '💰 Antes de continuar, preciso da faixa salarial completa. Qual é o salário mínimo e máximo para esta vaga?',
            timestamp: new Date()
          }
          setMessages(prev => [...prev, askSalaryMsg])
          return
        }
        
        // Validate min <= max
        if (minSal > maxSal) {
          const warningMsg: Message = {
            id: `salary-order-fallback-${Date.now()}`,
            role: 'assistant',
            content: '⚠️ O salário mínimo não pode ser maior que o máximo. Por favor, corrija os valores.',
            timestamp: new Date()
          }
          setMessages(prev => [...prev, warningMsg])
          return
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
        
        setTimeout(() => {
          goToNextStage()
        }, 1500)
        return
      }
      
      // Check for apply suggestions command
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
            const newBenefits = analysis.benefits.missingFromStandard.map(b => ({
              id: b.id,
              name: b.name,
              value: b.value,
              enabled: true
            }))
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
        
        setTimeout(() => {
          goToNextStage()
        }, 1500)
        return
      }
      
      // Check for salary adjustment command
      const adjustMatch = lowerContent.match(/ajust(?:ar|e)?\s*(?:para)?\s*(?:r\$?\s*)?(\d+[\d.,]*)\s*(?:a|até|-|–|\/)\s*(?:r\$?\s*)?(\d+[\d.,]*)/i)
      if (adjustMatch) {
        const minValue = parseInt(adjustMatch[1].replace(/[.,]/g, ''))
        const maxValue = parseInt(adjustMatch[2].replace(/[.,]/g, ''))
        
        setSalaryInfo(prev => ({
          ...prev,
          minSalary: minValue.toString(),
          maxSalary: maxValue.toString()
        }))
        
        setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
        setCompensationAnalysis(null)
        
        const formatCurrency = (value: number) => new Intl.NumberFormat('pt-BR', {
          style: 'currency',
          currency: 'BRL',
          minimumFractionDigits: 0
        }).format(value)
        
        const confirmMessage: Message = {
          id: `adjust-salary-fallback-${Date.now()}`,
          role: 'assistant',
          content: `✅ **Faixa salarial atualizada!**\n\n• Mínimo: ${formatCurrency(minValue)}\n• Máximo: ${formatCurrency(maxValue)}\n\nVocê pode confirmar ou ajustar novamente.`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, confirmMessage])
        return
      }
    }

    // === LOCAL COMMAND HANDLING (Navigation & Edit Commands) ===
    // Check if the message is a local command that can be handled without backend
    // IMPORTANT: Skip local command handling during input-evaluation stage
    // During input-evaluation, ALL messages should go to smart-orchestrate to properly extract job fields
    // Local command handling is only for later stages when user explicitly edits fields
    const shouldSkipLocalCommands = currentStage === 'input-evaluation'
    
    if (isInJobCreationMode && wizardMode === 'create_from_scratch' && !shouldSkipLocalCommands) {
      const parsedCommand = parseCommand(content)
      
      // Handle navigation commands (e.g., "voltar para salário", "ir para competências")
      if (parsedCommand.type === 'navigate') {
        const navCommand = parsedCommand as ParsedNavigationCommand
        const targetStage = navCommand.target
        const targetStageIndex = WIZARD_STAGES.findIndex(s => s.id === targetStage)
        const currentStageIndex = WIZARD_STAGES.findIndex(s => s.id === currentStage)
        
        // Check if already on target stage
        if (targetStage === currentStage) {
          const alreadyHereMessage: Message = {
            id: `nav-already-here-${Date.now()}`,
            role: 'assistant',
            content: `Você já está na etapa de **${getStageLabel(targetStage)}**. Como posso ajudar?`,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, alreadyHereMessage])
          return
        }
        
        // Can always go back to previous stages
        if (targetStageIndex < currentStageIndex) {
          setCurrentStage(targetStage)
          const navSuccessMessage: Message = {
            id: `nav-success-${Date.now()}`,
            role: 'assistant',
            content: `✅ Navegando para a etapa de **${getStageLabel(targetStage)}**.\n\nVocê pode revisar e ajustar os campos conforme necessário.`,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, navSuccessMessage])
          return
        }
        
        // For forward navigation, check if current stage requirements are met
        // (Simple check - can be enhanced with full quality gates)
        const stageConfig = WIZARD_STAGES.find(s => s.id === currentStage)
        if (stageConfig) {
          // Allow forward navigation with a hint about requirements
          setCurrentStage(targetStage)
          const navForwardMessage: Message = {
            id: `nav-forward-${Date.now()}`,
            role: 'assistant',
            content: `✅ Navegando para a etapa de **${getStageLabel(targetStage)}**.\n\n💡 *Dica: Lembre-se de revisar as etapas anteriores antes de finalizar.*`,
            timestamp: new Date()
          }
          setMessages(prev => [...prev, navForwardMessage])
          return
        }
      }
      
      // Handle edit commands (e.g., "alterar salário para 15k", "adicionar Python")
      if (parsedCommand.type === 'edit') {
        const editCommand = parsedCommand as ParsedEditCommand
        
        // Handle salary edits
        if (editCommand.field === 'salary' && editCommand.value) {
          const salaryResult = parseSalaryValue(String(editCommand.value))
          
          if (salaryResult.isValid) {
            const { updated, changes } = applySalaryUpdate(salaryInfo, salaryResult)
            
            // Track salary changes from chat command
            if (updated.minSalary !== salaryInfo.minSalary) {
              trackFieldChange({
                field: 'minSalary',
                oldValue: salaryInfo.minSalary,
                newValue: updated.minSalary,
                source: 'chat',
              })
            }
            if (updated.maxSalary !== salaryInfo.maxSalary) {
              trackFieldChange({
                field: 'maxSalary',
                oldValue: salaryInfo.maxSalary,
                newValue: updated.maxSalary,
                source: 'chat',
              })
            }
            
            setSalaryInfo(updated)
            
            // Clear old compensation analysis
            setMessages(prev => prev.filter(m => m.messageType !== 'compensation'))
            setCompensationAnalysis(null)
            
            const confirmMessage: Message = {
              id: `edit-salary-${Date.now()}`,
              role: 'assistant',
              content: `✅ **Salário atualizado!**\n\n${changes.length > 0 ? changes.join('\n') : `Faixa salarial definida: ${salaryResult.formatted}`}\n\n*Você pode confirmar ou ajustar novamente.*`,
              timestamp: new Date()
            }
            setMessages(prev => [...prev, confirmMessage])
            
            // Navigate to salary stage if not already there
            if (currentStage !== 'salary') {
              setCurrentStage('salary')
            }
            return
          } else {
            const errorMessage: Message = {
              id: `edit-salary-error-${Date.now()}`,
              role: 'assistant',
              content: `❌ Não consegui entender o valor do salário. Por favor, use formatos como:\n• "15k" (para R$ 15.000)\n• "R$ 10.000 a R$ 15.000"\n• "10k a 15k"`,
              timestamp: new Date()
            }
            setMessages(prev => [...prev, errorMessage])
            return
          }
        }
        
        // Handle skill add/remove
        if (editCommand.field === 'skill' && editCommand.value) {
          const skillName = String(editCommand.value)
          
          if (editCommand.action === 'add') {
            const result = addSkillIfNotExists(technicalSkills, skillName)
            if (result.added) {
              // Track skill addition from chat command
              trackFieldChange({
                field: 'technicalSkill',
                oldValue: null,
                newValue: { name: skillName },
                source: 'chat',
              })
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
            
            // Navigate to competencies stage if not already there
            if (currentStage !== 'competencies') {
              setCurrentStage('competencies')
            }
            return
          }
          
          if (editCommand.action === 'remove') {
            const result = removeSkillByName(technicalSkills, skillName)
            if (result.removed) {
              // Track skill removal from chat command
              trackFieldChange({
                field: 'technicalSkill',
                oldValue: { name: skillName },
                newValue: null,
                source: 'chat',
              })
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
            
            // Navigate to competencies stage if not already there
            if (currentStage !== 'competencies') {
              setCurrentStage('competencies')
            }
            return
          }
        }
      }
    }
    // === END LOCAL COMMAND HANDLING ===

    // Adicionar mensagem de processamento como histórico (estilo Manus)
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
      console.log('[DEBUG handleSendMessage] SENDING TO BACKEND - smart-orchestrate')
      setIsLoading(true)
      
      try {
        // Atualizar para "analisando"
        setTimeout(() => {
          setMessages(msgs => msgs.map(m => 
            m.id === processingMessageId 
              ? { ...m, content: '📊 Consultando LIA...', processingState: 'analyzing' as const }
              : m
          ))
        }, 300)

        // Use intelligent orchestrator for all wizard interactions
        const collectedData = buildCollectedData()
        const conversationHistory = messages.slice(-10).map(m => ({
          role: m.role,
          content: m.content
        }))
        
        // Include recent panel changes in LLM context for bidirectional sync
        const panelChangesContext = generateLLMContext()
        const enhancedMessage = panelChangesContext 
          ? `${content}\n\n${panelChangesContext}` 
          : content
        
        // Save user message to conversation memory
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
        
        // Always use smart-orchestrate response (no fallback to processBackendStep or local regex)
        console.log('[SmartOrchestrate] Using smart-orchestrate response (confidence:', orchestratorResult.confidence, ')')
        await processOrchestratorResponse(orchestratorResult, processingMessageId)
        setIsLoading(false)
        
        // After smart-orchestrate, optionally trigger evaluation step for compensation analysis
        // The smart-orchestrate already handles most logic, but we keep evaluation for additional analysis
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
            if (evalResult?.compensation_analysis) {
              setCompensationAnalysis(evalResult.compensation_analysis)
            }
            
            const evalResultAny = evalResult as any
            if (evalResultAny?.technical_skills || evalResultAny?.behavioral_competencies) {
              const technicalSuggestions: TechnicalSkillSuggestion[] = (evalResultAny.technical_skills || []).map((skill: any) => ({
                name: skill.name || skill,
                level: skill.level || 'Intermediário',
                weight: skill.weight || 3,
                weightJustification: skill.weight_justification || 'Baseado em análise de mercado',
                source: skill.source || 'market_benchmark',
                required: skill.required ?? true,
                category: skill.category || 'tool'
              }))
              
              const behavioralSuggestions: BehavioralCompetencySuggestion[] = (evalResultAny.behavioral_competencies || []).map((comp: any) => ({
                name: comp.name || comp,
                weight: comp.weight || 3,
                justification: comp.justification || '',
                weightJustification: comp.weight_justification || 'Baseado em histórico da empresa',
                source: comp.source || 'company_history'
              }))
              
              if (technicalSuggestions.length > 0 || behavioralSuggestions.length > 0) {
                setCompetencySuggestions({
                  technicalSkills: technicalSuggestions,
                  behavioralCompetencies: behavioralSuggestions
                })
                
                setTimeout(() => {
                  const competenciesMessage: Message = {
                    id: `lia-competencies-${Date.now()}`,
                    role: 'assistant',
                    content: '',
                    timestamp: new Date(),
                    messageType: 'competencies',
                    competenciesSuggestions: {
                      technicalSkills: technicalSuggestions,
                      behavioralCompetencies: behavioralSuggestions
                    }
                  }
                  setMessages(prev => [...prev, competenciesMessage])
                }, 1000)
              }
            }
          }).catch((err) => {
            console.error('Error calling evaluation step:', err)
          })
        }
        return
      } catch (error) {
        console.error('Error in wizard step:', error)
        
        // Fallback to local logic
        const newCriteria = extractCriteriaFromText(content)
        const fallbackText = generateCriteriaResponse(newCriteria)
        
        // Build fallback detected fields for DetectedFieldsCard
        const fallbackFieldsData: Array<{ label: string; value: string; confidence?: "high" | "medium" | "low" }> = []
        if (newCriteria.cargo) fallbackFieldsData.push({ label: "Cargo", value: newCriteria.cargo, confidence: "high" })
        if (newCriteria.senioridadeIdiomas) fallbackFieldsData.push({ label: "Senioridade", value: newCriteria.senioridadeIdiomas, confidence: "medium" })
        if (newCriteria.modeloTrabalho) fallbackFieldsData.push({ label: "Modelo", value: newCriteria.modeloTrabalho, confidence: "medium" })
        if (newCriteria.localizacao) fallbackFieldsData.push({ label: "Localização", value: newCriteria.localizacao, confidence: "medium" })
        if (newCriteria.competenciasTecnicas?.length > 0) fallbackFieldsData.push({ label: "Skills Técnicas", value: newCriteria.competenciasTecnicas.slice(0, 5).join(", "), confidence: "medium" })
        if (newCriteria.tipoContrato) fallbackFieldsData.push({ label: "Contrato", value: newCriteria.tipoContrato, confidence: "low" })
        
        // Marcar como concluído mesmo em erro
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
        setTimeout(() => {
          typeText(fallbackText, fallbackMessage.id)
        }, 300)
        setIsLoading(false)
      }
      return
    }

    setIsLoading(true)

    try {
      let responseText = "Entendi! Estou processando as informações..."
      
      if (onOrchestratedMessage) {
        const orchestratedResponse = await onOrchestratedMessage(content.trim())
        responseText = orchestratedResponse.content
        
        if (orchestratedResponse.ui_action === 'start_job_wizard') {
          setInternalJobCreationMode(true)
          setCurrentStage('input-evaluation')
          if (orchestratedResponse.ui_action_params?.initial_message) {
            setDynamicInitialMessage(INITIAL_JOB_CREATION_MESSAGE)
          }
        }
      } else {
        // Use unified orchestrator for general chat (routes to 9 specialized agents)
        // Integrate with conversation memory for context persistence
        
        // Initialize conversation memory for general context if not already active
        if (!conversationMemory.conversationId && user?.email) {
          await conversationMemory.initConversation(user.email, 'general')
        }
        
        // Get conversation context for AI memory
        const conversationContext = await conversationMemory.getContext()
        
        // Save user message to conversation memory first
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
          
          // Save assistant response to conversation memory
          if (conversationMemory.conversationId) {
            conversationMemory.addMessage('assistant', responseText, orchestratorResponse.intent).catch(() => {})
          }
          
          // Check for suggested_tool_call in the response
          const suggestedToolCall = orchestratorResponse.suggested_tool_call || orchestratorResponse.result?.suggested_tool_call
          if (suggestedToolCall) {
            // Extract tool call info
            const toolCall: ToolCall = {
              tool_name: suggestedToolCall.tool_name,
              parameters: suggestedToolCall.parameters || {},
              requires_confirmation: suggestedToolCall.requires_confirmation !== false,
              confirmation_message: suggestedToolCall.confirmation_message || responseText,
            }
            
            if (toolCall.requires_confirmation) {
              // Suggest the tool call and create confirmation message
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
              return // Don't add another message, we already added the confirmation
            } else {
              // Execute tool directly without confirmation
              setIsLoading(true)
              
              try {
                const result = await toolCalling.executeToolDirectly(toolCall.tool_name, toolCall.parameters)
                
                const feedbackMessage: Message = {
                  id: `tool-feedback-${Date.now()}`,
                  role: 'assistant',
                  content: result.success 
                    ? `✅ ${result.message}` 
                    : `❌ ${result.error || result.message}`,
                  timestamp: new Date(),
                  messageType: 'tool-execution-feedback',
                  toolExecutionResult: result,
                }
                setMessages(prev => [...prev, feedbackMessage])
                setIsLoading(false)
                return
              } catch (error) {
                console.error('[ToolCalling] Error executing tool directly:', error)
                // Fall through to normal response
              }
            }
          }
        } else {
          // Fallback to simple LIA response
          const response = await liaApi.sendMessage({
            content: content.trim(),
            conversation_id: conversationId || undefined,
            user_id: 'demo-user'
          })
          if (response.conversation?.id && !conversationId) {
            setConversationId(response.conversation.id)
          }
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
      
      setTimeout(() => {
        typeText(responseText, assistantMessage.id)
      }, 300)

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
      setTimeout(() => {
        typeText(errorText, errorMessage.id)
      }, 300)
    } finally {
      setIsLoading(false)
    }
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
            <div className="px-4 py-4 flex-shrink-0 bg-white mt-auto">
              <div className="flex justify-center">
                <div className="w-full max-w-lg">
                  <div className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-[24px]">
                    <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center">
                      <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
                    </div>
                    <input
                      ref={inputRef}
                      type="text"
                      value={inputValue}
                      onChange={(e) => {
                        setInputValue(e.target.value)
                        if (extractCriteriaDebounceRef.current) {
                          clearTimeout(extractCriteriaDebounceRef.current)
                        }
                        extractCriteriaDebounceRef.current = setTimeout(() => {
                          extractCriteriaFromText(e.target.value)
                        }, 600)
                      }}
                      onKeyDown={handleKeyDown}
                      placeholder="Envie mensagem para a LIA..."
                      data-testid="chat-input"
                      aria-label="Digite sua mensagem para a LIA"
                      aria-describedby="chat-input-hint"
                      className="flex-1 py-1 bg-transparent text-base-ui text-gray-900 dark:text-gray-50 placeholder:text-gray-400 focus:outline-none"
                      style={{ fontFamily: '"Open Sans", sans-serif' }}
                      disabled={isLoading || isTypingEffect}
                    />
                    <span id="chat-input-hint" className="sr-only">Pressione Enter para enviar a mensagem</span>

                    <div className="flex items-center gap-1">
                      <>
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept="image/*,application/pdf,.doc,.docx"
                          onChange={handleFileSelect}
                          className="hidden"
                        />
                        <button
                          className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors rounded-full"
                          type="button"
                          onClick={() => fileInputRef.current?.click()}
                          title="Anexar arquivo para análise"
                          aria-label="Anexar arquivo para análise"
                        >
                          <Paperclip className="w-4 h-4" aria-hidden="true" />
                        </button>
                      </>
                      <VoiceChatButton
                        sessionId={conversationId || undefined}
                        onTranscription={(text) => {
                          setInputValue(prev => prev ? `${prev} ${text}` : text)
                        }}
                        onResponse={handleVoiceResponse}
                        onError={(error) => {
                          const errorMsg: Message = {
                            id: `voice-error-${Date.now()}`,
                            role: 'assistant',
                            content: `⚠️ ${error}`,
                            timestamp: new Date()
                          }
                          setMessages(prev => [...prev, errorMsg])
                        }}
                        disabled={isLoading || isTypingEffect}
                      />
                      <button
                        onClick={() => handleSendMessage(inputValue)}
                        disabled={!inputValue.trim() || isLoading || isTypingEffect}
                        aria-label="Enviar mensagem"
                        aria-disabled={!inputValue.trim() || isLoading || isTypingEffect}
                        className={cn(
                          "w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 ml-1",
                          inputValue.trim() && !isLoading && !isTypingEffect
                            ? "bg-chat-cyan text-white hover:opacity-90"
                            : "bg-gray-200 text-gray-400 cursor-not-allowed"
                        )}
                        type="button"
                      >
                        {isLoading ? (
                          <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                        ) : (
                          <Send className="w-4 h-4" aria-hidden="true" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Tabs como badges abaixo do input (IA Natural, Job Description, Templates) - Sempre visível */}
                  {!hideModeButtons && (
                    <div className="flex items-center justify-center gap-1.5 mt-1.5">
                      <button
                        onClick={() => setActiveInputTab('ia-natural')}
                        className={cn(
                          "px-2.5 py-1 rounded-full text-xs font-medium transition-all",
                          activeInputTab === 'ia-natural' 
                            ? "text-white bg-gray-900 dark:bg-gray-50 dark:text-gray-900" 
                            : "text-gray-700 bg-gray-100 hover:bg-gray-200"
                        )}
                        style={{ fontFamily: '"Open Sans", sans-serif' }}
                      >
                        <div className="flex items-center gap-1">
                          <Brain className="w-2.5 h-2.5 text-chat-cyan" />
                          <span>IA Natural</span>
                        </div>
                      </button>
                      <button
                        onClick={() => setActiveInputTab('job-description')}
                        className={cn(
                          "px-2.5 py-1 rounded-full text-xs font-medium transition-all",
                          activeInputTab === 'job-description' 
                            ? "text-white bg-gray-900 dark:bg-gray-50 dark:text-gray-900" 
                            : "text-gray-700 bg-gray-100 hover:bg-gray-200"
                        )}
                        style={{ fontFamily: '"Open Sans", sans-serif' }}
                      >
                        <div className="flex items-center gap-1">
                          <FileText className="w-2.5 h-2.5" />
                          <span>Job Description</span>
                        </div>
                      </button>
                      <button
                        onClick={() => setActiveInputTab('templates')}
                        className={cn(
                          "px-2.5 py-1 rounded-full text-xs font-medium transition-all",
                          activeInputTab === 'templates' 
                            ? "text-white bg-gray-900 dark:bg-gray-50 dark:text-gray-900" 
                            : "text-gray-700 bg-gray-100 hover:bg-gray-200"
                        )}
                        style={{ fontFamily: '"Open Sans", sans-serif' }}
                      >
                        <div className="flex items-center gap-1">
                          <Target className="w-2.5 h-2.5" />
                          <span>Templates</span>
                        </div>
                      </button>
                    </div>
                  )}

                  {/* Badges de sugestão abaixo das tabs (só quando IA Natural selecionado) */}
                  {!hideModeButtons && activeInputTab === 'ia-natural' && (
                    <div className="flex flex-wrap items-center justify-center gap-1.5 mt-1.5">
                      <span className="text-micro font-medium text-gray-500" style={{ fontFamily: '"Open Sans", sans-serif' }}>Sugestões:</span>
                      {suggestionTags.map((tag) => {
                        const IconComponent = tag.icon
                        return (
                          <button
                            key={tag.action}
                            onClick={() => {
                              if (tag.action === 'criar_vaga') {
                                setInternalJobCreationMode(true)
                                
                                // Check for existing draft BEFORE showing any message
                                const { hasDraft, stageName, draftData } = checkForExistingDraftSync()
                                
                                if (hasDraft && stageName && draftData) {
                                  // Store draft data for restoration BEFORE showing message
                                  setPendingDraftData(draftData)
                                  setAwaitingDraftChoice(true)
                                  
                                  // Show only the draft choice message - let user decide
                                  const draftChoiceMsg: Message = {
                                    id: 'draft-choice-intro',
                                    role: 'assistant',
                                    content: DRAFT_DETECTED_MESSAGE(stageName),
                                    timestamp: new Date(),
                                    isTyping: true
                                  }
                                  setMessages([draftChoiceMsg])
                                  setDisplayedText("")
                                  setTimeout(() => {
                                    typeText(DRAFT_DETECTED_MESSAGE(stageName), 'draft-choice-intro')
                                  }, 300)
                                } else {
                                  // No draft - show welcome message
                                  const dynamicGreeting = wizardGreeting?.greeting_message || INITIAL_JOB_CREATION_MESSAGE
                                  setDynamicInitialMessage(dynamicGreeting)
                                  const jobCreationMsg: Message = {
                                    id: 'job-creation-intro',
                                    role: 'assistant',
                                    content: dynamicGreeting,
                                    timestamp: new Date(),
                                    isTyping: true
                                  }
                                  setMessages([jobCreationMsg])
                                  setDisplayedText("")
                                  setTimeout(() => {
                                    typeText(dynamicGreeting, 'job-creation-intro')
                                  }, 300)
                                }
                              } else {
                                handleSendMessage(tag.label)
                              }
                            }}
                            disabled={isTypingEffect || isLoading}
                            className={cn(
                              "inline-flex items-center gap-1 px-2 py-0.5 text-micro font-medium text-gray-700 bg-gray-100 rounded-full transition-all",
                              isTypingEffect || isLoading
                                ? "opacity-50 cursor-not-allowed"
                                : "hover:bg-gray-200"
                            )}
                            style={{ fontFamily: '"Open Sans", sans-serif' }}
                          >
                            <IconComponent className="w-2.5 h-2.5 text-gray-500" />
                            {tag.label}
                          </button>
                        )
                      })}
                      <LiaVacancyQueriesGuide
                        onSelectQuery={(query) => {
                          handleSendMessage(query)
                        }}
                        isOpen={showMoreIdeas}
                        onOpenChange={setShowMoreIdeas}
                      />
                    </div>
                  )}

                  {/* Conteúdo da aba Job Description */}
                  {activeInputTab === 'job-description' && (
                    <div className="mt-3 p-3 rounded-md border border-gray-100 bg-white">
                      <p className="text-xs text-gray-600 mb-2" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                        Cole ou anexe uma descrição de vaga e eu vou criar a vaga automaticamente para você, configurando todos os detalhes.
                      </p>
                      <textarea
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Cole aqui o job description completo (requisitos, responsabilidades, benefícios...)."
                        className="w-full px-3 py-2.5 text-xs rounded-md border border-gray-100 focus:border-gray-400 focus:outline-none resize-none transition-colors bg-gray-50"
                        style={{ 
                          fontFamily: '"Open Sans", sans-serif',
                          minHeight: '80px'
                        }}
                        rows={4}
                      />
                      <div className="flex items-center justify-between mt-2">
                        <div className="flex items-center gap-1">
                          <Paperclip className="w-3 h-3 text-gray-400" />
                          <span className="text-micro text-gray-400">PDF, Word, TXT</span>
                        </div>
                        <Button
                          size="sm"
                          className={cn(
                            "h-7 px-3 text-xs font-medium",
                            inputValue.trim() ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-400"
                          )}
                          style={{
                            fontFamily: '"Open Sans", sans-serif'
                          }}
                          onClick={() => {
                            if (inputValue.trim()) {
                              setInternalJobCreationMode(true)
                              const dynamicGreeting = wizardGreeting?.greeting_message || INITIAL_JOB_CREATION_MESSAGE
                              setDynamicInitialMessage(dynamicGreeting)
                              handleSendMessage(inputValue)
                              setActiveInputTab('ia-natural')
                            }
                          }}
                          disabled={!inputValue.trim()}
                        >
                          <Brain className="w-3 h-3 mr-1 text-chat-cyan" />
                          Criar Vaga a Partir do JD
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Conteúdo da aba Templates */}
                  {activeInputTab === 'templates' && (
                    <div className="mt-3 p-3 rounded-md border border-gray-100 bg-white space-y-3">
                      {/* Seção 1: Criar a partir de Template */}
                      <div>
                        <h4 className="text-xs font-medium mb-1 text-gray-800" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                          Criar Vaga a Partir de Template
                        </h4>
                        <p className="text-micro text-gray-500 mb-2">
                          Selecione um modelo pronto e eu inicio a criação da vaga para você
                        </p>
                        <div className="grid grid-cols-2 gap-1.5">
                          {[
                            { icon: '🚀', title: 'Backend Sênior Node.js', tags: ['Backend', 'Node.js'] },
                            { icon: '📊', title: 'Product Manager', tags: ['Product', 'Agile'] },
                            { icon: '🎨', title: 'UX/UI Designer', tags: ['Design', 'Figma'] },
                            { icon: '☁️', title: 'DevOps Engineer', tags: ['Cloud', 'CI/CD'] },
                          ].map((template) => (
                            <div 
                              key={template.title}
                              className="cursor-pointer transition-all rounded-md p-2 hover:border border-gray-100 bg-white hover:border-gray-900 dark:hover:border-gray-50"
                              onClick={() => {
                                setInternalJobCreationMode(true)
                                const dynamicGreeting = wizardGreeting?.greeting_message || INITIAL_JOB_CREATION_MESSAGE
                                setDynamicInitialMessage(dynamicGreeting)
                                const templateMsg = `Criar vaga ${template.title}`
                                handleSendMessage(templateMsg)
                                setActiveInputTab('ia-natural')
                              }}
                            >
                              <div className="flex items-center gap-1.5">
                                <span className="text-sm">{template.icon}</span>
                                <div className="flex-1 min-w-0">
                                  <h5 className="text-xs font-medium truncate text-gray-800" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                                    {template.title}
                                  </h5>
                                  <div className="flex gap-1 mt-0.5">
                                    {template.tags.map(tag => (
                                      <span key={tag} className="text-micro px-1 py-0.5 rounded-full bg-gray-100 text-gray-500">{tag}</span>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Seção 2: Criar a partir de Vaga Existente */}
                      <div className="pt-2 border-t border-gray-100">
                        <h4 className="text-xs font-medium mb-1 text-gray-800" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                          Criar a Partir de Vaga Existente
                        </h4>
                        <p className="text-micro text-gray-500 mb-2">
                          Copie uma vaga já criada e faça ajustes
                        </p>
                        <div className="relative">
                          <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                          <input
                            type="text"
                            placeholder="Buscar vaga por título ou ID..."
                            className="w-full pl-8 pr-3 py-2 text-xs rounded-md border border-gray-100 focus:border-gray-400 focus:outline-none transition-colors bg-gray-50"
                            style={{ 
                              fontFamily: '"Open Sans", sans-serif'
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  )}

                </div>
              </div>
            </div>
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
          <div 
            ref={resizeRef}
            className="flex flex-col rounded-md flex-shrink-0 m-3 ml-0 relative bg-gray-50 border border-gray-200" 
            style={{ 
              width: `${panelWidth}%`
            }}
          >
            {/* Resize Handle - cursor change only, no visual indicator */}
            <div 
              className="absolute left-0 top-0 bottom-0 w-2 cursor-col-resize z-10"
              onMouseDown={(e) => {
                e.preventDefault()
                setIsResizing(true)
              }}
            />
            
            {/* Panel Header with Stage Info */}
            <WizardHeader
              currentStageConfig={currentStageConfig}
              currentStageIndex={currentStageIndex}
              catalogStatus={wizardGreeting?.catalog_status}
              isAutoSaving={isAutoSaving}
              autoSaveLastSaved={autoSaveLastSaved}
              hasPendingChanges={hasPendingChanges}
              hasRestoredDraft={hasRestoredDraft}
              isFullscreen={isFullscreen}
              onFullscreenChange={(fullscreen) => {
                setIsFullscreen(fullscreen)
                onFullscreenChange?.(fullscreen)
              }}
              onPanelClose={() => setIsPanelOpen(false)}
              onClearDraft={() => setShowClearDraftConfirm(true)}
              getLastSavedText={getLastSavedText}
            />

            {/* WSI Quality Bar - visible in competencies and wsi-questions stages */}
            {(currentStage === 'competencies' || currentStage === 'wsi-questions') && (
              <div className="px-3 pb-2">
                <WSIQualityBar
                  score={wsiQualityGates.score}
                  fields={wsiQualityGates.fields}
                  summaryText={wsiQualityGates.summaryText}
                  scoreColor={wsiQualityGates.scoreColor}
                  canAdvance={wsiQualityGates.canAdvance}
                />
              </div>
            )}

            <div className="flex-1 overflow-y-auto p-4 relative">
              {/* Loading Overlay during stage transitions */}
              {stageTransition === 'loading' && (
                <div className="absolute inset-0 bg-white/90 backdrop-blur-sm z-50 flex flex-col items-center justify-center gap-4">
                  <div className="relative">
                    <div className="w-12 h-12 rounded-full border-3 border-gray-300 dark:border-gray-600 border-t-gray-300 dark:border-t-gray-600 animate-spin" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Brain className="w-5 h-5 text-chat-cyan" />
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-gray-700" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                      LIA está analisando...
                    </p>
                    <p className="text-xs text-gray-500 mt-1" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                      Preparando sugestões personalizadas
                    </p>
                  </div>
                </div>
              )}
              
              {/* Stage 1: Input Evaluation - Proactive Analysis */}
              {currentStage === 'input-evaluation' && (
                <InputEvaluationStage
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
                />
              )}

              {/* Stage: JD Enrichment - AI-powered suggestions */}
              {currentStage === 'jd-enrichment' && (
                <EnrichedJDStage
                  enrichedData={enrichedJDData}
                  onAcceptSuggestion={(suggestionId) => {
                    // Handle accepting a suggestion
                    console.log('[EnrichedJD] Accepted suggestion:', suggestionId)
                    setEnrichedJDData(prev => {
                      if (!prev) return prev
                      return {
                        ...prev,
                        sections: prev.sections.map(section => ({
                          ...section,
                          suggestions: section.suggestions.map(s => 
                            s.id === suggestionId ? { ...s, accepted: true } : s
                          )
                        }))
                      }
                    })
                  }}
                  onRejectSuggestion={(suggestionId) => {
                    // Handle rejecting a suggestion
                    console.log('[EnrichedJD] Rejected suggestion:', suggestionId)
                    setEnrichedJDData(prev => {
                      if (!prev) return prev
                      return {
                        ...prev,
                        sections: prev.sections.map(section => ({
                          ...section,
                          suggestions: section.suggestions.filter(s => s.id !== suggestionId)
                        }))
                      }
                    })
                  }}
                  onAcceptAll={() => {
                    // Accept all suggestions
                    console.log('[EnrichedJD] Accepted all suggestions')
                    setEnrichedJDData(prev => {
                      if (!prev) return prev
                      return {
                        ...prev,
                        sections: prev.sections.map(section => ({
                          ...section,
                          suggestions: section.suggestions.map(s => ({ ...s, accepted: true }))
                        }))
                      }
                    })
                  }}
                  isLoading={isLoadingEnrichment}
                  detectedCriteria={{
                    cargo: detectedCriteria.cargo,
                    senioridade: detectedCriteria.senioridadeIdiomas,
                    departamento: detectedCriteria.departamento,
                    responsabilidades: detectedCriteria.responsabilidades,
                    competenciasTecnicas: detectedCriteria.competenciasTecnicas,
                    competenciasComportamentais: detectedCriteria.competenciasComportamentais
                  }}
                />
              )}

              {/* Stage 2: Competencies (Technical + Behavioral) - Unified Layout */}
              {currentStage === 'competencies' && (
                <CompetenciesStage
                  technicalSkills={technicalSkills}
                  behavioralCompetencies={behavioralCompetencies}
                  highlightedFields={highlightedFields}
                  onSetTechnicalSkills={(newSkills) => {
                    // Track added/removed skills for chat sync
                    const prevNames = new Set(technicalSkills.map(s => s.name))
                    const newNames = new Set(newSkills.map(s => s.name))
                    newSkills.forEach(skill => {
                      if (!prevNames.has(skill.name)) {
                        trackFieldChange({
                          field: 'technicalSkill',
                          oldValue: null,
                          newValue: skill,
                          source: 'panel',
                        })
                      }
                    })
                    technicalSkills.forEach(skill => {
                      if (!newNames.has(skill.name)) {
                        trackFieldChange({
                          field: 'technicalSkill',
                          oldValue: skill,
                          newValue: null,
                          source: 'panel',
                        })
                      }
                    })
                    setTechnicalSkills(newSkills)
                  }}
                  onSetBehavioralCompetencies={(newComps) => {
                    // Track added/removed competencies for chat sync
                    const prevNames = new Set(behavioralCompetencies.filter(c => c.enabled).map(c => c.name))
                    const newNames = new Set(newComps.filter(c => c.enabled).map(c => c.name))
                    newComps.forEach(comp => {
                      if (comp.enabled && !prevNames.has(comp.name)) {
                        trackFieldChange({
                          field: 'behavioralCompetency',
                          oldValue: null,
                          newValue: comp,
                          source: 'panel',
                        })
                      }
                    })
                    behavioralCompetencies.forEach(comp => {
                      if (comp.enabled && !newNames.has(comp.name)) {
                        trackFieldChange({
                          field: 'behavioralCompetency',
                          oldValue: comp,
                          newValue: null,
                          source: 'panel',
                        })
                      }
                    })
                    setBehavioralCompetencies(newComps)
                  }}
                  basicInfoFields={basicInfoFields}
                  detectedCriteria={detectedCriteria}
                  companyConfig={companyConfig}
                  inferSkillWeight={inferSkillWeight}
                  isCollapsed={!competenciesPanelExpanded}
                  onExpandEdit={() => setCompetenciesPanelExpanded(!competenciesPanelExpanded)}
                  isFieldRequired={isFieldRequiredForWizard('competencias')}
                  onShowAddSkillModal={(category) => { setNewSkillCategory(category); setShowAddSkillModal(true) }}
                  onShowAddCompetencyModal={() => setShowAddCompetencyModal(true)}
                  onEditCompetency={setEditingCompetency}
                />
              )}

              {/* Stage 5: Salary and Benefits */}
              {currentStage === 'salary' && (
                <SalaryStage
                  salaryInfo={salaryInfo}
                  highlightedFields={highlightedFields}
                  onSalaryChange={(info) => {
                    // Track field changes for chat sync
                    Object.entries(info).forEach(([key, value]) => {
                      const oldValue = salaryInfo[key as keyof typeof salaryInfo]
                      if (oldValue !== value) {
                        trackFieldChange({
                          field: key,
                          oldValue,
                          newValue: value,
                          source: 'panel',
                        })
                      }
                    })
                    setSalaryInfo(prev => ({ ...prev, ...info }))
                  }}
                  salaryBenchmark={salaryBenchmark as any}
                  isLoadingBenchmark={isLoadingBenchmark}
                  companyConfig={companyConfig as any}
                  isCollapsed={!salaryPanelExpanded}
                  onExpandEdit={() => setSalaryPanelExpanded(!salaryPanelExpanded)}
                  isFieldRequired={isFieldRequiredForWizard('salario')}
                  onShowAddBenefitModal={() => setShowAddBenefitModal(true)}
                />
              )}

              {/* Stage 6: WSI Screening Questions */}
              {currentStage === 'wsi-questions' && (
                <WSIQuestionsStage
                  wsiCandidates={wsiCandidates}
                  highlightedFields={highlightedFields}
                  companyDefaultQuestions={companyDefaultQuestions as any}
                  onSetCompanyDefaultQuestions={setCompanyDefaultQuestions as any}
                  onToggleQuestionSelection={toggleWSIQuestionSelection}
                  onDeleteQuestion={deleteWSIQuestion}
                  onUpdateExpectedAnswer={updateWSIQuestionExpectedAnswer}
                  onUpdateCorrectOption={updateWSIQuestionCorrectOption}
                  isGeneratingWSI={isGeneratingWSI}
                  onGenerateWSIQuestions={generateWSIQuestions}
                  showCustomQuestionForm={showCustomQuestionForm}
                  onSetShowCustomQuestionForm={setShowCustomQuestionForm}
                  customQuestionText={customQuestionText}
                  onSetCustomQuestionText={setCustomQuestionText}
                  customQuestionType={customQuestionType}
                  onSetCustomQuestionType={setCustomQuestionType}
                  customQuestionRequired={customQuestionRequired}
                  onSetCustomQuestionRequired={setCustomQuestionRequired}
                  onAddCustomQuestion={addCustomQuestion}
                />
              )}

              {/* Stage 6: Review and Publish (Unified) */}
              {currentStage === 'review-publish' && (
                <ReviewPublishStage
                  basicInfoFields={basicInfoFields}
                  technicalSkills={technicalSkills}
                  behavioralCompetencies={behavioralCompetencies}
                  salaryInfo={salaryInfo}
                  wsiQuestions={wsiQuestions}
                  jobDescription={jobDescription}
                  isGeneratingDescription={isGeneratingDescription}
                  companyConfig={companyConfig}
                  publishingPlatforms={publishingPlatforms}
                  jobConfig={jobConfig}
                  detectedCriteria={detectedCriteria}
                  publishedJobId={publishedJobId}
                  onGoToStage={setCurrentStage}
                  onSetCompetenciesTab={setCompetenciesTab}
                  onSetPublishingPlatforms={setPublishingPlatforms}
                  onSetJobConfig={setJobConfig}
                  onSetDetectedCriteria={setDetectedCriteria}
                  onUpdateLanguages={updateLanguages}
                  onGenerateJobDescription={generateJobDescription}
                />
              )}

              {/* Stage 7: Search and Calibration (Unified) */}
              {currentStage === 'search-calibration' && (
                <SearchCalibrationStage
                  searchPhase={searchPhase}
                  calibrationCandidates={calibrationCandidates}
                  calibrationComplete={calibrationComplete}
                  isLoadingCalibration={isLoadingCalibration}
                  hasAttemptedCalibrationGeneration={hasAttemptedCalibrationGeneration}
                  approvedCandidates={approvedCandidates}
                  showCalibrationModal={showCalibrationModal}
                  publishedJobId={publishedJobId}
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
                />
              )}
            </div>

            {/* Navigation Buttons */}
            <div className="px-4 py-3 bg-white rounded-b-xl">
              {currentStage === 'search-calibration' ? (
                <SearchCalibrationNavButtons
                  calibrationCandidates={calibrationCandidates}
                  calibrationComplete={calibrationComplete}
                  isLoadingCalibration={isLoadingCalibration}
                  hasAttemptedCalibrationGeneration={hasAttemptedCalibrationGeneration}
                  approvedCandidates={approvedCandidates}
                  onSetShowCalibrationModal={setShowCalibrationModal}
                />
              ) : currentStage === 'input-evaluation' ? (
                <div className="text-center text-micro text-gray-500" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                  Continue descrevendo a vaga para detectar mais critérios
                </div>
              ) : currentStage === 'jd-enrichment' ? (
                <div className="text-center text-micro text-gray-500" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                  Revise as sugestões no chat e responda o que deseja aceitar ou modificar
                </div>
              ) : (
                <div className="flex gap-2">
                  {currentStageIndex > 0 && (
                    <Button
                      variant="outline"
                      className="flex-1 h-9 rounded-md text-xs font-medium border-gray-200 text-gray-600 hover:border-gray-900 dark:hover:border-gray-50 hover:text-gray-900 dark:hover:text-gray-50"
                      style={{ fontFamily: '"Open Sans", sans-serif' }}
                      onClick={goToPreviousStage}
                      aria-label="Voltar para etapa anterior"
                    >
                      <ChevronLeft className="w-3.5 h-3.5 mr-1" />
                      Voltar
                    </Button>
                  )}
                  {/* Hide confirmation button for conversational stages - flow is via chat, not buttons */}
                  {/* Note: jd-enrichment is already handled above with its own text message, so no need to check here */}
                  {currentStage !== 'salary' && currentStage !== 'competencies' && (
                  <Button
                    className={cn(
                      "flex-1 h-9 rounded-md text-xs font-semibold transition-all",
                      currentStageIndex === 0 ? "w-full" : "",
                      currentStage === 'review-publish'
                        ? "bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900"
                        : canAdvanceToNextStage()
                          ? "bg-gray-900 text-white"
                          : "bg-gray-200 text-gray-400"
                    )}
                    style={{ 
                      fontFamily: '"Open Sans", sans-serif'
                    }}
                    disabled={!canAdvanceToNextStage()}
                    onClick={currentStage === 'review-publish' ? handlePublishJob : goToNextStage}
                    aria-label={currentStage === 'review-publish' ? 'Publicar vaga' : 'Confirmar etapa atual'}
                  >
                    {(() => {
                      const stage = currentStage as string
                      if (stage === 'review-publish') {
                        return (
                          <>
                            <Rocket className="w-3.5 h-3.5 mr-1.5" />
                            Publicar Vaga
                          </>
                        )
                      }
                      if (stage === 'wsi-questions') {
                        return (
                          <>
                            <Check className="w-3.5 h-3.5 mr-1" />
                            Confirmar Triagem
                          </>
                        )
                      }
                      if (stage === 'input-evaluation') {
                        return (
                          <>
                            <Check className="w-3.5 h-3.5 mr-1" />
                            Confirmar Avaliação
                          </>
                        )
                      }
                      return (
                        <>
                          <Check className="w-3.5 h-3.5 mr-1" />
                          Confirmar
                        </>
                      )
                    })()}
                  </Button>
                  )}
                </div>
              )}
            </div>
          </div>
          )}
        </div>
        </>
      </div>

      {/* Modal: Add Technical Skill */}
      {showAddSkillModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-2xl w-[400px] p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4" style={{ fontFamily: '"Open Sans", sans-serif' }}>
              Adicionar {newSkillCategory === 'language' ? 'Linguagem' : newSkillCategory === 'framework' ? 'Framework' : newSkillCategory === 'database' ? 'Banco de Dados' : 'Ferramenta'}
            </h3>
            <input
              type="text"
              value={newSkillName}
              onChange={(e) => setNewSkillName(e.target.value)}
              placeholder={`Nome da ${newSkillCategory === 'language' ? 'linguagem' : newSkillCategory === 'framework' ? 'framework' : newSkillCategory === 'database' ? 'banco' : 'ferramenta'}...`}
              className="w-full px-4 py-3 border border-gray-200 rounded-md text-sm focus:outline-none focus:border-gray-400"
              style={{ fontFamily: '"Open Sans", sans-serif' }}
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && addNewSkill(newSkillName)}
            />
            <div className="flex gap-3 mt-4">
              <Button
                variant="outline"
                onClick={() => { setShowAddSkillModal(false); setNewSkillName('') }}
                className="flex-1 h-10 rounded-md border-gray-200"
              >
                Cancelar
              </Button>
              <Button
                onClick={() => addNewSkill(newSkillName)}
                disabled={!newSkillName.trim()}
                className={cn("flex-1 h-10 rounded-md", newSkillName.trim() ? "bg-gray-900 text-white" : "bg-gray-200")}
              >
                Adicionar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Add Behavioral Competency */}
      {showAddCompetencyModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-2xl w-[440px] p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4" style={{ fontFamily: '"Open Sans", sans-serif' }}>
              Adicionar Competência Comportamental
            </h3>
            
            {/* Company suggestions section */}
            {getBehavioralCompetencies().length > 0 && (
              <div className="mb-4">
                <label className="text-xs font-medium text-gray-500 mb-2 block">Sugestões da Empresa</label>
                <div className="flex flex-wrap gap-2">
                  {getBehavioralCompetencies().map((comp, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setNewCompetencyName(comp.competency)}
                      className={cn(
                        "px-3 py-1.5 text-xs rounded-md border transition-all",
                        newCompetencyName === comp.competency
                          ? "bg-gray-100 dark:bg-gray-800 border-gray-900 dark:border-gray-50 text-gray-600 dark:text-gray-400"
                          : "bg-gray-50 border-gray-200 text-gray-500 hover:border-gray-900 dark:hover:border-gray-50 hover:text-gray-900 dark:hover:text-gray-50"
                      )}
                    >
                      {comp.competency}
                      <span className="ml-1.5 text-micro opacity-70">
                        ({comp.weight === 'Essencial' ? '●●●' : comp.weight === 'Importante' ? '●●○' : '●○○'})
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            <div className="space-y-3">
              <input
                type="text"
                value={newCompetencyName}
                onChange={(e) => setNewCompetencyName(e.target.value)}
                placeholder="Nome da competência (ex: Liderança)"
                className="w-full px-4 py-3 border border-gray-200 rounded-md text-sm focus:outline-none focus:border-gray-400"
                style={{ fontFamily: '"Open Sans", sans-serif' }}
                autoFocus
              />
              <textarea
                value={newCompetencyJustification}
                onChange={(e) => setNewCompetencyJustification(e.target.value)}
                placeholder="Justificativa (ex: Necessário para gestão de equipe)"
                className="w-full px-4 py-3 border border-gray-200 rounded-md text-sm focus:outline-none focus:border-gray-400 resize-none"
                style={{ fontFamily: '"Open Sans", sans-serif' }}
                rows={3}
              />
            </div>
            <div className="flex gap-3 mt-4">
              <Button
                variant="outline"
                onClick={() => { setShowAddCompetencyModal(false); setNewCompetencyName(''); setNewCompetencyJustification('') }}
                className="flex-1 h-10 rounded-md border-gray-200"
              >
                Cancelar
              </Button>
              <Button
                onClick={addNewCompetency}
                disabled={!newCompetencyName.trim()}
                className={cn("flex-1 h-10 rounded-md", newCompetencyName.trim() ? "bg-gray-900 text-white" : "bg-gray-200")}
              >
                Adicionar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Add Benefit */}
      {showAddBenefitModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-2xl w-[400px] p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4" style={{ fontFamily: '"Open Sans", sans-serif' }}>
              Adicionar Benefício
            </h3>
            <div className="space-y-3">
              <input
                type="text"
                value={newBenefitName}
                onChange={(e) => setNewBenefitName(e.target.value)}
                placeholder="Nome do benefício (ex: Auxílio Creche)"
                className="w-full px-4 py-3 border border-gray-200 rounded-md text-sm focus:outline-none focus:border-gray-400"
                style={{ fontFamily: '"Open Sans", sans-serif' }}
                autoFocus
              />
              <input
                type="text"
                value={newBenefitValue}
                onChange={(e) => setNewBenefitValue(e.target.value)}
                placeholder="Valor (opcional, ex: R$ 500/mês)"
                className="w-full px-4 py-3 border border-gray-200 rounded-md text-sm focus:outline-none focus:border-gray-400"
                style={{ fontFamily: '"Open Sans", sans-serif' }}
              />
            </div>
            <div className="flex gap-3 mt-4">
              <Button
                variant="outline"
                onClick={() => { setShowAddBenefitModal(false); setNewBenefitName(''); setNewBenefitValue('') }}
                className="flex-1 h-10 rounded-md border-gray-200"
              >
                Cancelar
              </Button>
              <Button
                onClick={addNewBenefit}
                disabled={!newBenefitName.trim()}
                className={cn("flex-1 h-10 rounded-md", newBenefitName.trim() ? "bg-gray-900 text-white" : "bg-gray-200")}
              >
                Adicionar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Skip Competencies Warning */}
      {showSkipCompetenciesWarning && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-2xl w-[400px] p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-status-warning/10 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-status-warning" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                  Competências incompletas
                </h3>
              </div>
            </div>
            <p className="text-sm text-gray-500 mb-4" style={{ fontFamily: '"Open Sans", sans-serif' }}>
              Recomendamos pelo menos <strong>3 competências técnicas</strong> e <strong>3 comportamentais</strong> para que a LIA encontre candidatos de forma mais assertiva.
            </p>
            <p className="text-xs text-gray-400 mb-4" style={{ fontFamily: '"Open Sans", sans-serif' }}>
              Atualmente você tem: {technicalSkills.length} técnicas e {behavioralCompetencies.filter(c => c.enabled).length} comportamentais.
            </p>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setShowSkipCompetenciesWarning(false)}
                className="flex-1 h-10 rounded-md border-gray-900 dark:border-gray-50 text-gray-600 dark:text-gray-400"
              >
                Voltar e completar
              </Button>
              <Button
                onClick={() => { setShowSkipCompetenciesWarning(false); goToNextStage() }}
                className="flex-1 h-10 rounded-md"
                style={{ backgroundColor: 'var(--status-warning)', color: 'white' }}
              >
                Confirmar assim mesmo
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Clear Draft Confirmation */}
      <ClearDraftConfirmModal
        open={showClearDraftConfirm}
        onClose={() => setShowClearDraftConfirm(false)}
        onConfirm={handleClearDraftAndReset}
      />

      {/* Modal: Calibration Profile Review */}
      {showCalibrationModal && calibrationCandidates.length > 0 && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-2xl w-[95vw] max-w-[1200px] h-[90vh] flex flex-col overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowCalibrationModal(false)}
                  className="flex items-center gap-2 text-gray-500 hover:text-gray-800 transition-colors"
                >
                  <ChevronLeft className="w-5 h-5" />
                  <span className="text-sm font-medium" style={{ fontFamily: '"Open Sans", sans-serif' }}>Review Profiles</span>
                </button>
              </div>
              <button
                onClick={() => setShowCalibrationModal(false)}
                className="p-2 rounded-md hover:bg-gray-50 transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 flex overflow-hidden">
              {/* Left Panel - Candidate Profile */}
              <div className="flex-1 overflow-y-auto p-6 border-r border-gray-200">
                {(() => {
                  const candidate = calibrationCandidates[currentCalibrationIndex]
                  if (!candidate) return null
                  
                  return (
                    <div className="space-y-6">
                      {/* Candidate Header */}
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-full bg-gray-900 dark:bg-gray-50 flex items-center justify-center text-white font-semibold text-sm">
                          {candidate.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h2 className="text-base font-semibold text-gray-800" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                              {candidate.name}
                            </h2>
                            {candidate.linkedinUrl && (
                              <a href={candidate.linkedinUrl} target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-gray-800 dark:hover:text-gray-200 transition-colors">
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
                              </a>
                            )}
                            <button className="px-3 py-1 text-xs font-medium bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-md transition-colors">
                              Full Profile ↗
                            </button>
                          </div>
                          <p className="text-xs text-gray-500 mt-1" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                            {candidate.location}
                          </p>
                          <p className="text-xs text-gray-800 mt-1" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                            ↻ {candidate.currentRole} at {candidate.currentCompany}
                          </p>
                          <p className="text-xs text-gray-500 mt-1" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                            ★ {candidate.education}
                          </p>
                        </div>
                      </div>

                      {/* Tabs */}
                      <div className="flex gap-1 border-b border-gray-200">
                        {['experience', 'education', 'skillmap'].map((tab) => (
                          <button
                            key={tab}
                            onClick={() => setCandidateProfileTab(tab as 'experience' | 'education' | 'skillmap')}
                            className={cn(
                              "px-3 py-1.5 text-sm font-medium transition-colors border-b-2",
                              candidateProfileTab === tab
                                ? "text-gray-800 border-gray-800"
                                : "text-gray-500 border-transparent hover:text-gray-800"
                            )}
                            style={{ fontFamily: '"Open Sans", sans-serif' }}
                          >
                            {tab === 'experience' ? 'Experience' : tab === 'education' ? 'Education' : 'Skill Map'}
                          </button>
                        ))}
                      </div>

                      {/* Tab Content */}
                      {candidateProfileTab === 'experience' && (
                        <div className="space-y-4">
                          {/* Highlights */}
                          <div className="p-3 bg-gray-50 rounded-md border border-gray-200">
                            <h4 className="text-sm font-semibold text-gray-800 mb-3" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                              Highlights <span className="text-gray-500 font-normal">Show more ({candidate.highlights.length})</span>
                            </h4>
                            <div className="flex flex-wrap gap-3">
                              {candidate.highlights.map((highlight, idx) => (
                                <div key={idx} className="flex items-center gap-2 px-2 py-1.5 bg-white rounded-md border border-gray-200">
                                  <div className="w-6 h-6 rounded-md bg-gray-50 flex items-center justify-center">
                                    {highlight.icon === 'trophy' && <Star className="w-3.5 h-3.5 text-status-warning" />}
                                    {highlight.icon === 'clock' && <Clock className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />}
                                    {highlight.icon === 'building' && <Building2 className="w-3.5 h-3.5 text-violet-500" />}
                                    {highlight.icon === 'rocket' && <Rocket className="w-3.5 h-3.5 text-wedo-green" />}
                                    {highlight.icon === 'globe' && <MapPin className="w-3.5 h-3.5 text-pink-500" />}
                                  </div>
                                  <div>
                                    <p className="text-xs font-semibold text-gray-800">{highlight.label}</p>
                                    <p className="text-xs text-gray-500">{highlight.value}</p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Experience Stats */}
                          <div className="flex gap-6 py-3 border-b border-gray-200">
                            <div>
                              <p className="text-xs text-gray-500 uppercase tracking-wide">Average Tenure</p>
                              <p className="text-sm font-semibold text-gray-800">{candidate.averageTenure}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500 uppercase tracking-wide">Current Tenure</p>
                              <p className="text-sm font-semibold text-gray-800">{candidate.currentTenure}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500 uppercase tracking-wide">Total Experience</p>
                              <p className="text-sm font-semibold text-gray-800">{candidate.totalExperience}</p>
                            </div>
                          </div>

                          {/* Experiences */}
                          <div className="space-y-4">
                            <h4 className="text-sm font-semibold text-gray-800" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                              Experiences
                            </h4>
                            {candidate.experiences.map((exp) => (
                              <div key={exp.id} className="flex gap-3">
                                <div className="w-8 h-8 rounded-md bg-gray-50 flex items-center justify-center flex-shrink-0">
                                  <Building2 className="w-4 h-4 text-gray-500" />
                                </div>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <p className="text-sm font-semibold text-gray-800">{exp.company}</p>
                                    <span className="text-xs text-gray-500">{exp.duration}</span>
                                  </div>
                                  <div className="flex items-center gap-2 mt-1">
                                    <p className="text-sm text-gray-800">{exp.role}</p>
                                    {exp.isPromotion && (
                                      <span className="px-2 py-0.5 text-xs font-medium text-violet-500 bg-violet-500/10 rounded-full">
                                        Promotion
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-xs text-gray-500 mt-1">{exp.period}</p>
                                  {exp.skills.length > 0 && (
                                    <p className="text-xs text-gray-500 mt-2">
                                      Skills: {exp.skills.slice(0, 6).join(' · ')} 
                                      {exp.skills.length > 6 && <button className="text-gray-600 dark:text-gray-400 ml-1">Read More</button>}
                                    </p>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {candidateProfileTab === 'education' && (
                        <div className="space-y-4">
                          {candidate.educationHistory.map((edu) => (
                            <div key={edu.id} className="flex gap-4 p-3 bg-gray-50 rounded-md">
                              <div className="w-8 h-8 rounded-md bg-white flex items-center justify-center flex-shrink-0">
                                <GraduationCap className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                              </div>
                              <div>
                                <p className="text-sm font-semibold text-gray-800">{edu.institution}</p>
                                <p className="text-sm text-gray-500">{edu.degree} in {edu.field}</p>
                                <p className="text-xs text-gray-500 mt-1">{edu.period}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {candidateProfileTab === 'skillmap' && (
                        <div className="space-y-6">
                          {candidate.skillMap.map((category, idx) => (
                            <div key={idx}>
                              <h5 className="text-sm font-semibold text-gray-800 mb-2">{category.category}</h5>
                              <div className="flex flex-wrap gap-2">
                                {category.skills.map((skill, sidx) => (
                                  <span key={sidx} className="px-2 py-1 text-micro font-medium text-gray-800 bg-gray-50 rounded-full border border-gray-200">
                                    ★ {skill}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ))}
                          
                          <div>
                            <h5 className="text-sm font-semibold text-gray-800 mb-2">Additional Skills</h5>
                            <div className="flex flex-wrap gap-2">
                              {candidate.additionalSkills.slice(0, 10).map((skill, idx) => (
                                <span key={idx} className="px-3 py-1.5 text-xs text-gray-500 bg-gray-50 rounded-md">
                                  {skill}
                                </span>
                              ))}
                              {candidate.additionalSkills.length > 10 && (
                                <span className="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400 font-medium">
                                  +{candidate.additionalSkills.length - 10} more skills
                                </span>
                              )}
                            </div>
                          </div>

                          <div>
                            <h5 className="text-sm font-semibold text-gray-800 mb-2">Languages</h5>
                            <div className="flex flex-wrap gap-2">
                              {candidate.languages.map((lang, idx) => (
                                <span key={idx} className="px-2 py-1 text-xs font-medium text-gray-800 bg-cyan-100 rounded-md">
                                  {lang}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })()}
              </div>

              {/* Right Panel - LIA Analysis & Actions */}
              <div className="w-[380px] flex flex-col bg-gray-50">
                {/* Header - Por que encontramos este perfil */}
                <div className="shrink-0 px-4 pt-4 pb-2">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-800" style={{ fontFamily: '"Open Sans", sans-serif' }}>
                      Por que encontramos este perfil
                    </h3>
                    <button 
                      onClick={() => setShowEditCriteriaModal(true)}
                      className="text-xs text-gray-600 dark:text-gray-400 hover:text-wedo-cyan-dark font-medium transition-colors"
                    >
                      Editar Critérios
                    </button>
                  </div>
                </div>

                {/* LIA Insights Box - Scrollable with max height */}
                <div className="shrink-0 px-4 max-h-[180px] overflow-y-auto">
                  <div className="p-3 bg-white rounded-md border border-gray-200 space-y-3">
                    {calibrationCandidates[currentCalibrationIndex]?.matchCriteria.map((match) => (
                      <div key={match.id} className="space-y-1">
                        <div className="flex items-start gap-2">
                          <div className={cn(
                            "px-1.5 py-0.5 rounded-full text-micro font-medium",
                            match.isMatch ? "bg-wedo-green/10 text-wedo-green" : "bg-status-error/10 text-status-error"
                          )}>
                            {match.isMatch ? '✓ Match' : '✗ No Match'}
                          </div>
                        </div>
                        <p className="text-xs font-semibold text-gray-800">
                          {match.criteria}
                          <span className="ml-1.5 text-micro text-gray-500 font-normal">
                            {match.importance === 1 ? '①②' : '①'}
                          </span>
                        </p>
                        <p className="text-micro text-gray-500 leading-relaxed">
                          {match.explanation}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Comment field - Always visible */}
                <div className="shrink-0 px-4 py-3">
                  <label className="text-xs font-medium text-gray-800 mb-1.5 block">
                    Comentário para a LIA (opcional)
                  </label>
                  <textarea
                    value={calibrationComment}
                    onChange={(e) => setCalibrationComment(e.target.value)}
                    placeholder="Ex: Gostei do perfil mas prefiro candidatos com mais experiência em startups..."
                    className="w-full px-3 py-2 border border-gray-200 rounded-md text-xs focus:outline-none focus:border-gray-400 resize-none bg-white"
                    style={{ fontFamily: '"Open Sans", sans-serif' }}
                    rows={2}
                  />
                </div>

                {/* Edit criteria note - Always visible */}
                <div className="shrink-0 px-4 pb-3">
                  <div className="p-2 bg-gray-50 rounded-md border border-gray-200">
                    <p className="text-micro text-gray-500">
 Você pode <button onClick={() => setShowEditCriteriaModal(true)} className="font-medium">fixar critérios</button> obrigatórios ou <button onClick={() => setShowEditCriteriaModal(true)} className="text-gray-600 font-medium">reordenar</button> por importância.
                    </p>
                  </div>
                </div>

                {/* Actions Footer - Always visible */}
                <div className="shrink-0 px-4 py-3 border-t border-gray-200 bg-white mt-auto">
                  {/* Navigation */}
                  <div className="flex items-center justify-between mb-3">
                    <button
                      onClick={() => setCurrentCalibrationIndex(prev => Math.max(0, prev - 1))}
                      disabled={currentCalibrationIndex === 0}
                      className={cn(
                        "p-1.5 rounded-md transition-colors",
                        currentCalibrationIndex === 0 ? "text-gray-200 cursor-not-allowed" : "text-gray-500 hover:bg-gray-50"
                      )}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    <span className="text-xs text-gray-500">
                      Profile {currentCalibrationIndex + 1}/{calibrationCandidates.length}
                    </span>
                    <button
                      onClick={() => setCurrentCalibrationIndex(prev => Math.min(calibrationCandidates.length - 1, prev + 1))}
                      disabled={currentCalibrationIndex === calibrationCandidates.length - 1}
                      className={cn(
                        "p-1.5 rounded-md transition-colors",
                        currentCalibrationIndex === calibrationCandidates.length - 1 ? "text-gray-200 cursor-not-allowed" : "text-gray-500 hover:bg-gray-50"
                      )}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Approve/Reject Buttons */}
                  <div className="flex gap-2">
                    <button
                      onClick={handleApproveCandidate}
                      className="flex-1 py-2.5 px-3 bg-gray-900 text-white rounded-md font-medium text-xs hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 transition-colors flex items-center justify-center gap-1.5"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Aprovar
                      <span className="text-micro opacity-80">A</span>
                    </button>
                    <button
                      onClick={handleRejectCandidate}
                      className="flex-1 py-2.5 px-3 bg-white text-status-error border border-status-error rounded-md font-medium text-xs hover:bg-status-error/5 transition-colors flex items-center justify-center gap-1.5"
                    >
                      <X className="w-3.5 h-3.5" />
                      Reprovar
                      <span className="text-micro opacity-80">R</span>
                    </button>
                  </div>

                  <p className="text-micro text-gray-500 text-center mt-2">
                    Isso apenas calibra o agente e não envia emails.
                  </p>

                  {/* Progress */}
                  <div className="mt-2 flex items-center justify-center gap-1.5">
                    <span className="text-micro text-gray-500">Aprovados:</span>
                    <div className="flex gap-1">
                      {[0, 1, 2].map((i) => (
                        <div
                          key={i}
                          className={cn(
                            "w-5 h-5 rounded-full flex items-center justify-center text-micro font-medium",
                            approvedCandidates.length > i
                              ? "bg-wedo-green text-white"
                              : "bg-gray-200 text-gray-500"
                          )}
                        >
                          {approvedCandidates.length > i ? '✓' : i + 1}
                        </div>
                      ))}
                    </div>
                    <span className="text-micro text-gray-500">de 3</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

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
    onStageChange: (stage) => console.log('Stage changed to:', stage),
    onPendingChanges: (hasPending) => console.log('Has pending changes:', hasPending)
  })
  
  return (
    <ExpandedChatProvider value={wizardState}>
      <ExpandedChatModalContent {...props} />
    </ExpandedChatProvider>
  )
}
