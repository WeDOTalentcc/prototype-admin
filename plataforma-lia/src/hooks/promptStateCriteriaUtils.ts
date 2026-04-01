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
