/**
 * TypeScript types for the Wizard WSI pipeline.
 * Mirrors backend state.py WizardStage + ws_stage_payload format.
 */

export type WizardStage =
  | "intake"
  | "jd_enrichment"
  | "bigfive"
  | "salary"
  | "competency"
  | "wsi_questions"
  | "eligibility"
  | "review"
  | "publish"
  | "calibration"
  | "handoff"
  | "done"

export type ScreeningMode = "compact" | "full"

/**
 * WebSocket message payload for wizard stages.
 * Sent by backend graph nodes via ws_stage_payload.
 */
export interface WizardStagePayload {
  type: "wizard_stage"
  stage: WizardStage
  data: Record<string, unknown>
  completeness: number // 0.0 to 1.0
  requires_approval: boolean
}

// --- Stage-specific data interfaces ---

export interface IntakeData {
  raw_input: string
}

export interface JdEnrichmentData {
  jd_raw: string
  jd_enriched: EnrichedJobDescription | null
  quality_score: number
  quality_warnings: string[]
}

export interface EnrichedJobDescription {
  titulo_padronizado: string
  senioridade_confirmada: string
  about_role: string
  responsabilidades: string[]
  skills_obrigatorias: TechnicalSkill[]
  skills_desejaveis: string[]
  competencias_comportamentais: BehavioralCompetency[]
  context_signals: ContextSignals
  alteracoes_realizadas: string[]
  fairness_corrections: string[]
  wsi_quality_score: number
  wsi_quality_warnings: string[]
}

export interface TechnicalSkill {
  skill: string
  contexto: string
  proficiency_level?: string
  market_demand_trend?: "rising" | "stable" | "declining"
}

export interface BehavioralCompetency {
  competencia: string
  contexto: string
  trait_big_five: "openness" | "conscientiousness" | "extraversion" | "agreeableness" | "stability"
}

export interface ContextSignals {
  nivel_autonomia: "baixo" | "medio" | "alto"
  nivel_inovacao: "baixo" | "medio" | "alto"
  nivel_pressao: "baixo" | "medio" | "alto"
  nivel_colaboracao: "baixo" | "medio" | "alto"
}

export interface BigFiveData {
  bigfive_profile: {
    openness: number
    conscientiousness: number
    extraversion: number
    agreeableness: number
    stability: number
    evidences: Record<string, string[]>
  } | null
  trait_rankings: TraitRanking[]
}

export interface TraitRanking {
  trait: string
  score: number
  rank: number
  weight: number
}

export interface SalaryData {
  salary_min: number | null
  salary_max: number | null
  salary_currency: string
  benefits: string[]
  benchmark: Record<string, unknown> | null
}

export interface CompetencyData {
  seniority: string
  seniority_display: string
  seniority_confidence: number
  seniority_signals: Array<{ signal: string; value: string; weight: number }>
  screening_mode: ScreeningMode | null
  distribution: { technical: number; behavioral: number } | null
  competency_tree: CompetencyItem[]
}

export interface CompetencyItem {
  skill: string
  contexto: string
  block: "technical" | "behavioral"
  trait?: string
}

export interface WsiQuestionsData {
  questions: ScreeningQuestion[]
  screening_mode: ScreeningMode | null
  distribution: { technical: number; behavioral: number } | null
}

export interface ScreeningQuestion {
  id?: string
  question: string
  ideal_answer: string
  scoring_rubric: Record<string, string>
  framework: "CBI" | "Bloom" | "Dreyfus" | "BigFive"
  block: "technical" | "behavioral"
  skill: string
  trait_ocean?: string
  bloom_level?: number
  dreyfus_level?: number
  weight: number
  approved?: boolean
  edited_text?: string
}

export interface EligibilityData {
  questions: EligibilityQuestion[]
}

export interface EligibilityQuestion {
  id: string
  question: string
  required_answer: "yes" | "no"
  eliminatory: boolean
}

export interface ReviewData {
  readiness: {
    ready: boolean
    checks: Record<string, boolean>
    missing: string[]
  }
  defaults_applied: string[]
}

export interface PublishData {
  job_id: number | null
  platforms: string[]
  sourcing_mode: "local" | "global" | "hybrid" | null
  contact_channels: string[]
  share_link: string | null
  auto_screen: boolean
}

export interface CalibrationData {
  candidates: CalibrationCandidate[]
  threshold: number
  approved_count: number
  complete: boolean
}

export interface CalibrationCandidate {
  id: string
  name: string
  current_title: string
  current_company: string
  match_score: number
  match_criteria: Array<{ criterion: string; score: number; met: boolean }>
  decision?: "approved" | "rejected"
  reason?: string
}

export interface HandoffData {
  job_id: number | null
  handoff_url: string | null
  share_link: string | null
}

// --- Stage labels for UI ---

export const STAGE_LABELS: Record<WizardStage, string> = {
  intake: "Descricao da vaga",
  jd_enrichment: "Enriquecimento do JD",
  bigfive: "Perfil Big Five",
  salary: "Salario e beneficios",
  competency: "Competencias e triagem",
  wsi_questions: "Perguntas WSI",
  eligibility: "Elegibilidade",
  review: "Revisao final",
  publish: "Publicacao",
  calibration: "Calibracao",
  handoff: "Pagina da vaga",
  done: "Concluido",
}

export const STAGE_ORDER: WizardStage[] = [
  "intake", "jd_enrichment", "bigfive", "salary", "competency",
  "wsi_questions", "eligibility", "review", "publish", "calibration",
  "handoff", "done",
]
