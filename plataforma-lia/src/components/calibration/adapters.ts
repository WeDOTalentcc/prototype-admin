/**
 * Adapter functions to normalize different candidate shapes into NormalizedCandidate.
 * - fromAgentStudio: CalibrationCardModal inline type (snake_case, API data)
 *
 * The legacy `fromExpandedChat` adapter was removed alongside the deprecated
 * `expanded-chat-modal` surface (Task #860 — A-01 / A-10). Calibration is now
 * driven entirely from snake_case API payloads via `fromAgentStudio`.
 */

import type {
  NormalizedCandidate,
} from "./types"

// ---------- Agent Studio shape (snake_case) ----------

interface AgentStudioExperience {
  title: string
  company: string
  start_date: string
  end_date: string | null
  duration_years: number
  description: string
  is_current: boolean
}

interface AgentStudioEducation {
  institution: string
  degree: string
  field: string
}

interface AgentStudioMatchCriterion {
  criterion: string
  match: "good" | "partial" | "no"
  explanation: string
}

export interface AgentStudioCandidate {
  id: string
  name: string
  current_title: string
  current_company: string
  location: string
  avatar_url: string | null
  total_experience_years: number
  skills: string[]
  experiences: AgentStudioExperience[]
  education: AgentStudioEducation[]
  match_criteria: AgentStudioMatchCriterion[]
}

export function fromAgentStudio(c: AgentStudioCandidate): NormalizedCandidate {
  return {
    id: c.id,
    name: c.name,
    avatarUrl: c.avatar_url ?? undefined,
    currentTitle: c.current_title,
    currentCompany: c.current_company,
    location: c.location,
    totalExperience: `${c.total_experience_years}a`,
    skills: c.skills ?? [],
    experiences: (c.experiences ?? []).map((exp, i) => ({
      id: `exp-${i}`,
      title: exp.title,
      company: exp.company,
      period: `${exp.start_date} \u2013 ${exp.end_date || "Atual"}`,
      durationLabel: exp.duration_years > 0 ? `${exp.duration_years}a` : "",
      description: exp.description?.slice(0, 150) || undefined,
      isCurrent: exp.is_current,
    })),
    education: (c.education ?? []).map((edu, i) => ({
      id: `edu-${i}`,
      institution: edu.institution,
      degree: edu.degree,
      field: edu.field,
    })),
    matchCriteria: (c.match_criteria ?? []).map((mc, i) => ({
      id: `mc-${i}`,
      criterion: mc.criterion,
      match: mc.match,
      explanation: mc.explanation,
    })),
  }
}
