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
  // Sprint Pipeline Templates 2026-05-26 — Opção B (Paulo aprovou).
  // Stage formal entre jd_enrichment e bigfive; backend graph emite
  // wizard_stage com stage="pipeline_template" e o frontend renderiza
  // WizardPipelineTemplateStagePanel.
  | "pipeline_template"
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
 * Task #1070 — snapshot agregado de degradacao da IA emitido pelo backend
 * (`WizardFallbackTracker`). `scope="session"` quando a mesma sessao de wizard
 * acumulou >=3 fallbacks; `scope="tenant"` quando a empresa toda acumulou
 * >=5 fallbacks na ultima hora. `reason_breakdown` mostra a contagem por
 * causa (`timeout`/`provider_error`/`exception`).
 */
export interface AiDegradedMode {
  active: boolean
  scope: "session" | "tenant"
  count: number
  threshold: number
  window_seconds: number
  since: string
  reason_breakdown: Record<string, number>
}

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
  /**
   * Task #1065 — `true` quando o nó caiu no fallback determinístico
   * (timeout do LLM ou exception). Painel renderiza banner discreto
   * pedindo revisão extra antes da aprovação HITL.
   */
  jd_enrichment_used_fallback?: boolean
  /**
   * Task #1067 — root-cause label do fallback (`"timeout"`,
   * `"provider_error"`, `"exception"` ou `null`). Permite ao painel
   * exibir copy específica e oferecer "Tentar novamente" quando aplicável.
   */
  jd_enrichment_fallback_reason?: string | null
  /** Task #1070 — modo degradado agregado (sessao/tenant). */
  ai_degraded_mode?: AiDegradedMode | null
  /**
   * Canonical idle signal — backend emits this when raw_input is too thin
   * to enrich (e.g., recruiter said only "vamos abrir uma vaga" without JD).
   * Source: lia-agent-system/app/domains/job_creation/nodes/jd_enrichment.py:269.
   * Panel MUST render idle state (no badge, no loading timer) when true.
   */
  awaiting_jd_input?: boolean
  /**
   * Canonical message field — Task #1099 invariant of build_ws_stage_payload.
   * Carries the agent text for this stage (used by idle/loading copy fallback).
   */
  message?: string
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
  /** Task #1065 — `true` quando o nó caiu no fallback (timeout LLM → 0.5 neutro). */
  bigfive_used_fallback?: boolean
  /** Task #1067 — root-cause label do fallback. */
  bigfive_fallback_reason?: string | null
  /** Task #1070 — modo degradado agregado (sessao/tenant). */
  ai_degraded_mode?: AiDegradedMode | null
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
  /** Task #1065 — `true` quando o benchmark fetch caiu em fallback (timeout). */
  salary_used_fallback?: boolean
  /** Task #1067 — root-cause label do fallback. */
  salary_fallback_reason?: string | null
  /** Task #1070 — modo degradado agregado (sessao/tenant). */
  ai_degraded_mode?: AiDegradedMode | null
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
  /** Task #1065 — `true` quando o nó caiu no fallback (timeout LLM → CBI mínimo). */
  wsi_questions_used_fallback?: boolean
  /** Task #1067 — root-cause label do fallback. */
  wsi_questions_fallback_reason?: string | null
  /** Task #1070 — modo degradado agregado (sessao/tenant). */
  ai_degraded_mode?: AiDegradedMode | null
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
  // PR-8 ONDA 3 / F-3.5: sourcing_mode escolhido no review (default null = fallback "local" no backend + warning).
  sourcing_mode?: "local" | "global" | "hybrid" | null
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
  // Sprint Pipeline Templates 2026-05-26 — Opção B.
  pipeline_template: "Pipeline · Template",
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
  // Sprint Pipeline Templates 2026-05-26 — Opção B (Paulo aprovou)
  pipeline_template: "Pipeline · Template",
  done: "Vaga criada",
  scheduling: "Agendando · Entrevistas",
}

export const STAGE_ORDER: WizardStage[] = [
  "intake", "jd_enrichment",
  // Sprint Pipeline Templates 2026-05-26 — Opção B (Paulo aprovou).
  // Stage formal entre jd_enrichment e bigfive.
  "pipeline_template",
  "bigfive", "salary", "competency",
  "wsi_questions", "eligibility", "review", "publish", "calibration",
  "handoff", "done", "scheduling",
]


// ============================================================================
// Pipeline Template Suggestion (Fase 3 — auto-suggest no wizard chat)
// ============================================================================
//
// Quando o backend (Phase 1.6) detecta department/seniority/job_family após
// jd_enrichment, ele emite um WizardStagePayload com `ui_action` extra +
// `data.templates: WizardPipelineTemplateSuggestion[]` (até top-3 ranked).
//
// O type WizardStagePayloadContract gerado tem `ui_action` ausente porque
// o contract Pydantic ainda não expõe esse campo opcional. Quando o
// generator regenerar, este alias pode ser absorvido.
//

export interface WizardPipelineTemplateSuggestion {
  template_id: string
  name: string
  description?: string | null
  stages_count: number
  /** Score 0-1 vindo do ranker do backend; UI formata como `${Math.round(score*100)}% match`. */
  score: number
}

/** Lista discriminada de ui_actions emitidos no payload do wizard. */
export type WizardUiAction = "suggest_pipeline_template"

/**
 * Payload completo do wizard incluindo o campo opcional `ui_action` que
 * acompanha sugestões discretas (não toma o controle do stage). Quando
 * presente, `data` carrega o shape correspondente à action.
 *
 * Exemplo (Phase 1.6 — pipeline template suggestion):
 * ```json
 * {
 *   "type": "wizard_stage",
 *   "stage": "jd_enrichment",
 *   "completeness": 0.45,
 *   "ui_action": "suggest_pipeline_template",
 *   "data": { "templates": [...] }
 * }
 * ```
 */
export type WizardStagePayloadWithUiAction = WizardStagePayload & {
  ui_action?: WizardUiAction | null
}

/** Shape de `data` quando `ui_action === "suggest_pipeline_template"`. */
export interface WizardPipelineTemplateSuggestionPayload {
  templates: WizardPipelineTemplateSuggestion[]
}
