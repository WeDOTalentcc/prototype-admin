/**
 * useCandidateFilters — Sprint E god object extraction
 *
 * Extracted from candidates-page.tsx (12375 lines).
 * Contains all filter-related state and logic for the candidates table.
 *
 * TODO (Sprint E phase 2): Move the useState declarations from candidates-page.tsx
 * (lines ~3430-3480) and related filter handlers into this hook, then import
 * and call it from CandidatesPage.
 */
"use client"

import { useState, useCallback } from "react"

// ── Types ─────────────────────────────────────────────────────────────────────

export interface TableFilters {
  // Status e Tags
  statuses: string[]
  tags: string[]

  // Perfil profissional
  seniorityLevels: string[]
  workModels: string[]
  contractTypes: string[]

  // Experiência e Score
  minExperience?: number
  maxExperience?: number
  minScore?: number
  maxScore?: number

  // Salário
  minSalary?: number
  maxSalary?: number

  // Localização
  locations: string[]
  remoteOnly: boolean

  // Contato
  hasEmail: boolean
  hasPhone: boolean
  hasLinkedin: boolean

  // Fonte
  sources: string[]

  // Campos adicionais do modal de filtros avançados
  jobTitles: string[]
  skills: string[]
  companies: string[]
  industries: string[]
  companySizes: string[]
  universities: string[]
  degrees: string[]
  fieldsOfStudy: string[]
  languages: string[]

  // Indicadores de perfil
  isOpenToWork: boolean
  isDecisionMaker: boolean
  isTopUniversities: boolean
  isStartup: boolean

  // Novos filtros
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

export function getDefaultTableFilters(): TableFilters {
  return {
    statuses: [],
    tags: [],
    seniorityLevels: [],
    workModels: [],
    contractTypes: [],
    minExperience: undefined,
    maxExperience: undefined,
    minScore: undefined,
    maxScore: undefined,
    minSalary: undefined,
    maxSalary: undefined,
    locations: [],
    remoteOnly: false,
    hasEmail: false,
    hasPhone: false,
    hasLinkedin: false,
    sources: [],
    jobTitles: [],
    skills: [],
    companies: [],
    industries: [],
    companySizes: [],
    universities: [],
    degrees: [],
    fieldsOfStudy: [],
    languages: [],
    isOpenToWork: false,
    isDecisionMaker: false,
    isTopUniversities: false,
    isStartup: false,
    hasGithub: false,
    hasPortfolio: false,
    softSkills: [],
    certifications: [],
    willingToRelocate: null,
    mobility: null,
    updatedAtFrom: undefined,
    updatedAtTo: undefined,
    lastContactedFrom: undefined,
    lastContactedTo: undefined,
    availabilityWindow: undefined,
    shortlistedDateFrom: undefined,
    shortlistedDateTo: undefined,
    shortlistedVacancyOrigin: undefined,
    placementDateFrom: undefined,
    placementDateTo: undefined,
    placementVacancyDestination: undefined,
    placementClientCompany: undefined,
    specificVacancyId: undefined,
    registrationDateFrom: undefined,
    registrationDateTo: undefined,
  }
}

// ── Hook ─────────────────────────────────────────────────────────────────────

export interface UseCandidateFiltersReturn {
  tableFilters: TableFilters
  setTableFilters: React.Dispatch<React.SetStateAction<TableFilters>>
  showTableFiltersPanel: boolean
  setShowTableFiltersPanel: React.Dispatch<React.SetStateAction<boolean>>
  newSoftSkillFilter: string
  setNewSoftSkillFilter: React.Dispatch<React.SetStateAction<string>>
  newCertificationFilter: string
  setNewCertificationFilter: React.Dispatch<React.SetStateAction<string>>
  columnFilters: Record<string, string[] | unknown>
  setColumnFilters: React.Dispatch<React.SetStateAction<Record<string, string[] | unknown>>>
  openFilterDropdown: string | null
  setOpenFilterDropdown: React.Dispatch<React.SetStateAction<string | null>>
  resetFilters: () => void
  hasActiveFilters: boolean
}

/**
 * Centralizes all candidates table filter state.
 * Ready to be imported in CandidatesPage as part of Sprint E phase 2 extraction.
 */
export function useCandidateFilters(): UseCandidateFiltersReturn {
  const [tableFilters, setTableFilters] = useState<TableFilters>(getDefaultTableFilters())
  const [showTableFiltersPanel, setShowTableFiltersPanel] = useState(false)
  const [newSoftSkillFilter, setNewSoftSkillFilter] = useState("")
  const [newCertificationFilter, setNewCertificationFilter] = useState("")
  const [columnFilters, setColumnFilters] = useState<Record<string, string[] | unknown>>({
    position: [],
    company: [],
    location: [],
    scoreRange: [],
    bigFive: {
      openness: '',
      conscientiousness: '',
      extraversion: '',
      agreeableness: '',
      neuroticism: ''
    }
  })
  const [openFilterDropdown, setOpenFilterDropdown] = useState<string | null>(null)

  const resetFilters = useCallback(() => {
    setTableFilters(getDefaultTableFilters())
    setColumnFilters({})
    setNewSoftSkillFilter("")
    setNewCertificationFilter("")
    setOpenFilterDropdown(null)
  }, [])

  const hasActiveFilters =
    tableFilters.statuses.length > 0 ||
    tableFilters.tags.length > 0 ||
    tableFilters.seniorityLevels.length > 0 ||
    tableFilters.skills.length > 0 ||
    tableFilters.locations.length > 0 ||
    tableFilters.remoteOnly ||
    tableFilters.hasEmail ||
    tableFilters.hasPhone ||
    tableFilters.isOpenToWork ||
    tableFilters.isDecisionMaker ||
    tableFilters.softSkills.length > 0 ||
    tableFilters.certifications.length > 0

  return {
    tableFilters,
    setTableFilters,
    showTableFiltersPanel,
    setShowTableFiltersPanel,
    newSoftSkillFilter,
    setNewSoftSkillFilter,
    newCertificationFilter,
    setNewCertificationFilter,
    columnFilters,
    setColumnFilters,
    openFilterDropdown,
    setOpenFilterDropdown,
    resetFilters,
    hasActiveFilters,
  }
}
