export interface JobVacancy {
  id: string
  title: string
  department?: string
  location?: string
  workModel: 'remote' | 'hybrid' | 'onsite'
  status: 'draft' | 'active' | 'paused' | 'closed' | 'cancelled'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  
  seniority?: string
  salaryMin?: number
  salaryMax?: number
  salaryCurrency?: string
  
  requiredSkills?: string[]
  niceToHaveSkills?: string[]
  
  description?: string
  descriptionPreview?: string
  
  hiringManagerId?: string
  hiringManagerName?: string
  recruiterId?: string
  recruiterName?: string
  
  candidatesCount: number
  applicationsCount: number
  interviewsScheduled: number
  offersExtended: number
  
  openDate?: string
  targetCloseDate?: string
  actualCloseDate?: string
  daysOpen?: number
  
  createdAt: string
  updatedAt: string
  publishedAt?: string
  
  confidenceScore?: number
  fieldOrigins?: Record<string, FieldOrigin>
  
  tags?: string[]
  isConfidential?: boolean
}

export interface FieldOrigin {
  source: 'user' | 'lia_suggested' | 'lia_confirmed' | 'company_config' | 'market_benchmark'
  confidence: number
  timestamp: string
}

export interface JobsPageState {
  jobs: JobVacancy[]
  selectedJob: JobVacancy | null
  isLoading: boolean
  filters: JobFilters
  sortConfig: JobSortConfig
  viewMode: 'list' | 'cards' | 'kanban'
  currentTab: 'all' | 'active' | 'drafts' | 'closed'
}

export interface JobFilters {
  status?: string[]
  department?: string[]
  location?: string[]
  priority?: string[]
  hiringManager?: string[]
  recruiter?: string[]
  dateRange?: {
    start: string
    end: string
  }
  hasApplicants?: boolean
  search?: string
}

export interface JobSortConfig {
  column: 'title' | 'status' | 'candidates' | 'createdAt' | 'daysOpen' | 'priority'
  direction: 'asc' | 'desc'
}

export interface JobAction {
  type: 'edit' | 'duplicate' | 'pause' | 'close' | 'delete' | 'publish' | 'view_candidates'
  jobId: string
}

export interface JobMetrics {
  totalJobs: number
  activeJobs: number
  draftJobs: number
  closedJobs: number
  totalCandidates: number
  avgTimeToFill: number
  avgCandidatesPerJob: number
}

export interface WizardStep {
  id: number
  name: string
  description: string
  isComplete: boolean
  isOptional: boolean
  fieldCount: number
  completedFields: number
}
