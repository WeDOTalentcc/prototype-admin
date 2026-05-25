/**
 * PoolAgentAssignment — types canonical Sprint 7B-1.
 *
 * Espelha `lia-agent-system/app/schemas/pool_agent_assignment.py` (Sub-sprint 7A).
 * Single source of truth no frontend para a entidade M2M
 * `pool_agent_assignments` (custom_agents × talent_pools).
 *
 * Endpoints canonical (via proxy Next):
 *   GET    /api/backend-proxy/talent-pools/:id/agents
 *   POST   /api/backend-proxy/talent-pools/:id/agents
 *   PATCH  /api/backend-proxy/talent-pools/:id/agents/:assignmentId
 *   DELETE /api/backend-proxy/talent-pools/:id/agents/:assignmentId
 *   POST   /api/backend-proxy/talent-pools/:id/agents/:assignmentId/run
 */

/** Tipo de agendamento do assignment. `cron`/`event_driven` ativos em Sprint 7C. */
export type ScheduleType = "on_demand" | "cron" | "event_driven"

/** Status do assignment. UI cliente edita active↔paused; outros são read-only. */
export type AssignmentStatus = "active" | "paused" | "completed" | "error"

/** Status do último run (informativo — populado pelo Celery em 7C). */
export type LastRunStatus = "queued" | "running" | "success" | "error" | null

/**
 * Estrutura canonical persistida. `custom_agent_name`/`custom_agent_category`
 * são enriched no list endpoint (single round-trip in-memory join), portanto
 * podem vir `null` em respostas de mutation que não façam enrichment.
 */
export interface PoolAgentAssignment {
  id: string
  talent_pool_id: string
  custom_agent_id: string
  /** Enriched no GET list — pode vir null em POST/PATCH responses. */
  custom_agent_name: string | null
  custom_agent_category: string | null
  status: AssignmentStatus
  schedule_type: ScheduleType
  schedule_config: Record<string, unknown>
  config_overrides: Record<string, unknown>
  last_run_at: string | null
  last_run_status: LastRunStatus
  runtime_metrics: Record<string, unknown>
  created_at: string
  updated_at: string
  created_by: string
}

/** Payload canonical de criação (POST). `company_id` NUNCA vai no body — vem do JWT. */
export interface PoolAgentAssignmentCreatePayload {
  custom_agent_id: string
  schedule_type?: ScheduleType
  schedule_config?: Record<string, unknown>
  config_overrides?: Record<string, unknown>
}

/** Payload canonical de update (PATCH). Todos os campos são opcionais. */
export interface PoolAgentAssignmentUpdatePayload {
  status?: Extract<AssignmentStatus, "active" | "paused">
  schedule_type?: ScheduleType
  schedule_config?: Record<string, unknown>
  config_overrides?: Record<string, unknown>
}

/** Resposta canonical do endpoint `/run` (202 Accepted). Full impl em 7C. */
export interface DispatchOnDemandResponse {
  status: "queued"
  assignment_id: string
  sprint?: string
}
