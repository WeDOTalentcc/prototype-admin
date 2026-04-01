import type { SearchCriterion } from "@/hooks/usePromptState"

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
  if (!filled) return { bg: "var(--gray-50)", text: "var(--gray-400)", iconBg: "var(--gray-400)" }
  switch (key) {
    case "job_title":
      return { bg: "var(--gray-50)", text: "var(--gray-600)", iconBg: "var(--gray-600)" }
    case "location":
      return { bg: "var(--gray-50)", text: "var(--wedo-purple)", iconBg: "var(--wedo-purple)" }
    case "skills":
      return { bg: "var(--gray-50)", text: "var(--status-success)", iconBg: "var(--wedo-green-light)" }
    case "years_experience":
      return { bg: "var(--gray-50)", text: "var(--status-warning)", iconBg: "var(--wedo-orange)" }
    case "industry":
      return { bg: "var(--gray-50)", text: "var(--gray-600)", iconBg: "var(--gray-600)" }
    default:
      return { bg: "var(--gray-50)", text: "var(--gray-600)", iconBg: "var(--gray-600)" }
  }
}

import type { BackendEntities } from "@/hooks/usePromptState"
import { ENTITY_LABELS } from "@/hooks/usePromptState"

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
