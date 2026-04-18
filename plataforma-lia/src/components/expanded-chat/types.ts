/**
 * Expanded Chat Modal — Local Types
 *
 * Sprint 4.1 — 2026-03-27
 * Tipos locais do expanded-chat-modal extraídos para arquivo separado.
 * Não duplica tipos já exportados por ExpandedChatContext.
 * Sem dependências React — compatível com migração Vue.
 */

import type { WSIQuestion, TechnicalSkill, BehavioralCompetency, SalaryInfo, DetectedCriteria, BasicInfoFields } from './ExpandedChatContext'
import type { ToolCall, ToolExecutionResult } from './hooks'
import type { CompensationAnalysisResult } from '../job-creation/compensation-analysis-panel'
import type { TechnicalSkillSuggestion, BehavioralCompetencySuggestion } from '../job-creation/competencies-chat-message'
import type { VacancySummary } from '../job-creation/vacancy-search-results'
import type { VacancyFullDetails } from '../job-creation/vacancy-full-summary'
import type { ParecerLIAData } from '../chat/parecer-lia-card'

export interface WSIQuestionCandidate extends WSIQuestion {
  selected: boolean
  batch: number
  isWSI?: boolean
  competency?: string
  framework?: string
  category?: 'technical' | 'behavioral' | 'autodeclaracao_contexto' | 'micro_case' | 'situacional' | 'fit' | 'autodeclaracao'
}

// Calibration interfaces
export interface CalibrationCandidateExperience {
  id: string
  company: string
  role: string
  period: string
  duration: string
  location?: string
  isPromotion?: boolean
  skills: string[]
}

export interface CalibrationCandidateEducation {
  id: string
  institution: string
  degree: string
  field: string
  period: string
}

export interface CalibrationMatchCriteria {
  id: string
  criteria: string
  isMatch: boolean
  explanation: string
  importance: 1 | 2
}

export interface CalibrationCandidate {
  id: string
  name: string
  photoUrl?: string
  linkedinUrl?: string
  currentRole: string
  currentCompany: string
  location: string
  education: string
  highlights: {
    icon: string
    label: string
    value: string
  }[]
  experiences: CalibrationCandidateExperience[]
  educationHistory: CalibrationCandidateEducation[]
  skillMap: {
    category: string
    skills: string[]
  }[]
  languages: string[]
  additionalSkills: string[]
  matchCriteria: CalibrationMatchCriteria[]
  overallNota: number
  averageTenure: string
  currentTenure: string
  totalExperience: string
}

/**
 * Flexible shape for basicInfoFields when coming from the backend draft mapping.
 * applyPendingDraft reads English keys (jobTitle, locality, etc.) from this shape
 * even though BasicInfoFields uses Portuguese keys — both are accepted here.
 */
export type WizardBasicInfoDraftFields = BasicInfoFields | {
  jobTitle?: string
  department?: string
  area?: string
  seniority?: string
  locality?: string
  workModel?: string
  employmentType?: string
  manager?: string
  managerEmail?: string
  isAffirmative?: boolean
}

export interface WizardDraftData {
  currentStage?: string
  basicInfoFields?: WizardBasicInfoDraftFields
  technicalSkills?: TechnicalSkill[]
  behavioralCompetencies?: BehavioralCompetency[]
  salaryInfo?: SalaryInfo
  wsiQuestions?: WSIQuestion[]
  detectedCriteria?: DetectedCriteria
  generatedJobDescription?: string
  [key: string]: unknown
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  contextData?: Record<string, unknown>
  isTyping?: boolean
  isProcessing?: boolean
  processingState?: 'thinking' | 'analyzing' | 'searching' | 'generating' | 'completed'
  messageType?: 'text' | 'compensation' | 'competencies' | 'vacancy-search' | 'vacancy-summary' | 'tool-confirmation' | 'tool-execution-feedback' | 'proactive' | 'action-result' | 'parecer-lia' | 'detected-fields' | 'pipeline-rail'
  pipelineRail?: import('@/components/chat/pipeline-rail-card').PipelineRailCardData
  toolCall?: ToolCall
  toolExecutionResult?: ToolExecutionResult
  compensationAnalysis?: CompensationAnalysisResult
  competenciesSuggestions?: {
    technicalSkills: TechnicalSkillSuggestion[]
    behavioralCompetencies: BehavioralCompetencySuggestion[]
  }
  vacancySearchResults?: VacancySummary[]
  vacancyFullDetails?: VacancyFullDetails
  proactiveData?: {
    actionId: string
    severity: string
    actionLabel: string
    suggestedAction: Record<string, unknown>
  }
  isFieldUpdate?: boolean
  awaitingStageConfirmation?: string
  actionType?: string
  actionResult?: Record<string, unknown>
  detectedFieldsData?: Array<{ label: string; value: string; confidence?: "high" | "medium" | "low" }>
  detectedFields?: Array<{ label: string; value: string; confidence?: "high" | "medium" | "low" }>
  parecerData?: ParecerLIAData
  executionPlan?: import('@/components/chat/plan-progress-card').ExecutionPlanData
  execution_plan?: import('@/components/chat/plan-progress-card').ExecutionPlanData
}

// Fast Track wizard mode types
export type WizardMode = 'pre_wizard' | 'create_from_scratch' | 'fast_track' | 'general'
export type FastTrackState = 'initial' | 'collecting_criteria' | 'searching' | 'selecting' | 'reviewing' | 'adjusting' | 'publishing' | 'completed'

export interface ExpandedChatModalProps {
  isOpen: boolean
  onClose: () => void
  onMinimize?: () => void
  initialMessage?: string
  initialMessages?: Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: Date }>
  contextTitle?: string
  inline?: boolean
  mode?: 'general' | 'job-creation'
  onJobCreated?: () => void
  onReturnToLateral?: (messages: Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: Date }>) => void
  hideModeButtons?: boolean
  onOrchestratedMessage?: (message: string) => Promise<{
    content: string
    ui_action?: string | null
    ui_action_params?: Record<string, unknown>
  }>
  onFullscreenChange?: (isFullscreen: boolean) => void
  onMessagesUpdate?: (messages: Array<{ id: string; role: 'user' | 'assistant'; content: string; timestamp: Date }>) => void
}
