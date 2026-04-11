import type { RecruitmentStage, SubStatus } from "@/lib/recruitment-stages"
import type { SubStatusOption } from "@/components/settings/recruitment-journey.types"

export interface InterviewStageFromJob {
  stageName: string
  order: number
  sla?: number
  type: 'automated' | 'manual' | 'hybrid' | 'system' | 'interview' | 'test' | 'custom'
}

export interface DynamicStage {
  id: string
  name: string
  displayName: string
  order: number
  color: string
  stageType: 'active' | 'final'
  isInitial?: boolean
  isFinal?: boolean
  isHired?: boolean
  isRejection?: boolean
  isActive?: boolean
  actionBehavior?: string
  defaultChannel?: string
  subStatuses?: SubStatusOption[]
}

export interface KanbanCandidate {
  id: string
  name: string
  email?: string
  phone?: string
  avatar?: string
  role?: string | null
  currentTitle?: string
  currentCompany?: string | null
  company?: string
  location?: string | null
  jobTitle?: string | null
  jobId?: string | null
  recruiter?: string | null
  manager?: string | null
  score?: number | null
  fitScore?: number | null
  wsiScore?: number | null
  warnings?: number
  source?: string
  origin?: 'web' | 'whatsapp' | 'sourcing' | 'ats' | string
  stage?: string
  status?: string
  subStatus?: string
  sub_status?: string
  appliedDate?: string
  mappedDate?: string
  addedDate?: string
  experience?: string
  education?: string
  skills?: string[]
  languages?: string[]
  expectedSalary?: string
  currentSalary?: string
  contractType?: string
  workModel?: string
  availability?: string
  linkedin?: string
  github?: string
  portfolio?: string
  needsAction?: boolean
  actionBehavior?: string
  lastActionDate?: string
  slaHours?: number
  agendada?: string
  interviewDate?: string
  stageId?: string
  bigFive?: {
    openness: number
    conscientiousness: number
    extraversion: number
    agreeableness: number
    neuroticism: number
  } | null
  workHistory?: Array<{
    company: string
    title: string
    startDate: string
    endDate: string | null
    description?: string
  }> | null
  educationHistory?: Array<{
    institution: string
    degree: string
    field: string
    startYear: number
    endYear: number | null
  }> | null
  is_hired?: boolean
  hired_job_title?: string
  is_blacklisted?: boolean
  blacklist_reason?: string
  candidateCode?: string
  liaScore?: number | null
  skillsMatch?: number
  technicalTestScore?: number | null
  englishTestScore?: number | null
  bigFiveScores?: Record<string, number>
  position?: string
}

export interface CandidatesDataMap {
  [stageId: string]: KanbanCandidate[]
}

export interface DragState {
  candidate: KanbanCandidate | null
  fromColumn: string | null
  overColumn: string | null
}

export interface TransitionState {
  isOpen: boolean
  candidates: KanbanCandidate[]
  fromStage: string
  toStage: string
}

export interface KanbanViewMode {
  mode: 'kanban' | 'table'
}

export interface KanbanFilters {
  search: string
  stages: string[]
  sources: string[]
  scores: { min: number; max: number }
}
