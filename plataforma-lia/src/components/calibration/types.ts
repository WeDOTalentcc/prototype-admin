/**
 * Shared calibration types — normalized interface consumed by CalibrationCandidateCard.
 * Each caller (CalibrationCardModal, CalibrationProfileModal) adapts its own
 * data model into this shape via adapter functions exported from ./adapters.ts.
 */

// ---------- Normalized Match Criterion ----------

export type MatchLevel = "good" | "partial" | "no"

export interface NormalizedMatchCriterion {
  id: string
  criterion: string
  match: MatchLevel
  explanation: string
}

// ---------- Normalized Experience ----------

export interface NormalizedExperience {
  id: string
  title: string
  company: string
  period: string
  durationLabel: string
  description?: string
  isCurrent?: boolean
  isPromotion?: boolean
  skills?: string[]
}

// ---------- Normalized Education ----------

export interface NormalizedEducation {
  id: string
  institution: string
  degree: string
  field: string
  period?: string
}

// ---------- Normalized Candidate ----------

export interface NormalizedCandidate {
  id: string
  name: string
  avatarUrl?: string
  linkedinUrl?: string
  currentTitle: string
  currentCompany: string
  location: string
  totalExperience: string
  skills: string[]
  experiences: NormalizedExperience[]
  education: NormalizedEducation[]
  matchCriteria: NormalizedMatchCriterion[]
}
