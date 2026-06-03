/**
 * candidate-card-data — pure helpers that normalize the backend candidate /
 * screening payloads into the plain data our chat-feed cards render.
 *
 * Mirrors the `wizard-plan-card.ts` philosophy: no React, no DOM, no i18n —
 * just defensive coercion of the canonical backend schemas so the cards are
 * trivial to unit-test and trivial to port to Vue/Vuetify later. The
 * presentation layer only ever consumes these typed shapes.
 *
 * Single sources of truth honored here:
 *   - Profile card  → a candidate record (search result / candidate row).
 *   - Evaluation card → `_build_screening_result` (cv_scoring_service.py),
 *     the shared schema produced by both `screen_candidate` (persisted) and
 *     `score_candidate_standalone` (dry-run, persisted=False).
 *
 * Color tiers reuse the canonical WSI visual tokens (`@/lib/wsi/visual`) — we
 * never duplicate score thresholds in the components.
 */
import { getWsiVisualState, type WsiVisualState } from "@/lib/wsi/visual"

/** `metadata.type` discriminators the chat-feed render switch keys on. */
export const CANDIDATE_PROFILE_CARD_TYPE = "candidate_profile"
export const CANDIDATE_EVALUATION_CARD_TYPE = "candidate_evaluation"

// ---------------------------------------------------------------------------
// Coercion primitives
// ---------------------------------------------------------------------------

function str(value: unknown): string | null {
  return typeof value === "string" && value.trim() !== "" ? value.trim() : null
}

function num(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function strArray(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value
    .map((entry) => str(entry))
    .filter((entry): entry is string => entry !== null)
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {}
}

// ---------------------------------------------------------------------------
// Card A — Candidate profile
// ---------------------------------------------------------------------------

export interface CandidateProfileCardData {
  candidateId: string | null
  name: string
  /** Current role / title. */
  role: string | null
  /** Current company / employer. */
  company: string | null
  location: string | null
  avatarUrl: string | null
  skills: string[]
  /** WSI score on the canonical 0-10 scale, when the candidate has one. */
  matchScore: number | null
  matchClassification: string | null
}

/**
 * Build the profile card data from a candidate record. Lenient on field
 * names (search results, candidate rows and enrichment payloads differ),
 * but returns `null` when there is no name to render — the card never shows
 * an anonymous candidate.
 */
export function buildCandidateProfileCard(
  raw: unknown,
): CandidateProfileCardData | null {
  if (!raw || typeof raw !== "object") return null
  const r = raw as Record<string, unknown>
  const name = str(r.name) ?? str(r.candidate_name)
  if (!name) return null
  return {
    candidateId: str(r.id) ?? str(r.candidate_id),
    name,
    role: str(r.role) ?? str(r.current_role) ?? str(r.title) ?? str(r.headline),
    company: str(r.company) ?? str(r.current_company) ?? str(r.employer),
    location: str(r.location) ?? str(r.city),
    avatarUrl: str(r.avatar_url) ?? str(r.avatarUrl) ?? str(r.photo_url),
    skills: strArray(r.skills),
    matchScore: num(r.wsi_score) ?? num(r.match_score) ?? num(r.score),
    matchClassification: str(r.classification) ?? str(r.wsi_classification),
  }
}

// ---------------------------------------------------------------------------
// Card B — Candidate evaluation (BARS / CV screening)
// ---------------------------------------------------------------------------

export interface CandidateEvaluationItem {
  requirement: string
  /** BARS level label (e.g. "Avançado"). */
  level: string | null
  points: number | null
  weightedPoints: number | null
  evidence: string | null
}

export interface CandidateEvaluationCardData {
  candidateId: string | null
  candidateName: string
  vacancyId: string | null
  jobTitle: string | null
  /** Rubric percentage on the backend's 0-99 scale. */
  rubricScore: number
  /** CV-fit indicator on the 0-5 scale (preliminary, CV-only). */
  cvFitScore: number | null
  cvFitClassification: string | null
  recommendation: string | null
  recommendationLabel: string | null
  subStatus: string | null
  strengths: string[]
  concerns: string[]
  reasoning: string | null
  evaluations: CandidateEvaluationItem[]
  evaluatedAt: string | null
  /** True when the result was written to a VacancyCandidate. */
  persisted: boolean
  /** True for dry-run scoring that was NOT persisted. */
  standalone: boolean
}

/**
 * Build the evaluation card data from the canonical `_build_screening_result`
 * schema. Returns `null` only when there is neither a name nor a score — i.e.
 * nothing meaningful to render.
 */
export function buildCandidateEvaluationCard(
  raw: unknown,
): CandidateEvaluationCardData | null {
  if (!raw || typeof raw !== "object") return null
  const r = raw as Record<string, unknown>
  const candidateName = str(r.candidate_name) ?? str(r.name)
  const rubricScore = num(r.rubric_score)
  if (!candidateName && rubricScore === null) return null

  const cvFit = asRecord(r.cv_fit)
  const rawEvals = Array.isArray(r.evaluations) ? r.evaluations : []
  const evaluations: CandidateEvaluationItem[] = rawEvals
    .map((entry): CandidateEvaluationItem | null => {
      const o = asRecord(entry)
      const requirement = str(o.requirement)
      if (!requirement) return null
      return {
        requirement,
        level: str(o.level),
        points: num(o.points),
        weightedPoints: num(o.weighted_points),
        evidence: str(o.evidence),
      }
    })
    .filter((entry): entry is CandidateEvaluationItem => entry !== null)

  const persisted = r.persisted === true
  return {
    candidateId: str(r.candidate_id) ?? str(r.id),
    candidateName: candidateName ?? "Candidato",
    vacancyId: str(r.vacancy_id),
    jobTitle: str(r.job_title),
    rubricScore: rubricScore ?? 0,
    cvFitScore: num(cvFit.cv_fit_score),
    cvFitClassification: str(cvFit.classification),
    recommendation: str(r.recommendation),
    recommendationLabel: str(r.recommendation_label) ?? str(r.recommendation),
    subStatus: str(r.sub_status),
    strengths: strArray(r.strengths),
    concerns: strArray(r.concerns),
    reasoning: str(r.reasoning),
    evaluations,
    evaluatedAt: str(r.evaluated_at),
    persisted,
    standalone: r.standalone === true || (r.standalone === undefined && !persisted),
  }
}

// ---------------------------------------------------------------------------
// Visual tier — reuses canonical WSI tokens, no thresholds duplicated
// ---------------------------------------------------------------------------

export type EvaluationTier = "success" | "warning" | "error"

export interface EvaluationTierClasses {
  tier: EvaluationTier
  text: string
  bg: string
  border: string
}

/**
 * The backend's own 3-tier pipeline decision (`sub_status`) is the canonical
 * source for the card color — it already encodes the recommendation cutoffs,
 * so the visual tier always matches the recommendation label shown to the
 * recruiter.
 */
const TIER_BY_SUB_STATUS: Record<string, EvaluationTier> = {
  cv_approved: "success",
  cv_analyzing: "warning",
  cv_rejected: "error",
}

const TIER_CLASSES: Record<EvaluationTier, Omit<EvaluationTierClasses, "tier">> = {
  success: { text: "text-status-success", bg: "bg-status-success/15", border: "border-status-success/30" },
  warning: { text: "text-status-warning", bg: "bg-status-warning/15", border: "border-status-warning/30" },
  error: { text: "text-status-error", bg: "bg-status-error/15", border: "border-status-error/30" },
}

/**
 * Resolve the card's color tier. Prefers the backend `sub_status`; falls back
 * to the canonical WSI visual state (scaling the 0-99 rubric onto the 0-10
 * WSI scale) so no score thresholds are ever duplicated in the frontend.
 */
export function evaluationTierClasses(data: {
  subStatus: string | null
  rubricScore: number
}): EvaluationTierClasses {
  let tier = data.subStatus ? TIER_BY_SUB_STATUS[data.subStatus] : undefined
  if (!tier) {
    const visual: WsiVisualState = getWsiVisualState(data.rubricScore / 10)
    if (visual.classification === "medio") {
      tier = "warning"
    } else if (
      visual.classification === "abaixo_da_media" ||
      visual.classification === "regular"
    ) {
      tier = "error"
    } else {
      tier = "success"
    }
  }
  return { tier, ...TIER_CLASSES[tier] }
}
