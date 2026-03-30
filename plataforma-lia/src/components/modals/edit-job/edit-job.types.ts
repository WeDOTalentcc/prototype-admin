import { type JobVacancy } from "@/services/lia-api"

export interface InterviewStage {
  stageName: string
  order: number
  sla: number
  type: automated | manual | hybrid
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
  level: string
  salary: string
  benefits: string[]
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
  funnel: { total: number; screening: number; interview: number; final: number; hired: number }
  publishedLinkedIn: boolean
  publishedWebsite: boolean
  publishedIndeed?: boolean
  isConfidential: boolean
  isAffirmative?: boolean
  affirmativeType?: pcd | racial | gender | age | lgbtqia+
  nps: number
  budget?: number
  budgetUsed?: number
  nextActions: string[]
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
  languages?: { language: string; level: string; required?: boolean }[]
  technicalRequirements?: { category: string; technology: string; level: string; required: boolean }[]
  behavioralCompetencies?: { competency: string; weight: string }[]
  screeningQuestions?: { id?: string; text: string; category: string; type?: string; weight?: number; is_eliminatory?: boolean; expected_answer?: string }[]
  eligibilityQuestions?: { id?: string; question: string; type?: string; category?: string; enabled?: boolean }[]
  confidentialityConfig?: {
    can_reveal_company_name?: boolean
    can_discuss_salary?: boolean
    can_discuss_benefits?: boolean
    can_discuss_location?: boolean
    masked_intro?: string
  }
  createdBy?: string
  createdByEmail?: string
  createdAt?: string
  publicSlug?: string
}

export interface EditJobModalProps {
  isOpen: boolean
  onClose: () => void
  job: Job | null
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
