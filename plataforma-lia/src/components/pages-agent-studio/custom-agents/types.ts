/**
 * Agent Studio — Shared TypeScript types
 * Mirrors backend schemas (app/schemas/custom_agent.py + agent_deployment.py)
 */

export type AgentCategory = "screening" | "sourcing" | "communication" | "analytics" | "job_management" | "automation" | "general"

/**
 * T5b UX Transformação 5 — vertical industry for template specialization.
 * `null` means generic template (no industry specialization).
 */
export type AgentVertical = "tech" | "health" | "education" | "retail" | null

export type ContextLevel = "full" | "standard" | "minimal"

export type AgentStatus = "draft" | "pending_approval" | "active" | "paused" | "archived"

export type ApprovalStatus = "pending" | "approved" | "rejected"

export interface AgentVersionSummary {
  id: string
  agent_id: string
  version: number
  changed_fields: string[]
  change_reason: string | null
  changed_by: string
  created_at: string | null
}

export interface AgentVersionDetail {
  id: string
  agent_id: string
  company_id: string
  version: number
  snapshot_data: Record<string, unknown>
  changed_fields: string[]
  change_reason: string | null
  changed_by: string
  created_at: string | null
}

export interface AgentApproval {
  id: string
  agent_id: string
  company_id: string
  requested_by: string
  reviewed_by: string | null
  status: ApprovalStatus
  review_notes: string | null
  requested_at: string | null
  reviewed_at: string | null
  agent_name?: string
}

export type DeploymentTargetType = "job" | "talent_pool" | "pipeline_stage" | "candidate_list"

export type TriggerMode = "manual" | "on_new_candidate" | "on_stage_change" | "scheduled"

export interface AgentTemplate {
  id: string
  name: string
  description: string
  category: AgentCategory
  domain: string
  icon: string
  system_prompt: string
  allowed_tools: string[]
  context_level: ContextLevel
  max_steps: number
  temperature: number
  enable_memory: boolean
  excluded_tools: string[]
  tags: string[]
  /** T5b UX Transformação 5: vertical industry specialization (null = generic). */
  vertical?: AgentVertical
  /**
   * T5b: optional industry-specific sub-prompts. Wizard pode usar como sugestão
   * de override do system_prompt quando o cliente escolhe vertical.
   */
  vertical_prompts?: {
    tech?: string
    health?: string
    education?: string
    retail?: string
  }
}

export interface CustomAgent {
  id: string
  company_id: string
  name: string
  role: string
  description: string | null
  system_prompt: string
  allowed_tools: string[]
  domain: string
  icon: string
  status: AgentStatus
  config: Record<string, unknown>
  max_steps: number
  temperature: number
  model_override: string | null
  enable_memory: boolean
  context_level: ContextLevel
  excluded_tools: string[]
  /** Sprint 3.7 W4-1: per-agent voice (PSTN, Twilio) flag — default OFF. Cliente toggles via UI. */
  voice_enabled?: boolean
  /** W-Channels-A (2026-05-23): per-agent VoIP (browser, Twilio VoIP + Gemini Live) — default OFF. */
  voip_enabled?: boolean
  /** W-Channels-A (2026-05-23): per-agent chat lateral interno — default ON (backward compat). */
  /** T5a UX Transformação 5: per-agent WhatsApp flag (default OFF). Cliente toggles via UI. */
  whatsapp_enabled?: boolean
  /** Workstream A 2026-05-23: per-agent capability "criar convite triagem" (default OFF). */
  triagem_invite_enabled?: boolean
  /** Sprint 7A unification (migration 202): category source-of-truth. Nullable até migration 204 (Sprint 8) tornar NOT NULL. */
  category?: AgentCategory | string | null
  /** Sprint 7A: runtime metrics agregadas (last_run_at, success_rate, etc). Populated assíncrono. */
  runtime_metrics?: Record<string, unknown>
  /** Sprint 7A: sourcing-only payload (criterios busca). null em agentes non-sourcing. */
  search_strategy?: Record<string, unknown> | null
  /** Sprint 7A: sourcing-only payload (config outreach). null em agentes non-sourcing. */
  outreach_config?: Record<string, unknown> | null
  /** Sprint 7A: back-reference para legacy sourcing_agents.id (drop em Sprint 8 / migration 204). */
  legacy_sourcing_agent_id?: string | null
  total_executions: number
  avg_confidence: number
  last_executed_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface AgentDeployment {
  id: string
  agent_id: string
  company_id: string
  target_type: DeploymentTargetType
  target_id: string
  target_name: string | null
  trigger_mode: TriggerMode
  schedule_cron: string | null
  is_active: boolean
  config_overrides: Record<string, unknown>
  execution_count: number
  candidates_processed: number
  last_execution_at: string | null
  created_by: string
  created_at: string | null
}

export interface CreateDeploymentRequest {
  target_type: DeploymentTargetType
  target_id: string
  target_name?: string
  trigger_mode?: TriggerMode
  schedule_cron?: string
  config_overrides?: Record<string, unknown>
}

/** i18n key suffixes for category display — use with t(`categories.${key}`) */
export const CATEGORY_KEYS: Record<AgentCategory, string> = {
  screening: "screening",
  sourcing: "sourcing",
  communication: "communication",
  analytics: "analytics",
  job_management: "jobManagement",
  automation: "automation",
  general: "general",
}

export const VALID_CATEGORIES = new Set<string>(Object.keys(CATEGORY_KEYS))

const CATEGORY_ALIASES: Record<string, AgentCategory> = {
  jobManagement: "job_management",
}

export function safeCategoryKey(domain: string | undefined | null): AgentCategory {
  if (!domain) return 'general'
  if (VALID_CATEGORIES.has(domain)) return domain as AgentCategory
  if (CATEGORY_ALIASES[domain]) return CATEGORY_ALIASES[domain]
  return 'general'
}

/** i18n key suffixes for tools — use with t(`tools.${key}`) */
export const TOOL_KEYS: string[] = [
  "search_candidates",
  "list_jobs",
  "get_job_details",
  "get_candidate_details",
  "get_pipeline_summary",
  "search_talent_pool",
  "get_analytics_summary",
  "get_company_culture",
  "get_evaluation_criteria",
  "summarize_context",
  "clarify_request",
  "move_candidate",
  "send_email",
  "update_candidate_field",
  "schedule_interview",
  "create_note",
]

/** i18n key suffixes for trigger modes — use with t(`triggers.${key}`) */
export const TRIGGER_KEYS: Record<TriggerMode, string> = {
  manual: "manual",
  on_new_candidate: "onNewCandidate",
  on_stage_change: "onStageChange",
  scheduled: "scheduled",
}

/** i18n key suffixes for deployment targets — use with t(`targets.${key}`) */
export const TARGET_KEYS: Record<DeploymentTargetType, string> = {
  job: "job",
  talent_pool: "talentPool",
  pipeline_stage: "pipelineStage",
  candidate_list: "candidateList",
}
