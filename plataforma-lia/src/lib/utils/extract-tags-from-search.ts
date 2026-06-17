import type { SearchSpec } from "@/lib/api/candidate-search"

export interface ExtractedTag {
  type: string
  label: string
  value: string
}

const SENIORITY_LABELS: Record<string, string> = {
  junior: "Júnior",
  pleno: "Pleno",
  senior: "Sênior",
  lead: "Lead",
  manager: "Gerente",
  director: "Diretor",
  executive: "Executivo",
}

const WORK_MODEL_LABELS: Record<string, string> = {
  remote: "Remoto",
  hybrid: "Híbrido",
  onsite: "Presencial",
  "on-site": "Presencial",
}

export function extractTagsFromSearchSpec(searchSpec: SearchSpec | null | undefined): ExtractedTag[] {
  if (!searchSpec) return []

  const tags: ExtractedTag[] = []

  if (searchSpec.job_title) {
    tags.push({ type: "job_title", label: "Cargo", value: searchSpec.job_title })
  }

  if (searchSpec.seniority) {
    const seniorityLabel = SENIORITY_LABELS[searchSpec.seniority.toLowerCase()] || searchSpec.seniority
    tags.push({ type: "seniority", label: "Senioridade", value: seniorityLabel })
  }

  const location = searchSpec.location || 
    [searchSpec.location_city, searchSpec.location_state, searchSpec.location_country]
      .filter(Boolean)
      .join(", ")
  if (location) {
    tags.push({ type: "location", label: "Localização", value: location })
  }

  if (searchSpec.years_experience) {
    tags.push({ type: "experience", label: "Experiência", value: searchSpec.years_experience })
  } else if (searchSpec.years_experience_min || searchSpec.years_experience_max) {
    const min = searchSpec.years_experience_min
    const max = searchSpec.years_experience_max
    let experienceText = ""
    if (min && max) {
      experienceText = `${min}-${max} anos`
    } else if (min) {
      experienceText = `${min}+ anos`
    } else if (max) {
      experienceText = `até ${max} anos`
    }
    if (experienceText) {
      tags.push({ type: "experience", label: "Experiência", value: experienceText })
    }
  }

  const industry = searchSpec.industry || 
    (searchSpec.industries && searchSpec.industries.length > 0 ? searchSpec.industries[0] : null)
  if (industry) {
    tags.push({ type: "industry", label: "Setor", value: industry })
  }

  const allSkills = [
    ...(searchSpec.skills || []),
    ...(searchSpec.required_skills || []),
    ...(searchSpec.preferred_skills || []),
  ]
  const uniqueSkills = [...new Set(allSkills)]
  uniqueSkills.slice(0, 5).forEach((skill) => {
    tags.push({ type: "skill", label: "Habilidade", value: skill })
  })

  if (searchSpec.company) {
    tags.push({ type: "company", label: "Empresa", value: searchSpec.company })
  }

  if (searchSpec.companies && searchSpec.companies.length > 0) {
    searchSpec.companies.slice(0, 3).forEach((company) => {
      tags.push({ type: "company", label: "Empresa", value: company })
    })
  }

  if (searchSpec.work_model) {
    const workModelLabel = WORK_MODEL_LABELS[searchSpec.work_model.toLowerCase()] || searchSpec.work_model
    tags.push({ type: "work_model", label: "Modelo", value: workModelLabel })
  }

  if (searchSpec.education_level) {
    tags.push({ type: "education", label: "Educação", value: searchSpec.education_level })
  }

  if (searchSpec.languages && searchSpec.languages.length > 0) {
    searchSpec.languages.slice(0, 3).forEach((lang) => {
      tags.push({ type: "language", label: "Idioma", value: lang })
    })
  }

  return tags
}

export function suggestArchetypeName(searchSpec: SearchSpec | null | undefined): string {
  if (!searchSpec) return "Novo Arquétipo"

  const parts: string[] = []

  if (searchSpec.job_title) {
    parts.push(searchSpec.job_title)
  }

  if (searchSpec.seniority) {
    const seniorityLabel = SENIORITY_LABELS[searchSpec.seniority.toLowerCase()] || searchSpec.seniority
    parts.push(seniorityLabel)
  }

  if (parts.length === 0) {
    if (searchSpec.skills && searchSpec.skills.length > 0) {
      parts.push(searchSpec.skills[0])
    } else if (searchSpec.required_skills && searchSpec.required_skills.length > 0) {
      parts.push(searchSpec.required_skills[0])
    } else if (searchSpec.industry) {
      parts.push(searchSpec.industry)
    }
  }

  if (parts.length === 0) {
    return "Novo Arquétipo"
  }

  return parts.join(" ")
}

export function extractIndustryFromSpec(searchSpec: SearchSpec | null | undefined): string {
  if (!searchSpec) return ""
  return searchSpec.industry || (searchSpec.industries && searchSpec.industries[0]) || ""
}

export function extractSeniorityFromSpec(searchSpec: SearchSpec | null | undefined): string {
  if (!searchSpec) return ""
  return searchSpec.seniority?.toLowerCase() || ""
}
