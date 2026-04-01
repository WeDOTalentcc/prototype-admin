// Filter types extracted from CandidatesFilterPanel
// Shared with hooks/use-candidate-filters

export interface TableFilters {
  statuses: string[]
  tags: string[]
  seniorityLevels: string[]
  workModels: string[]
  contractTypes: string[]
  minExperience?: number
  maxExperience?: number
  minScore?: number
  maxScore?: number
  minSalary?: number
  maxSalary?: number
  locations: string[]
  remoteOnly: boolean
  hasEmail: boolean
  hasPhone: boolean
  hasLinkedin: boolean
  sources: string[]
  jobTitles: string[]
  skills: string[]
  companies: string[]
  industries: string[]
  companySizes: string[]
  universities: string[]
  degrees: string[]
  fieldsOfStudy: string[]
  languages: string[]
  isOpenToWork: boolean
  isDecisionMaker: boolean
  isTopUniversities: boolean
  isStartup: boolean
  hasGithub: boolean
  hasPortfolio: boolean
  softSkills: string[]
  certifications: string[]
  willingToRelocate: boolean | null
  mobility: boolean | null
  updatedAtFrom?: string
  updatedAtTo?: string
  lastContactedFrom?: string
  lastContactedTo?: string
  availabilityWindow?: "immediate" | "15_days" | "30_days" | "60_days"
  shortlistedDateFrom?: string
  shortlistedDateTo?: string
  shortlistedVacancyOrigin?: string
  placementDateFrom?: string
  placementDateTo?: string
  placementVacancyDestination?: string
  placementClientCompany?: string
  specificVacancyId?: string
  registrationDateFrom?: string
  registrationDateTo?: string
}
