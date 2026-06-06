// useCandidatesFilters.ts
// Derived filter-count helpers and clear/toggle actions that operate on the
// TableFilters, quickFilters and advancedFilters shapes.
// Pure logic — no UI components, no Next.js deps.

import type { TableFilters } from "@/hooks/candidates/use-candidate-filters"
import { getDefaultTableFilters } from "@/hooks/candidates/use-candidate-filters"

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AdvancedFilters {
  work_models: string[]
  skills: string[]
  companies: string[]
  locations: string[]
  job_titles: string[]
}

export const DEFAULT_ADVANCED_FILTERS: AdvancedFilters = {
  work_models: [],
  skills: [],
  companies: [],
  locations: [],
  job_titles: [],
}

// ── Count helpers ─────────────────────────────────────────────────────────────

export function getActiveTableFiltersCount(tableFilters: TableFilters): number {
  let count = 0
  count += tableFilters.statuses.length
  count += tableFilters.tags.length
  count += tableFilters.seniorityLevels.length
  count += tableFilters.workModels.length
  count += tableFilters.contractTypes.length
  count += tableFilters.locations.length
  count += tableFilters.sources.length
  // P2-1: filtros eliminatorios que faltavam no contador (aplicados em useCandidatesFilterSort)
  count += tableFilters.skills.length
  count += tableFilters.jobTitles.length
  count += tableFilters.companies.length
  count += tableFilters.industries.length
  if (tableFilters.minExperience !== undefined) count++
  if (tableFilters.maxExperience !== undefined) count++
  if (tableFilters.minScore !== undefined) count++
  if (tableFilters.maxScore !== undefined) count++
  if (tableFilters.minSalary !== undefined) count++
  if (tableFilters.maxSalary !== undefined) count++
  if (tableFilters.remoteOnly) count++
  if (tableFilters.hasEmail) count++
  if (tableFilters.hasPhone) count++
  if (tableFilters.hasLinkedin) count++
  if (tableFilters.hasGithub) count++
  if (tableFilters.hasPortfolio) count++
  count += tableFilters.softSkills.length
  count += tableFilters.certifications.length
  if (tableFilters.willingToRelocate !== null) count++
  if (tableFilters.mobility !== null) count++
  if (tableFilters.updatedAtFrom) count++
  if (tableFilters.updatedAtTo) count++
  if (tableFilters.lastContactedFrom) count++
  if (tableFilters.lastContactedTo) count++
  if (tableFilters.availabilityWindow) count++
  if (tableFilters.shortlistedDateFrom) count++
  if (tableFilters.shortlistedDateTo) count++
  if (tableFilters.shortlistedVacancyOrigin) count++
  if (tableFilters.placementDateFrom) count++
  if (tableFilters.placementDateTo) count++
  if (tableFilters.placementVacancyDestination) count++
  if (tableFilters.placementClientCompany) count++
  if (tableFilters.specificVacancyId) count++
  if (tableFilters.registrationDateFrom) count++
  if (tableFilters.registrationDateTo) count++
  return count
}

export function getActiveAdvancedFiltersCount(advancedFilters: AdvancedFilters): number {
  return Object.values(advancedFilters).reduce((sum, arr) => sum + arr.length, 0)
}

export function getActiveSearchFiltersCount(
  quickFilters: Set<string>,
  advancedFilters: AdvancedFilters,
): number {
  return quickFilters.size + getActiveAdvancedFiltersCount(advancedFilters)
}

// ── Toggle helper ─────────────────────────────────────────────────────────────

export function toggleTableFilterValue(
  prev: TableFilters,
  category: keyof TableFilters,
  value: string,
): TableFilters {
  const current = prev[category]
  if (!Array.isArray(current)) return prev
  return {
    ...prev,
    [category]: current.includes(value)
      ? current.filter(v => v !== value)
      : [...current, value],
  }
}
