import { type JobVacancy } from "@/services/lia-api"
import type { Job as PageJob } from "@/components/jobs/jobsPageTypes"

export interface InterviewStage {
  id?: string | number
  stageName?: string
  stage_name?: string
  order?: number
  sla?: number
  type?: string
  interviewers?: string[]
  format?: string
  duration?: number
  [key: string]: unknown
}

export interface ScreeningQuestion {
  id?: string
  text: string
  category: string
  type?: string
  weight?: number
  is_eliminatory?: boolean
  expected_answer?: string
}

export interface PipelineTemplate {
  id: string
  company_id: string
  name: string
  description: string | null
  stages: { name: string; order: number; type: string; sla_days: number; instructions?: string }[]
  is_default: boolean
  is_active: boolean
  usage_count: number
}

export interface Job {
  id: number
  jobId: string
  backendId: string
  title: string
  department: string
  location: string
  workModel: "presencial" | "híbrido" | "remoto"
  type: string
  seniority: string
  salary: string
  benefits: (string | { id?: string; name: string })[]
  status: string
  stage: string
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
  funnel?: Record<string, number>
  publishedLinkedIn: boolean
  publishedWebsite: boolean
  publishedIndeed?: boolean
  isConfidential: boolean
  isAffirmative?: boolean
  affirmativeType?: 'pcd' | 'racial' | 'gender' | 'age' | 'lgbtqia+'
  nps: number
  budget?: number
  budgetUsed?: number
  nextActions?: string[]
  urgencyLevel: 1 | 2 | 3 | 4 | 5
  hiringProcess?: string[]
  targetAudience?: string
  interviewStages?: InterviewStage[]
  visibility?: "public" | "internal" | "confidential" | "hidden"
  accessList?: string[]
  maskedCompanyName?: string
  salaryRange?: { min: number; max: number; currency: string }
  salaryMin?: number
  salaryMax?: number
  bonusMin?: number
  bonusMax?: number
  targetSector?: string
  targetSegment?: string
  languages?: { language: string; level: string; required?: boolean }[] | Record<string, unknown>[]
  technicalRequirements?: { category: string; technology: string; level: string; required: boolean }[] | Record<string, unknown>[]
  behavioralCompetencies?: { competency: string; weight: string }[] | Record<string, unknown>[]
  screeningQuestions?: ScreeningQuestion[]
  eligibilityQuestions?: { id?: string; question: string; type?: string; category?: string; enabled?: boolean }[]
  confidentialityConfig?: {
    can_reveal_company_name?: boolean
    can_discuss_salary?: boolean
    can_discuss_benefits?: boolean
    can_discuss_location?: boolean
    masked_intro?: string
  }
  compensation_policy_id?: string
  createdBy?: string
  createdByEmail?: string
  createdAt?: string
  publicSlug?: string
  [key: string]: unknown
}

export interface EditJobModalProps {
  isOpen: boolean
  onClose: () => void
  job: PageJob | null
  onSave: (jobId: string, updates: Partial<JobVacancy>) => Promise<void>
}

export interface CompanyDefaultQuestion {
  id: string
  question_text: string
  question_type: string
  options?: string[]
  category?: string
  is_required: boolean
  is_eliminatory: boolean
}
