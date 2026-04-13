import type { JobBenefit } from '@/types/benefits'

export type { JobBenefit } from '@/types/benefits'
export type Benefit = JobBenefit

export type WizardStage = 'input-evaluation' | 'job-description' | 'competencies' | 'salary' | 'wsi-questions' | 'review-publish' | 'search-calibration'

export type WizardPhase = 'construction' | 'activation' | 'selection'

export interface WizardPhaseConfig {
  id: WizardPhase
  label: string
  stages: WizardStage[]
}

export interface TechnicalSkill {
  id: string
  name: string
  level: 'Básico' | 'Intermediário' | 'Avançado'
  required: boolean
  category: 'language' | 'framework' | 'database' | 'tool'
  weight: number
  weightJustification?: string
  isWeightInferred?: boolean
}

export interface BehavioralCompetency {
  id: string
  name: string
  weight: number
  justification: string
  enabled: boolean
  weightJustification?: string
  isWeightInferred?: boolean
}

export interface SalaryInfo {
  minSalary: string
  maxSalary: string
  minBonus: string
  maxBonus: string
  bonusCriteria: string
  benefits: JobBenefit[]
}

export interface WSIQuestion {
  id: string
  question: string
  type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  required: boolean
  options?: string[]
  expectedAnswer?: string | number | boolean
  correctOptionIndex?: number
}

export interface WSIQuestionCandidate extends WSIQuestion {
  selected: boolean
  batch: number
  isWSI?: boolean
  competency?: string
  framework?: string
  category?: 'technical' | 'behavioral' | 'autodeclaracao_contexto' | 'micro_case' | 'situacional' | 'fit' | 'autodeclaracao'
}

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
  highlights: { icon: string; label: string; value: string }[]
  experiences: CalibrationCandidateExperience[]
  educationHistory: CalibrationCandidateEducation[]
  skillMap: { category: string; skills: string[] }[]
  languages: string[]
  additionalSkills: string[]
  matchCriteria: CalibrationMatchCriteria[]
  overallNota: number
  averageTenure: string
  currentTenure: string
  totalExperience: string
}

export interface WizardStageConfig {
  id: WizardStage
  title: string
  subtitle: string
  panelTitle: string
  liaMessage: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  contextData?: Record<string, unknown>
  isTyping?: boolean
  isProcessing?: boolean
  processingState?: 'thinking' | 'analyzing' | 'searching' | 'generating' | 'completed'
}

export interface DetectedCriteria {
  cargo: string | null
  gestorArea: string | null
  responsabilidades: string[]
  competenciasTecnicas: string[]
  competenciasComportamentais: string[]
  senioridadeIdiomas: string | null
  modeloTrabalho: string | null
  localizacao: string | null
  tipoContrato: string | null
  salario: string | null
  departamento: string | null
  isAffirmative: boolean | null
  affirmativeCriteriaPrimary: string | null
  affirmativeCriteriaSecondary: string | null
  affirmativeDescription: string | null
}

export interface BasicInfoFields {
  cargo: string
  area: string
  gestor: string
  localidade: string
  modeloTrabalho: string
  tipoContrato: string
}

export interface JobConfig {
  urgencyLevel: number
  visibility: 'public' | 'internal' | 'confidential'
  isConfidential: boolean
  isAffirmative: boolean
  deadline: string
  deadlineScreening: string
  deadlineShortlist: string
  languages: { name: string; level: string }[]
  hybridDaysOnsite?: number
}

export interface PublishingPlatform {
  id: string
  name: string
  type: 'ats' | 'jobboard' | 'website'
  enabled: boolean
  logo?: string
}

export interface CompanyConfig {
  workModel?: string
  hybridDaysOnsite?: number
  employmentTypes?: string[]
  techStack?: string[]
  values?: string[]
  coreCompetencies?: string[]
  departments?: { id: string; name: string }[]
  benefits?: { name: string; category: string; value?: number; is_active: boolean }[]
  evpBullets?: string[]
  headquarters?: string
  locations?: string[]
}

export interface SalaryBenchmark {
  internal?: { min: number; max: number; median: number; sample_size: number; trend?: string }
  market?: { min: number; max: number; median: number; sources: string[]; confidence: string; learning_adjusted?: boolean }
  combined?: { min: number; max: number; median: number; confidence: string; recommendation: string }
}

export interface SkillWeightInference {
  weight: number
  justificativa: string
}

export type FieldOrigin = 'company_config' | 'job_history' | 'detected' | 'market_benchmark' | 'manual' | 'ai_suggestion'

export interface CompanyDefaultQuestion {
  id: string
  question: string
  type: 'yes-no' | 'numeric' | 'open' | 'multiple-choice'
  enabled: boolean
  fromConfig: boolean
}
