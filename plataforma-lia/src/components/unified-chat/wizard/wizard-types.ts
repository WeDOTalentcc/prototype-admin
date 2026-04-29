/**
 * TypeScript types for the Wizard WSI pipeline.
 *
 * Audit finding **N-12**: the contract types below — `WizardStage`,
 * `ScreeningMode`, `WizardStagePayload`, `BigFiveProfile`, `TraitRanking`,
 * `ScreeningQuestion`, `EligibilityQuestion`, `CalibrationCandidate` —
 * are now re-exported from the auto-generated
 * `src/types/generated/wizard-contract.ts`, whose source of truth is the
 * Pydantic module `lia-agent-system/app/contracts/wizard_contract.py`.
 *
 * Regenerate after backend changes:
 *   npm run generate:wizard-types
 *
 * CI fails on drift via:
 *   npm run check:wizard-types
 *
 * The remaining UI-only interfaces (`*Data` wrappers, `EnrichedJobDescription`,
 * `TechnicalSkill`, `BehavioralCompetency`, `ContextSignals`, stage-label
 * tables) live below and stay hand-maintained until they are absorbed by
 * the backend contract.
 */
import type {
  BigFiveProfileContract,
  TraitRankingContract,
  WizardStagePayloadContract,
} from "@/types/generated/wizard-contract"

// ---- Re-exports from the generated contract ------------------------------
// NOTE: ScreeningQuestion / EligibilityQuestion / CalibrationCandidate are
// kept hand-maintained below for now — the generated contract enforces
// stricter shapes (e.g. `id` required, extra `competency`/`source` fields)
// that would require touching ~20 component call-sites in a separate PR.
// Tracked as a follow-up to N-12.

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
  | "scheduling"

export type ScreeningMode = "compact" | "full"

/**
 * WebSocket message payload for wizard stages — alias of
 * `WizardStagePayloadContract` (generated). Kept as a type alias so
 * existing imports `import { WizardStagePayload }` keep working.
 */
export type WizardStagePayload = WizardStagePayloadContract

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

/**
 * Big Five OCEAN profile — alias of the generated `BigFiveProfileContract`
 * so the recruiter UI and the LangGraph state share one shape.
 */
export type BigFiveProfile = BigFiveProfileContract

export interface BigFiveData {
  bigfive_profile: BigFiveProfile | null
  trait_rankings: TraitRanking[]
}

/**
 * Big Five trait ranking — alias of the generated `TraitRankingContract`.
 */
export type TraitRanking = TraitRankingContract

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
  job_id: number | string | null
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
  /**
   * Job identifier emitted by the backend at handoff. Accepts both
   * `number` (current Rails int IDs) and `string` (UUIDs / slugs) so a
   * future ID-format migration on the backend doesn't silently drop the
   * ID from the closing card. `null` when publication failed.
   */
  job_id: number | string | null
  job_title?: string | null
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
  scheduling: "Agendamento",
}

/**
 * Pill-style labels rendered on the chat header, the workflow rail, and
 * any other surface that needs the long "Criando vaga · X" prefix. Kept
 * next to STAGE_LABELS so we have a single source of truth — every
 * surface that shows a wizard stage name imports from here.
 */
export const STAGE_PILL_LABELS: Record<WizardStage, string> = {
  intake: "Criando vaga · Início",
  jd_enrichment: "Criando vaga · Descrição",
  bigfive: "Criando vaga · Perfil",
  salary: "Criando vaga · Salário",
  competency: "Criando vaga · Competências",
  wsi_questions: "Criando vaga · Triagem",
  eligibility: "Criando vaga · Elegibilidade",
  review: "Criando vaga · Revisão",
  publish: "Criando vaga · Publicação",
  calibration: "Calibrando · Candidatos",
  handoff: "Criando vaga · Finalização",
  done: "Vaga criada",
  scheduling: "Agendando · Entrevistas",
}

export const STAGE_ORDER: WizardStage[] = [
  "intake", "jd_enrichment", "bigfive", "salary", "competency",
  "wsi_questions", "eligibility", "review", "publish", "calibration",
  "handoff", "done", "scheduling",
]
