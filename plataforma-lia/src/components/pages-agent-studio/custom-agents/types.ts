/**
 * Agent Studio — Shared TypeScript types
 * Mirrors backend schemas (app/schemas/custom_agent.py + agent_deployment.py)
 */

export type AgentCategory = "screening" | "sourcing" | "communication" | "analytics" | "job_management" | "automation"

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

/** Human-readable labels for category display */
export const CATEGORY_LABELS: Record<AgentCategory, string> = {
  screening: "Triagem",
  sourcing: "Captação",
  communication: "Comunicacao",
  analytics: "Analise",
  job_management: "Vagas",
  automation: "Automacao",
}

/** Human-readable labels for tools */
export const TOOL_LABELS: Record<string, string> = {
  search_candidates: "Buscar candidatos",
  list_jobs: "Listar vagas",
  get_job_details: "Ver detalhes da vaga",
  get_candidate_details: "Ver detalhes do candidato",
  get_pipeline_summary: "Resumo do funil",
  search_talent_pool: "Buscar no banco de talentos",
  get_analytics_summary: "Resumo de analytics",
  get_company_culture: "Cultura da empresa",
  get_evaluation_criteria: "Criterios de avaliacao",
  summarize_context: "Resumir contexto",
  clarify_request: "Pedir esclarecimento",
  move_candidate: "Mover candidato",
  send_email: "Enviar email",
  update_candidate_field: "Atualizar candidato",
  schedule_interview: "Agendar entrevista",
  create_note: "Criar anotacao",
}

export const TRIGGER_LABELS: Record<TriggerMode, string> = {
  manual: "Manual",
  on_new_candidate: "A cada novo candidato",
  on_stage_change: "Ao mudar de etapa",
  scheduled: "Agendado",
}

export const TARGET_LABELS: Record<DeploymentTargetType, string> = {
  job: "Vaga",
  talent_pool: "Banco de Talentos",
  pipeline_stage: "Etapa do Funil",
  candidate_list: "Lista de Candidatos",
}
