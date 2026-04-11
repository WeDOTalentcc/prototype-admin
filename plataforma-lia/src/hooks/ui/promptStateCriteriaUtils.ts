import type { SearchCriterion } from "@/hooks/ui/usePromptState"

const KNOWN_LOCATIONS = [
  "são paulo", "rio de janeiro", "belo horizonte", "curitiba",
  "porto alegre", "brasília", "sp", "rj",
]

const KNOWN_SKILLS = [
  "python", "react", "node", "java", "typescript", "javascript", "aws",
  "docker", "kubernetes", "sql", "figma", "ux", "ui", "angular", "vue",
  "spring", "django", "flask", "fastapi",
]

const KNOWN_LANGUAGES = [
  "inglês", "espanhol", "francês", "alemão", "english", "spanish",
  "fluente", "avançado",
]

const SENIORITY_MAP: Record<string, string> = {
  "sênior": "Sênior",
  "senior": "Sênior",
  "pleno": "Pleno",
  "júnior": "Júnior",
  "junior": "Júnior",
  "lead": "Tech Lead",
  "tech lead": "Tech Lead",
  "especialista": "Especialista",
  "staff": "Staff",
}

/**
 * Pure function that extracts SearchCriterion items from a free-text query.
 * Extracted from usePromptState to keep that file under 1000 lines while
 * making the extraction logic independently testable.
 */
export function extractCriteriaFromText(
  query: string,
  prev: SearchCriterion[]
): SearchCriterion[] {
  const queryLower = query.toLowerCase().trim()
  const newlyExtracted: SearchCriterion[] = []

  for (const loc of KNOWN_LOCATIONS) {
    if (queryLower.includes(loc)) {
      const id = `loc-${loc.replace(/\s/g, "-")}`
      if (!prev.find(c => c.id === id)) {
        newlyExtracted.push({
          id, type: "location", label: "Localização",
          value: loc.charAt(0).toUpperCase() + loc.slice(1), active: true,
        })
      }
      break
    }
  }

  const expMatch = queryLower.match(/(\d+)\+?\s*anos?|(\d+)\+?\s*years?/)
  if (expMatch) {
    const years = expMatch[1] || expMatch[2]
    const id = `exp-${years}`
    if (!prev.find(c => c.id === id)) {
      newlyExtracted.push({
        id, type: "experience", label: "Experiência",
        value: `${years}+ anos`, active: true,
      })
    }
  }

  for (const skill of KNOWN_SKILLS) {
    if (queryLower.includes(skill)) {
      const id = `skill-${skill}`
      if (!prev.find(c => c.id === id)) {
        newlyExtracted.push({
          id, type: "skills", label: "Skills",
          value: skill.charAt(0).toUpperCase() + skill.slice(1), active: true,
        })
      }
    }
  }

  for (const lang of KNOWN_LANGUAGES) {
    if (queryLower.includes(lang)) {
      const id = `lang-${lang}`
      if (!prev.find(c => c.id === id)) {
        newlyExtracted.push({
          id, type: "language", label: "Idioma",
          value: lang.charAt(0).toUpperCase() + lang.slice(1), active: true,
        })
      }
      break
    }
  }

  for (const [key, value] of Object.entries(SENIORITY_MAP)) {
    if (queryLower.includes(key)) {
      const id = `seniority-${key.replace(/\s/g, "-")}`
      if (!prev.find(c => c.id === id)) {
        newlyExtracted.push({
          id, type: "job_title", label: "Senioridade", value, active: true,
        })
      }
      break
    }
  }

  const manuallyModified = prev.filter(c => !c.active)
  const existingActive = prev.filter(c => c.active)
  const merged = [...existingActive, ...manuallyModified]
  for (const newCrit of newlyExtracted) {
    if (!merged.find(c => c.id === newCrit.id)) {
      merged.push(newCrit)
    }
  }
  return merged
}

/** Pure colour lookup for search tag badges — no React state needed. */
export function getTagColors(key: string, filled: boolean) {
  if (!filled) return { bg: "var(--lia-bg-secondary)", text: "var(--lia-text-tertiary)", iconBg: "var(--lia-text-tertiary)" }
  switch (key) {
    case "job_title":
      return { bg: "var(--lia-bg-secondary)", text: "var(--lia-text-secondary)", iconBg: "var(--lia-text-secondary)" }
    case "location":
      return { bg: "var(--lia-bg-secondary)", text: "var(--wedo-purple)", iconBg: "var(--wedo-purple)" }
    case "skills":
      return { bg: "var(--lia-bg-secondary)", text: "var(--status-success)", iconBg: "var(--wedo-green-light)" }
    case "years_experience":
      return { bg: "var(--lia-bg-secondary)", text: "var(--status-warning)", iconBg: "var(--wedo-orange)" }
    case "industry":
      return { bg: "var(--lia-bg-secondary)", text: "var(--lia-text-secondary)", iconBg: "var(--lia-text-secondary)" }
    default:
      return { bg: "var(--lia-bg-secondary)", text: "var(--lia-text-secondary)", iconBg: "var(--lia-text-secondary)" }
  }
}

import type { BackendEntities } from "@/hooks/ui/usePromptState"
import { ENTITY_LABELS } from "@/hooks/ui/usePromptState"

/**
 * Maps parsed backend entities to SearchCriterion array.
 * Pure function, extracted from usePromptState.parseEntitiesFromQuery.
 */
export function mapEntitiesToCriteria(entities: BackendEntities): SearchCriterion[] {
  const newCriteria: SearchCriterion[] = []
  let idx = 0
  if (entities.job_title) {
    newCriteria.push({ id: `entity-job_title-${idx++}`, type: "job_title", label: ENTITY_LABELS.job_title, value: entities.job_title, active: true })
  }
  if (entities.location) {
    newCriteria.push({ id: `entity-location-${idx++}`, type: "location", label: ENTITY_LABELS.location, value: entities.location, active: true })
  }
  if (entities.years_experience) {
    newCriteria.push({ id: `entity-years_experience-${idx++}`, type: "years_experience", label: ENTITY_LABELS.years_experience, value: entities.years_experience, active: true })
  }
  if (entities.industry) {
    newCriteria.push({ id: `entity-industry-${idx++}`, type: "industry", label: ENTITY_LABELS.industry, value: entities.industry, active: true })
  }
  if (entities.skills && entities.skills.length > 0) {
    entities.skills.forEach((skill, skillIdx) => {
      newCriteria.push({ id: `entity-skills-${idx++}-${skillIdx}`, type: "skills", label: "Habilidade", value: skill, active: true })
    })
  }
  if (entities.seniority) {
    newCriteria.push({ id: `entity-seniority-${idx++}`, type: "seniority", label: ENTITY_LABELS.seniority, value: entities.seniority, active: true })
  }
  if (entities.company) {
    newCriteria.push({ id: `entity-company-${idx++}`, type: "company", label: ENTITY_LABELS.company, value: entities.company, active: true })
  }
  return newCriteria
}

/**
 * Extracts display tags from an archetype's criteria object.
 * Pure function, extracted from usePromptState.openEditArchetype.
 */
export function extractTagsFromArchetypeCriteria(criteria: Record<string, unknown>): string[] {
  const tags: string[] = []
  if (criteria.job_title) tags.push(String(criteria.job_title))
  if (criteria.location) tags.push(String(criteria.location))
  if (criteria.seniority) tags.push(String(criteria.seniority))
  if (criteria.industry) tags.push(String(criteria.industry))
  if (criteria.skills && Array.isArray(criteria.skills)) tags.push(...(criteria.skills as string[]))
  return tags
}

import type { FileAnalysisResult } from "@/components/ui/file-upload-button"

/**
 * Extracts unique search keywords from a file analysis result.
 * Pure function extracted from usePromptState.handleFileAnalyzed.
 */
export function extractKeywordsFromFileAnalysis(analysis: FileAnalysisResult): string[] {
  if (!analysis.success) return []
  const keywords: string[] = []
  if (analysis.keywords && analysis.keywords.length > 0) {
    keywords.push(...analysis.keywords.slice(0, 5))
  }
  if (analysis.entities) {
    if (analysis.entities.skills) keywords.push(...analysis.entities.skills.slice(0, 3))
    if (analysis.entities.job_titles) keywords.push(...analysis.entities.job_titles.slice(0, 2))
    if (analysis.entities.locations) keywords.push(...analysis.entities.locations.slice(0, 2))
  }
  return [...new Set(keywords)]
}

import type { SearchFilters } from "@/components/search/advanced-filters-modal"

/**
 * Builds a backend search spec object from parsed entities and advanced filters.
 * Pure function extracted from usePromptState.buildSearchSpec.
 */
export function buildSearchSpecFromParsed(
  parsedEntities: BackendEntities,
  advancedFilters: SearchFilters
): Record<string, unknown> {
  const spec: Record<string, unknown> = {}
  if (parsedEntities.job_title) spec.job_title = parsedEntities.job_title
  if (parsedEntities.location) spec.location = parsedEntities.location
  if (parsedEntities.seniority) spec.seniority = parsedEntities.seniority
  if (parsedEntities.industry) spec.industry = parsedEntities.industry
  if (parsedEntities.company) spec.company = parsedEntities.company
  if (parsedEntities.years_experience) spec.years_experience = parsedEntities.years_experience
  if (parsedEntities.skills && parsedEntities.skills.length > 0) spec.skills = parsedEntities.skills
  const filtersRec = advancedFilters as Record<string, Record<string, unknown>>
  if (filtersRec.locations?.locations && Array.isArray(filtersRec.locations.locations) && (filtersRec.locations.locations as unknown[]).length > 0) {
    spec.locations = filtersRec.locations.locations as string[]
  }
  if (advancedFilters.job?.titles && advancedFilters.job.titles.length > 0) spec.job_titles = advancedFilters.job.titles
  if (advancedFilters.job?.levels && advancedFilters.job.levels.length > 0) spec.seniority_levels = advancedFilters.job.levels
  if (advancedFilters.skills?.skillItems && advancedFilters.skills.skillItems.length > 0) {
    spec.required_skills = advancedFilters.skills.skillItems.map((s: { name: string }) => s.name)
  }
  if (advancedFilters.languages?.languages && advancedFilters.languages.languages.length > 0) spec.languages = advancedFilters.languages.languages
  if (advancedFilters.general?.minExperience) spec.years_experience_min = advancedFilters.general.minExperience
  if (advancedFilters.general?.maxExperience) spec.years_experience_max = advancedFilters.general.maxExperience
  return spec
}

/**
 * Generates a human-readable archetype name from parsed entities.
 * Pure function extracted from usePromptState.generateArchetypeName.
 */
export function generateArchetypeNameFromEntities(parsedEntities: BackendEntities): string | undefined {
  const nameParts: string[] = []
  if (parsedEntities.job_title) nameParts.push(parsedEntities.job_title)
  if (parsedEntities.seniority) nameParts.push(parsedEntities.seniority)
  if (parsedEntities.location) nameParts.push(parsedEntities.location)
  if (parsedEntities.skills && parsedEntities.skills.length > 0) {
    nameParts.push(parsedEntities.skills.slice(0, 2).join("/"))
  }
  return nameParts.length > 0 ? nameParts.slice(0, 3).join(" - ") : undefined
}

/** Returns true if the entity set has at least one field populated. */
export function hasParsedEntitiesData(parsedEntities: BackendEntities): boolean {
  return !!(
    parsedEntities.job_title || parsedEntities.location || parsedEntities.seniority ||
    parsedEntities.industry || parsedEntities.company || parsedEntities.years_experience ||
    (parsedEntities.skills && parsedEntities.skills.length > 0)
  )
}
