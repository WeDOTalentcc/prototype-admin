/**
 * Interview / Triagem public-facing types.
 *
 * InterviewInfo is returned by GET /api/v1/triagem/{token} (via the
 * session config) and used by the InterviewLobby component to render
 * the consent + channel selection UI before the candidate begins.
 *
 * Phase 1a LGPD Consent (2026-06-11).
 */

export interface InterviewInfo {
  /** AI assistant name per tenant (from CompanyHiringPolicy.communication_rules.ai_persona.name). Default "Lia". */
  ai_name: string
  /** Whether the vacancy is part of an affirmative action programme. */
  is_affirmative: boolean
  /** Type of affirmative action (e.g. "PcD", "racial", "gender"). null when is_affirmative=false. */
  affirmative_type: string | null
  /** Whether a practice question will be shown before the real screening starts. */
  has_practice_question: boolean
  /** ISO 8601 timestamp — when the session link expires. */
  expires_at: string
  /** Company display name */
  company_name: string
  /** Company logo URL (may be null) */
  company_logo_url: string | null
  /** Job title for the vacancy */
  job_title: string
  /** Candidate display name */
  candidate_name: string
  /** Whether this company wants the WeDOTalent branding shown */
  show_wedotalent_branding?: boolean
  /** Privacy policy URL */
  privacy_policy_url: string
}
