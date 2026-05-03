export interface JobFunnel {
  total: number
  screening: number
  interview: number
  final: number
  hired: number
}

export interface LiaMetrics {
  pipeline_lia: number
  triagens_agendadas: number
  triagens_realizadas: number
  sem_resposta: number
  entrevistas_agendadas: number
}

export interface JobFilters {
  status?: {
    statuses?: string[]
    priorities?: string[]
    stages?: string[]
  }
  dates?: {
    openedWithinDays?: number
    closingWithinDays?: number
    noActivityDays?: number
  }
  team?: {
    recruiters?: string[]
    managers?: string[]
    departments?: string[]
  }
  position?: {
    levels?: string[]
    types?: string[]
    workModels?: string[]
    locations?: string[]
  }
  funnel?: {
    minCandidates?: number
    maxCandidates?: number
    emptyPipeline?: boolean
    stuckInStage?: string
  }
  metrics?: {
    minNPS?: number
    maxDaysOpen?: number
    lowConversion?: boolean
  }
  publishing?: {
    channels?: string[]
    unpublished?: boolean
  }
}

export interface TechnicalRequirement {
  category: "Linguagens" | "Frameworks" | "Banco de Dados" | "Cloud" | "Containers" | "CI/CD" | "Outros"
  technology: string
  level: "Básico" | "Intermediário" | "Avançado"
  required: boolean
}

export interface Language {
  language: string
  level: "Básico" | "Intermediário" | "Avançado" | "Fluente"
  required: boolean
}

export interface BehavioralCompetency {
  competency: string
  weight: "Essencial" | "Importante" | "Desejável"
}

export interface InterviewStage {
  id?: string | number
  stageName?: string
  stage_name?: string
  interviewers?: string[]
  format?: string
  duration?: number
  schedulingWindow?: string
  scheduling_window?: string
  hasScript?: boolean
  has_script?: boolean
  [key: string]: unknown
}

export interface ScreeningQuestion {
  id: string | number
  question: string
  type?: string
  options?: string[]
  expectedAnswer?: string
  weight?: number
  required?: boolean
}

export interface SalaryRange {
  min: number
  max: number
  currency: string
  bonus?: {
    min: number
    max: number
    criteria: string
  }
}

export interface OrganizationalStructure {
  directManager: string
  teamSize: number
  teamComposition: Array<{
    role: string
    count: number
    level: string
  }>
}

export interface Timeline {
  shortlistDeadline?: string
  totalWeeks: number
  weeklyBreakdown: Array<{
    week: number
    focus: string
    deadline: string
    status: "pending" | "in_progress" | "completed"
  }>
}

export interface GovernanceRules {
  autoScheduleInterviews: boolean
  autoSendNegativeFeedback: boolean
  requiresValidationBeforeShortlist: boolean
}

// Eligibility Questions - Pre-screening eliminatory questions
export type EligibilityQuestionType = 
  | "language"           // Language proficiency check
  | "affirmative"        // Affirmative action eligibility
  | "availability"       // Work schedule/availability
  | "location"           // Location/relocation
  | "legal"              // Work authorization
  | "experience"         // Minimum experience
  | "education"          // Minimum education
  | "salary_expectation" // Salary expectation alignment
  | "custom"             // Custom question

export interface EligibilityQuestion {
  id: string
  type: EligibilityQuestionType
  question: string
  expected_answer?: string     // For language type: required language (e.g., "Inglês")
  min_years?: number           // For experience type: minimum years required
  min_education?: string       // For education type: minimum education level
  group?: string               // For affirmative: "PCD", "Negro/Pardo", "Mulheres", etc.
  locations?: string[]         // For location type: acceptable locations
  salary_max?: number          // For salary type: maximum salary expectation
  required: boolean
  disqualify_on_fail: boolean  // If true, candidate is eliminated if they don't meet criteria
  order: number
}

// Confidentiality Configuration - Controls what LIA can reveal
export interface ConfidentialityConfig {
  can_reveal_company_name: boolean    // Can LIA say the company name?
  reveal_after_stage?: string         // Stage after which company name can be revealed
  masked_intro?: string               // "Uma empresa líder no segmento de pagamentos"
  can_discuss_salary: boolean         // Can LIA discuss salary range?
  can_discuss_benefits: boolean       // Can LIA discuss benefits?
  can_discuss_location: boolean       // Can LIA discuss work location?
  standard_responses?: {              // Pre-defined responses for common questions
    company_identity?: string         // "Por enquanto, estou representando uma empresa em processo de recrutamento confidencial"
    salary_info?: string              // "A faixa salarial será discutida em etapas posteriores"
  }
}

export type JobStatus = "Ativa" | "Aprovada" | "Aguardando aprovação" | "Reaberta" | "Paralisada" | "Interna" | "Fechada (preenchida)" | "Fechada (expirada)" | "Cancelada" | "Rascunho" | "Arquivada" | "Concluída"

export type JobStage = "Planejamento" | "Aprovação" | "Publicada" | "Triagem" | "Entrevistas" | "Finalização" | "Encerrada"

export type JobPriority = "alta" | "média" | "baixa"

export type JobVisibility = "public" | "internal" | "confidential" | "hidden"

export type JobApprovalStatus = "pendente" | "aprovada" | "rejeitada"

export type JobWorkModel = "presencial" | "híbrido" | "remoto"

import type { ScreeningConfig } from "@/hooks/recruitment/useScreeningConfig"

export interface Job {
  id: number
  jobId: string
  backendId: string
  title: string
  department: string
  location: string
  workModel: JobWorkModel
  type: string
  /** Senioridade canônica da vaga (SSOT em `lib/schemas/job.schema.ts`).
   * O campo legacy `level` foi removido na Task #539 — sempre leia via
   * `getJobSeniority(job)` para tolerar fontes parcialmente preenchidas.
   * Task #559 — opcional: mappers propagam `undefined` quando o backend
   * não devolve `seniority_level`/`seniority` em vez de chutar `'Pleno'`. */
  seniority?: string
  salary: string
  benefits: string[]
  status: JobStatus
  stage: JobStage
  openDate: string
  deadline?: string
  deadlineScreening?: string
  deadlineShortlist?: string
  deadlineClosing?: string
  description: string
  requirements: string[]
  manager: string
  managerEmail: string
  recruiter: string
  recruiterEmail: string
  priority: JobPriority
  funnel: JobFunnel
  liaMetrics?: LiaMetrics
  publishedLinkedIn: boolean
  publishedWebsite: boolean
  publishedIndeed?: boolean
  isConfidential: boolean
  isAffirmative?: boolean
  nps: number
  budget?: number
  budgetUsed?: number
  nextActions: string[]
  urgencyLevel: 1 | 2 | 3 | 4 | 5
  approvalStatus: JobApprovalStatus
  tags?: string[]
  hiringProcess?: string[]
  targetAudience?: string
  screeningQuestions?: ScreeningQuestion[]
  interviewStages?: InterviewStage[]
  technicalRequirements?: TechnicalRequirement[] | Record<string, unknown>[]
  languages?: Language[] | Record<string, unknown>[]
  behavioralCompetencies?: BehavioralCompetency[] | Record<string, unknown>[]
  salaryRange?: SalaryRange | Record<string, unknown>
  organizationalStructure?: OrganizationalStructure
  timeline?: Timeline
  governanceRules?: GovernanceRules
  whatsappTemplateType?: "cold" | "reengagement" | "confidential"
  targetSector?: string
  targetSegment?: string
  conversationId?: string
  visibility?: JobVisibility
  accessList?: string[]
  maskedCompanyName?: string
  excludeFromSync?: boolean
  screeningConfig?: ScreeningConfig
  screeningStatus?: 'not_configured' | 'not_started' | 'active' | 'paused' | 'completed'
  publicSlug?: string
  createdBy?: string
  createdByEmail?: string
  closedAt?: string
  publishedAt?: string
  createdAt?: string
  updatedAt?: string
  funnelData?: Record<string, number>
  eligibilityQuestions?: EligibilityQuestion[]
  // Phase 4H — source + wizard_stage
  source?: 'wizard' | 'ats_import' | 'ats_external' | 'manual'
  wizardStage?: string  // intake|jd_enrichment|bigfive|salary|competency|wsi_questions|eligibility|review|published|calibration|handoff
  confidentialityConfig?: ConfidentialityConfig
  enrichedJd?: {
    description?: string
    responsibilities?: string[]
    technical_skills?: string[]
    behavioral_competencies?: string[]
    generated_jd_text?: string
    updated_at?: string
  }
  is_published?: boolean
  published_channels?: string[]
  readinessStage?: string
  readinessBlockers?: string[]
}

export type ViewMode = 'compact' | 'expanded'

export type PreviewTab = 'overview' | 'pipeline' | 'screening' | 'lia-performance'

export interface WSIBlock {
  id: number | string
  name: string
  description: string
  duration: string
  editable: boolean
  type: string
}

export interface WSIAutomaticMessage {
  title: string
  message: string
  note: string
}
