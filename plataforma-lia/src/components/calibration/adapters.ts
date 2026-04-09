/**
 * Adapter functions to normalize different candidate shapes into NormalizedCandidate.
 * - fromAgentStudio: CalibrationCardModal inline type (snake_case, API data)
 * - fromExpandedChat: CalibrationProfileModal type (camelCase, expanded-chat/types)
 */

import type {
  NormalizedCandidate,
  NormalizedExperience,
  NormalizedEducation,
  NormalizedMatchCriterion,
  MatchLevel,
} from "./types"
import type { CalibrationCandidate as ExpandedChatCandidate } from "@/components/expanded-chat/types"

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

// ---------- Expanded Chat shape (camelCase) ----------

export function fromExpandedChat(c: ExpandedChatCandidate): NormalizedCandidate {
  const matchLevel = (isMatch: boolean): MatchLevel => isMatch ? "good" : "no"

  return {
    id: c.id,
    name: c.name,
    avatarUrl: c.photoUrl,
    linkedinUrl: c.linkedinUrl,
    currentTitle: c.currentRole,
    currentCompany: c.currentCompany,
    location: c.location,
    totalExperience: c.totalExperience,
    skills: c.additionalSkills?.slice(0, 8) ?? [],
    experiences: (c.experiences ?? []).map((exp) => ({
      id: exp.id,
      title: exp.role,
      company: exp.company,
      period: exp.period,
      durationLabel: exp.duration,
      isPromotion: exp.isPromotion,
      skills: exp.skills,
    })),
    education: (c.educationHistory ?? []).map((edu) => ({
      id: edu.id,
      institution: edu.institution,
      degree: edu.degree,
      field: edu.field,
      period: edu.period,
    })),
    matchCriteria: (c.matchCriteria ?? []).map((mc) => ({
      id: mc.id,
      criterion: mc.criteria,
      match: matchLevel(mc.isMatch),
      explanation: mc.explanation,
    })),
  }
}
